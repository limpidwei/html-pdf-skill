"""Input preparation and asset localization for html-pdf skill.

Strategy:
1. Parse the HTML with BeautifulSoup and rewrite real DOM attributes
   (img/script/source src, srcset, link href, style attrs, <style> blocks,
   SVG image hrefs). BeautifulSoup is used instead of regex so attributes
   in any order are handled correctly.
2. Additionally rewrite asset references inside <script> text (JS template
   literals often contain raw markup like `<img src="...">`).
3. Remote assets are downloaded; local relative assets are copied. All are
   stored in <work>/assets/ and referenced relatively.
"""

import re
import urllib.parse
from pathlib import Path
from typing import Dict, Optional
from urllib.request import url2pathname

_SKIP_PREFIXES = ("data:", "#", "javascript:", "mailto:", "tel:", "blob:", "about:", "${")

# Some servers block or throttle default library user-agents
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

_CSS_URL_RE = re.compile(r'url\(\s*(["\']?)([^"\')]+?)\1\s*\)')
_CSS_IMPORT_RE = re.compile(r'@import\s+(["\'])([^"\']+)\1')
_JS_SRC_RE = re.compile(r'src\s*=\s*(["\'])([^"\']+)\1')

_SRC_TAGS = ("img", "script", "source", "video", "audio", "iframe", "embed", "track", "input")
_RESOURCE_RELS = {"stylesheet", "icon", "shortcut icon", "apple-touch-icon", "preload", "prefetch", "manifest"}


def is_url(value: str) -> bool:
    """Return True if value is an http(s) URL."""
    return value.startswith(("http://", "https://"))


def is_skippable(ref: str) -> bool:
    """References that must never be rewritten (anchors, data URIs, JS placeholders...)."""
    ref = ref.strip()
    if not ref:
        return True
    return ref.startswith(_SKIP_PREFIXES)


_META_CHARSET_RE = re.compile(rb'<meta[^>]+charset\s*=\s*["\']?\s*([\w\-]+)', re.IGNORECASE)


def decode_bytes(raw: bytes, encoding_hint: Optional[str] = None) -> str:
    """Decode bytes to text.

    Priority: <meta charset> declaration > UTF-8 > explicit hint > charset
    detection. The HTTP header hint (requests' response.encoding) is tried
    late because it defaults to ISO-8859-1 when the server omits charset,
    and ISO-8859-1 decodes ANY bytes into mojibake without ever failing.
    Meta declarations and UTF-8 are far more reliable for HTML.
    """
    candidates = []

    head = raw[:4096]
    m = _META_CHARSET_RE.search(head)
    if m:
        try:
            candidates.append(m.group(1).decode("ascii", errors="ignore"))
        except Exception:
            pass

    candidates.append("utf-8")

    if encoding_hint and encoding_hint.lower() not in ("iso-8859-1", "latin-1", "ascii"):
        candidates.append(encoding_hint)

    for enc in candidates:
        if not enc:
            continue
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue

    try:
        from charset_normalizer import from_bytes

        best = from_bytes(raw).best()
        if best is not None:
            return str(best)
    except ImportError:
        pass
    return raw.decode("utf-8", errors="replace")


class AssetLocalizer:
    """Downloads/copies assets into assets_dir and returns relative references."""

    def __init__(self, base_url: str, assets_dir: Path, html_dir: Path, session=None):
        self.base_url = base_url
        self.assets_dir = assets_dir
        self.html_dir = html_dir
        self.cache: Dict[str, str] = {}
        if session is not None:
            self.session = session
        else:
            try:
                import requests

                self.session = requests.Session()
                self.session.headers.update({"User-Agent": _USER_AGENT})
            except ImportError:
                self.session = None

    def localize(self, ref: str) -> str:
        """Return a rewritten reference, or the original if not localizable."""
        if is_skippable(ref):
            return ref

        absolute = urllib.parse.urljoin(self.base_url, ref)
        if absolute in self.cache:
            return self.cache[absolute]

        result = ref
        try:
            if is_url(absolute) or absolute.startswith("file://"):
                data = self._fetch(absolute)
                local_path = self._store(absolute, data)
                result = local_path.relative_to(self.html_dir).as_posix()
        except Exception as exc:
            print(f"WARNING: failed to localize asset {absolute}: {exc}")

        self.cache[absolute] = result
        return result

    def _fetch(self, absolute: str) -> bytes:
        if absolute.startswith("file://"):
            fs_path = Path(url2pathname(urllib.parse.urlparse(absolute).path))
            return fs_path.read_bytes()
        if self.session is None:
            raise RuntimeError("requests is required for downloading assets")
        response = self.session.get(absolute, timeout=60)
        response.raise_for_status()
        return response.content

    def _store(self, absolute: str, data: bytes) -> Path:
        name = Path(urllib.parse.urlparse(absolute).path).name or "asset"
        name = re.sub(r"[^\w\-.]+", "_", name) or "asset"

        local = self.assets_dir / name
        stem, suffix = local.stem, local.suffix
        counter = 1
        while local.exists():
            local = self.assets_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        local.write_bytes(data)
        return local


