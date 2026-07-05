from dataclasses import dataclass, field
from typing import List, Optional

from core.confirmation_intent import resolve_confirmation_intent
from core.excel_reader_adapter import EXCEL_EXTENSIONS
from core.file_path_extraction import extract_multiple_file_paths_from_text


MAX_FILES_PER_REQUEST = 5


@dataclass
class ExcelReaderConfirmation:
    """Excel Reader実行前の確認メッセージ結果です。"""

    needs_confirmation: bool
    path: Optional[str]
    tool_name: Optional[str]
    action: Optional[str]
    message: str
    reason: str
    paths: List[str] = field(default_factory=list)

    def to_dict(self):
        """checkやデバッグで扱いやすいdict形式にします。"""
        return {
            "needs_confirmation": self.needs_confirmation,
            "path": self.path,
            "paths": list(self.paths),
            "tool_name": self.tool_name,
            "action": self.action,
            "message": self.message,
            "reason": self.reason,
        }


@dataclass
class ExcelReaderConfirmationResult:
    """Excel Reader確認へのユーザー応答を整理した結果です。"""

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


def build_excel_reader_confirmation(user_input):
    """ユーザー入力からExcel Reader実行前の確認メッセージを作ります。

    .xlsx以外や、パスが見つからない場合は確認対象にしません。
    複数のExcelファイルパスが列挙された場合は、まとめて確認しまとめて読み取ります
    （ディレクトリ丸ごとの読み取りには対応しません）。
    この関数はローカルファイルへ一切アクセスせず、メッセージだけを作ります。
    """
    paths = extract_multiple_file_paths_from_text(user_input, EXCEL_EXTENSIONS, max_files=MAX_FILES_PER_REQUEST)

    if not paths:
        return ExcelReaderConfirmation(
            needs_confirmation=False,
            path=None,
            paths=[],
            tool_name=None,
            action=None,
            message="",
            reason="読み取り対象のExcelファイルパスが見つかりませんでした。",
        )

    if len(paths) == 1:
        return ExcelReaderConfirmation(
            needs_confirmation=True,
            path=paths[0],
            paths=paths,
            tool_name="excel_reader",
            action="read_excel",
            message=(
                "このExcelファイルをExcel Readerで読み取ってもよいですか？\n"
                f"{paths[0]}\n\n"
                "ローカルファイルへアクセスするため、実行前に確認が必要です。"
            ),
            reason="ローカルファイルアクセスにはユーザー確認が必要です。",
        )

    path_list_text = "\n".join(paths)

    return ExcelReaderConfirmation(
        needs_confirmation=True,
        path=paths[0],
        paths=paths,
        tool_name="excel_reader",
        action="read_excels",
        message=(
            f"次の{len(paths)}件のExcelファイルをExcel Readerで読み取ってもよいですか？\n"
            f"{path_list_text}\n\n"
            "ローカルファイルへアクセスするため、実行前に確認が必要です。"
        ),
        reason="ローカルファイルアクセスにはユーザー確認が必要です。",
    )


def resolve_excel_reader_confirmation_response(user_input, pending_confirmation=None, ask_llm_func=None):
    """Excel Reader確認への返答を分類し、実行候補を作ります。

    ここでは実行せず、確認済みの実行候補（ToolRequest候補）だけを作ります。
    """
    if not pending_confirmation:
        return ExcelReaderConfirmationResult(
            status="no_pending",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message="",
            reason="保留中のExcel Reader確認がありません。",
        )

    intent = resolve_confirmation_intent(user_input, context_type="excel_reader", ask_llm_func=ask_llm_func)

    if intent.get("status") == "confirmed":
        candidate = build_excel_reader_tool_request_candidate(pending_confirmation)

        return ExcelReaderConfirmationResult(
            status="confirmed",
            should_execute=False,
            user_confirmed=True,
            tool_request_candidate=candidate,
            message="Excel Readerの実行許可を確認しました。",
            reason="ユーザーはExcel Reader実行を許可しました。",
        )

    if intent.get("status") == "rejected":
        return ExcelReaderConfirmationResult(
            status="cancelled",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message=(
                "Excel Readerは実行しませんでした。\n"
                "必要になったら、もう一度Excelファイルパスを送ってください。"
            ),
            reason="ユーザーがExcel Reader実行をキャンセルしました。",
        )

    return ExcelReaderConfirmationResult(
        status="unclear",
        should_execute=False,
        user_confirmed=False,
        tool_request_candidate=None,
        message=intent.get("message", ""),
        reason="Excel Reader確認待ち中の入力を確認応答として解釈できませんでした。",
    )


def build_excel_reader_tool_request_candidate(pending_confirmation):
    """将来の実行に渡せる候補情報だけをdictで作ります。"""
    path = _get_value(pending_confirmation, "path")
    paths = _get_value(pending_confirmation, "paths") or ([path] if path else [])
    original_input = _get_value(pending_confirmation, "original_input", "")

    return {
        "tool_name": "excel_reader",
        "action": "read_excel" if len(paths) <= 1 else "read_excels",
        "input_data": {
            "path": path,
            "paths": paths,
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
