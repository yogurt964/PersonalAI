from core.reading_keywords import (
    BASE_PC_OPERATION_KEYWORDS,
    BASE_READING_INTENT_KEYWORDS,
    EXCEL_DOCUMENT_KEYWORDS,
    PDF_TO_FILE_KEYWORDS,
    WORD_DOCUMENT_KEYWORDS,
)


class CapabilityManager:
    """PersonalAIが利用できる能力を管理するクラスです。"""

    def __init__(self):
        # 現時点では、実際にツールを実行せず「能力の一覧」と「今できるか」を管理します。
        self._capabilities = {
            "chat": {
                "description": "通常の会話を行う",
                "risk": "low",
                "requires_permission": False,
            },
            "memory_read": {
                "description": "長期記憶を参照する",
                "risk": "low",
                "requires_permission": False,
            },
            "memory_write": {
                "description": "長期記憶を保存・更新する",
                "risk": "medium",
                "requires_permission": False,
            },
            "llm_qwen": {
                "description": "Qwenを使って回答や記憶抽出を行う",
                "risk": "medium",
                "requires_permission": False,
            },
            "local_conversation": {
                "description": "Qwenと既存Memoryだけで通常会話・相談・説明を行う",
                "risk": "low",
                "requires_permission": False,
            },
            "preference_memory": {
                "description": "好き・嫌いなどのPreference記憶を扱う",
                "risk": "medium",
                "requires_permission": False,
            },
            "web_read_required": {
                "description": "Webページ本文の読み取りが必要",
                "risk": "medium",
                "requires_permission": True,
            },
            "youtube_read_required": {
                "description": "YouTube動画の読み取りが必要",
                "risk": "medium",
                "requires_permission": True,
            },
            "pdf_read_required": {
                "description": "PDF本文の読み取りが必要",
                "risk": "medium",
                "requires_permission": True,
            },
            "image_read_required": {
                "description": "画像内容の読み取りが必要",
                "risk": "medium",
                "requires_permission": True,
            },
            "file_read_required": {
                "description": "ローカルファイルや添付ファイルの読み取りが必要",
                "risk": "medium",
                "requires_permission": True,
            },
            "document_creation_required": {
                "description": "Word / Excel / PDF / Markdownなどの実ファイル作成が必要",
                "risk": "medium",
                "requires_permission": True,
            },
            "pc_operation_required": {
                "description": "VS Code、PowerShell、ブラウザなどPC操作が必要",
                "risk": "high",
                "requires_permission": True,
            },
            "external_api_required": {
                "description": "外部API接続が必要",
                "risk": "medium",
                "requires_permission": True,
            },
            "openai_required": {
                "description": "Qwenだけでは精度不足の可能性があり、高性能モデルが必要",
                "risk": "medium",
                "requires_permission": True,
            },
            "unsupported_or_unimplemented": {
                "description": "現在のPersonalAIでは未実装または安全に実行できない",
                "risk": "medium",
                "requires_permission": False,
            },
        }

    def analyze(self, user_input, input_analysis=None):
        """入力に必要な能力と、今のPersonalAIで対応できるかを判定します。

        ここでは実行は行いません。
        「何が必要か」「何が足りないか」を整理して、未実装機能をできたふりしないための判断材料にします。
        """
        text = str(user_input or "").strip()
        lowered_text = text.lower()
        input_type = self._get_analysis_value(input_analysis, "input_type")
        task_type = self._get_analysis_value(input_analysis, "task_type")
        requires_file_creation = self._get_analysis_value(
            input_analysis,
            "requires_file_creation",
            False,
        )

        if not text:
            return self._build_result(
                False,
                "unsupported_or_unimplemented",
                ["unsupported_or_unimplemented"],
                [],
                "low",
                "空の入力のため、対応内容を判断できません。",
                "入力内容が空です。何をしたいか入力してください。",
            )

        if self._requires_pc_operation(text):
            return self._missing_result(
                "pc_operation_required",
                "pc_operator",
                "VS Code、PowerShell、ブラウザなどのPC操作が必要ですが、PC Operatorは未実装です。",
                "PC操作はまだ未実装です。必要な操作内容をテキストで教えてくれれば、手順案は説明できます。",
                risk_level="high",
            )

        if self._requires_document_creation(text, requires_file_creation):
            return self._missing_result(
                "document_creation_required",
                "document_creator",
                "Word / Excel / PDF / Markdownなどの実ファイル作成が必要ですが、Document Creatorは未実装です。",
                "実ファイル作成はまだ未実装です。文書の構成案や本文案なら、現在のQwenで作成できます。",
            )

        if self._requires_youtube_reading(text, lowered_text, input_type):
            return self._missing_result(
                "youtube_read_required",
                "youtube_reader",
                "YouTube動画の内容読み取りが必要ですが、YouTube Readerは未実装です。",
                "YouTube動画の内容を直接読む機能はまだ未実装です。文字起こしや要点を貼ってくれれば、その内容を要約できます。",
            )

        if self._requires_web_reading(text, lowered_text, input_type):
            return self._missing_result(
                "web_read_required",
                "web_reader",
                "URL本文の読み取りにはURLとWeb Reader実行前確認が必要です。",
                "URLを読み取るには、URLを含めて「このURLを読んで」と送ってください。",
            )

        if self._requires_pdf_reading(text):
            return self._missing_result(
                "pdf_read_required",
                "pdf_reader",
                "PDF本文の読み取りが必要ですが、PDF Readerは未実装です。",
                "PDFの中身を直接読む機能はまだ未実装です。本文を貼ってくれれば、その内容を要約できます。",
            )

        if self._requires_image_reading(text):
            return self._missing_result(
                "image_read_required",
                "image_reader",
                "画像の内容読み取りが必要ですが、Image Readerは未実装です。",
                "画像の内容を直接見る機能はまだ未実装です。画像の内容を文章で説明してくれれば、それをもとに整理できます。",
            )

        if self._requires_file_reading(text):
            return self._missing_result(
                "file_read_required",
                "file_reader",
                "ローカルファイルや添付ファイルの読み取りが必要ですが、File Readerは未実装です。",
                "ファイルの中身を直接読む機能はまだ未実装です。読み取りたい本文を貼ってくれれば、その内容を扱えます。",
            )

        if self._requires_external_api(text):
            return self._missing_result(
                "external_api_required",
                "external_api",
                "外部API接続が必要ですが、外部API連携は未実装です。",
                "外部API接続はまだ未実装です。APIから得た結果を貼ってくれれば、その内容を整理できます。",
            )

        if self._requires_high_accuracy_model(text):
            return self._missing_result(
                "openai_required",
                "openai",
                "高精度な判断が必要で、Qwenのみでは精度不足の可能性があります。",
                "この内容は高い正確性が必要です。現時点ではOpenAIなどの高性能モデル連携は未実装のため、断定せず一般的な整理までに留めます。",
            )

        if self._requires_memory_write(text, task_type):
            required_capabilities = ["memory_write"]

            if self._is_preference_memory(text):
                required_capabilities.append("preference_memory")

            return self._build_result(
                True,
                "memory_write",
                required_capabilities,
                [],
                "medium",
                "ユーザーが記憶保存を求めているため、現在のMemory機能で対応可能です。",
                "",
            )

        if self._requires_memory_read(text):
            return self._build_result(
                True,
                "memory_read",
                ["memory_read"],
                [],
                "low",
                "過去の記憶参照として、現在のMemory機能で対応可能です。",
                "",
            )

        return self._build_result(
            True,
            "local_conversation",
            ["local_conversation"],
            [],
            "low",
            "通常会話としてQwenと既存Memoryで回答可能です。",
            "",
        )

    def get_all_capabilities(self):
        """登録されているすべてのcapabilityを返します。"""
        return {
            name: capability.copy()
            for name, capability in self._capabilities.items()
        }

    def get_capability(self, name):
        """名前を指定して、capabilityを1つ取得します。"""
        capability = self._capabilities.get(name)

        if capability is None:
            return None

        return capability.copy()

    def get_available_capabilities(self, user_input=None):
        """現在利用可能なcapabilityを返します。

        user_inputは将来の絞り込み用です。
        現時点では入力内容に関係なく、すべてのcapabilityを返します。
        """
        return self.get_all_capabilities()

    def _missing_result(
        self,
        primary_capability,
        missing_capability,
        reason,
        user_message,
        risk_level="medium",
    ):
        """未実装機能が必要な場合の戻り値を作ります。"""
        return self._build_result(
            False,
            primary_capability,
            [primary_capability],
            [missing_capability],
            risk_level,
            reason,
            user_message,
        )

    def _build_result(
        self,
        can_handle_now,
        primary_capability,
        required_capabilities,
        missing_capabilities,
        risk_level,
        reason,
        user_message,
    ):
        """Capability判定結果を、後続処理で使いやすいdictにします。"""
        return {
            "can_handle_now": can_handle_now,
            "primary_capability": primary_capability,
            "required_capabilities": list(required_capabilities),
            "missing_capabilities": list(missing_capabilities),
            "risk_level": risk_level,
            "reason": reason,
            "user_message": user_message,
        }

    def _requires_memory_write(self, text, task_type):
        return task_type == "remember" or self._contains_any(
            text,
            ["覚えて", "記憶して", "忘れないで"],
        )

    def _requires_memory_read(self, text):
        return self._contains_any(
            text,
            [
                "私の名前は？",
                "私の名前は?",
                "僕の名前は？",
                "僕の名前は?",
                "好きな食べ物は？",
                "好きな食べ物は?",
                "何が好き",
                "覚えてる",
                "記憶してる",
            ],
        )

    def _is_preference_memory(self, text):
        return self._contains_any(text, ["好き", "嫌い", "好きじゃない", "好み"])

    def _requires_web_reading(self, text, lowered_text, input_type):
        if input_type == "url" or "http://" in lowered_text or "https://" in lowered_text:
            return True

        if self._contains_any(
            text, ["この記事", "このサイト", "このWebページ", "このwebページ"]
        ) and not self._has_non_reading_action_intent(text):
            return True

        return (
            self._contains_any(text, ["Webページ", "webページ", "サイト", "記事", "URL"])
            and self._has_reading_intent(text)
        )

    def _requires_youtube_reading(self, text, lowered_text, input_type):
        if input_type == "youtube" or "youtube.com" in lowered_text or "youtu.be" in lowered_text:
            return True

        if self._contains_any(
            text, ["このYouTube", "このyoutube", "この動画"]
        ) and not self._has_non_reading_action_intent(text):
            return True

        return self._contains_any(text, ["YouTube", "youtube", "動画"]) and self._has_reading_intent(text)

    def _requires_pdf_reading(self, text):
        if self._requires_document_creation(text, False):
            return False

        if self._contains_any(text, ["このPDF", "このpdf"]) and not self._has_non_reading_action_intent(text):
            return True

        return ("PDF" in text or "pdf" in text) and self._has_reading_intent(text)

    def _requires_image_reading(self, text):
        if self._contains_any(
            text, ["この画像", "この写真", "このスクショ"]
        ) and not self._has_non_reading_action_intent(text):
            return True

        return (
            self._contains_any(text, ["画像", "写真", "スクショ", "スクリーンショット"])
            and self._has_reading_intent(text)
        )

    def _requires_file_reading(self, text):
        if self._has_non_reading_action_intent(text):
            return self._contains_any(text, ["添付ファイル", "ファイルを読", "ファイルの中身"])

        return self._contains_any(text, ["添付ファイル", "ファイルを読", "ファイルの中身", "このファイル"])

    def _has_non_reading_action_intent(self, text):
        """削除・編集など、読み取り以外の操作を示す動詞を含むかを判定します（Ver2.62）。

        「このファイル」のような素の言及だけで即座にReader要求と判定すると、
        実際には記憶の削除・編集などを求めているだけの発言（例:「このファイル情報を削除して」）まで
        Reader未実装の定型応答に誤って回ってしまうため、これらの動詞が含まれる場合は除外します。
        """
        return self._contains_any(
            text, ["削除して", "消して", "編集して", "書き換えて", "書き直して", "修正して"]
        )

    def _requires_document_creation(self, text, requires_file_creation):
        if requires_file_creation:
            return True

        return self._contains_any(
            text,
            [
                *WORD_DOCUMENT_KEYWORDS,
                *EXCEL_DOCUMENT_KEYWORDS,
                *PDF_TO_FILE_KEYWORDS,
                "Markdownファイル",
                "mdファイル",
                "ファイルを作って",
                "表を作って",
            ],
        )

    def _requires_pc_operation(self, text):
        return self._contains_any(
            text,
            [
                "VS Codeを開",
                "vscodeを開",
                *BASE_PC_OPERATION_KEYWORDS,
                "アプリを開",
            ],
        )

    def _requires_external_api(self, text):
        return self._contains_any(text, ["API接続", "外部API", "APIを呼", "APIで"])

    def _requires_high_accuracy_model(self, text):
        return self._contains_any(
            text,
            [
                "論文レベル",
                "厳密に比較",
                "法律的",
                "法的",
                "医学的",
                "医療",
                "安全性を判断",
                "正確に判断",
            ],
        )

    def _has_reading_intent(self, text):
        return self._contains_any(text, [*BASE_READING_INTENT_KEYWORDS, "文字起こし"])

    def _get_analysis_value(self, input_analysis, key, default=None):
        if input_analysis is None:
            return default

        if isinstance(input_analysis, dict):
            return input_analysis.get(key, default)

        return getattr(input_analysis, key, default)

    def _contains_any(self, text, keywords):
        return any(keyword in text for keyword in keywords)
