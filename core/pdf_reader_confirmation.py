from dataclasses import dataclass
from typing import Optional

from core.confirmation_intent import resolve_confirmation_intent
from core.pdf_reader_adapter import extract_pdf_path_from_text


@dataclass
class PDFReaderConfirmation:
    """PDF Reader実行前の確認メッセージ結果です。"""

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
class PDFReaderConfirmationResult:
    """PDF Reader確認へのユーザー応答を整理した結果です。"""

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


def build_pdf_reader_confirmation(user_input):
    """ユーザー入力からPDF Reader実行前の確認メッセージを作ります。

    .pdf以外や、パスが見つからない場合は確認対象にしません。
    この関数はローカルファイルへ一切アクセスせず、メッセージだけを作ります。
    """
    path = extract_pdf_path_from_text(user_input)

    if not path:
        return PDFReaderConfirmation(
            needs_confirmation=False,
            path=None,
            tool_name=None,
            action=None,
            message="",
            reason="読み取り対象のPDFパスが見つかりませんでした。",
        )

    return PDFReaderConfirmation(
        needs_confirmation=True,
        path=path,
        tool_name="pdf_reader",
        action="read_pdf",
        message=(
            "このPDFをPDF Readerで読み取ってもよいですか？\n"
            f"{path}\n\n"
            "ローカルファイルへアクセスするため、実行前に確認が必要です。"
        ),
        reason="ローカルファイルアクセスにはユーザー確認が必要です。",
    )


def resolve_pdf_reader_confirmation_response(user_input, pending_confirmation=None, ask_llm_func=None):
    """PDF Reader確認への返答を分類し、実行候補を作ります。

    ここでは実行せず、確認済みの実行候補（ToolRequest候補）だけを作ります。
    """
    if not pending_confirmation:
        return PDFReaderConfirmationResult(
            status="no_pending",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message="",
            reason="保留中のPDF Reader確認がありません。",
        )

    intent = resolve_confirmation_intent(user_input, context_type="pdf_reader", ask_llm_func=ask_llm_func)

    if intent.get("status") == "confirmed":
        candidate = build_pdf_reader_tool_request_candidate(pending_confirmation)

        return PDFReaderConfirmationResult(
            status="confirmed",
            should_execute=False,
            user_confirmed=True,
            tool_request_candidate=candidate,
            message="PDF Readerの実行許可を確認しました。",
            reason="ユーザーはPDF Reader実行を許可しました。",
        )

    if intent.get("status") == "rejected":
        return PDFReaderConfirmationResult(
            status="cancelled",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message=(
                "PDF Readerは実行しませんでした。\n"
                "必要になったら、もう一度PDFパスを送ってください。"
            ),
            reason="ユーザーがPDF Reader実行をキャンセルしました。",
        )

    return PDFReaderConfirmationResult(
        status="unclear",
        should_execute=False,
        user_confirmed=False,
        tool_request_candidate=None,
        message=intent.get("message", ""),
        reason="PDF Reader確認待ち中の入力を確認応答として解釈できませんでした。",
    )


def build_pdf_reader_tool_request_candidate(pending_confirmation):
    """将来の実行に渡せる候補情報だけをdictで作ります。"""
    path = _get_value(pending_confirmation, "path")
    original_input = _get_value(pending_confirmation, "original_input", "")

    return {
        "tool_name": "pdf_reader",
        "action": "read_pdf",
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