def rewrite_srcset(value: str, localizer: AssetLocalizer) -> str:
    """Rewrite every URL in a srcset attribute, keeping descriptors."""
    parts = []
    for entry in value.split(","):
        entry = entry.strip()
        if not entry:
            continue
        bits = entry.split()
        bits[0] = localizer.localize(bits[0])
        parts.append(" ".join(bits))
    return ", ".join(parts)


def rewrite_css(css: str, localizer: AssetLocalizer) -> str:
    """Rewrite url(...) and @import references in a CSS fragment."""

    def repl_url(m: re.Match) -> str:
        quote, ref = m.group(1), m.group(2)
        return f"url({quote}{localizer.localize(ref)}{quote})"

    def repl_import(m: re.Match) -> str:
        quote, ref = m.group(1), m.group(2)
        return f"@import {quote}{localizer.localize(ref)}{quote}"

    css = _CSS_URL_RE.sub(repl_url, css)
    css = _CSS_IMPORT_RE.sub(repl_import, css)
    return css


def rewrite_js_text(js: str, localizer: AssetLocalizer) -> str:
    """Rewrite src="..." and url(...) references inside JS text (template literals)."""

    def repl_src(m: re.Match) -> str:
        quote, ref = m.group(1), m.group(2)
        return f"src={quote}{localizer.localize(ref)}{quote}"

    js = _JS_SRC_RE.sub(repl_src, js)
    js = rewrite_css(js, localizer)
    return js


def rewrite_html(html: str, localizer: AssetLocalizer) -> str:
    """Rewrite all localizable asset references in the document."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # 1. src / srcset / poster / data-src on media tags (any attribute order)
    for tag in soup.find_all(_SRC_TAGS):
        for attr in ("src", "data-src", "poster"):
            if tag.get(attr):
                tag[attr] = localizer.localize(tag[attr])
        if tag.get("srcset"):
            tag["srcset"] = rewrite_srcset(tag["srcset"], localizer)

    # 2. <link> resource hrefs only (never touches <a href> navigation links)
    for tag in soup.find_all("link"):
        rels = {r.lower() for r in (tag.get("rel") or [])}
        if rels & _RESOURCE_RELS and tag.get("href"):
            tag["href"] = localizer.localize(tag["href"])

    # 3. Inline style attributes
    for tag in soup.find_all(style=True):
        tag["style"] = rewrite_css(tag["style"], localizer)

    # 4. <style> blocks
    for tag in soup.find_all("style"):
        if tag.string:
            tag.string.replace_with(rewrite_css(tag.string, localizer))

    # 5. SVG <image> references (xlink:href / href); fragment-only refs are skipped
    for tag in soup.find_all("image"):
        for attr in ("xlink:href", "href"):
            if tag.get(attr):
                tag[attr] = localizer.localize(tag[attr])

    # 6. <script> inline text: JS template literals often contain raw markup
    for tag in soup.find_all("script"):
        if tag.get("src"):
            continue
        if tag.string:
            tag.string.replace_with(rewrite_js_text(tag.string, localizer))

    return str(soup)


def prepare_input(value: str, work_dir: Path) -> Path:
    """Prepare HTML input: download URL or copy local file, then localize assets."""
    work_dir = work_dir.expanduser().resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = work_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    if is_url(value):
        try:
            import requests
        except ImportError:
            raise RuntimeError("requests is required to download URLs")

        response = requests.get(value, timeout=60, headers={"User-Agent": _USER_AGENT})
        response.raise_for_status()
        html_text = decode_bytes(response.content, response.encoding)
        html_path = work_dir / "index.html"
        base_url = value
    else:
        src = Path(value).expanduser().resolve()
        if not src.exists():
            raise FileNotFoundError(f"HTML file not found: {src}")
        html_text = decode_bytes(src.read_bytes())
        html_path = work_dir / src.name
        # Resolve relative asset refs against the ORIGINAL file's directory
        base_url = src.parent.as_uri() + "/"

    localizer = AssetLocalizer(base_url, assets_dir, work_dir)
    html_path.write_text(rewrite_html(html_text, localizer), encoding="utf-8")
    return html_path
