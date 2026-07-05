from pathlib import Path

from core.file_path_extraction import extract_single_file_path_from_text
from core.tool_adapter import ToolAdapter, ToolResult


EXCEL_EXTENSIONS = (".xlsx",)


def extract_excel_path_from_text(text):
    """テキストから、ユーザーが指定した単一のExcel(.xlsx)ファイルパスを取り出します。

    ディレクトリ全体やワイルドカードは対象にせず、拡張子で終わる1つのパスだけを拾います。
    スペースを含むファイル名（例: Windowsの重複ダウンロードによる「 (1).xlsx」）にも対応します。
    """
    return extract_single_file_path_from_text(text, EXCEL_EXTENSIONS)


class ExcelReaderAdapter(ToolAdapter):
    """最小実用版のExcel Reader Adapterです。

    ユーザーが明示した単一の.xlsxファイルだけを、確認後にテキスト抽出します。
    ディレクトリ探索、ワイルドカード、書き込み、実行は一切行いません。
    数式は評価値ではなく、保存されている計算済みの値を読み取ります（マクロは実行しません）。
    古い形式の.xls（バイナリ）には対応しません。
    """

    def __init__(
        self,
        max_file_bytes=20 * 1024 * 1024,
        max_rows_per_sheet=200,
        max_text_chars=12000,
        workbook_reader_factory=None,
    ):
        super().__init__(
            name="excel_reader",
            description="Read a single local Excel (.xlsx) file specified by the user.",
        )
        self.max_file_bytes = max_file_bytes
        self.max_rows_per_sheet = max_rows_per_sheet
        self.max_text_chars = max_text_chars
        # 自動checkでfakeのワークブック読み取りに差し替えられるようにします。
        self._workbook_reader_factory = workbook_reader_factory

    def is_available(self):
        return True

    def execute(self, request):
        """ToolRequestを受け取り、Excel本文をToolResultとして返します。"""
        path_text = self._get_path_from_request(request)

        if not path_text:
            return ToolResult(
                success=False,
                message="読み取るExcelファイルパスが見つからないため、Excel Readerは実行していません。",
                data=None,
                error="missing_path",
                executed=False,
            )

        path = Path(path_text)

        if path.suffix.lower() != ".xlsx":
            return ToolResult(
                success=False,
                message=(
                    "対応していない拡張子のため、Excel Readerは実行していません。"
                    "（対応拡張子: .xlsx。古い.xls形式には対応していません）"
                ),
                data={"path": path_text},
                error="unsupported_extension",
                executed=False,
            )

        if not path.exists():
            return ToolResult(
                success=False,
                message="指定されたファイルが見つからないため、Excel Readerは実行していません。",
                data={"path": path_text},
                error="file_not_found",
                executed=False,
            )

        if not path.is_file():
            return ToolResult(
                success=False,
                message="指定されたパスはファイルではないため、Excel Readerは実行していません。",
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
                    "ファイルサイズが上限を超えているため、Excel Readerは実行していません。"
                    f"（上限: {self.max_file_bytes}バイト）"
                ),
                data={"path": path_text, "size_bytes": size_bytes},
                error="file_too_large",
                executed=False,
            )

        try:
            sheet_count, text = self._extract_text(path)
        except Exception as error:
            return ToolResult(
                success=False,
                message="Excelファイルの読み取りに失敗しました。読めたふりはしません。（破損・非対応形式の可能性があります）",
                data={"path": path_text},
                error=str(error),
                executed=True,
            )

        truncated_text = len(text) > self.max_text_chars
        limited_text = text[: self.max_text_chars]

        if not limited_text.strip():
            return ToolResult(
                success=False,
                message="Excelファイルは開けましたが、テキストを取り出せませんでした（空のシートの可能性があります）。",
                data={"path": path_text, "size_bytes": size_bytes, "sheet_count": sheet_count},
                error="empty_text",
                executed=True,
            )

        return ToolResult(
            success=True,
            message="Excelファイルを読み取りました。",
            data={
                "path": path_text,
                "resolved_path": str(path.resolve()),
                "file_name": path.name,
                "text": limited_text,
                "text_preview": limited_text[:500],
                "size_bytes": size_bytes,
                "sheet_count": sheet_count,
                "truncated": truncated_text,
            },
            error=None,
            executed=True,
        )

    def _extract_text(self, path):
        workbook = self._build_workbook_reader(path)

        try:
            sheet_names = getattr(workbook, "sheetnames", [])
            sheet_texts = []

            for sheet_name in sheet_names:
                sheet = workbook[sheet_name]
                all_rows = list(sheet.iter_rows(values_only=True))
                limited_rows = all_rows[: self.max_rows_per_sheet]
                row_texts = []

                for row in limited_rows:
                    cell_values = [str(value) for value in row if value is not None]

                    if cell_values:
                        row_texts.append(" | ".join(cell_values))

                if not row_texts:
                    continue

                # 集計値は行データより先に置き、文字数上限で切り詰められても
                # 正確な合計・平均・グループ比較が残るようにします。
                row_block = f"[{sheet_name}]\n" + "\n".join(row_texts)
                summary_block = self._build_numeric_column_summary(sheet_name, all_rows)
                group_by_block = self._build_group_by_summary(sheet_name, all_rows)

                header_blocks = [block for block in (summary_block, group_by_block) if block]
                sheet_block = "\n\n".join(header_blocks + [row_block]) if header_blocks else row_block
                sheet_texts.append(sheet_block)

            return len(sheet_names), "\n\n".join(sheet_texts)
        finally:
            # Windowsではread_onlyワークブックのファイルハンドルが残りやすいため、明示的に閉じます。
            close = getattr(workbook, "close", None)

            if callable(close):
                close()

    def _build_numeric_column_summary(self, sheet_name, all_rows):
        """1行目をヘッダーとみなし、数値だけの列について合計・平均・最小・最大・件数を
        Pythonで正確に計算します。

        LLMにテキストから合計や平均を再計算させると誤りやすいため、
        よく聞かれる集計値はここで確定させ、資料の一部として渡します。
        """
        if len(all_rows) < 2:
            return ""

        header_row = all_rows[0]
        data_rows = all_rows[1:]
        summary_lines = []

        for column_index, column_name in enumerate(header_row):
            if column_name is None:
                continue

            numeric_values = []
            non_empty_count = 0

            for row in data_rows:
                if column_index >= len(row):
                    continue

                value = row[column_index]

                if value is None:
                    continue

                non_empty_count += 1

                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    numeric_values.append(value)

            if not numeric_values or len(numeric_values) != non_empty_count:
                # 数値以外が混ざっている列は、誤った集計を避けるため対象にしません。
                continue

            total = sum(numeric_values)
            average = total / len(numeric_values)
            summary_lines.append(
                f"列「{column_name}」: 合計={total:g}, 平均={average:.2f}, "
                f"最小={min(numeric_values):g}, 最大={max(numeric_values):g}, "
                f"件数={len(numeric_values)}"
            )

        if not summary_lines:
            return ""

        return (
            f"[{sheet_name} 自動集計（数値列のみ、Pythonで正確に計算済み）]\n"
            "合計・平均・最小・最大を聞かれた場合は、この値をそのまま使ってください。"
            "本文の行データから自分で再計算しないでください。\n"
            + "\n".join(summary_lines)
        )

    def _build_group_by_summary(self, sheet_name, all_rows):
        """カテゴリ列（店舗名など、繰り返し値を持つ文字列列）でグループ化し、
        数値列ごとの合計が最大・最小になるグループをPythonで正確に計算します。

        「一番売上が高い店舗はどこ？」のような、列をまたぐ比較質問に対応します。
        グループの内訳は多くなりすぎないよう、最大・最小のグループだけを報告します。
        """
        if len(all_rows) < 2:
            return ""

        header_row = all_rows[0]
        data_rows = all_rows[1:]
        column_count = len(header_row)

        numeric_columns = set()
        category_columns = []

        for column_index in range(column_count):
            column_name = header_row[column_index]

            if column_name is None:
                continue

            values = []
            distinct_values = set()
            non_empty_count = 0
            all_numeric = True

            for row in data_rows:
                if column_index >= len(row):
                    continue

                value = row[column_index]

                if value is None:
                    continue

                non_empty_count += 1
                values.append(value)
                distinct_values.add(value)

                if not (isinstance(value, (int, float)) and not isinstance(value, bool)):
                    all_numeric = False

            if non_empty_count == 0:
                continue

            if all_numeric:
                # 全行が一意な値（注文IDなどの識別子）は、合計しても意味がないため除外します。
                if len(distinct_values) < non_empty_count:
                    numeric_columns.add(column_index)

                continue

            # グループ化に向くのは、値が繰り返される列（一意キーのような列は除く）。
            if 2 <= len(distinct_values) <= min(30, non_empty_count // 2 or 1):
                category_columns.append(column_index)

        if not category_columns or not numeric_columns:
            return ""

        summary_lines = []

        for category_index in category_columns:
            category_name = header_row[category_index]

            for numeric_index in numeric_columns:
                numeric_name = header_row[numeric_index]
                totals_by_group = {}

                for row in data_rows:
                    if category_index >= len(row) or numeric_index >= len(row):
                        continue

                    category_value = row[category_index]
                    numeric_value = row[numeric_index]

                    if category_value is None or not isinstance(numeric_value, (int, float)) or isinstance(
                        numeric_value, bool
                    ):
                        continue

                    totals_by_group[category_value] = totals_by_group.get(category_value, 0) + numeric_value

                if len(totals_by_group) < 2:
                    continue

                max_group = max(totals_by_group.items(), key=lambda item: item[1])
                min_group = min(totals_by_group.items(), key=lambda item: item[1])

                summary_lines.append(
                    f"「{category_name}」ごとの「{numeric_name}」合計: "
                    f"最大は「{max_group[0]}」で{max_group[1]:g}, "
                    f"最小は「{min_group[0]}」で{min_group[1]:g}"
                )

        if not summary_lines:
            return ""

        return (
            f"[{sheet_name} グループ集計（カテゴリ列ごとの合計、Pythonで正確に計算済み）]\n"
            "「どの◯◯が一番多い/少ない」のような質問には、この値をそのまま使ってください。"
            "本文の行データから自分で再計算しないでください。\n"
            + "\n".join(summary_lines)
        )

    def _build_workbook_reader(self, path):
        if self._workbook_reader_factory is not None:
            return self._workbook_reader_factory(path)

        from openpyxl import load_workbook

        return load_workbook(str(path), read_only=True, data_only=True)

    def _get_path_from_request(self, request):
        input_data = getattr(request, "input_data", {}) or {}
        path_text = input_data.get("path")

        if path_text:
            return str(path_text).strip()

        original_input = input_data.get("original_input", "")
        return extract_excel_path_from_text(original_input)
