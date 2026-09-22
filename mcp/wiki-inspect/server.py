#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""wiki-inspect MCP Server — Quick 上 LLM Wiki 的只读校验层。

给 Quick 里的 agent 提供它自己做不到或容易做错的检查：

- `kg_search` 每个节点最多回 3 条边，页面连接多时数不准；这里读文件，没有上限
- agent 现场写校验代码结果不稳定 —— 常见的错是边没按 (from, to) 去重、
  没剥掉代码块里的 `[[X]]` 语法示例、sandbox 拦住读盘
- 结构健康（枢纽分布、孤儿页、死链）要全量扫，逐页问 agent 既慢又漏

**全部检查都从 `.md` 文件解析。** 新版 Quick 把索引、chunk、实体、
`kg_add` 灌的节点和边都放在云端 Quick Space，本机 `knowledge_v1.db` 里
跟 vault 有关的表都是 0 行 —— 唯一还查本机库的是权限层
（`allowed_folders.db`，判断文件夹注册状态）。图谱层的校验用 `kg_search`
在 Quick 里做。

所有工具都是**只读**的 —— 绕过 Quick 自己写入会让索引和计量不一致。
写操作仍然走 kg_add / kg_edit / file_write。
"""

from __future__ import annotations

import glob
import logging
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

# 元文件：出链是导航（目录条目 / 记录引用），不是知识关联
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
# 代码块 / 行内代码 —— 里面的 [[X]] 是语法示例，不是链接
FENCED_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---", re.S)


# ---------- SQL ----------
#
# 只剩一条，查的是**权限层**（本机唯一还有 vault 数据的库）。
# 索引、chunk、实体、`kg_add` 灌的节点和边全在云端 Quick Space，
# 本机 `knowledge_v1.db` 里跟 vault 有关的表都是 0 行 —— 不再查它。
#
# 常量，没有一处把外部数据拼进来。

SQL_ALLOWED = """
    SELECT path, read_allowed, write_allowed, added_at, sync_status, storage_type
    FROM allowed_folders ORDER BY path
