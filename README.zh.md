# DocSpine

<p align="center">
  <a href="README.md">English</a> &bull;
  <a href="README.zh.md">中文</a>
</p>

---

PDF 对 AI Agent 来说太长了，无法高效阅读。DocSpine 将 PDF 转换为可导航的 Markdown 文件树，让 Agent 只读取需要的部分。

## 工作原理

DocSpine 不是把整个 PDF 文本丢给 Agent，而是生成一棵树，每个节点包含：

- `index.md` — 章节列表，带有字数、是否含表格、页码等提示，Agent 可据此决定要打开哪些节点
- `content.md` — 该章节的完整文本
- `node.json` — 机器可读的元数据

Agent 从根目录的 `index.md` 出发，读取提示信息，只钻取与当前任务相关的章节。

## 输出格式

```text
out/
  AGENTS.md         ← 从这里开始阅读
  index.md          ← 导航入口
  content.md        ← 根节点文本
  node.json         ← 根节点元数据
  sections/
    01-section-slug/
      index.md
      content.md
      node.json
```

### index.md 示例

```markdown
# 冰轮环境技术股份有限公司

## Subsections
- [第一节 重要提示、目录和释义](sections/01-.../index.md) — 381 words · tables · p.2
- [第二节 公司简介和主要财务指标](sections/02-.../index.md) — 567 words · tables · p.6
- [第三节 管理层讨论与分析](sections/03-.../index.md) — 3,017 words · tables · p.10
```

### node.json 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 节点唯一标识符 |
| `title` | string | 章节标题 |
| `slug` | string | URL 友好的标题 |
| `level` | int | 树中深度（0 为根节点） |
| `word_count` | int | 本章节内容的字数 |
| `has_tables` | bool | 章节是否包含 Markdown 表格 |
| `asset_count` | int | 引用的资产数量（图片、表格等） |
| `asset_types` | string[] | 存在的资产类型列表 |
| `page_start` | int? | 在源 PDF 中的起始页码（如有） |
| `children` | string[] | 子节点 ID 列表 |

## 使用方法

安装依赖：

```bash
uv sync --group dev
```

从 PDF 构建文档树：

```bash
uv run docspine build input.pdf --out out
```

调试时限制页数范围：

```bash
uv run docspine build input.pdf --out out --pages 1-30
```

运行测试：

```bash
uv run --group dev pytest
```

## AI Agent 使用指引

从输出根目录的 `AGENTS.md` 和 `index.md` 开始阅读。根据链接上的提示决定读什么：

- 需要详细内容时，跳过 `word_count` 较低的章节
- 需要结构化数据时，优先查看 `has_tables` 为 true 的章节
- 需要对照源文件时，使用 `page_start` 定位原始 PDF 页码
- 确认章节相关后再打开 `content.md`，避免浪费 token
- 通过 `sections/` 子目录递归获取更深层的层级结构

转换时使用的结构优先级为：**PDF 书签大纲 → 文本目录 → 标题扫描**。
