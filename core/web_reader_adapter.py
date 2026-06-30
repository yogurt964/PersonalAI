import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from core.tool_adapter import ToolAdapter, ToolResult


URL_PATTERN = re.compile(r"https?://[^\s<>'\"]+", re.IGNORECASE)
TRAILING_URL_CHARS = ".,;:、。)]}）】」』"


def extract_url_from_text(text):
    """テキストから最初の http / https URL を取り出します。"""
    if not text:
        return None

    match = URL_PATTERN.search(str(text))

    if match is None:
        return None

    return match.group(0).rstrip(TRAILING_URL_CHARS)


def strip_html_to_text(html):
    """HTMLから本文テキストだけをできるだけ安全に取り出します。"""
    parsed = _parse_html(html)
    return parsed["text"]


class WebReaderAdapter(ToolAdapter):
    """最小実用版のWeb Reader Adapterです。

    fetcherを差し込めるようにして、自動checkでは実Webアクセスを避けます。
    """

    def __init__(
        self,
        fetcher=None,
        timeout=10,
        max_text_chars=12000,
        max_fetch_bytes=1024 * 1024,
        user_agent="PersonalAI-WebReader/2.0",
    ):
        super().__init__(
            name="web_reader",
            description="Read a web page from a URL.",
        )
        self.fetcher = fetcher
        self.timeout = timeout
        self.max_text_chars = max_text_chars
        self.max_fetch_bytes = max_fetch_bytes
        self.user_agent = user_agent

    def is_available(self):
        return True

    def execute(self, request):
        """ToolRequestを受け取り、Webページ本文をToolResultとして返します。"""
        url = self._get_url_from_request(request)

        if not url:
            return ToolResult(
                success=False,
                message="URLが見つからないため、Web Readerは実行していません。",
                data=None,
                error="missing_url",
                executed=False,
            )

        if not _is_http_url(url):
            return ToolResult(
                success=False,
                message="http / https URLではないため、Web Readerは実行していません。",
                data={"url": url},
                error="invalid_url",
                executed=False,
            )

        try:
            fetch_result = self._fetch(url)
        except Exception as error:
            return ToolResult(
                success=False,
                message="Webページの取得に失敗しました。読めたふりはしません。",
                data={"url": url},
                error=str(error),
                executed=True,
            )

        html = _get_fetch_value(fetch_result, "html", "")
        final_url = _get_fetch_value(fetch_result, "final_url", url)
        status_code = _get_fetch_value(fetch_result, "status_code")
        content_type = _get_fetch_value(fetch_result, "content_type")
        truncated_fetch = bool(_get_fetch_value(fetch_result, "truncated", False))

        parsed = _parse_html(html)
        text = parsed["text"]
        title = parsed["title"]
        truncated_text = len(text) > self.max_text_chars
        limited_text = text[: self.max_text_chars]

        if not limited_text:
            return ToolResult(
                success=False,
                message="Webページは取得しましたが、本文テキストを取り出せませんでした。",
                data={
                    "url": url,
                    "final_url": final_url,
                    "title": title,
                    "status_code": status_code,
                    "content_type": content_type,
                },
                error="empty_text",
                executed=True,
            )

        return ToolResult(
            success=True,
            message="Webページを読み取りました。",
            data={
                "url": url,
                "final_url": final_url,
                "title": title,
                "text": limited_text,
                "text_preview": limited_text[:500],
                "status_code": status_code,
                "content_type": content_type,
                "truncated": truncated_text or truncated_fetch,
            },
            error=None,
            executed=True,
        )

    def _get_url_from_request(self, request):
        input_data = getattr(request, "input_data", {}) or {}
        url = input_data.get("url")

        if url:
            return str(url).strip()

        original_input = input_data.get("original_input", "")
        return extract_url_from_text(original_input)

    def _fetch(self, url):
        if self.fetcher is not None:
            return _normalize_fetch_result(self.fetcher(url), url)

        return _normalize_fetch_result(self._urllib_fetch(url), url)

    def _urllib_fetch(self, url):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": self.user_agent},
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = response.read(self.max_fetch_bytes + 1)
            truncated = len(raw) > self.max_fetch_bytes
            raw = raw[: self.max_fetch_bytes]
            content_type = response.headers.get("content-type", "")
            encoding = _extract_charset(content_type) or "utf-8"

            return {
                "html": raw.decode(encoding, errors="replace"),
                "final_url": response.geturl(),
                "status_code": getattr(response, "status", None),
                "content_type": content_type,
                "truncated": truncated,
            }


class _HTMLTextExtractor(HTMLParser):
    """script/styleを除外しながら、titleと本文を取り出す小さなParserです。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._in_title = False
        self.title_parts = []
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return

        if tag == "title":
            self._in_title = True
            return

        if self._skip_depth == 0 and tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.text_parts.append(" ")

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
            return

        if tag == "title":
            self._in_title = False
            return

        if self._skip_depth == 0 and tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.text_parts.append(" ")

    def handle_data(self, data):
        if self._skip_depth:
            return

        if self._in_title:
            self.title_parts.append(data)
            return

        self.text_parts.append(data)


def _parse_html(html):
    parser = _HTMLTextExtractor()
    parser.feed(str(html or ""))
    parser.close()

    return {
        "title": _clean_text(" ".join(parser.title_parts)),
        "text": _clean_text(" ".join(parser.text_parts)),
    }


def _normalize_fetch_result(result, original_url):
    if isinstance(result, dict):
        html = (
            result.get("html")
            or result.get("body")
            or result.get("content")
            or result.get("text")
            or ""
        )

        return {
            "html": _decode_if_bytes(html),
            "final_url": result.get("final_url") or result.get("url") or original_url,
            "status_code": result.get("status_code") or result.get("status"),
            "content_type": result.get("content_type"),
            "truncated": result.get("truncated", False),
        }

    if isinstance(result, (tuple, list)):
        html = result[0] if result else ""
        final_url = result[1] if len(result) > 1 else original_url

        return {
            "html": _decode_if_bytes(html),
            "final_url": final_url or original_url,
            "status_code": None,
            "content_type": None,
            "truncated": False,
        }

    return {
        "html": _decode_if_bytes(result),
        "final_url": original_url,
        "status_code": None,
        "content_type": None,
        "truncated": False,
    }


def _get_fetch_value(fetch_result, key, default=None):
    if isinstance(fetch_result, dict):
        return fetch_result.get(key, default)

    return default


def _is_http_url(url):
    parsed = urllib.parse.urlparse(str(url))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _decode_if_bytes(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    return str(value or "")


def _extract_charset(content_type):
    match = re.search(r"charset=([\w.-]+)", str(content_type or ""), re.IGNORECASE)

    if match:
        return match.group(1)

    return None


def _clean_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()
