#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""quick_wiki_lint.py — Quick 上 LLM Wiki 的确定性体检

比对两个数据源：vault 里的 markdown 文件 vs Quick 的 SQLite 库。
只读，从不写库 —— 直写会绕过 Quick 的索引更新、content_hash 校验和 token 计量。

用法:
    quick_wiki_lint.py                    # 全部检查，人类可读输出
    quick_wiki_lint.py --strict           # 有真问题时退出码 1
    quick_wiki_lint.py --json             # 机器可读
    quick_wiki_lint.py --vault ~/Other    # 指定 vault

为什么用脚本而不是让 agent 现场写：逻辑固定、结果可复现。
查询 bug 比数据故障常见得多，所以异常数字先怀疑查询写错。
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

# 抽取管线产的 relation，不对应 wikilink，数边时排除
EXTRACTED_RELATIONS = {
    "relatedTo", "mentions", "isPartOf", "about",
    "hasPart", "dependsOn", "author", "object",
}

# 元文件：出链是导航（目录条目/记录引用），不是知识关联
META_PAGES = {"index", "log"}

VALID_CATEGORIES = {"Concept", "Entity", "Source", "Synthesis"}
REQUIRED_FRONTMATTER = ("type", "tags", "status", "summary")

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---", re.S)


def parse_links(text: str) -> list[str]:
    """取 wikilink 目标名，做归一化。

    [[X|别名]] → X    [[X#章节]] → X    ![[X]] → X
    [[X\\|别名]] → X  ← markdown 表格里 | 必须转义成 \\|，正则切完会留下尾部反斜杠
    """
    return [m.rstrip("\\").strip() for m in WIKILINK_RE.findall(text)]


# ---------- SQL ----------
#
# 全部是常量，没有一处把外部数据拼进来。用三引号而不是隐式字符串拼接，
# 是为了让「这是一整条 SQL」在语法上就明确。

SQL_FOLDERS = """
    SELECT id, path, agent_allowed, rag_enabled, embed_mode, kg_enabled,
           rag_status, kg_status
    FROM folders WHERE path LIKE ? ORDER BY id
"""

SQL_FOLDER_PATHS = "SELECT path FROM folders"

# search_content.text_content 存的是「name + 空格 + summary」拼接
SQL_ENTITIES = """
    SELECT n.id, n.node_id, n.category, n.source, n.source_type, s.text_content
    FROM nodes n JOIN search_content s ON s.node = n.id
    WHERE n.node_class = 'entity'
"""

SQL_EDGES = """
    SELECT e.id, e.relation, e.source, e.properties,
           sf.text_content AS from_text, st.text_content AS to_text
    FROM edges e
    JOIN search_content sf ON sf.node = e.from_node
    JOIN search_content st ON st.node = e.to_node
"""

_SQL_FILES = """
    SELECT name, path, folder_id, rag_index_time, kg_index_time, modified_at
    FROM files WHERE folder_id IN (__IDS__)
"""


