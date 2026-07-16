---
name: html-pdf
description: Convert HTML files or URLs to PDF. Use whenever the user uploads an HTML file and asks to convert, export, save, or print it to PDF; when they provide an HTTP/HTTPS URL and ask for a PDF capture; when they mention HTML-to-PDF, webpage to PDF, slide deck to PDF, presentation HTML to PDF, or want a high-resolution PDF render of a local or remote HTML page. Also use when the user wants both a standard PDF and an optional HD (2x) PDF. This skill works cross-platform on Windows, macOS, and Linux.
version: 1.0.0
author: limpidwei
license: MIT
tags: [pdf, html, conversion, playwright, screenshot, cross-platform]
---

# html-pdf

把 HTML 文件或网页 URL 转成 PDF，尤其适合幻灯片、演示稿、单页长图等场景。

## 触发条件

- 用户上传了 `.html`/`.htm` 文件并要求转成 PDF；
- 用户给了一个 `http(s)://` URL 并要求保存/导出为 PDF；
- 用户提到 "HTML 转 PDF"、"网页转 PDF"、"slide 转 PDF"、"演示稿转 PDF" 等。

## 工作流

1. **确认输入**：询问或识别用户提供的本地 HTML 路径 / URL。
2. **确定输出目录**：默认使用输入文件所在目录；URL 输入默认用 `~/html-pdf-output/<timestamp>/`。
3. **环境检查**：运行 `python scripts/setup_env.py` 检查并安装依赖（Playwright、Chromium、img2pdf 等）。
4. **执行转换**：运行
   ```bash
   python -m html_pdf --input "<INPUT>" --output-dir "<OUTPUT_DIR>" [--hd]
   ```
5. **验证输出**：确认 `output.pdf`（以及 `output-hd.pdf`）已生成且非空。
6. **报告结果**：向用户展示生成文件的绝对路径和大小。

## 依赖清单

- Python >= 3.10
- `playwright` + Chromium 浏览器
- `img2pdf`
- `requests`
- `beautifulsoup4`
- 系统命令：`curl`、`git`

## 跨平台说明

本 skill 在 Windows、macOS、Linux 上均可运行：
- 所有路径使用 `pathlib` 处理；
- 命令检测使用 `shutil.which`；
- 系统包安装提示按平台自动切换（winget/choco / brew / apt / dnf / pacman）。

## 高级：自动触发 Hook

如需让 Claude 在用户上传 HTML 时更可靠地自动调用本 skill，可在 `~/.claude/settings.json` 中加入：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "name": "html-pdf-trigger",
        "pattern": "(?i)\\.(html?|htm)\\b|convert\\s+.*html\\s+.*pdf|html\\s+to\\s+pdf|save\\s+html\\s+pdf|print\\s+html|pdf\\s+of\\s+html|slide\\s+.*pdf|presentation\\s+.*pdf",
        "skill": "html-pdf"
      }
    ]
  }
}
```

## 命令行独立使用

安装后可脱离 Claude 直接使用：

```bash
# 标准清晰度
python -m html_pdf --input ./slides.html --output-dir ./pdf-output

# 同时生成 2x 高清版
python -m html_pdf --input ./slides.html --output-dir ./pdf-output --hd

# URL 输入
python -m html_pdf --input https://example.com/page.html --output-dir ./pdf-output --hd
```
