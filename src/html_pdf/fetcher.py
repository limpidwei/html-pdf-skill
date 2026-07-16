"""Input preparation and asset localization for html-pdf skill."""

import re
import urllib.parse
from pathlib import Path
from typing import Set


def resolve_url(base: str, rel: str) -> str:
    """Resolve a relative URL against a base URL, skipping template literals."""
    if not rel or rel.startswith(("${", "#", "data:")):
        return rel
    return urllib.parse.urljoin(base, rel)


def is_url(value: str) -> bool:
    """Return True if value is an http(s) URL."""
    return value.startswith(("http://", "https://")) and not value.startswith("${")


def make_relative_to(path: Path, base: Path) -> str:
    """Return a POSIX relative path string from base to path."""
    return path.relative_to(base).as_posix()


def download_asset(url: str, assets_dir: Path, session=None) -> Path:
    """Download a remote asset and return its local path."""
    try:
        import requests
    except ImportError:
        raise RuntimeError("requests is required for downloading assets")

    parsed = urllib.parse.urlparse(url)
    name = Path(parsed.path).name or "asset"
    # Sanitize filename
    name = re.sub(r"[^\w\-.]+", "_", name)
    if not name:
        name = "asset"

    local_path = assets_dir / name
    counter = 1
    stem = local_path.stem
    suffix = local_path.suffix
    while local_path.exists():
        local_path = assets_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    if session is None:
        session = requests.Session()

    try:
        response = session.get(url, timeout=60)
        response.raise_for_status()
        local_path.write_bytes(response.content)
    except Exception as exc:
        print(f"WARNING: failed to download asset {url}: {exc}")
        raise

    return local_path


def collect_asset_urls(html: str, base_url: str) -> Set[str]:
    """Collect all remote asset URLs referenced in HTML."""
    urls: Set[str] = set()

    # img / script / source src
    for match in re.finditer(r'<(img|script|source|video|audio|iframe)\s+[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE):
        urls.add(resolve_url(base_url, match.group(2)))

    # link href
    for match in re.finditer(r'<link\s+[^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE):
        urls.add(resolve_url(base_url, match.group(1)))

    # CSS url() including background-image
    for match in re.finditer(r'url\((["\']?)([^"\')]+)\1\)', html):
        urls.add(resolve_url(base_url, match.group(2)))

    return {u for u in urls if is_url(u)}


def rewrite_html(html: str, base_url: str, assets_dir: Path, html_dir: Path, session=None) -> str:
    """Rewrite HTML so all remote assets point to local copies."""
    if session is None:
        try:
            import requests
            session = requests.Session()
        except ImportError:
            session = None

    def local_url(remote_url: str) -> str:
        if not is_url(remote_url):
            return remote_url
        try:
            local_path = download_asset(remote_url, assets_dir, session)
            return make_relative_to(local_path, html_dir)
        except Exception:
            return remote_url

    # Rewrite src attributes
    def replace_src(match: re.Match) -> str:
        tag = match.group(1)
        quote = match.group(2)
        url = match.group(3)
        resolved = resolve_url(base_url, url)
        if is_url(resolved):
            return f'<{tag} src={quote}{local_url(resolved)}{quote}'
        return match.group(0)

    html = re.sub(
        r'<(img|script|source|video|audio|iframe)\s+([^>]*?)src=["\']([^"\']+)["\']',
        replace_src,
        html,
        flags=re.IGNORECASE,
    )

    # Rewrite href attributes for link tags
    def replace_href(match: re.Match) -> str:
        quote = match.group(1)
        url = match.group(2)
        resolved = resolve_url(base_url, url)
        if is_url(resolved):
            return f'href={quote}{local_url(resolved)}{quote}'
        return match.group(0)

    html = re.sub(
        r'href=["\']([^"\']+)["\']',
        replace_href,
        html,
        flags=re.IGNORECASE,
    )

    # Rewrite CSS url()
    def replace_url(match: re.Match) -> str:
        quote = match.group(1)
        url = match.group(2)
        resolved = resolve_url(base_url, url)
        if is_url(resolved):
            return f'url({quote}{local_url(resolved)}{quote})'
        return match.group(0)

    html = re.sub(r'url\((["\']?)([^"\')]+)\1\)', replace_url, html)

    return html


def prepare_input(value: str, work_dir: Path) -> Path:
    """Prepare HTML input: download URL or localize assets in local file."""
    work_dir = work_dir.expanduser().resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    if is_url(value):
        try:
            import requests
        except ImportError:
            raise RuntimeError("requests is required to download URLs")

        response = requests.get(value, timeout=60)
        response.raise_for_status()
        html_path = work_dir / "index.html"

        # Try UTF-8 first (common for modern HTML), then fall back to requests' detected encoding
        try:
            html_text = response.content.decode("utf-8")
        except UnicodeDecodeError:
            response.encoding = response.apparent_encoding
            html_text = response.text

        html_path.write_text(html_text, encoding="utf-8")
        base_url = value
    else:
        html_path = Path(value).expanduser().resolve()
        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path}")
        # Copy local HTML to work dir to avoid polluting original location
        dest_path = work_dir / html_path.name
        dest_path.write_text(html_path.read_text(encoding="utf-8"), encoding="utf-8")
        html_path = dest_path
        base_url = html_path.parent.as_uri() + "/"

    html = html_path.read_text(encoding="utf-8")
    assets_dir = work_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    localized_html = rewrite_html(html, base_url, assets_dir, html_path.parent)
    html_path.write_text(localized_html, encoding="utf-8")

    return html_path
