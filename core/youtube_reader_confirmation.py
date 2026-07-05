from dataclasses import dataclass
from typing import Optional

from core.confirmation_intent import resolve_confirmation_intent
from core.youtube_reader_adapter import (
    extract_youtube_url_from_text,
    extract_youtube_video_id_from_text,
)


@dataclass
class YouTubeReaderConfirmation:
    """YouTube Reader実行前の確認メッセージ結果です。"""

    needs_confirmation: bool
    video_id: Optional[str]
    url: Optional[str]
    tool_name: Optional[str]
    action: Optional[str]
    message: str
    reason: str

    def to_dict(self):
        """checkやデバッグで扱いやすいdict形式にします。"""
        return {
            "needs_confirmation": self.needs_confirmation,
            "video_id": self.video_id,
            "url": self.url,
            "tool_name": self.tool_name,
            "action": self.action,
            "message": self.message,
            "reason": self.reason,
        }


@dataclass
class YouTubeReaderConfirmationResult:
    """YouTube Reader確認へのユーザー応答を整理した結果です。"""

    status: str
    should_execute: bool
    user_confirmed: bool
    tool_request_candidate: Optional[dict]
    message: str
    reason: str

    def to_dict(self):
        """checkやデバッグで扱いやすいdict形式にします。"""
        return {
            "status": self.status,
            "should_execute": self.should_execute,
            "user_confirmed": self.user_confirmed,
            "tool_request_candidate": self.tool_request_candidate,
            "message": self.message,
            "reason": self.reason,
        }


def build_youtube_reader_confirmation(user_input):
    """ユーザー入力からYouTube Reader実行前の確認メッセージを作ります。

    YouTube動画のURLが見つからない場合は確認対象にしません。
    この関数は外部へ一切アクセスせず、メッセージだけを作ります。
    """
    video_id = extract_youtube_video_id_from_text(user_input)

    if not video_id:
        return YouTubeReaderConfirmation(
            needs_confirmation=False,
            video_id=None,
            url=None,
            tool_name=None,
            action=None,
            message="",
            reason="読み取り対象のYouTube動画URLが見つかりませんでした。",
        )

    url = extract_youtube_url_from_text(user_input) or f"https://www.youtube.com/watch?v={video_id}"

    return YouTubeReaderConfirmation(
        needs_confirmation=True,
        video_id=video_id,
        url=url,
        tool_name="youtube_reader",
        action="read_youtube",
        message=(
            "このYouTube動画の字幕をYouTube Readerで取得してもよいですか？\n"
            f"{url}\n\n"
            "外部へアクセスするため、実行前に確認が必要です。"
            "取得できるのは既存の字幕・自動生成トランスクリプトのみで、"
            "音声や映像そのものは扱いません。"
        ),
        reason="外部アクセスにはユーザー確認が必要です。",
    )


def resolve_youtube_reader_confirmation_response(user_input, pending_confirmation=None):
    """YouTube Reader確認への返答を分類し、実行候補を作ります。

    ここでは実行せず、確認済みの実行候補（ToolRequest候補）だけを作ります。
    """
    if not pending_confirmation:
        return YouTubeReaderConfirmationResult(
            status="no_pending",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message="",
            reason="保留中のYouTube Reader確認がありません。",
        )

    intent = resolve_confirmation_intent(user_input, context_type="youtube_reader")

    if intent.get("status") == "confirmed":
        candidate = build_youtube_reader_tool_request_candidate(pending_confirmation)

        return YouTubeReaderConfirmationResult(
            status="confirmed",
            should_execute=False,
            user_confirmed=True,
            tool_request_candidate=candidate,
            message="YouTube Readerの実行許可を確認しました。",
            reason="ユーザーはYouTube Reader実行を許可しました。",
        )

    if intent.get("status") == "rejected":
        return YouTubeReaderConfirmationResult(
            status="cancelled",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message=(
                "YouTube Readerは実行しませんでした。\n"
                "必要になったら、もう一度動画のURLを送ってください。"
            ),
            reason="ユーザーがYouTube Reader実行をキャンセルしました。",
        )

    return YouTubeReaderConfirmationResult(
        status="unclear",
        should_execute=False,
        user_confirmed=False,
        tool_request_candidate=None,
        message=intent.get("message", ""),
        reason="YouTube Reader確認待ち中の入力を確認応答として解釈できませんでした。",
    )


def build_youtube_reader_tool_request_candidate(pending_confirmation):
    """将来の実行に渡せる候補情報だけをdictで作ります。"""
    video_id = _get_value(pending_confirmation, "video_id")
    original_input = _get_value(pending_confirmation, "original_input", "")

    return {
        "tool_name": "youtube_reader",
        "action": "read_youtube",
        "input_data": {
            "video_id": video_id,
            "original_input": original_input,
        },
        "risk_level": "medium",
        "requires_permission": True,
        "user_confirmed": True,
    }


def _get_value(obj, key, default=None):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)
