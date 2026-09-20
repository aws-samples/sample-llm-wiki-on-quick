#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""quick_wiki_lint.py — Quick 上 LLM Wiki 的确定性体检

扫 vault 里的 markdown 文件，报死链、孤儿页、frontmatter 缺失、目录不一致、
type 放错目录、缺页候选。只读，从不写任何东西。

**检查全部从 `.md` 解析，不查索引库。** 新版 Quick 把索引、chunk、实体、
`kg_add` 灌的节点和边都放在云端 Quick Space，本机 `knowledge_v1.db` 里跟
vault 有关的表都是 0 行 —— 唯一还读本机库的是权限层
（`allowed_folders.db`，判断文件夹注册状态）。图谱层的校验在 Quick 里用
`kg_search` 做。

用法:
    quick_wiki_lint.py                    # 全部检查，人类可读输出
    quick_wiki_lint.py --strict           # 有真问题时退出码 1
    quick_wiki_lint.py --json             # 机器可读
    quick_wiki_lint.py --vault ~/Other    # 指定 vault

为什么用脚本而不是让 agent 现场写：逻辑固定、结果可复现。现场写最容易错的
三处 —— 边没按 (from, to) 去重、没剥掉代码块里的 `[[X]]` 语法示例、
sandbox 拦住读盘。
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
from collections import Counter
from pathlib import Path

# 元文件：出链是导航（目录条目/记录引用），不是知识关联
META_PAGES = {"index", "log"}

# frontmatter 的 type → 它该待的子目录。
# 不能靠「type + s」推：entity 的目录是 entities（不是 entitys），
# synthesis 本身就是复数形（不是 synthesiss）。
TYPE_DIR = {
    "concept": "concepts",
    "entity": "entities",
    "source": "sources",
    "synthesis": "synthesis",
}
REQUIRED_FRONTMATTER = ("type", "tags", "status", "summary")

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---", re.S)
# 代码块 / 行内代码 —— 里面的 [[X]] 是语法示例，不是链接
FENCED_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")


def parse_links(text: str) -> list[str]:
    """取 wikilink 目标名并归一化。

    [[X|别名]] → X    [[X#章节]] → X    ![[X]] → X
    [[X\\|别名]] → X   ← markdown 表格里 | 必须转义，正则切完会留尾部反斜杠

    **先剥掉代码块和行内代码。** 讲双链语法的页面里会写 `` `[[...]]` ``
    或代码块里贴 `[[页名]]` 示例 —— 那是展示语法，不是真链接。不剥的话
    会把它们报成死链。
    """
    stripped = FENCED_RE.sub(" ", text)
    stripped = INLINE_CODE_RE.sub(" ", stripped)
    return [m.rstrip("\\").strip() for m in WIKILINK_RE.findall(stripped)]


# ---------- 权限层 ----------

SQL_ALLOWED = """
    SELECT path, read_allowed, write_allowed, added_at, sync_status, storage_type
    FROM allowed_folders ORDER BY path
"""


