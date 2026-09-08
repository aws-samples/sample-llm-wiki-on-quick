#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""wiki-inspect MCP Server — Quick 上 LLM Wiki 的只读内省层。

给 Quick 里的 agent 提供它自己做不到或容易做错的检查：

- agent 用 kg_search 读不到边的元数据
- agent 读不到索引时间戳，无法判断索引是否滞后
- agent 现场写校验代码结果不稳定，把逻辑固定下来更可靠

所有工具都是**只读**的 —— 绕过 Quick 自己写入会让索引和计量不一致。
写操作仍然走 kg_add / kg_edit / file_write。
"""

from __future__ import annotations

import glob
import os
import re
import sqlite3
import time
from collections import Counter
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

mcp = FastMCP("Wiki Inspect")

DEFAULT_VAULT = "~/Wiki-Vault"

# 抽取管线产的 relation —— 不对应 wikilink，数边时排除
EXTRACTED_RELATIONS = {
    "relatedTo", "mentions", "isPartOf", "about",
    "hasPart", "dependsOn", "author", "object",
}

# 元文件：出链是导航（目录条目 / 记录引用），不是知识关联
META_PAGES = {"index", "log"}

VALID_CATEGORIES = {"Concept", "Entity", "Source", "Synthesis"}
REQUIRED_FRONTMATTER = ("type", "tags", "status", "summary")

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---", re.S)


# ---------- SQL ----------
#
# 全部是常量，没有一处把外部数据拼进来。用三引号而不是隐式字符串拼接，
# 是为了让「这是一整条 SQL」在语法上就明确 —— 相邻字符串字面量容易和
# 「漏了逗号的列表」混淆。

SQL_FOLDER_PATHS = "SELECT path FROM folders"

SQL_ENTITIES = """
    SELECT n.id, n.node_id, n.category, n.source, n.source_type, s.text_content
    FROM nodes n JOIN search_content s ON s.node = n.id
    WHERE n.node_class = 'entity'
"""

SQL_EDGES_PLAIN = "SELECT e.id, e.relation, e.source, e.properties FROM edges e"

SQL_EDGES_NAMED = """
    SELECT e.id, e.relation, e.source, e.properties,
           sf.text_content ft, st.text_content tt
    FROM edges e
    JOIN search_content sf ON sf.node = e.from_node
    JOIN search_content st ON st.node = e.to_node
    ORDER BY e.id
"""

SQL_FOLDERS_LINT = """
    SELECT id, path, agent_allowed, rag_enabled, embed_mode, kg_enabled,
           rag_status, kg_status, file_count, chunk_count
    FROM folders WHERE path LIKE ? ORDER BY id
"""

SQL_FOLDERS_STATUS = """
    SELECT id, path, agent_allowed, rag_enabled, embed_mode, kg_enabled,
           rag_status, kg_status, file_count, chunk_count,
           rag_index_time, kg_tokens_used
    FROM folders WHERE path LIKE ? ORDER BY id
"""

SQL_FILES_BASE = """
    SELECT name, folder_id, rag_index_time, kg_index_time, modified_at
    FROM files WHERE folder_id IN (__IDS__)
"""


def _files_sql(template: str, n: int) -> str:
    """把 IN (__IDS__) 展开成 n 个 ? 占位符。

    DB-API 不支持给 IN 绑定序列，占位符个数只能由代码生成。**插进 SQL 的
    只有 ? 本身**（个数来自 len()），实际值仍走参数绑定 —— 没有任何外部
    数据进入 SQL 文本。
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    return template.replace("__IDS__", ",".join("?" * n))


# ---------- 内部工具 ----------

def _parse_links(text: str) -> list[str]:
    """取 wikilink 目标名并归一化。

    [[X|别名]] → X    [[X#章节]] → X    ![[X]] → X
    [[X\\|别名]] → X   ← markdown 表格里 | 必须转义，正则切完会留尾部反斜杠
    """
    return [m.rstrip("\\").strip() for m in WIKILINK_RE.findall(text)]


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


