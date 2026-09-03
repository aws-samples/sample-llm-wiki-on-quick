# 抽取规则模板

用于 `kg_folder_configure` 的 `special_instructions`。把 Quick 默认的「从正文挖命名实体」
改成「一个文件 = 一个实体」。

## 用法

在 Quick 对话里：

```
kg_folder_configure(
  folder_path="~/Wiki-Vault/wiki",
  special_instructions="<下面这段>"
)
kg_folder_rebuild(folder_path="~/Wiki-Vault/wiki")
```

`folder_path` 必须是**已注册的文件夹路径**（`folders` 表里的行），不是任意子目录。
整个 `wiki/` 注册成一行，四类页面都在它下面，所以配一次就够。

要给某一类单独配不同规则（比如只让 `sources/` 抽更细的实体），得先把它拆出来
注册成独立一行 —— 但注意父目录 `wiki/` 已开索引时无法再加子目录，
需要先移除父行、再分别注册各子目录。

## 规则正文

```
这个文件夹是 LLM Wiki，不是普通文档集。抽取时严格遵守：

1. 每个 .md 文件本身就是一个实体，实体名 = 文件名去掉 .md 后缀。
   一个文件产出恰好一个实体，不多也不少。

2. 不要从散文正文里抽取任何额外实体。正文里出现的 API 名、版本号、
   事件名等术语，不要建成独立实体。

3. frontmatter 的 type 字段作为节点 category（concept / entity / note），
   不要用 Service / DefinedTerm / Decision 这类默认类型。

4. frontmatter 的 tags 存进 properties.tags，status 存进 properties.status。

5. frontmatter 的 summary 字段（若有）直接作为实体 summary，
   不要加「LLM Wiki 页面：」这类模板前缀，也不要把「## 关联」小节的
   wikilink 列表拼进 summary —— 那会稀释语义向量。

6. 若某页 frontmatter 有 status: superseded 且正文写明被某页取代，
   额外建一条 relation = supersedes 的边（从新页指向旧页），
   properties.reason 写明判断依据。
```

## 为什么需要这段

Quick 的 Knowledge Graph 开关说明是 "Extract people, projects, and dates" ——
它面向会议记录和邮件设计，在正文里挖命名实体。对 wiki 场景，默认行为会：

- 把正文里提到的术语建成独立实体（而不是把文件当实体）
- 用自己的本体（`Service` / `DefinedTerm` / `Decision`）而忽略 frontmatter 的 `type`

加上这段规则后，category 会对齐 frontmatter，正文术语不再被当成实体。

## 一个改不了的行为

`special_instructions` 是附加到抽取 prompt 后面的文字，它能改「抽什么、怎么归类」，
但改不了管线行为 —— **本地文件抽取不产 edge**。即使在规则里明确要求「每个 `[[X]]`
建一条边」，`edges` 表也仍然是空的。

所以 `[[双链]]` 必须经 `kg_add` 显式灌入，见 `sync-task-prompt.md`。