def _deny_attach(action: int, _a1, _a2, _db, _trigger) -> int:
    """拒绝 ATTACH / DETACH，其余放行。

    mode=ro 挡住了全部写操作，但**不挡 ATTACH DATABASE** —— 那能挂载并
    创建其它库文件，等于绕开只读。SQL 全是字面量所以现在触发不了，加这道
    授权回调是让「只读」在引擎层面完整成立。
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


def registrations(profile: Path) -> list[dict]:
    """读一个 profile 注册的文件夹（权限层）。

    `allowed_folders.db` 是本机唯一还有 vault 数据的库。每条记录除 path
    还带 `sync_status` 和 `storage_type`。
    """
    db = profile / "allowed_folders.db"
    if not db.exists():
        return []
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        conn.set_authorizer(_deny_attach)
        conn.row_factory = sqlite3.Row
        conn.text_factory = lambda b: b.decode("utf-8", "replace")
        rows = [dict(r) for r in conn.execute(SQL_ALLOWED)]
        conn.close()
        return rows
    except sqlite3.Error:
        return []


def find_profile(vault: Path) -> Path | None:
    """找到注册了这个 vault 的 profile 目录（本机可能有多个 profile）。"""
    for prof in sorted(glob.glob(os.path.expanduser("~/.quickwork/profiles/*/"))):
        profile = Path(prof)
        # 要求 vault 自身或其子目录被注册过 —— 不接受「vault 是注册路径的
        # 父目录」这种关系，否则 vault="/" 对任何注册路径都成立
        if any(within(r["path"], vault) for r in registrations(profile)):
            return profile
    return None


# ---------- 读页面 ----------

def disk_facts(vault: Path, regs: list[dict], home: str) -> list[dict]:
    """每个注册文件夹在**盘上**的事实：文件数 + 最新 mtime。

    存在理由：让 agent 自己递归 stat 几十个文件算最大 mtime 不可靠 —— 实测某个
    每小时任务报出的文件数和盘上不符（报 wiki 64 个，实际 48 个），mtime 也停在
    旧值上。判断依据不可信，就算结论碰巧对也不能用。

    脚本在自己的进程里跑，`rglob` + `stat` 拿到的是当下的真值。

    子文件夹归给**最深的**那个注册路径，避免同一个文件被 `Wiki-Vault` 和
    `Wiki-Vault/wiki` 重复计入。
    """
    paths = sorted({Path(os.path.expanduser(r["path"])).resolve() for r in regs},
                   key=lambda p: len(p.parts), reverse=True)
    buckets: dict[Path, list[Path]] = {p: [] for p in paths}
    for md in vault.rglob("*.md"):
        for p in paths:
            if md == p or p in md.parents:
                buckets[p].append(md)
                break
    out = []
    for p in sorted(paths, key=str):
        files = buckets[p]
        if not files:
            continue
        newest = max(f.stat().st_mtime for f in files)
        out.append({
            "path": str(p).replace(home, "~"),
            "md_files": len(files),
            "newest_mtime_epoch": int(newest),
            "newest_mtime": time.strftime("%Y-%m-%d %H:%M:%S",
                                          time.localtime(newest)),
            "newest_file": str(max(files, key=lambda f: f.stat().st_mtime)
                               .relative_to(vault)),
        })
    return out


def read_pages(vault: Path) -> dict[str, dict]:
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
            "links": parse_links(text),
            "mtime": path.stat().st_mtime,
            "is_meta": path.stem in META_PAGES,
        }
    return pages


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

def run_checks(vault: Path, pages: dict, profile: Path | None) -> list[dict]:
    findings: list[dict] = []

    def add(num, name, severity, items, note=""):
        findings.append({
            "num": num, "name": name, "severity": severity,
            "items": items, "count": len(items), "note": note,
        })

    content = {k: v for k, v in pages.items() if not v["is_meta"]}
    all_names = set(pages)

    # 边：只取内容页的 wikilink（元文件的出链是导航），按 (from, to) 去重
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

    # frontmatter 必填字段
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

    # type 取值 —— 必须是四类之一，且和所在子目录一致
    bad_type = []
    for _, p in sorted(content.items()):
        t = p["frontmatter"].get("type")
        if not t:
            continue                      # 缺 type 已由 #3 报
        if t not in TYPE_DIR:
            bad_type.append(f"{p['rel']}: type={t} 不是四类之一")
        elif p["subdir"] and p["subdir"] != TYPE_DIR[t]:
            bad_type.append(
                f"{p['rel']}: type={t} 该放在 {TYPE_DIR[t]}/ 却在 {p['subdir']}/")
    add(9, "type 取值", "warn", bad_type,
        "允许 " + "/".join(sorted(TYPE_DIR)) + "，且要和子目录对应")

    # 枢纽分布（信息项）—— 核心概念该入链多，边缘页少
    if file_edges:
        top = indeg.most_common(5)
        share = sum(c for _, c in top[:3]) / len(file_edges) * 100
        add(15, "枢纽分布", "info",
            [f"{n}: 入链 {c}" for n, c in top],
            f"前 3 名占全部入链的 {share:.0f}%（>50% 说明结构偏星形，"
            f"知识集中在少数几页）")

    # 文件夹注册（信息项）—— 读权限层
    home = os.path.expanduser("~")
    if profile is None:
        add(13, "文件夹注册", "error", [f"{vault} 没在 Quick 里注册"],
            "在 Quick 的 Files 面板添加这个文件夹，否则 agent 读不到")
    else:
        regs = [r for r in registrations(profile) if within(r["path"], vault)]
        add(13, "文件夹注册", "info",
            [f"{r['path'].replace(home, '~')}  读={bool(r['read_allowed'])} "
             f"写={bool(r['write_allowed'])} {r['sync_status']}/{r['storage_type']}"
             for r in regs],
            f"profile: {profile.name}")
        unsynced = [r["path"] for r in regs if r["sync_status"] != "synced"]
        if unsynced:
            add(13.5, "未同步的文件夹", "warn",
                [p.replace(home, "~") for p in unsynced],
                "sync_status 不是 synced —— 云端可能还没拿到这些文件")

    # 索引时效（信息项）—— 只给盘上的一半，云端那半要用 file_rag_status 取
    if profile:
        facts = disk_facts(vault, registrations(profile), home)
        add(10, "索引时效（需补另一半）", "info",
            [f"{d['path']}: {d['md_files']} 个 .md，最新改动 {d['newest_mtime']}"
             f"（epoch {d['newest_mtime_epoch']}）← {d['newest_file']}"
             for d in facts],
            "拿这里的 epoch 和 Quick 里 file_rag_status 给的 rag_index_time 比："
            "mtime 更大 = 索引过期")

    # 缺页候选（信息项）—— 结构提取 + 前缀族，全确定性，零 token
    cands = _missing_page_candidates(vault, set(content))
    if cands:
        add(14, "缺页候选", "info",
            [f"{c['name']}（提及 {c['mentions']} 次"
             + (f"，同族 {'/'.join(c['family'])}" if c['family'] else "")
             + f"）← {', '.join(c['in_files'])}"
             for c in cands],
            "从 raw/ 的表格和列表结构里提的 —— 该不该建页你自己判断，"
            "不要为只有一句话描述的建 stub 页")

    return findings


# ---------- 输出 ----------

SEV_MARK = {"error": "❌", "warn": "⚠️ ", "info": "ℹ️ "}


def report(findings: list[dict], vault: Path, profile: Path | None,
           edges: int, npages: int) -> int:
    print(f"# Quick Wiki 体检 — {vault}")
    print(f"# 内容页 {npages} / 边 {edges}（按 (from,to) 去重，已剥代码块）")
    print(f"# profile: {profile.name if profile else '（未注册）'}\n")
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
    print("\n图谱层（实体是否齐、边有没有灌进去）在云端，用 kg_search 在 Quick 里查")
    print("以下需人判断：矛盾、过期声明、缺页、缺交叉引用、数据缺口")
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

    profile = find_profile(vault)
    findings = run_checks(vault, pages, profile)

    content = {k: v for k, v in pages.items() if not v["is_meta"]}
    edges = len({(n, l) for n, p in content.items() for l in set(p["links"])})

    if args.json:
        print(json.dumps({
            "vault": str(vault),
            "profile": profile.name if profile else None,
            "total_pages": len(content),
            "total_edges": edges,
            "findings": findings,
        }, ensure_ascii=False, indent=1, default=str))
        real = sum(f["count"] for f in findings
                   if f["severity"] in ("error", "warn"))
    else:
        real = report(findings, vault, profile, edges, len(content))

    return 1 if (args.strict and real) else 0


if __name__ == "__main__":
    sys.exit(main())
