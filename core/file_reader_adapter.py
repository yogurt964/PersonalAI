import re
from pathlib import Path

from core.tool_adapter import ToolAdapter, ToolResult


ALLOWED_EXTENSIONS = (".txt", ".md")

# 引用符つき、またはスペースなしで拡張子まで含む1トークンのパスだけを対象にします。
# ディレクトリ指定やワイルドカードは意図的にサポートしません。
QUOTED_PATH_PATTERN = re.compile(r'"([^"]+\.(?:txt|md))"|\'([^\']+\.(?:txt|md))\'', re.IGNORECASE)
BARE_PATH_PATTERN = re.compile(r'(\S+\.(?:txt|md))', re.IGNORECASE)


def extract_file_path_from_text(text):
    """テキストから、ユーザーが指定した単一のtxt/mdファイルパスを取り出します。

    ディレクトリ全体やワイルドカードは対象にせず、拡張子で終わる1つのパスだけを拾います。
    """
    if not text:
        return None

    quoted_match = QUOTED_PATH_PATTERN.search(str(text))

    if quoted_match:
        return quoted_match.group(1) or quoted_match.group(2)

    bare_match = BARE_PATH_PATTERN.search(str(text))

    if bare_match:
        return bare_match.group(1)

    return None


class FileReaderAdapter(ToolAdapter):
    """最小実用版のFile Reader Adapterです。

    ユーザーが明示した単一のtxt/mdファイルだけを、確認後に読み取ります。
    ディレクトリ探索、ワイルドカード、書き込み、実行は一切行いません。
    """

    def __init__(
        self,
        allowed_extensions=ALLOWED_EXTENSIONS,
        max_file_bytes=1024 * 1024,
        max_text_chars=12000,
    ):
        super().__init__(
            name="file_reader",
            description="Read a single local text/markdown file specified by the user.",
        )
        self.allowed_extensions = tuple(ext.lower() for ext in allowed_extensions)
        self.max_file_bytes = max_file_bytes
        self.max_text_chars = max_text_chars

    def is_available(self):
        return True

    def execute(self, request):
        """ToolRequestを受け取り、ローカルファイルの本文をToolResultとして返します。"""
        path_text = self._get_path_from_request(request)

        if not path_text:
            return ToolResult(
                success=False,
                message="読み取るファイルパスが見つからないため、File Readerは実行していません。",
                data=None,
                error="missing_path",
                executed=False,
            )

        path = Path(path_text)

        if path.suffix.lower() not in self.allowed_extensions:
            return ToolResult(
                success=False,
                message=(
                    "対応していない拡張子のため、File Readerは実行していません。"
                    f"（対応拡張子: {', '.join(self.allowed_extensions)}）"
                ),
                data={"path": path_text},
                error="unsupported_extension",
                executed=False,
            )

        if not path.exists():
            return ToolResult(
                success=False,
                message="指定されたファイルが見つからないため、File Readerは実行していません。",
                data={"path": path_text},
                error="file_not_found",
                executed=False,
            )

        if not path.is_file():
            return ToolResult(
                success=False,
                message="指定されたパスはファイルではないため、File Readerは実行していません。",
                data={"path": path_text},
                error="not_a_file",
                executed=False,
            )

        try:
            size_bytes = path.stat().st_size
        except OSError as error:
            return ToolResult(
                success=False,
                message="ファイル情報の取得に失敗しました。読めたふりはしません。",
                data={"path": path_text},
                error=str(error),
                executed=True,
            )

        if size_bytes > self.max_file_bytes:
            return ToolResult(
                success=False,
                message=(
                    "ファイルサイズが上限を超えているため、File Readerは実行していません。"
                    f"（上限: {self.max_file_bytes}バイト）"
                ),
                data={"path": path_text, "size_bytes": size_bytes},
                error="file_too_large",
                executed=False,
            )

        try:
            raw_bytes = path.read_bytes()
        except Exception as error:
            return ToolResult(
                success=False,
                message="ファイルの読み取りに失敗しました。読めたふりはしません。",
                data={"path": path_text},
                error=str(error),
                executed=True,
            )

        text = raw_bytes.decode("utf-8", errors="replace")
        truncated = len(text) > self.max_text_chars
        limited_text = text[: self.max_text_chars]

        if not limited_text.strip():
            return ToolResult(
                success=False,
                message="ファイルは読み取れましたが、本文が空でした。",
                data={"path": path_text, "size_bytes": size_bytes},
                error="empty_text",
                executed=True,
            )

        return ToolResult(
            success=True,
            message="ファイルを読み取りました。",
            data={
                "path": path_text,
                "resolved_path": str(path.resolve()),
                "file_name": path.name,
                "text": limited_text,
                "text_preview": limited_text[:500],
                "size_bytes": size_bytes,
                "truncated": truncated,
            },
            error=None,
            executed=True,
        )

    def _get_path_from_request(self, request):
        input_data = getattr(request, "input_data", {}) or {}
        path_text = input_data.get("path")

        if path_text:
            return str(path_text).strip()

        original_input = input_data.get("original_input", "")
        return extract_file_path_from_text(original_input)
