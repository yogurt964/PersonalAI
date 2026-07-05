from pathlib import Path

from core.file_path_extraction import extract_single_file_path_from_text
from core.tool_adapter import ToolAdapter, ToolResult


PDF_EXTENSIONS = (".pdf",)


def extract_pdf_path_from_text(text):
    """テキストから、ユーザーが指定した単一のPDFファイルパスを取り出します。

    ディレクトリ全体やワイルドカードは対象にせず、拡張子で終わる1つのパスだけを拾います。
    スペースを含むファイル名（例: Windowsの重複ダウンロードによる「 (1).pdf」）にも対応します。
    """
    return extract_single_file_path_from_text(text, PDF_EXTENSIONS)


class PDFReaderAdapter(ToolAdapter):
    """最小実用版のPDF Reader Adapterです。

    ユーザーが明示した単一のPDFファイルだけを、確認後にテキスト抽出します。
    ディレクトリ探索、ワイルドカード、書き込み、実行は一切行いません。
    画像だけのスキャンPDFなど、テキストを持たないPDFは空文字として扱います。
    """

    def __init__(
        self,
        max_file_bytes=20 * 1024 * 1024,
        max_pages=50,
        max_text_chars=12000,
        pdf_reader_factory=None,
    ):
        super().__init__(
            name="pdf_reader",
            description="Read a single local PDF file specified by the user.",
        )
        self.max_file_bytes = max_file_bytes
        self.max_pages = max_pages
        self.max_text_chars = max_text_chars
        # 自動checkでfakeのPDF読み取りに差し替えられるようにします。
        self._pdf_reader_factory = pdf_reader_factory

    def is_available(self):
        return True

    def execute(self, request):
        """ToolRequestを受け取り、PDF本文をToolResultとして返します。"""
        path_text = self._get_path_from_request(request)

        if not path_text:
            return ToolResult(
                success=False,
                message="読み取るPDFパスが見つからないため、PDF Readerは実行していません。",
                data=None,
                error="missing_path",
                executed=False,
            )

        path = Path(path_text)

        if path.suffix.lower() != ".pdf":
            return ToolResult(
                success=False,
                message="対応していない拡張子のため、PDF Readerは実行していません。（対応拡張子: .pdf）",
                data={"path": path_text},
                error="unsupported_extension",
                executed=False,
            )

        if not path.exists():
            return ToolResult(
                success=False,
                message="指定されたファイルが見つからないため、PDF Readerは実行していません。",
                data={"path": path_text},
                error="file_not_found",
                executed=False,
            )

        if not path.is_file():
            return ToolResult(
                success=False,
                message="指定されたパスはファイルではないため、PDF Readerは実行していません。",
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
                    "ファイルサイズが上限を超えているため、PDF Readerは実行していません。"
                    f"（上限: {self.max_file_bytes}バイト）"
                ),
                data={"path": path_text, "size_bytes": size_bytes},
                error="file_too_large",
                executed=False,
            )

        try:
            page_count, text, truncated_pages = self._extract_text(path)
        except Exception as error:
            return ToolResult(
                success=False,
                message="PDFの読み取りに失敗しました。読めたふりはしません。（暗号化・破損PDFの可能性があります）",
                data={"path": path_text},
                error=str(error),
                executed=True,
            )

        truncated_text = len(text) > self.max_text_chars
        limited_text = text[: self.max_text_chars]

        if not limited_text.strip():
            return ToolResult(
                success=False,
                message=(
                    "PDFは開けましたが、テキストを取り出せませんでした。"
                    "画像だけのスキャンPDFの可能性があります。"
                ),
                data={"path": path_text, "size_bytes": size_bytes, "page_count": page_count},
                error="empty_text",
                executed=True,
            )

        return ToolResult(
            success=True,
            message="PDFを読み取りました。",
            data={
                "path": path_text,
                "resolved_path": str(path.resolve()),
                "file_name": path.name,
                "text": limited_text,
                "text_preview": limited_text[:500],
                "size_bytes": size_bytes,
                "page_count": page_count,
                "truncated": truncated_text or truncated_pages,
            },
            error=None,
            executed=True,
        )

    def _extract_text(self, path):
        reader = self._build_pdf_reader(path)
        pages = getattr(reader, "pages", [])
        total_pages = len(pages)
        truncated_pages = total_pages > self.max_pages
        text_parts = []

        for page in pages[: self.max_pages]:
            page_text = page.extract_text() or ""

            if page_text:
                text_parts.append(page_text)

        return total_pages, "\n".join(text_parts), truncated_pages

    def _build_pdf_reader(self, path):
        if self._pdf_reader_factory is not None:
            return self._pdf_reader_factory(path)

        from pypdf import PdfReader

        return PdfReader(str(path))

    def _get_path_from_request(self, request):
        input_data = getattr(request, "input_data", {}) or {}
        path_text = input_data.get("path")

        if path_text:
            return str(path_text).strip()

        original_input = input_data.get("original_input", "")
        return extract_pdf_path_from_text(original_input)
