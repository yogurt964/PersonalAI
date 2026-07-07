"""Reader要否・文書作成要否などの判定で複数ファイルにまたがって重複していた
キーワード群を集約する共有モジュールです（Ver2.66, Stage 1）。

`core/input_analyzer.py` / `core/capability_manager.py` / `core/tool_request_builder.py`
は、それぞれ独立してほぼ同じキーワードリストを持っており、Ver2.30/2.36で表面化した
「ワード」/「キーワード」誤爆バグはこの3ファイルへ同じ修正を別々に適用する形で対処していた
（重複構造自体は解消されていなかった）。

3ファイルのキーワードリストは完全に同一ではなく、呼び出し文脈ごとに意図的な違いもあるため、
無理に1つのリストへ統合すると挙動が変わる恐れがある。ここでは実際に複数ファイルで
一致していた部分だけを共通定数として切り出し、各ファイルは必要に応じてこの共通部分に
独自のキーワードを追加する形にする。挙動は変更しない。
"""

WORD_DOCUMENT_KEYWORDS = [
    "Word file",
    "Word document",
    "word document",
    "in Word",
    "Wordで",
    "ワード文書",
    "ワードで",
    "ワードファイル",
]

EXCEL_DOCUMENT_KEYWORDS = [
    "Excel file",
    "Excel document",
    "excel document",
    "in Excel",
    "エクセル",
]

PDF_TO_FILE_KEYWORDS = [
    "PDFにして",
    "pdfにして",
]

BASE_READING_INTENT_KEYWORDS = [
    "読んで",
    "読み取",
    "要約",
    "まとめ",
    "内容",
    "見て",
    "解析",
    "説明して",
]

BASE_PC_OPERATION_KEYWORDS = [
    "PCを操作",
    "パソコンを操作",
    "ブラウザを操作",
    "コマンドを実行",
    "PowerShellで実行",
    "powershellで実行",
]
