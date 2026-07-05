from dataclasses import dataclass
from typing import Optional

from core.confirmation_intent import resolve_confirmation_intent
from core.file_reader_adapter import extract_file_path_from_text


@dataclass
class FileReaderConfirmation:
    """File Reader実行前の確認メッセージ結果です。"""

    needs_confirmation: bool
    path: Optional[str]
    tool_name: Optional[str]
    action: Optional[str]
    message: str
    reason: str

    def to_dict(self):
        """checkやデバッグで扱いやすいdict形式にします。"""
        return {
            "needs_confirmation": self.needs_confirmation,
            "path": self.path,
            "tool_name": self.tool_name,
            "action": self.action,
            "message": self.message,
            "reason": self.reason,
        }


@dataclass
class FileReaderConfirmationResult:
    """File Reader確認へのユーザー応答を整理した結果です。"""

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


def build_file_reader_confirmation(user_input):
    """ユーザー入力からFile Reader実行前の確認メッセージを作ります。

    txt / md 以外の拡張子や、パスが見つからない場合は確認対象にしません。
    この関数はローカルファイルへ一切アクセスせず、メッセージだけを作ります。
    """
    path = extract_file_path_from_text(user_input)

    if not path:
        return FileReaderConfirmation(
            needs_confirmation=False,
            path=None,
            tool_name=None,
            action=None,
            message="",
            reason="読み取り対象のファイルパスが見つかりませんでした。",
        )

    return FileReaderConfirmation(
        needs_confirmation=True,
        path=path,
        tool_name="file_reader",
        action="read_file",
        message=(
            "このファイルをFile Readerで読み取ってもよいですか？\n"
            f"{path}\n\n"
            "ローカルファイルへアクセスするため、実行前に確認が必要です。"
        ),
        reason="ローカルファイルアクセスにはユーザー確認が必要です。",
    )


def resolve_file_reader_confirmation_response(user_input, pending_confirmation=None, ask_llm_func=None):
    """File Reader確認への返答を分類し、実行候補を作ります。

    ここでは実行せず、確認済みの実行候補（ToolRequest候補）だけを作ります。
    """
    if not pending_confirmation:
        return FileReaderConfirmationResult(
            status="no_pending",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message="",
            reason="保留中のFile Reader確認がありません。",
        )

    intent = resolve_confirmation_intent(user_input, context_type="file_reader", ask_llm_func=ask_llm_func)

    if intent.get("status") == "confirmed":
        candidate = build_file_reader_tool_request_candidate(pending_confirmation)

        return FileReaderConfirmationResult(
            status="confirmed",
            should_execute=False,
            user_confirmed=True,
            tool_request_candidate=candidate,
            message="File Readerの実行許可を確認しました。",
            reason="ユーザーはFile Reader実行を許可しました。",
        )

    if intent.get("status") == "rejected":
        return FileReaderConfirmationResult(
            status="cancelled",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message=(
                "File Readerは実行しませんでした。\n"
                "必要になったら、もう一度ファイルパスを送ってください。"
            ),
            reason="ユーザーがFile Reader実行をキャンセルしました。",
        )

    return FileReaderConfirmationResult(
        status="unclear",
        should_execute=False,
        user_confirmed=False,
        tool_request_candidate=None,
        message=intent.get("message", ""),
        reason="File Reader確認待ち中の入力を確認応答として解釈できませんでした。",
    )


def build_file_reader_tool_request_candidate(pending_confirmation):
    """将来の実行に渡せる候補情報だけをdictで作ります。"""
    path = _get_value(pending_confirmation, "path")
    original_input = _get_value(pending_confirmation, "original_input", "")

    return {
        "tool_name": "file_reader",
        "action": "read_file",
        "input_data": {
            "path": path,
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
