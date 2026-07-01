from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from core.web_reader_adapter import extract_url_from_text


@dataclass
class WebReaderConfirmation:
    """Web Reader実行前の確認メッセージdry-run結果です。"""

    needs_confirmation: bool
    url: Optional[str]
    tool_name: Optional[str]
    action: Optional[str]
    message: str
    reason: str

    def to_dict(self):
        """checkやデバッグで扱いやすいdict形式にします。"""
        return {
            "needs_confirmation": self.needs_confirmation,
            "url": self.url,
            "tool_name": self.tool_name,
            "action": self.action,
            "message": self.message,
            "reason": self.reason,
        }


@dataclass
class WebReaderConfirmationResult:
    """Web Reader確認へのユーザー応答を整理したdry-run結果です。"""

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


def build_web_reader_confirmation(user_input):
    """URL入力からWeb Reader実行前の確認メッセージだけを作ります。

    この関数はdry-run専用です。ToolRunnerもWebReaderAdapterのfetchも呼びません。
    """
    url = extract_url_from_text(user_input)

    if not url or not _is_http_url(url):
        return WebReaderConfirmation(
            needs_confirmation=False,
            url=None,
            tool_name=None,
            action=None,
            message="",
            reason="URLが見つかりませんでした。",
        )

    return WebReaderConfirmation(
        needs_confirmation=True,
        url=url,
        tool_name="web_reader",
        action="read_url",
        message=(
            "このURLをWeb Readerで読み取ってもよいですか？\n"
            f"{url}\n\n"
            "外部Webへアクセスするため、実行前に確認が必要です。"
        ),
        reason="外部Webアクセスにはユーザー確認が必要です。",
    )


def resolve_web_reader_confirmation_response(user_input, pending_confirmation=None):
    """Web Reader確認への返答を分類し、実行候補だけをdry-runで作ります。

    Ver2.4では、肯定応答でも実行には進みません。
    """
    if not pending_confirmation:
        return WebReaderConfirmationResult(
            status="no_pending",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message="",
            reason="保留中のWeb Reader確認がありません。",
        )

    text = str(user_input or "").strip()

    if _is_affirmative_response(text):
        candidate = build_web_reader_tool_request_candidate(pending_confirmation)

        return WebReaderConfirmationResult(
            status="confirmed",
            should_execute=False,
            user_confirmed=True,
            tool_request_candidate=candidate,
            message=(
                "Web Readerの実行接続はまだ未実装です。\n"
                "現在は、確認応答を受け取り、実行候補を作るdry-runまで対応しています。"
            ),
            reason="ユーザーはWeb Reader実行を許可しましたが、Ver2.4では候補作成までに留めます。",
        )

    if _is_negative_response(text):
        return WebReaderConfirmationResult(
            status="cancelled",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message="了解しました。Web Readerは実行しません。",
            reason="ユーザーがWeb Reader実行をキャンセルしました。",
        )

    return WebReaderConfirmationResult(
        status="ignored",
        should_execute=False,
        user_confirmed=False,
        tool_request_candidate=None,
        message="",
        reason="確認応答ではないため、保留を解除して通常処理へ戻します。",
    )


def build_web_reader_tool_request_candidate(pending_confirmation):
    """将来の実行に渡せる候補情報だけをdictで作ります。"""
    url = _get_value(pending_confirmation, "url")
    original_input = _get_value(pending_confirmation, "original_input", "")

    return {
        "tool_name": "web_reader",
        "action": "read_url",
        "input_data": {
            "url": url,
            "original_input": original_input,
        },
        "risk_level": "medium",
        "requires_permission": True,
        "user_confirmed": True,
    }


def _is_affirmative_response(text):
    normalized = str(text or "").strip()
    return normalized in [
        "はい",
        "お願いします",
        "お願い",
        "OK",
        "ok",
        "Yes",
        "yes",
        "実行して",
        "読んで",
    ]


def _is_negative_response(text):
    normalized = str(text or "").strip()
    return normalized in [
        "いいえ",
        "やめて",
        "キャンセル",
        "不要",
        "しないで",
        "no",
        "No",
    ]


def _is_http_url(url):
    parsed = urlparse(str(url))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _get_value(obj, key, default=None):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)
