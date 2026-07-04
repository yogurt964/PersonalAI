from dataclasses import dataclass
from typing import Optional

from core.confirmation_intent import resolve_confirmation_intent
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

    intent = resolve_confirmation_intent(user_input, context_type="web_reader")

    if intent.get("status") == "confirmed":
        candidate = build_web_reader_tool_request_candidate(pending_confirmation)

        return WebReaderConfirmationResult(
            status="confirmed",
            should_execute=False,
            user_confirmed=True,
            tool_request_candidate=candidate,
            message=(
                "Web Readerの実行許可を確認しました。\n"
                "このresolverではdry-runとして実行候補だけを作ります。"
            ),
            reason="ユーザーはWeb Reader実行を許可しました。",
        )

    if intent.get("status") == "rejected":
        return WebReaderConfirmationResult(
            status="cancelled",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message=(
                "Web Readerは実行しませんでした。\n"
                "必要になったら、もう一度URLを送ってください。"
            ),
            reason="ユーザーがWeb Reader実行をキャンセルしました。",
        )

    return WebReaderConfirmationResult(
        status="unclear",
        should_execute=False,
        user_confirmed=False,
        tool_request_candidate=None,
        message=intent.get("message", ""),
        reason="Web Reader確認待ち中の入力を確認応答として解釈できませんでした。",
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
    return resolve_confirmation_intent(text, context_type="web_reader").get("status") == "confirmed"


def _is_negative_response(text):
    return resolve_confirmation_intent(text, context_type="web_reader").get("status") == "rejected"


def _is_http_url(url):
    text = str(url or "").strip()
    return (
        (text.startswith("http://") or text.startswith("https://"))
        and len(text.split("://", 1)[-1].split("/", 1)[0]) > 0
    )


def _get_value(obj, key, default=None):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)
