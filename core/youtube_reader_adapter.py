import re

from core.tool_adapter import ToolAdapter, ToolResult


YOUTUBE_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)"
    r"([A-Za-z0-9_-]{11})",
    re.IGNORECASE,
)


def extract_youtube_video_id_from_text(text):
    """テキストから、最初のYouTube動画IDを取り出します。

    対応する形式:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    """
    if not text:
        return None

    match = YOUTUBE_URL_PATTERN.search(str(text))

    if match is None:
        return None

    return match.group(1)


def extract_youtube_url_from_text(text):
    """テキストから、最初のYouTube URL全体を取り出します（確認メッセージ表示用）。"""
    if not text:
        return None

    match = YOUTUBE_URL_PATTERN.search(str(text))

    if match is None:
        return None

    return match.group(0)


class YouTubeReaderAdapter(ToolAdapter):
    """最小実用版のYouTube Reader Adapterです。

    ユーザーが指定した単一のYouTube動画について、公開されている字幕・
    自動生成トランスクリプトだけを取得します。動画・音声のダウンロードや
    文字起こしの実行は行いません。字幕が存在しない・無効化されている場合は
    読めたふりをせず、正直に失敗を返します。
    """

    def __init__(
        self,
        languages=("ja", "en"),
        max_text_chars=12000,
        transcript_fetcher=None,
    ):
        super().__init__(
            name="youtube_reader",
            description="Fetch the existing captions/transcript of a single YouTube video.",
        )
        self.languages = tuple(languages)
        self.max_text_chars = max_text_chars
        # 自動checkでfakeのトランスクリプト取得に差し替えられるようにします。
        self._transcript_fetcher = transcript_fetcher

    def is_available(self):
        return True

    def execute(self, request):
        """ToolRequestを受け取り、字幕テキストをToolResultとして返します。"""
        video_id = self._get_video_id_from_request(request)

        if not video_id:
            return ToolResult(
                success=False,
                message="読み取るYouTube動画のURLが見つからないため、YouTube Readerは実行していません。",
                data=None,
                error="missing_video_id",
                executed=False,
            )

        try:
            fetch_result = self._fetch_transcript(video_id)
        except Exception as error:
            return ToolResult(
                success=False,
                message=(
                    "字幕の取得に失敗しました。読めたふりはしません。"
                    "（字幕が存在しない、無効化されている、動画が非公開・削除済みの可能性があります）"
                ),
                data={"video_id": video_id},
                error=str(error),
                executed=True,
            )

        text = _normalize_transcript_text(fetch_result)
        truncated_text = len(text) > self.max_text_chars
        limited_text = text[: self.max_text_chars]

        if not limited_text.strip():
            return ToolResult(
                success=False,
                message="字幕は取得できましたが、テキストを取り出せませんでした。",
                data={"video_id": video_id},
                error="empty_text",
                executed=True,
            )

        return ToolResult(
            success=True,
            message="YouTube動画の字幕を取得しました。",
            data={
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "text": limited_text,
                "text_preview": limited_text[:500],
                "truncated": truncated_text,
            },
            error=None,
            executed=True,
        )

    def _fetch_transcript(self, video_id):
        if self._transcript_fetcher is not None:
            return self._transcript_fetcher(video_id)

        from youtube_transcript_api import YouTubeTranscriptApi

        return YouTubeTranscriptApi().fetch(video_id, languages=list(self.languages))

    def _get_video_id_from_request(self, request):
        input_data = getattr(request, "input_data", {}) or {}
        video_id = input_data.get("video_id")

        if video_id:
            return str(video_id).strip()

        original_input = input_data.get("original_input", "")
        return extract_youtube_video_id_from_text(original_input)


def _normalize_transcript_text(fetch_result):
    """fetcherの戻り値を、字幕本文の1つの文字列にまとめます。

    実際のyoutube-transcript-apiの戻り値（FetchedTranscript）だけでなく、
    自動checkで使うfakeの戻り値（文字列のリストや辞書のリスト）にも対応します。
    """
    if isinstance(fetch_result, str):
        return fetch_result

    parts = []

    for item in fetch_result:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict):
            parts.append(str(item.get("text", "")))
        else:
            parts.append(str(getattr(item, "text", "")))

    return " ".join(part.strip() for part in parts if part and part.strip())