def _within(registered: str, vault: Path) -> bool:
    """注册路径是否等于 vault 或落在 vault 之内。"""
    try:
        rp = Path(os.path.expanduser(registered)).resolve()
    except (OSError, ValueError):
        return False
    return rp == vault or vault in rp.parents


def _find_db(vault: Path) -> Optional[Path]:
    """找到注册了这个 vault 的 profile 库（可能有多个 profile）。"""
    pattern = os.path.expanduser(
        "~/.quickwork/profiles/*/knowledge_storage/knowledge_v1.db")
    for path in sorted(glob.glob(pattern)):
        try:
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            conn.set_authorizer(_deny_attach)
            rows = conn.execute(SQL_FOLDER_PATHS).fetchall()
            conn.close()
            # 要求 vault 自身或其子目录被注册过 —— 不接受「vault 是注册路径的
            # 父目录」这种关系，否则 vault="/" 对任何注册路径都成立
            if any(_within(r[0], vault) for r in rows):
                return Path(path)
        except sqlite3.Error:
            continue
    return None


def _ro(db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.set_authorizer(_deny_attach)
    conn.row_factory = sqlite3.Row
    # properties 是 JSONB（二进制），默认 UTF-8 解码会整行报错 —— 宽松解码
    conn.text_factory = lambda b: b.decode("utf-8", "replace")
    return conn


def _props_text(raw) -> str:
    """JSONB / bytes / str 都转成可搜索的文本。"""
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", "replace")
    return str(raw)


def _read_pages(vault: Path) -> dict[str, dict]:
    """读 wiki/ 下全部 .md，解析 frontmatter 和 wikilink。"""
    pages: dict[str, dict] = {}
    wiki = vault / "wiki"
    if not wiki.is_dir():
        return pages
    for path in sorted(wiki.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        m = FRONTMATTER_RE.match(text)
        fm_raw = m.group(1) if m else ""
        fm = {}
        for field in REQUIRED_FRONTMATTER:
            fmatch = re.search(rf"^{field}:\s*(.*)$", fm_raw, re.M)
            if fmatch:
                fm[field] = fmatch.group(1).strip()
        pages[path.stem] = {
            "rel": str(path.relative_to(vault)),
            "subdir": path.parent.name if path.parent != wiki else "",
            "frontmatter": fm,
            "links": _parse_links(text),
            "mtime": path.stat().st_mtime,
            "is_meta": path.stem in META_PAGES,
        }
    return pages


def _entity_name(text_content: str, known: set[str]) -> str:
    """search_content 存 "name + 空格 + summary" 拼接 —— 用最长匹配取出名字。"""
    best = ""
    for name in known:
        if text_content.startswith(name) and len(name) > len(best):
            best = name
    return best


def _resolve(vault_path: str) -> tuple[Path, Optional[Path]]:
    """展开并校验 vault 路径。

    `vault` 参数由调用方（agent）填，而 agent 的输入可能来自 raw/ 里的
    不可信素材 —— 所以不能直接拿去读盘。两道闸：

    1. 必须是 Quick 里**注册过的文件夹**本身（不是它的父目录）。
       `path LIKE '<vault>%'` 单独用是不够的：`vault="/"` 能匹配任何注册路径。
    2. 必须有 wiki/ 子目录 —— 挡掉指向注册树之外的路径。

    过不了闸就返回 db=None，工具统一回「找不到注册了此 vault 的库」。
    """
    vault = Path(os.path.expanduser(vault_path)).resolve()
    if not (vault / "wiki").is_dir():
        return vault, None
    return vault, _find_db(vault)


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


# ---------- 对外工具 ----------

@mcp.tool()
def wiki_lint(vault: str = DEFAULT_VAULT, brief: bool = False) -> dict:
    """对 LLM Wiki 跑全套确定性体检，返回结构化结果。

    比自己用 run_python 现场写校验代码可靠 —— 这里的逻辑是固定的、测过的。
    覆盖 11 项：死链、孤儿页（含豁免）、frontmatter 完整性、index.md 一致性、
    边一致性、文件↔实体完整性、来源可疑的实体、实体名污染、同名实体、
    category 合规、索引时效、来源不明的边。

    brief=True 只返回 {ok, summary, problems}（全绿时约 80 字符，省 token）；
    默认返回完整 findings。先用 brief 看有没有问题，有问题再取完整结果。

    返回 dict：{ok, summary, findings: [{num,name,severity,count,items,note}], folders}
    severity 为 error/warn 的项才算真问题，info 是参考。

    查不了的 5 项（需要你自己判断）：矛盾、过期声明、缺页、缺交叉引用、数据缺口。
    """
    v, db = _resolve(vault)
    if not v.is_dir():
        return {"ok": False, "error": f"vault 不存在: {v}"}

    pages = _read_pages(v)
    if not pages:
        return {"ok": False, "error": f"{v}/wiki 下没有 .md 文件"}

    findings: list[dict] = []

    def add(num, name, severity, items, note=""):
        findings.append({"num": num, "name": name, "severity": severity,
                         "count": len(items), "items": items[:40], "note": note})

    content = {k: p for k, p in pages.items() if not p["is_meta"]}
    all_names = set(pages)

    # 边：只取内容页的 wikilink（元文件出链是导航）
    file_edges: set[tuple[str, str]] = set()
    dead = []
    for name, p in content.items():
        for link in set(p["links"]):
            file_edges.add((name, link))
            if link not in all_names:
                dead.append(f"{p['rel']} -> [[{link}]]")
    add(1, "死链", "error", sorted(dead))

    # 孤儿页（豁免 sources/ 单向被引；当天新建或 stub 归为「待接线」）
    indeg = Counter(t for _, t in file_edges)
    now = time.time()
    orphans, pending = [], []
    for name, p in content.items():
        if indeg[name] or p["subdir"] == "sources":
            continue
        fresh = (now - p["mtime"]) < 86400
        stub = p["frontmatter"].get("status") == "stub"
        (pending if (fresh or stub) else orphans).append(p["rel"])
    add(2, "孤儿页", "warn", sorted(orphans), "已豁免 sources/（单向被引）")
    if pending:
        add(2.5, "待接线的新页", "info", sorted(pending),
            "当天新建或 status: stub —— 还没入链是正常的")

    # frontmatter
    missing = [f"{p['rel']}: 缺 {','.join(lack)}"
               for _, p in sorted(content.items())
               if (lack := [f for f in REQUIRED_FRONTMATTER
                            if f not in p["frontmatter"]])]
    add(3, "frontmatter 完整性", "warn", missing)

    # index.md 一致性
    if (idx := pages.get("index")):
        listed = {l.strip() for l in idx["links"]}
        disk = set(content)
        add(4, "index.md 一致性", "warn",
            [f"盘上未登记: {n}" for n in sorted(disk - listed)] +
            [f"index 有但盘上没有: {n}" for n in sorted(listed - disk)],
            f"index 登记 {len(listed)} / 内容页 {len(disk)}")

    if db is None:
        add(0, "数据库", "error", ["找不到注册了此 vault 的 profile 库"])
        return {"ok": False, "summary": "库不可读，只做了文件层检查",
                "findings": findings, "folders": []}

    conn = _ro(db)
    entities = [dict(r) for r in conn.execute(SQL_ENTITIES)]
    edges = [dict(r) for r in conn.execute(SQL_EDGES_PLAIN)]
    folders = [dict(r) for r in conn.execute(SQL_FOLDERS_LINT, (f"{v}%",))]
    fids = [f["id"] for f in folders]
    files = []
    if fids:
        files = [dict(r) for r in conn.execute(_files_sql(SQL_FILES_BASE, len(fids)), fids)]
    conn.close()

    ent_names = {e["id"]: (_entity_name(e["text_content"], all_names)
                           or e["text_content"][:40]) for e in entities}

    # 边一致性（只数 linksTo）
    links_to = [e for e in edges if e["relation"] == "linksTo"]
    add(5, "边一致性", "error",
        [] if len(links_to) == len(file_edges) else
        [f"文件解析 {len(file_edges)} ≠ 库里 linksTo {len(links_to)}"],
        f"文件 {len(file_edges)} == 库 {len(links_to)}")

    # 文件↔实体完整性（按名字归属 —— source 字段不可靠，见下）
    matched = {n for n in ent_names.values() if n in content}
    add(6, "文件↔实体完整性", "error",
        [f"无对应实体: {content[n]['rel']}" for n in sorted(set(content) - matched)],
        f"内容页 {len(content)} / 已建实体 {len(matched)}")

    # 来源可疑的实体
    #   kg_add 建的      → source='kg_agent'（工具标识，不是路径）
    #   抽取管线产的      → source=<注册的文件夹路径>
    #   其它（网页等）    → source='generated_processor' / 'other'
    suspect = []
    for e in entities:
        n = ent_names[e["id"]]
        if n not in content:
            continue
        src = e.get("source") or ""
        if src == "kg_agent" or src.startswith(str(v)):
            continue
        suspect.append(f"{n}: id={e['id']} source={src or '(空)'} "
                       f"(type={e.get('source_type')})")
    add(6.5, "来源可疑的实体", "warn", suspect,
        "正常应为 kg_agent（agent 灌）或本 vault 路径（抽取管线）")

    # 实体名污染（工程层面问题：文件 frontmatter 干净，是拼接环节插入的）
    polluted = []
    for e in entities:
        n = ent_names[e["id"]]
        if n not in all_names:
            continue
        rest = e["text_content"][len(n):].lstrip()
        if rest.startswith("|") or "\n" in n:
            polluted.append(f"id={e['id']} ({n}) summary 前有多余分隔符")
    add(7, "实体名污染", "warn", polluted, "只能靠比对发现，加规则解决不了")

    # 同名实体
    dup: dict[str, list] = {}
    for e in entities:
        dup.setdefault(ent_names[e["id"]], []).append(e["id"])
    add(8, "同名实体", "warn",
        [f"{n}: id {ids}" for n, ids in sorted(dup.items()) if len(ids) > 1],
        "需人裁定合并还是改名")

    # category 合规
    add(9, "category 合规", "warn",
        [f"{ent_names[e['id']]}: category={e['category']}" for e in entities
         if e["category"] and e["category"] not in VALID_CATEGORIES],
        f"应为 {'/'.join(sorted(VALID_CATEGORIES))}")

    # 索引时效
    #
    # ⚠️ rag_index_time 为空不代表没索引 —— fts_only 模式（只勾 Keyword）本来就不填
    # 这个字段，它只在 embed_mode='full'（建了向量）时有值。所以只对 full 的文件夹查。
    full_ids = {f["id"] for f in folders if f.get("embed_mode") == "full"}
    stale, skipped = [], 0
    for f in files:
        mt = f.get("modified_at") or 0
        if not mt:
            continue
        if f.get("folder_id") not in full_ids:
            skipped += 1
            continue
        rt = f.get("rag_index_time")
        if rt is None or rt < mt:
            stale.append(f"{f['name']}: 索引落后于文件修改")
    note = f"{len(files)} 个文件已索引"
    if skipped:
        note += f"（{skipped} 个在 fts_only 文件夹，无向量索引时间戳，跳过）"
    add(10, "索引时效", "warn", stale, note)

    # 来源不明的 linksTo（agent 灌的每条都有 reason）
    add(11, "来源不明的 linksTo", "warn",
        [f"id={e['id']}" for e in links_to
         if "reason" not in _props_text(e.get("properties"))],
        "agent 灌的每条都写了 'wikilink in <文件名>'")

    # 缺页候选（信息项）—— 结构提取 + 前缀族，全确定性，零 token
    cands = _missing_page_candidates(v, set(content))
    if cands:
        add(14, "缺页候选", "info",
            [f"{c['name']}（提及 {c['mentions']} 次"
             + (f"，同族 {'/'.join(c['family'])}" if c['family'] else "")
             + f"）← {', '.join(c['in_files'])}"
             for c in cands],
            "从 raw/ 的表格和列表结构里提的 —— 该不该建页你自己判断，"
            "不要为只有一句话描述的建 stub 页")

    # 抽取管线产的边（信息项）
    extracted = Counter(e["relation"] for e in edges
                        if e["relation"] in EXTRACTED_RELATIONS)
    if extracted:
        add(12, "抽取管线产的边", "info",
            [f"{r}: {c} 条" for r, c in extracted.most_common()],
            "不对应 wikilink，不计入边一致性")

    real = sum(f["count"] for f in findings if f["severity"] in ("error", "warn"))
    summary = (f"内容页 {len(content)} / 实体 {len(matched)} / "
               f"linksTo {len(links_to)} / 需处理 {real} 项")

    if brief:
        return {
            "ok": real == 0,
            "summary": summary,
            "problems": [{"name": f["name"], "count": f["count"],
                          "items": f["items"][:5]}
                         for f in findings
                         if f["count"] and f["severity"] in ("error", "warn")],
            "cannot_check": ["矛盾", "过期声明", "缺页", "缺交叉引用", "数据缺口"],
        }

    return {
        "ok": real == 0,
        "summary": summary,
        "needs_attention": real,
        "findings": sorted(findings, key=lambda x: x["num"]),
        "folders": [{k: f[k] for k in
                     ("path", "agent_allowed", "rag_enabled", "embed_mode",
                      "kg_enabled", "rag_status", "file_count", "chunk_count")}
                    for f in folders],
        "cannot_check": ["矛盾", "过期声明", "缺页", "缺交叉引用", "数据缺口"],
    }


@mcp.tool()
def wiki_edges(page: Optional[str] = None, vault: str = DEFAULT_VAULT) -> dict:
    """读全量边，不受 kg_search 的 3 条上限。

    page 给页名（不含 .md）时只返回和它相关的边；不给则返回全库统计。
    每条边带 relation、reason（properties 里的溯源信息）、两端页名。

    kg_search 返回的 edges 有 3 条上限，枢纽页会被截断 —— 要准确数边用这个。
    """
    v, db = _resolve(vault)
    if db is None:
        return {"ok": False, "error": "找不到注册了此 vault 的 profile 库"}

    pages = _read_pages(v)
    all_names = set(pages)
    conn = _ro(db)
    rows = [dict(r) for r in conn.execute(SQL_EDGES_NAMED)]
    conn.close()

    out = []
    for r in rows:
        f_name = _entity_name(r["ft"], all_names) or r["ft"][:32]
        t_name = _entity_name(r["tt"], all_names) or r["tt"][:32]
        if page and page not in (f_name, t_name):
            continue
        reason = ""
        props = _props_text(r.get("properties"))
        if "reason" in props:
            # JSONB 里键值紧邻，字段名后紧跟长度前缀和内容
            # JSONB 无分隔符，下一个字段名紧跟其后 —— 截到 .md 为止
            if (m := re.search(r"(wikilink in .+?\.md)", props)):
                reason = m.group(1)
        out.append({"id": r["id"], "relation": r["relation"],
                    "from": f_name, "to": t_name, "reason": reason,
                    "source": r["source"]})

    by_rel = Counter(e["relation"] for e in out)
    return {
        "ok": True,
        "scope": f"页面 {page}" if page else "全库",
        "total": len(out),
        "by_relation": dict(by_rel.most_common()),
        "linksTo_without_reason": sum(
            1 for e in out if e["relation"] == "linksTo" and not e["reason"]),
        "edges": out[:200],
        "truncated": len(out) > 200,
    }


@mcp.tool()
def wiki_index_status(vault: str = DEFAULT_VAULT) -> dict:
    """读文件夹注册配置和索引时间戳 —— 判断索引有没有真的跑。

    你报告「已触发重新索引」之后应该用这个确认：rag_index_time 是否真的
    比 modified_at 新。仅凭工具返回的成功消息不足以证明索引生效。

    embed_mode 说明：fts_only = 只建全文；full = 全文 + 向量（语义检索可用）。
    """
    v, db = _resolve(vault)
    if db is None:
        return {"ok": False, "error": "找不到注册了此 vault 的 profile 库"}

    conn = _ro(db)
    folders = [dict(r) for r in conn.execute(SQL_FOLDERS_STATUS, (f"{v}%",))]
    fids = [f["id"] for f in folders]
    files = []
    if fids:
        files = [dict(r) for r in conn.execute(
            _files_sql(SQL_FILES_BASE + " ORDER BY name", len(fids)), fids)]
    conn.close()

    def ts(x):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x)) if x else None

    stale = [f["name"] for f in files
             if (f.get("modified_at") or 0) and
             (f.get("rag_index_time") is None or
              f["rag_index_time"] < f["modified_at"])]

    return {
        "ok": not stale,
        "folders": [{
            "path": f["path"].replace(os.path.expanduser("~"), "~"),
            "agent_access": bool(f["agent_allowed"]),
            "keyword": bool(f["rag_enabled"]),
            "semantic": f["embed_mode"] == "full",
            "kg": bool(f["kg_enabled"]),
            "rag_status": f["rag_status"], "kg_status": f["kg_status"],
            "files": f["file_count"], "chunks": f["chunk_count"],
            "last_indexed": ts(f["rag_index_time"]),
            "kg_tokens_used": f["kg_tokens_used"],
        } for f in folders],
        "indexed_files": len(files),
        "stale_files": stale,
        "note": "stale_files 非空 = 这些文件改动后还没进索引，检索会拿到旧内容",
    }


