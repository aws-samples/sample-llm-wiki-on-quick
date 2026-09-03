---
type: entity
tags: [obsidian, tool, markdown, editor]
status: developing
summary: 基于本地 markdown 文件的知识管理工具；在 LLM Wiki 模式里充当人的浏览端与「IDE」，提供 graph view、Marp、Dataview、Web Clipper 等能力。
---
# Obsidian

基于本地 markdown 文件的知识管理 / 笔记工具。在 [[LLM Wiki]] 模式里，它是人这一侧的**浏览端**：作者一边开 LLM agent、一边开 Obsidian，LLM 做编辑，人实时浏览结果（跟链接、看 graph、读更新的页）。原文类比：**Obsidian 是 IDE，LLM 是程序员，wiki 是代码库**。

## 相关能力（原文提到的周边）

- **graph view**——看 wiki 形状的最佳方式：什么连着什么、哪些页是枢纽、哪些是孤儿。
- **Marp**——基于 markdown 的幻灯片格式，Obsidian 有插件，可直接从 wiki 内容生成演示。
- **Dataview**——插件，对页面 frontmatter 跑查询，生成动态表格/列表（依赖 wiki 页有 YAML frontmatter）。
- **Web Clipper**——浏览器扩展，把网页文章转成 markdown，快速入 raw 集合；配合下载热键可把图片下到本地（如 `raw/assets/`）。

> 这些周边工具原文均只一句带过，暂并入本页；有专门素材时再各自单开。

常见叫法：Obsidian、黑曜石、markdown 笔记、本地知识库工具、双链笔记、graph view、Dataview、Marp、Web Clipper 剪藏。

## 关联
- 用于模式: [[LLM Wiki]]
- 检索工具: [[qmd]]
