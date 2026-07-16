# html-pdf

一个跨平台（Windows / macOS / Linux）的 Claude Code skill，用于把本地 HTML 文件或网页 URL 转成 PDF。

核心思路：
1. 把 HTML 里的远程资源（图片、CSS 背景图等）全部下载到本地；
2. 用 Playwright + Chromium 按原尺寸渲染每一页/每一张 slide；
3. 用 `img2pdf` 把截图合成为 PDF；
4. 可选生成 2x 高清版。

这样可避免因浏览器打印模式、相对路径、JS 动态生成内容等导致的图片丢失、文字截断、排版错乱。

## 适用场景

- HTML 幻灯片 / 演示稿转 PDF
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
# 标准清晰度
python -m html_pdf --input ./slides.html --output-dir ./pdf-output

# 同时生成 2x 高清版
python -m html_pdf --input ./slides.html --output-dir ./pdf-output --hd

# URL 输入
python -m html_pdf --input https://example.com/page.html --output-dir ./pdf-output --hd
```

输出文件：
- `pdf-output/output.pdf` — 标准版（与原始 HTML 同分辨率）
- `pdf-output/output-hd.pdf` — 高清版（2x 分辨率）

## 跨平台说明

本工具在 Windows、macOS、Linux 上均可运行：
- 路径处理使用 Python `pathlib`；
- 命令检测使用 `shutil.which`；
- 系统包安装失败时会给出对应平台的安装命令（winget/choco / brew / apt / dnf / pacman）。

## 自动触发 Hook（可选）

如需更可靠的自动触发，可在 `~/.claude/settings.json` 中添加：

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

## 项目结构

```
html-pdf-skill/
├── SKILL.md                  # Claude Code skill 描述
├── README.md                 # 本文件
├── pyproject.toml            # Python 包配置
├── requirements.txt          # 依赖列表
├── scripts/
│   └── setup_env.py          # 一键环境检测与安装
└── src/html_pdf/
    ├── __init__.py
    ├── __main__.py           # CLI 入口
    ├── check_deps.py         # 环境检查
    ├── install_deps.py       # 依赖安装
    ├── fetcher.py            # 资源本地化
    ├── renderer.py           # Playwright 截图
    └── pdf_builder.py        # PDF 合成
```

## License

MIT