@mcp.tool()
def wiki_hubs(limit: int = 15, vault: str = DEFAULT_VAULT) -> dict:
    """按入链数排名找枢纽页，同时报出零入链的页。

    Lint 时用来判断结构健康：核心概念应该是枢纽（入链多），而新页/边缘页入链少。
    也用来发现「星形结构」—— 一堆页都只连主页、彼此不互链。

    从文件解析，不查库 —— 所以不受 kg_search 的 3 条边上限影响，
    也不依赖边有没有灌进图谱。

    返回 {hubs: [{page, in, out, type}], no_inbound: [...], shape}
    """
    v, _ = _resolve(vault)
    if not v.is_dir():
        return {"ok": False, "error": f"vault 不存在: {v}"}

    pages = _read_pages(v)
    content = {k: p for k, p in pages.items() if not p["is_meta"]}
    if not content:
        return {"ok": False, "error": "没有内容页"}

    edges = set()
    for name, p in content.items():
        for link in set(p["links"]):
            edges.add((name, link))

    indeg = Counter(t for _, t in edges)
    outdeg = Counter(f for f, _ in edges)

    ranked = sorted(content, key=lambda n: (-indeg[n], -outdeg[n], n))
    hubs = [{
        "page": n,
        "in": indeg[n],
        "out": outdeg[n],
        "type": content[n]["frontmatter"].get("type", "?"),
        "status": content[n]["frontmatter"].get("status", "?"),
    } for n in ranked[:limit]]

    no_in = [n for n in content if indeg[n] == 0]

    # 星形判断：入链高度集中在少数页 = 星形；分布均匀 = 网状
    total = sum(indeg[n] for n in content)
    top3 = sum(indeg[n] for n in ranked[:3])
    shape = "网状"
    if total and top3 / total > 0.5:
        shape = "星形（入链过半集中在前 3 页 —— 其余页多是各自连主页、彼此不互链）"
    elif total and top3 / total > 0.35:
        shape = "偏星形"

    return {
        "ok": True,
        "total_pages": len(content),
        "total_edges": len(edges),
        "hubs": hubs,
        "no_inbound": sorted(no_in),
        "shape": shape,
        "note": "no_inbound 里 sources/ 下的页是设计如此（单向被引），不算孤儿",
    }


if __name__ == "__main__":
    mcp.run()
