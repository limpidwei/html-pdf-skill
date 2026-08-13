# html-pdf

一个跨平台（Windows / macOS / Linux）的 Claude Code skill，用于把本地 HTML 文件或网页 URL 转成 PDF。支持两种模式：

- **raster（默认）**：把 HTML 里的远程资源全部本地化 → 用 Playwright + Chromium 按原尺寸逐页截图 → `img2pdf` 合成。像素级还原，适合幻灯片、演示稿、海报、单页长图。**产出是纯图片 PDF，文字不可选中**。
- **print**：Chromium 打印引擎直接生成矢量 PDF，**文字可选中**。适合文章、文档、报告类 HTML。

这样可避免因浏览器打印模式、相对路径、JS 动态生成内容等导致的图片丢失、文字截断、排版错乱。

## 适用场景

- HTML 幻灯片 / 演示稿转 PDF（用 `raster`）
- 文章 / 文档 / 长文报告转 PDF，要能选中文字（用 `print`）
- 网页截图保存为 PDF
- 需要保留原始样式、背景图、emoji、渐变效果的页面

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/limpidwei/html-pdf-skill.git
cd html-pdf-skill
```

### 2. 安装依赖

```bash
python scripts/setup_env.py
```

该脚本会检查并自动安装：
- Python 包：`playwright`、`img2pdf`、`requests`、`beautifulsoup4`
- Playwright Chromium 浏览器
- 提示安装系统命令 `curl` 和 `git`（若缺失）

## 使用

### 作为 Claude Code skill

把本仓库复制到 Claude Code skill 目录：

```bash
# Windows (PowerShell)
Copy-Item -Recurse -Force . "$env:USERPROFILE\.claude\skills\html-pdf"

# macOS / Linux
cp -R . ~/.claude/skills/html-pdf
```

之后，当你在对话中上传 HTML 文件并说“转成 PDF”时，Claude 会自动调用本 skill。

### 命令行独立使用

```bash
# 幻灯片：标准清晰度截图版（本地文件，默认输出到文件所在目录）
python -m html_pdf --input ./slides.html

# 幻灯片：同时生成 2x 高清版
python -m html_pdf --input ./slides.html --output-dir ./pdf-output --hd

# 文章/文档：文字可选中的矢量 PDF
python -m html_pdf --input ./article.html --mode print

# 文章横向版式
python -m html_pdf --input ./article.html --mode print --landscape

# URL 输入（默认输出到 ~/html-pdf-output/<timestamp>/）
python -m html_pdf --input https://example.com/page.html --hd

# 页面加载慢时加大等待时间（毫秒）
python -m html_pdf --input ./slides.html --wait 5000
```

输出文件：
- `output.pdf` — 标准版（raster 模式与原始 HTML 同分辨率；print 模式为 A4 矢量 PDF）
- `output-hd.pdf` — 高清版（2x 分辨率，仅在 raster + `--hd` 时生成；print 模式忽略 `--hd`，矢量输出分辨率无关）

## 跨平台说明

本工具在 Windows、macOS、Linux 上均可运行：
- 路径处理使用 Python `pathlib`；
- 命令检测使用 `shutil.which`；
- 系统包安装失败时会给出对应平台的安装命令（winget/choco / brew / apt / dnf / pacman）。

## 自动触发 Hook（可选）

如需在用户提到 HTML 转 PDF 时给 Claude 额外提示，可在 `~/.claude/settings.json` 中添加（Claude Code 真实支持的 hook 格式）：

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

`hook_trigger.py` 从 stdin 读取 prompt JSON，命中 HTML→PDF 意图时输出 `additionalContext`，提示 Claude 调用本 skill；未命中时静默退出。macOS/Linux 下把路径换成 `~/.claude/skills/html-pdf/scripts/hook_trigger.py`。

## 项目结构

```
html-pdf-skill/
├── SKILL.md                  # Claude Code skill 描述
├── README.md                 # 本文件
├── pyproject.toml            # Python 包配置
├── requirements.txt          # 依赖列表
├── scripts/
│   ├── setup_env.py          # 一键环境检测与安装
│   └── hook_trigger.py       # UserPromptSubmit hook（可选自动触发）
└── src/html_pdf/
    ├── __init__.py
    ├── __main__.py           # CLI 入口
    ├── check_deps.py         # 环境检查
    ├── install_deps.py       # 依赖安装
    ├── fetcher.py            # 资源本地化
    ├── renderer.py           # Playwright 截图（raster 模式）
    ├── printer.py            # Chromium 打印引擎（print 模式）
    └── pdf_builder.py        # PDF 合成
```

## License

MIT