def files_sql(n: int) -> str:
    """把 IN (__IDS__) 展开成 n 个 ? 占位符。

    DB-API 不支持给 IN 绑定序列，占位符个数只能由代码生成。**插进 SQL 的
    只有 ? 本身**（个数来自 len()），实际值仍走参数绑定 —— 没有任何外部
    数据进入 SQL 文本。
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    return _SQL_FILES.replace("__IDS__", ",".join("?" * n))


# ---------- 数据采集 ----------

def _deny_attach(action: int, _a1, _a2, _db, _trigger) -> int:
    """拒绝 ATTACH / DETACH，其余放行。

    mode=ro 挡住了全部写操作（INSERT/UPDATE/DELETE/CREATE/DROP），但**不挡
    ATTACH DATABASE** —— 那能挂载并创建其它库文件，等于绕开只读。

    本模块的 SQL 全是字面量、参数走 ? 绑定，所以现在触发不了。加这道授权回调
    是为了让「只读」在引擎层面完整成立，而不是依赖「调用方不会写出坏 SQL」。
    """
    if action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH):
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def within(registered: str, vault: Path) -> bool:
    """注册路径是否等于 vault 或落在 vault 之内。"""
    try:
        rp = Path(os.path.expanduser(registered)).resolve()
    except (OSError, ValueError):
        return False
    return rp == vault or vault in rp.parents


def find_db(vault: Path) -> Path | None:
    """找到注册了这个 vault 的 profile 库。多 profile 时按注册路径判定。

    只认「vault 自身或其子目录被注册过」。用 `LIKE '<vault>%'` 是不够的 ——
    `--vault /` 会匹配到任何注册路径，挑出一个不相干的库。
    """
    pattern = os.path.expanduser(
        "~/.quickwork/profiles/*/knowledge_storage/knowledge_v1.db")
    for path in sorted(glob.glob(pattern)):
        try:
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            conn.set_authorizer(_deny_attach)
            rows = conn.execute(SQL_FOLDER_PATHS).fetchall()
            conn.close()
            if any(within(r[0], vault) for r in rows):
                return Path(path)
        except sqlite3.Error:
            continue
    return None


def read_pages(vault: Path) -> dict[str, dict]:
    """读 wiki/ 下全部 .md，解析 frontmatter 和 wikilink。key = 文件名去 .md"""
    pages = {}
    wiki = vault / "wiki"
    if not wiki.is_dir():
        return pages
    for path in sorted(wiki.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm_raw = ""
        m = FRONTMATTER_RE.match(text)
        if m:
            fm_raw = m.group(1)
        fm = {}
        for field in REQUIRED_FRONTMATTER:
            fmatch = re.search(rf"^{field}:\s*(.*)$", fm_raw, re.M)
            if fmatch:
                fm[field] = fmatch.group(1).strip()
        links = parse_links(text)
        pages[path.stem] = {
            "path": path,
            "rel": str(path.relative_to(vault)),
            "subdir": path.parent.name if path.parent != wiki else "",
            "frontmatter": fm,
            "links": links,
            "mtime": path.stat().st_mtime,
            "is_meta": path.stem in META_PAGES,
        }
    return pages


def read_db(db: Path, vault: Path) -> dict:
    """从库里读实体、边、文件索引状态。只读连接。"""
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.set_authorizer(_deny_attach)
    conn.row_factory = sqlite3.Row
    out: dict = {"entities": [], "edges": [], "files": [], "folders": []}

    out["folders"] = [dict(r)
                      for r in conn.execute(SQL_FOLDERS, (f"{vault}%",))]

    # 实体的 source 字段按建节点的路径不同而不同，不能用它筛：
    #   - kg_add 建的      → source='kg_agent'（工具标识，不是路径）
    #   - 抽取管线产的      → source=<注册的文件夹路径>
    #   - 其它来源（网页等）→ source='generated_processor' / 'other'
    # 所以取全部 entity，靠「名字能否匹配上本 vault 的文件」来归属。
    out["entities"] = [dict(r) for r in conn.execute(SQL_ENTITIES)]
    out["edges"] = [dict(r) for r in conn.execute(SQL_EDGES)]

    folder_ids = [f["id"] for f in out["folders"]]
    if folder_ids:
        out["files"] = [dict(r) for r in conn.execute(
            files_sql(len(folder_ids)), folder_ids)]

    conn.close()
    return out


def entity_name(text_content: str, known: set[str]) -> str:
    """从拼接的 text_content 里取出实体名 —— 最长匹配的已知页名优先。"""
    best = ""
    for name in known:
        if text_content.startswith(name) and len(name) > len(best):
            best = name
    return best


# ---------- 缺页候选：结构提取 + 前缀族 ----------

# 官方文档常把产品清单排成表格，抓取后被压平成「表头 + 连续短行」。
# 这类结构比语义可靠 —— 按「文中是否显著」抽会挑走反复出现的第三方名字，
# 漏掉表格里真正的族成员。按结构提取则一个不漏。
TABLE_HEADERS = [
    ("Service", "Description"),
    ("Name", "Description"),
    ("Feature", "Description"),
    ("组件", "说明"),
]


def _extract_from_tables(text: str) -> set[str]:
    """从被压平的表格里提第一列 —— 表头之后的连续短行。"""
    lines = [l.rstrip() for l in text.splitlines()]
    found: set[str] = set()
    for i in range(len(lines) - 2):
        head = (lines[i].strip(), lines[i + 1].strip())
        if head not in TABLE_HEADERS:
            continue
        # 表头之后：≤4 词、不以句号结尾、首字母大写 = 像是名字
        for l in lines[i + 3:]:
            sv = l.strip()
            if not sv:
                continue
            if sv.startswith("#") or sv.lower().startswith(("next step", "see also")):
                break
            w = sv.split()
            if len(w) <= 4 and not sv.endswith((".", "。", ":", "：")) and sv[:1].isupper():
                found.add(sv)
            elif len(found) >= 3 and len(w) <= 2:
                break
    return found


def _extract_from_lists(text: str) -> set[str]:
    """从 markdown 列表项里提「粗体开头」或「名字 —— 描述」形态的专名。"""
    found: set[str] = set()
    for m in re.finditer(r"^[-*]\s+\*\*([A-Z][^*]{2,40})\*\*", text, re.M):
        found.add(m.group(1).strip())
    for m in re.finditer(r"^[-*]\s+([A-Z][A-Za-z0-9 ]{2,34}?)\s+[—–-]{1,2}\s", text, re.M):
        found.add(m.group(1).strip())
    return found


def _prefix_family(name: str, pages: set[str]) -> list[str]:
    """和这个候选共享首词的已有页 —— 共享得越多，越像同族兄弟。"""
    head = name.split()[0] if name.split() else ""
    if not head:
        return []
    return sorted(p for p in pages if p.split()[:1] == [head] and p != name)


def _missing_page_candidates(vault: Path, pages: set[str]) -> list[dict]:
    """扫 raw/ 素材，找「被结构化列为族成员、但 wiki 里没有页」的名字。

    只用**结构信号**（表格第一列、列表项的粗体开头），不用语义、不用前缀猜测。
    前缀族启发式（和已有页共享首词）噪声压不住 —— 会产出重复词、截断词、
    语法碎片这类不可用的候选。结构提取的每一项都有据可查。

    发现归代码，判断归 agent —— 该不该建页、会不会变成 stub，由它定。
    """
    raw = vault / "raw"
    if not raw.is_dir():
        return []

    # 泛词和结构噪声：单词太短、纯泛称、带尾部标点的
    STOP = {"Agent", "Service", "Name", "Description", "Integrations",
            "Overview", "Next Steps", "See Also", "Note", "Example",
            "Feature", "Type", "Field", "Value", "Default"}

    hits: dict[str, dict] = {}
    for f in sorted(raw.rglob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        for name in _extract_from_tables(text) | _extract_from_lists(text):
            n = name.rstrip(":：,，.。")
            if n in pages or n in STOP or len(n) < 4:
                continue
            # 单个词且很短 —— 大概率是表头残留或泛称
            if len(n.split()) == 1 and len(n) < 8:
                continue
            rec = hits.setdefault(n, {"files": set(), "mentions": 0})
            rec["files"].add(f.name)
            rec["mentions"] = max(rec["mentions"], text.count(n))

    out = [{
        "name": n,
        "mentions": r["mentions"],
        "in_files": sorted(r["files"])[:3],
        "family": _prefix_family(n, pages)[:3],
    } for n, r in hits.items() if r["mentions"] >= 2]

    out.sort(key=lambda x: (-len(x["family"]), -x["mentions"], x["name"]))
    return out[:20]


# ---------- 检查项 ----------

def run_checks(vault: Path, pages: dict, db_data: dict | None,
               db_path: Path | None = None) -> list[dict]:
    findings: list[dict] = []

    def add(num, name, severity, items, note=""):
        findings.append({
            "num": num, "name": name, "severity": severity,
            "items": items, "count": len(items), "note": note,
        })

    content = {k: v for k, v in pages.items() if not v["is_meta"]}
    all_names = set(pages)

    # 边：只取内容页的 wikilink（元文件的出链是导航）
    file_edges: set[tuple[str, str]] = set()
    dead = []
    for name, p in content.items():
        for link in set(p["links"]):
            file_edges.add((name, link))
            if link not in all_names:
                dead.append(f"{p['rel']} -> [[{link}]]")

    # ① 死链
    add(1, "死链", "error", sorted(dead))

    # ② 孤儿页（含豁免）
    indeg = Counter(t for _, t in file_edges)
    now = time.time()
    orphans, pending = [], []
    for name, p in content.items():
        if indeg[name]:
            continue
        if p["subdir"] == "sources":
            continue  # 豁免 1：source 页按设计单向被引
        fresh = (now - p["mtime"]) < 86400
        stub = p["frontmatter"].get("status") == "stub"
        (pending if (fresh or stub) else orphans).append(p["rel"])
    add(2, "孤儿页", "warn", sorted(orphans),
        "已豁免 sources/（单向被引）")
    if pending:
        add(2.5, "待接线的新页", "info", sorted(pending),
            "当天新建或 status: stub —— 还没入链是正常的")

    # ③ frontmatter 完整性
    missing = []
    for name, p in sorted(content.items()):
        lack = [f for f in REQUIRED_FRONTMATTER if f not in p["frontmatter"]]
        if lack:
            missing.append(f"{p['rel']}: 缺 {','.join(lack)}")
    add(3, "frontmatter 完整性", "warn", missing)

    # ④ index.md 一致性
    idx = pages.get("index")
    if idx:
        listed = {l.strip() for l in idx["links"]}
        disk = set(content)
        problems = ([f"盘上有未登记: {n}" for n in sorted(disk - listed)] +
                    [f"index 登记但盘上没有: {n}" for n in sorted(listed - disk)])
        add(4, "index.md 一致性", "warn", problems,
            f"index 登记 {len(listed)} / 内容页 {len(disk)}")

    if db_data is None:
        add(0, "数据库", "error", ["找不到注册了此 vault 的 profile 库 —— 后续检查跳过"])
        return findings

    entities = db_data["entities"]
    ent_names = {}
    for e in entities:
        n = entity_name(e["text_content"], all_names)
        ent_names[e["id"]] = n or e["text_content"][:40]

    # ⑤ 边一致性（只数 linksTo）
    links_to = [e for e in db_data["edges"] if e["relation"] == "linksTo"]
    add(5, "边一致性", "error",
        [] if len(links_to) == len(file_edges) else
        [f"文件解析 {len(file_edges)} 条 ≠ 库里 linksTo {len(links_to)} 条"],
        f"文件 {len(file_edges)} == 库 {len(links_to)}")

    # ⑥ 文件↔实体完整性（按名字归属 —— source 字段不可靠，见 read_db 注释）
    matched = {n for n in ent_names.values() if n in content}
    missing_pages = sorted(set(content) - matched)
    add(6, "文件↔实体完整性", "error",
        [f"无对应实体: {content[n]['rel']}" for n in missing_pages],
        f"内容页 {len(content)} / 已建实体 {len(matched)}")

    # ⑥.5 来源可疑的实体 —— 名字能对上本 vault 的页，但不是 kg_add 建的。
    # 可能是抽取管线产的，或从别的环境残留下来 —— 前者会和 agent 灌的节点
    # 争夺同一个名字，后者会被 kg_add 的模糊匹配复用。
    suspect = []
    for e in entities:
        name = ent_names[e["id"]]
        if name not in content:
            continue
        src = e.get("source") or ""
        stype = e.get("source_type") or ""
        if src == "kg_agent":
            continue  # 正常：agent 用 kg_add 灌的
        if src.startswith(str(vault)):
            continue  # 抽取管线产的，本 vault 内，合规
        suspect.append(f"{name}: id={e['id']} source={src or '(空)'} "
                       f"(type={stype}) —— 不是本 vault 的 kg_add 产出")
    add(6.5, "来源可疑的实体", "warn", suspect,
        "正常应为 source='kg_agent'（agent 灌）或本 vault 路径（抽取管线）")

    # ⑦ 实体名污染
    polluted = []
    for e in entities:
        name = ent_names[e["id"]]
        rest = e["text_content"][len(name):].lstrip() if name in all_names else ""
        if name not in all_names:
            polluted.append(f"id={e['id']} 名字对不上任何文件: {e['text_content'][:44]}")
        elif rest.startswith("|") or "\n" in name:
            polluted.append(f"id={e['id']} ({name}) summary 前有多余分隔符")
    add(7, "实体名污染", "warn", polluted,
        "工程层面问题 —— 文件 frontmatter 干净，是拼接环节插入的")

    # ⑧ 同名实体
    dup = defaultdict(list)
    for e in entities:
        dup[ent_names[e["id"]]].append(e["id"])
    add(8, "同名实体", "warn",
        [f"{n}: id {ids}" for n, ids in sorted(dup.items()) if len(ids) > 1],
        "需人裁定合并还是改名")

    # ⑨ category 是否合规
    bad_cat = [f"{ent_names[e['id']]}: category={e['category']}"
               for e in entities
               if e["category"] and e["category"] not in VALID_CATEGORIES]
    add(9, "category 合规", "warn", bad_cat,
        f"应为 {'/'.join(sorted(VALID_CATEGORIES))}")

    # ⑩ 索引时效
    #
    # ⚠️ rag_index_time 为空不代表没索引 —— fts_only 模式（只勾 Keyword）
    # 本来就不填这个字段，它只在 embed_mode='full'（建了向量）时有值。
    # 所以先按文件夹的 embed_mode 分组，只对 full 的文件夹查这一项。
    full_folder_ids = {f["id"] for f in db_data["folders"]
                       if f.get("embed_mode") == "full"}
    stale, skipped = [], 0
    for f in db_data["files"]:
        mt = f.get("modified_at") or 0
        if not mt:
            continue
        if f.get("folder_id") not in full_folder_ids:
            skipped += 1
            continue
        rt = f.get("rag_index_time")
        if rt is None or rt < mt:
            stale.append(f"{f['name']}: 索引落后于文件修改")
    note = f"{len(db_data['files'])} 个文件已索引"
    if skipped:
        note += f"（{skipped} 个在 fts_only 文件夹，无向量索引时间戳，跳过）"
    add(10, "索引时效", "warn", stale, note)

    # ⑪ 来源不明的 linksTo
    unknown = []
    for e in links_to:
        props = e.get("properties")
        raw = props if isinstance(props, str) else (
            props.decode("utf-8", "replace") if props else "")
        if "reason" not in (raw or ""):
            unknown.append(
                f"id={e['id']} {e['from_text'][:18]} -> {e['to_text'][:18]}")
    add(11, "来源不明的 linksTo", "warn", unknown,
        "agent 灌的每条都有 reason；空的可能来自抽取管线")

    # 缺页候选（信息项）—— 结构提取，零 token
    cands = _missing_page_candidates(vault, set(content))
    if cands:
        add(14, "缺页候选", "info",
            [f"{c['name']}（提及 {c['mentions']} 次"
             + (f"，同族 {'/'.join(c['family'])}" if c['family'] else "")
             + f"）← {', '.join(c['in_files'])}"
             for c in cands],
            "从 raw/ 的表格和列表结构里提的 —— 该不该建页自己判断，"
            "别为只有一句话描述的建 stub 页")

    # ⑫ 抽取管线产的边（信息项）
    extracted = Counter(e["relation"] for e in db_data["edges"]
                        if e["relation"] in EXTRACTED_RELATIONS)
    if extracted:
        add(12, "抽取管线产的边", "info",
            [f"{r}: {c} 条" for r, c in extracted.most_common()],
            "不对应 wikilink，不计入边一致性")

    # ⑬ 文件夹配置
    cfg = []
    for f in db_data["folders"]:
        p = f["path"].replace(str(Path.home()), "~")
        cfg.append(f"{p}  agent={f['agent_allowed']} rag={f['rag_enabled']} "
                   f"{f['embed_mode']} kg={f['kg_enabled']} ({f['rag_status']})")
    add(13, "文件夹注册", "info", cfg)

    return findings


# ---------- 输出 ----------

SEV_MARK = {"error": "❌", "warn": "⚠️ ", "info": "ℹ️ "}


def report(findings: list[dict], vault: Path, db: Path | None) -> int:
    print(f"# Quick Wiki 体检 — {vault}")
    print(f"# 库: {db if db else '（未找到）'}\n")
    real = 0
    for f in sorted(findings, key=lambda x: x["num"]):
        mark = "✅" if not f["count"] else SEV_MARK[f["severity"]]
        num = f["num"]
        label = str(int(num)) if float(num).is_integer() else str(num)
        head = f"{mark} {label:>4}  {f['name']}"
        if f["note"]:
            head += f"   — {f['note']}"
        print(head)
        for item in f["items"][:30]:
            print(f"        {item}")
        if f["count"] > 30:
            print(f"        …还有 {f['count'] - 30} 项")
        if f["count"] and f["severity"] in ("error", "warn"):
            real += f["count"]
    print(f"\n需要处理的项: {real}")
    print("\n以下需人判断，脚本查不了：矛盾、过期声明、缺页、缺交叉引用、数据缺口")
    return real


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default="~/Wiki-Vault")
    ap.add_argument("--strict", action="store_true", help="有真问题时退出码 1")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    vault = Path(os.path.expanduser(args.vault)).resolve()
    if not vault.is_dir():
        print(f"vault 不存在: {vault}", file=sys.stderr)
        return 2

    pages = read_pages(vault)
    if not pages:
        print(f"{vault}/wiki 下没有 .md 文件", file=sys.stderr)
        return 2

    db = find_db(vault)
    db_data = read_db(db, vault) if db else None
    findings = run_checks(vault, pages, db_data, db)

    if args.json:
        print(json.dumps({
            "vault": str(vault), "db": str(db) if db else None,
            "findings": findings,
        }, ensure_ascii=False, indent=1, default=str))
        real = sum(f["count"] for f in findings
                   if f["severity"] in ("error", "warn"))
    else:
        real = report(findings, vault, db)

    return 1 if (args.strict and real) else 0


if __name__ == "__main__":
    sys.exit(main())
