---
name: html-pdf
description: Convert HTML files or URLs to PDF. Use whenever the user uploads an HTML file and asks to convert, export, save, or print it to PDF; when they provide an HTTP/HTTPS URL and ask for a PDF capture; when they mention HTML-to-PDF, webpage to PDF, slide deck to PDF, presentation HTML to PDF, or want a high-resolution PDF render of a local or remote HTML page. Also use when the user wants both a standard PDF and an optional HD (2x) PDF. This skill works cross-platform on Windows, macOS, and Linux.
version: 1.0.1
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

1. **确认输入**：识别用户提供的本地 HTML 路径 / URL。
2. **环境检查**（首次使用或怀疑环境缺失时）：运行本 skill 目录下的
   ```bash
   python "<SKILL_DIR>/scripts/setup_env.py"
   ```
   其中 `<SKILL_DIR>` 为本 skill 的安装目录（通常是 `~/.claude/skills/html-pdf`）。该脚本会检查并安装 Python 依赖与 Chromium。
3. **执行转换**：
   ```bash
   python -m html_pdf --input "<INPUT>" [--output-dir "<DIR>"] [--hd]
   ```
   - `--output-dir` 可省略：本地文件默认输出到文件所在目录，URL 默认输出到 `~/html-pdf-output/<timestamp>/`；
   - `--hd` 额外生成 2 倍分辨率高清版；
   - `--wait <ms>` 调整页面加载后等待时间（默认 3000，图片多/网络慢时加大）。
4. **验证输出**：确认 `output.pdf`（以及 `output-hd.pdf`）已生成且非空。
5. **报告结果**：向用户展示生成文件的绝对路径和大小。
6. 如转换失败，先按报错提示运行 `setup_env.py`；仍失败则把完整报错展示给用户。

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

## 高级：自动触发 Hook（可选）

如需在用户提到 HTML 转 PDF 时给 Claude 额外提示，可在 `~/.claude/settings.json` 中加入（这是 Claude Code 真实支持的 hook 格式）：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Users/<用户名>/.claude/skills/html-pdf/scripts/hook_trigger.py\""
          }
        ]
      }
    ]
  }
}
```

`hook_trigger.py` 从 stdin 读取 prompt JSON，命中 HTML→PDF 意图时输出 `additionalContext` 提示 Claude 使用本 skill；未命中时不输出任何内容。macOS/Linux 下把 `command` 中的路径换成 `~/.claude/skills/html-pdf/scripts/hook_trigger.py` 即可。

## 命令行独立使用

安装后可脱离 Claude 直接使用：

```bash
# 标准清晰度（本地文件，输出到文件所在目录）
python -m html_pdf --input ./slides.html

# 同时生成 2x 高清版
python -m html_pdf --input ./slides.html --output-dir ./pdf-output --hd

# URL 输入
python -m html_pdf --input https://example.com/page.html --hd
```
