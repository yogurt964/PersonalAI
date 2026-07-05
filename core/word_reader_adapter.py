from pathlib import Path

from core.file_path_extraction import extract_single_file_path_from_text
from core.tool_adapter import ToolAdapter, ToolResult


WORD_EXTENSIONS = (".docx",)


def extract_word_path_from_text(text):
    """テキストから、ユーザーが指定した単一のWord(.docx)ファイルパスを取り出します。

    ディレクトリ全体やワイルドカードは対象にせず、拡張子で終わる1つのパスだけを拾います。
    スペースを含むファイル名（例: Windowsの重複ダウンロードによる「 (1).docx」）にも対応します。
    """
    return extract_single_file_path_from_text(text, WORD_EXTENSIONS)


class WordReaderAdapter(ToolAdapter):
    """最小実用版のWord Reader Adapterです。

    ユーザーが明示した単一の.docxファイルだけを、確認後にテキスト抽出します。
    ディレクトリ探索、ワイルドカード、書き込み、実行は一切行いません。
    古い形式の.doc（バイナリ形式）には対応しません。
    """

    def __init__(
        self,
        max_file_bytes=20 * 1024 * 1024,
        max_text_chars=12000,
        docx_reader_factory=None,
    ):
        super().__init__(
            name="word_reader",
            description="Read a single local Word (.docx) file specified by the user.",
        )
        self.max_file_bytes = max_file_bytes
        self.max_text_chars = max_text_chars
        # 自動checkでfakeのdocx読み取りに差し替えられるようにします。
        self._docx_reader_factory = docx_reader_factory

    def is_available(self):
        return True

    def execute(self, request):
        """ToolRequestを受け取り、Word本文をToolResultとして返します。"""
        path_text = self._get_path_from_request(request)

        if not path_text:
            return ToolResult(
                success=False,
                message="読み取るWordファイルパスが見つからないため、Word Readerは実行していません。",
                data=None,
                error="missing_path",
                executed=False,
            )

        path = Path(path_text)

        if path.suffix.lower() != ".docx":
            return ToolResult(
                success=False,
                message=(
                    "対応していない拡張子のため、Word Readerは実行していません。"
                    "（対応拡張子: .docx。古い.doc形式には対応していません）"
                ),
                data={"path": path_text},
                error="unsupported_extension",
                executed=False,
            )

        if not path.exists():
            return ToolResult(
                success=False,
                message="指定されたファイルが見つからないため、Word Readerは実行していません。",
                data={"path": path_text},
                error="file_not_found",
                executed=False,
            )

        if not path.is_file():
            return ToolResult(
                success=False,
                message="指定されたパスはファイルではないため、Word Readerは実行していません。",
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
                    "ファイルサイズが上限を超えているため、Word Readerは実行していません。"
                    f"（上限: {self.max_file_bytes}バイト）"
                ),
                data={"path": path_text, "size_bytes": size_bytes},
                error="file_too_large",
                executed=False,
            )

        try:
            paragraph_count, text = self._extract_text(path)
        except Exception as error:
            return ToolResult(
                success=False,
                message="Wordファイルの読み取りに失敗しました。読めたふりはしません。（破損・非対応形式の可能性があります）",
                data={"path": path_text},
                error=str(error),
                executed=True,
            )

        truncated_text = len(text) > self.max_text_chars
        limited_text = text[: self.max_text_chars]

        if not limited_text.strip():
            return ToolResult(
                success=False,
                message="Wordファイルは開けましたが、テキストを取り出せませんでした。",
                data={"path": path_text, "size_bytes": size_bytes, "paragraph_count": paragraph_count},
                error="empty_text",
                executed=True,
            )

        return ToolResult(
            success=True,
            message="Wordファイルを読み取りました。",
            data={
                "path": path_text,
                "resolved_path": str(path.resolve()),
                "file_name": path.name,
                "text": limited_text,
                "text_preview": limited_text[:500],
                "size_bytes": size_bytes,
                "paragraph_count": paragraph_count,
                "truncated": truncated_text,
            },
            error=None,
            executed=True,
        )

    def _extract_text(self, path):
        document = self._build_docx_reader(path)
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]

        table_texts = []
        for table in getattr(document, "tables", []):
            for row in table.rows:
                row_text = " | ".join(cell.text for cell in row.cells if cell.text)

                if row_text:
                    table_texts.append(row_text)

        all_parts = paragraphs + table_texts
        return len(paragraphs), "\n".join(all_parts)

    def _build_docx_reader(self, path):
        if self._docx_reader_factory is not None:
            return self._docx_reader_factory(path)

        from docx import Document

        return Document(str(path))

    def _get_path_from_request(self, request):
        input_data = getattr(request, "input_data", {}) or {}
        path_text = input_data.get("path")

        if path_text:
            return str(path_text).strip()

        original_input = input_data.get("original_input", "")
        return extract_word_path_from_text(original_input)