"""


# ---------- 内部工具 ----------

def _parse_links(text: str) -> list[str]:
    """取 wikilink 目标名并归一化。

    [[X|别名]] → X    [[X#章节]] → X    ![[X]] → X
    [[X\\|别名]] → X   ← markdown 表格里 | 必须转义，正则切完会留尾部反斜杠

    **先剥掉代码块和行内代码。** 讲双链语法的页面里会写 `` `[[...]]` ``
    或代码块里贴 `[[页名]]` 示例 —— 那是在展示语法，不是真链接。
    不剥的话 lint 会把它们报成死链（实测在讲 kg_add 约定的 synthesis 页上踩到过）。
    """
    stripped = FENCED_RE.sub(" ", text)      # ``` 围栏代码块
    stripped = INLINE_CODE_RE.sub(" ", stripped)   # `行内代码`
    return [m.rstrip("\\").strip() for m in WIKILINK_RE.findall(stripped)]


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


def _registrations(profile: Path) -> list[dict]:
    """读一个 profile 注册的文件夹（权限层）。

    **`allowed_folders.db` 是本机唯一还有 vault 数据的库。** 索引、chunk、
    实体、`kg_add` 灌的节点和边全在云端 Quick Space —— `knowledge_v1.db`
    里跟 vault 相关的表都是 0 行，查它只会拿到误导性的空结果，所以不查。

    每条记录除 path 还带 `sync_status`（同步状态）和 `storage_type`
    （local / …），可以直接判断该文件夹有没有同步上去。
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


def _find_profile(vault: Path) -> Optional[Path]:
    """找到注册了这个 vault 的 profile 目录（本机可能有多个 profile）。"""
    for prof in sorted(glob.glob(os.path.expanduser("~/.quickwork/profiles/*/"))):
        profile = Path(prof)
        # 要求 vault 自身或其子目录被注册过 —— 不接受「vault 是注册路径的
        # 父目录」这种关系，否则 vault="/" 对任何注册路径都成立
        if any(_within(r["path"], vault) for r in _registrations(profile)):
            return profile
    return None


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


def _disk_facts(vault: Path, regs: list[dict], home: str) -> list[dict]:
    """每个注册文件夹在**盘上**的事实：文件数 + 最新 mtime。

    这一项存在的理由：让 agent 用 `folder_list` / `run_python` 递归 stat 几十个
    文件、自己算最大 mtime —— 那步不可靠。实测某个每小时同步任务报出的文件数
    就和盘上不符（报 wiki 64 个，实际 48 个），mtime 也停在旧值上。数错了不一定
    导致漏索引（同步管道自己也会扫），但**它的判断依据是不可信的**。

    MCP 在自己的进程里跑，`rglob` + `stat` 拿到的是当下的真值。agent 只需要
    把这里的 `newest_mtime_epoch` 和 `file_rag_status` 给的 `rag_index_time`
    做一次数值比较 —— 一步比较代替几十步 stat，错不了，也省 token。

    只统计 `.md`。子文件夹归给**最深的**那个注册路径，避免同一个文件被
    `Wiki-Vault` 和 `Wiki-Vault/wiki` 重复计入。
    """
    # 按路径深度倒序 —— 深的先匹配，一个文件只归一个文件夹
    paths = sorted(
        ({Path(os.path.expanduser(r["path"])).resolve() for r in regs}),
        key=lambda p: len(p.parts), reverse=True)

    buckets: dict[Path, list[Path]] = {p: [] for p in paths}
    for md in vault.rglob("*.md"):
        for p in paths:                    # 深的在前，第一个命中即归属
            if md == p or p in md.parents:
                buckets[p].append(md)
                break

    out = []
    for p in sorted(paths, key=lambda x: str(x)):
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


def _resolve(vault_path: str) -> tuple[Path, Optional[Path]]:
    """展开并校验 vault 路径，返回 (vault, profile)。

    `vault` 参数由调用方（agent）填，而 agent 的输入可能来自 raw/ 里的
    不可信素材 —— 所以不能直接拿去读盘。两道闸：

    1. 必须是 Quick 里**注册过的文件夹**本身（不是它的父目录）。
    2. 必须有 wiki/ 子目录 —— 挡掉指向注册树之外的路径。

    过不了闸 profile 返回 None，工具统一回「此 vault 没在 Quick 里注册」。
    """
    vault = Path(os.path.expanduser(vault_path)).resolve()
    if not (vault / "wiki").is_dir():
        return vault, None
    return vault, _find_profile(vault)


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
    现场写最容易错的三处：边没按 (from, to) 去重、没剥掉代码块里的
    `` `[[X]]` `` 语法示例、sandbox 拦住读盘。

    **全部检查都从 `.md` 文件解析，不查数据库。** 新版 Quick 把索引、chunk、
    实体、`kg_add` 灌的节点和边全放在云端 Quick Space，本机不留副本 ——
    图谱层的校验（实体是否齐、边有没有灌进去）在本机无从查证，改用
    `kg_search` 在 Quick 里查。

    覆盖 9 项：
    `#1` 死链、`#2` 孤儿页（含豁免）、`#3` frontmatter 完整性、
    `#4` `index.md` 一致性、`#9` type 取值、`#10` 索引时效（盘上一半）、
    `#13` 文件夹注册（+ 未同步告警）、`#14` 缺页候选、`#15` 枢纽分布。

    `#10` 只给盘上的最新 mtime —— 云端的 `rag_index_time` 要你自己用
    `file_rag_status` 取，两个数一比就知道索引有没有过期。

    brief=True 只返回 {ok, summary, problems}（全绿时约 80 字符，省 token）；
    默认返回完整 findings。先用 brief 看有没有问题，有问题再取完整结果。

    返回 dict：{ok, summary, findings: [{num,name,severity,count,items,note}], folders}
    severity 为 error/warn 的项才算真问题，info 是参考。

    查不了的 5 项（需要你自己读页面判断）：矛盾、过期声明、缺页、
    缺交叉引用、数据缺口。
    """
    v, profile = _resolve(vault)
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

    # 边：只取内容页的 wikilink（元文件出链是导航），按 (from, to) 去重
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

    # index.md 一致性
    if (idx := pages.get("index")):
        listed = {l.strip() for l in idx["links"]}
        disk = set(content)
        add(4, "index.md 一致性", "warn",
            [f"盘上未登记: {n}" for n in sorted(disk - listed)] +
            [f"index 有但盘上没有: {n}" for n in sorted(listed - disk)],
            f"index 登记 {len(listed)} / 内容页 {len(disk)}")

    # 文件夹注册（信息项）—— 读权限层
    regs = _registrations(profile) if profile else []
    home = os.path.expanduser("~")
    reg_items = [
        f"{r['path'].replace(home, '~')}  读={bool(r['read_allowed'])} "
        f"写={bool(r['write_allowed'])} {r['sync_status']}/{r['storage_type']}"
        for r in regs if _within(r["path"], v)]
    if profile is None:
        add(13, "文件夹注册", "error",
            [f"{v} 没在 Quick 里注册"],
            "在 Quick 的 Files 面板添加这个文件夹，否则 agent 读不到")
    else:
        add(13, "文件夹注册", "info", reg_items,
            f"profile: {profile.name}")
        unsynced = [r["path"].replace(home, "~") for r in regs
                    if _within(r["path"], v) and r["sync_status"] != "synced"]
        if unsynced:
            add(13.5, "未同步的文件夹", "warn", unsynced,
                "sync_status 不是 synced —— 云端可能还没拿到这些文件")

    # 枢纽分布（信息项）—— 核心概念该入链多，边缘页少
    if file_edges:
        top = indeg.most_common(5)
        share = sum(c for _, c in top[:3]) / len(file_edges) * 100
        add(15, "枢纽分布", "info",
            [f"{n}: 入链 {c}" for n, c in top],
            f"前 3 名占全部入链的 {share:.0f}%"
            f"（>50% 说明结构偏星形，知识集中在少数几页）")

    # 索引时效（信息项）—— 只给盘上的一半，另一半 agent 用 file_rag_status 取
    if profile:
        facts = _disk_facts(v, regs, home)
        add(10, "索引时效（需你补另一半）", "info",
            [f"{d['path']}: {d['md_files']} 个 .md，最新改动 {d['newest_mtime']}"
             f"（epoch {d['newest_mtime_epoch']}）← {d['newest_file']}"
             for d in facts],
            "拿这里的 epoch 和 file_rag_status 给的 rag_index_time 比："
            "mtime 更大 = 索引过期，对该文件夹 index_directory。"
            "**别自己递归 stat 文件** —— 实测那步在 sandbox 里会拿到旧值")

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

    real = sum(f["count"] for f in findings if f["severity"] in ("error", "warn"))
    summary = (f"内容页 {len(content)} / 边 {len(file_edges)} / "
               f"需处理 {real} 项")

    cannot = ["矛盾", "过期声明", "缺页", "缺交叉引用", "数据缺口"]

    if brief:
        return {
            "ok": real == 0,
            "summary": summary,
            "problems": [{"name": f["name"], "count": f["count"],
                          "items": f["items"][:5]}
                         for f in findings
                         if f["count"] and f["severity"] in ("error", "warn")],
            "cannot_check": cannot,
        }

    return {
        "ok": real == 0,
        "summary": summary,
        "needs_attention": real,
        "total_edges": len(file_edges),
        "findings": sorted(findings, key=lambda x: x["num"]),
        "folders": reg_items,
        "cannot_check": cannot,
        "note": "图谱在云端，实体和边的校验用 kg_search 在 Quick 里做",
    }


@mcp.tool()
def wiki_edges(page: Optional[str] = None, vault: str = DEFAULT_VAULT,
               for_kg: bool = False) -> dict:
    """列出双链关系，可按页过滤。**从 `.md` 解析，不查库。**

    `kg_search` 每个节点最多回 3 条边，页面连接多的时候会漏。这里读文件，
    没有上限，也不依赖边有没有灌进云端图谱。

    `page` 给页名（不含 .md）时只回该页的出链和入链；不给则回全部。

    `for_kg=True`（只在不带 page 时有效）返回**灌边任务直接能用的结构**：

        {"pages": [...], "edges": [{"from": ..., "to": ...}], "dead": [...]}

    - `pages` 是所有涉及的页名 —— 拿去 `kg_search` 批量取 `node_id`
    - `edges` 已去重、已剥代码块、**已剔除死链**（指向不存在的页的不给，
      免得 `kg_add` 凭空建空实体把死链掩盖成正常节点）
    - `dead` 单列出来，报告用，不要灌
    补边排程用这个 —— 把「解析 + 去重 + 剥代码块 + 滤死链」这几步最容易写错的
    活儿包进测过的代码，agent 只管 `kg_search` 填 id + `kg_add`。

    返回的边**按 (from, to) 去重**，并且解析前剥掉了代码块和行内代码 ——
    讲双链语法的页里 `` `[[X]]` `` 是示例，不是链接。自己按 `[[` 硬数
    出来的会更大，那是含重复、含示例的原始 wikilink 数。

    元文件（index / log）的出链算导航不算知识关联，不计入。
    """
    v, _ = _resolve(vault)
    if not v.is_dir():
        return {"ok": False, "error": f"vault 不存在: {v}"}

    pages = _read_pages(v)
    if not pages:
        return {"ok": False, "error": f"{v}/wiki 下没有 .md 文件"}

    content = {k: p for k, p in pages.items() if not p["is_meta"]}
    all_names = set(pages)

    edges: set[tuple[str, str]] = set()
    for name, p in content.items():
        for link in set(p["links"]):
            edges.add((name, link))

    if for_kg and not page:
        live = sorted((f, t) for f, t in edges if t in all_names)
        dead = sorted(f"{f} -> [[{t}]]" for f, t in edges if t not in all_names)
        involved = sorted({n for e in live for n in e})
        return {
            "ok": not dead,
            "pages": involved,
            "edges": [{"from": f, "to": t} for f, t in live],
            "dead": dead,
            "total_edges": len(live),
            "note": "edges 已去重、已滤死链，可直接灌；先对 pages 批量 kg_search "
                    "拿 node_id，再用 from_id/to_id 灌（别用名字，会挂错节点）",
        }

    if page:
        key = page[:-3] if page.endswith(".md") else page
        if key not in pages:
            near = sorted(n for n in all_names if key.lower() in n.lower())
            return {"ok": False, "error": f"没有这一页: {key}",
                    "did_you_mean": near[:8]}
        # 元文件（index / log）不进全局边集，但单独查它时出链要看得到
        out = (sorted(set(pages[key]["links"])) if pages[key]["is_meta"]
               else sorted(t for f, t in edges if f == key))
        inb = sorted(f for f, t in edges if t == key)
        return {
            "ok": True,
            "page": key,
            "is_meta": pages[key]["is_meta"],
            "outbound": out,
            "inbound": inb,
            "dead": [t for t in out if t not in all_names],
            "note": "outbound 里出现在 dead 里的是死链（指向不存在的页）"
                    + ("；元文件的出链是导航，不计入 total_edges"
                       if pages[key]["is_meta"] else ""),
        }

    dead = sorted(f"{f} -> [[{t}]]" for f, t in edges if t not in all_names)
    return {
        "ok": not dead,
        "total_edges": len(edges),
        "total_pages": len(content),
        "edges": sorted(f"{f} -> {t}" for f, t in edges),
        "dead_links": dead,
        "note": "total_edges 是按 (from, to) 去重后的唯一有向边数",
    }


@mcp.tool()
def wiki_index_status(vault: str = DEFAULT_VAULT) -> dict:
    """报文件夹的注册状态 —— 读本机权限层（`allowed_folders.db`）。

    **索引状态本机查不到。** 新版 Quick 把索引建在云端 Quick Space，本机
    没有 chunk 数、没有索引时间戳。想知道索引建到哪一步、什么时候建的，
    在 Quick 里用 `file_rag_status`。

    这里能回答的是注册层的问题：哪些文件夹注册了、agent 有没有读写权限、
    同步状态如何、盘上有多少 `.md`。**注册 ≠ 建了索引** —— 添加文件夹只
    给权限，索引由客户端的文件同步管道另外建。
    """
    v, profile = _resolve(vault)
    if not v.is_dir():
        return {"ok": False, "error": f"vault 不存在: {v}"}
    if profile is None:
        return {
            "ok": False,
            "error": f"{v} 没在 Quick 里注册",
            "how": "在 Quick 的 Files 面板添加这个文件夹并打开 Indexing 开关",
        }

    home = os.path.expanduser("~")
    regs = [r for r in _registrations(profile) if _within(r["path"], v)]
    unsynced = [r["path"].replace(home, "~") for r in regs
                if r["sync_status"] != "synced"]

    return {
        "ok": not unsynced,
        "profile": profile.name,
        "folders": [{
            "path": r["path"].replace(home, "~"),
            "read": bool(r["read_allowed"]),
            "write": bool(r["write_allowed"]),
            "sync_status": r["sync_status"],
            "storage_type": r["storage_type"],
            "added_at": time.strftime("%Y-%m-%d %H:%M:%S",
                                      time.localtime(r["added_at"])),
        } for r in regs],
        "unsynced": unsynced,
        "disk": _disk_facts(v, regs, home),
        "how_to_check_staleness":
            "拿 disk 里每个文件夹的 newest_mtime_epoch，和 file_rag_status 给出的"
            "该文件夹 rag_index_time 比：mtime 更大 = 索引过期，要 index_directory。"
            "**别自己递归 stat 文件** —— 那步在 sandbox 里不可靠，实测会拿到旧值",
        "note": "索引状态（chunk 数、索引时间）在云端，用 file_rag_status 查",
    }


@mcp.tool()
def wiki_hubs(limit: int = 15, vault: str = DEFAULT_VAULT) -> dict:
    """按入链数排名找枢纽页，同时报出零入链的页，并给出准确的边数。

    Lint 时用来判断结构健康：核心概念应该是枢纽（入链多），而新页/边缘页入链少。
    也用来发现「星形结构」—— 一堆页都只连主页、彼此不互链。

    **从文件解析，不查库。** 三个好处：
    - 不受 `kg_search` 的 3 条边上限影响
    - 不依赖边有没有灌进图谱
    - **索引和图谱在云端时它照常可用** —— 这时它是唯一能准确数边的工具

    数出来的 `total_edges` 是**按 (from, to) 去重后的唯一有向边数**，
    且解析前剥掉了代码块和行内代码（讲双链语法的页里 `` `[[...]]` `` 不算链接）。
    如果你另算出一个更大的数，先检查是不是漏了这两步。

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
    # stdio 传输下 stderr 要保持安静：FastMCP 4.x 默认往 stderr 打一大段 ASCII
    # banner 和 INFO 日志，有些 MCP 客户端会把它当成启动异常 —— 表现为「测试连接
    # 成功、工具也列得出来，但状态一直 Failed — retrying」。
    logging.getLogger("FastMCP").setLevel(logging.WARNING)
    logging.getLogger("fastmcp").setLevel(logging.WARNING)
    mcp.run(show_banner=False)
