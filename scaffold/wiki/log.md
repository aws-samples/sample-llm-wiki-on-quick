---
type: log
tags: [meta]
status: developing
summary: 只追加的操作日志。每条以「## [YYYY-MM-DD] 操作 | 标题」开头，可用 grep 解析。
---
# Log

只追加的操作记录。**永不删除历史条目。**

每条以固定前缀开头，便于用 unix 工具解析：

```
grep "^## \[" log.md | tail -5     # 最近五条
```

格式：`## [YYYY-MM-DD] <ingest|query|lint> | <标题>`

---
