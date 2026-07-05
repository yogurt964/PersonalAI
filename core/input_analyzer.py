import re


class InputAnalyzer:
    """ユーザー入力を簡単に構造化するクラスです。"""

    def analyze(self, user_input):
        """ユーザー入力を解析し、後続処理で使いやすいdictにして返します。"""
        text = str(user_input).strip()

        if not text:
            return {
                "input_type": "unknown",
                "task_type": "unknown",
                "has_url": False,
                "url": None,
                "requires_external_reading": False,
                "requires_file_creation": False,
                "notes": "空の入力です",
            }

        url = self._extract_url(text)
        input_type = self._detect_input_type(text, url)
        requires_file_creation = self._requires_file_creation(text)
        task_type = self._detect_task_type(text, requires_file_creation)

        # URLやYouTubeは、将来的には外部情報の読み取りが必要になる入力です。
        requires_external_reading = input_type in ["url", "youtube"]

        return {
            "input_type": input_type,
            "task_type": task_type,
            "has_url": url is not None,
            "url": url,
            "requires_external_reading": requires_external_reading,
            "requires_file_creation": requires_file_creation,
            "notes": self._build_notes(input_type, task_type),
        }

    def _extract_url(self, text):
        """入力文から最初のURLを取り出します。"""
        match = re.search(r"https?://\S+", text)

        if match is not None:
            return match.group(0)

        youtube_match = re.search(
            r"(?:www\.)?(?:youtube\.com|youtu\.be)/?\S*",
            text,
            re.IGNORECASE,
        )

        if youtube_match is not None:
            return youtube_match.group(0)

        return None

    def _detect_input_type(self, text, url):
        """入力が通常テキスト、URL、YouTubeのどれに近いかを判定します。"""
        lowered_text = text.lower()

        if "youtube.com" in lowered_text or "youtu.be" in lowered_text:
            return "youtube"

        if url is not None:
            return "url"

        return "text"

    def _detect_task_type(self, text, requires_file_creation):
        """入力文から、依頼の種類を簡単に判定します。"""
        if requires_file_creation:
            return "create_document"

        summarize_keywords = [
            "要約",
            "まとめて",
            "まとめ",
            "内容を教えて",
            "簡単に説明",
        ]

        if self._contains_any(text, summarize_keywords):
            return "summarize"

        recommend_keywords = [
            "おすすめ",
            "オススメ",
            "候補",
            "どれがいい",
            "提案",
        ]

        if self._contains_any(text, recommend_keywords):
            return "recommend"

        remember_keywords = [
            "覚えて",
            "記憶して",
            "忘れないで",
        ]

        if self._contains_any(text, remember_keywords):
            return "remember"

        question_keywords = [
            "？",
            "?",
            "どうすれば",
            "なぜ",
            "なんで",
            "方法",
            "教えて",
        ]

        if self._contains_any(text, question_keywords):
            return "question"

        return "chat"

    def _requires_file_creation(self, text):
        """Wordや文書作成が必要そうな入力かどうかを判定します。"""
        create_document_keywords = [
            "Word file",
            "Word document",
            "word document",
            "in Word",
            "Wordで",
            "ワード文書",
            "ワードで",
            "ワードファイル",
            "文書",
            "レポート",
            "資料",
            "PDFにして",
            "pdfにして",
            "文章にして",
        ]

        return self._contains_any(text, create_document_keywords)

    def _build_notes(self, input_type, task_type):
        """解析結果を人が読みやすい短いメモにします。"""
        if input_type == "youtube" and task_type == "summarize":
            return "YouTube URLの要約依頼"

        if input_type == "youtube":
            return "YouTube URLを含む入力"

        if input_type == "url" and task_type == "summarize":
            return "URLの要約依頼"

        if task_type == "summarize":
            return "要約依頼"

        if task_type == "create_document":
            return "文書作成が必要な可能性があります"

        if task_type == "recommend":
            return "おすすめ・提案依頼"

        if task_type == "remember":
            return "記憶依頼"

        if task_type == "question":
            return "質問"

        if input_type == "url":
            return "URLを含む入力"

        return "通常のテキスト入力"

    def _contains_any(self, text, keywords):
        """入力文に候補キーワードが1つでも含まれているかを調べます。"""
        return any(keyword in text for keyword in keywords)
