from dataclasses import dataclass, field
from typing import List, Optional

from core.confirmation_intent import resolve_confirmation_intent
from core.word_reader_adapter import WORD_EXTENSIONS
from core.file_path_extraction import extract_multiple_file_paths_from_text


MAX_FILES_PER_REQUEST = 5


@dataclass
class WordReaderConfirmation:
    """Word Reader実行前の確認メッセージ結果です。"""

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
class WordReaderConfirmationResult:
    """Word Reader確認へのユーザー応答を整理した結果です。"""

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


def build_word_reader_confirmation(user_input):
    """ユーザー入力からWord Reader実行前の確認メッセージを作ります。

    .docx以外や、パスが見つからない場合は確認対象にしません。
    複数のWordファイルパスが列挙された場合は、まとめて確認しまとめて読み取ります
    （ディレクトリ丸ごとの読み取りには対応しません）。
    この関数はローカルファイルへ一切アクセスせず、メッセージだけを作ります。
    """
    paths = extract_multiple_file_paths_from_text(user_input, WORD_EXTENSIONS, max_files=MAX_FILES_PER_REQUEST)

    if not paths:
        return WordReaderConfirmation(
            needs_confirmation=False,
            path=None,
            paths=[],
            tool_name=None,
            action=None,
            message="",
            reason="読み取り対象のWordファイルパスが見つかりませんでした。",
        )

    if len(paths) == 1:
        return WordReaderConfirmation(
            needs_confirmation=True,
            path=paths[0],
            paths=paths,
            tool_name="word_reader",
            action="read_word",
            message=(
                "このWordファイルをWord Readerで読み取ってもよいですか？\n"
                f"{paths[0]}\n\n"
                "ローカルファイルへアクセスするため、実行前に確認が必要です。"
            ),
            reason="ローカルファイルアクセスにはユーザー確認が必要です。",
        )

    path_list_text = "\n".join(paths)

    return WordReaderConfirmation(
        needs_confirmation=True,
        path=paths[0],
        paths=paths,
        tool_name="word_reader",
        action="read_words",
        message=(
            f"次の{len(paths)}件のWordファイルをWord Readerで読み取ってもよいですか？\n"
            f"{path_list_text}\n\n"
            "ローカルファイルへアクセスするため、実行前に確認が必要です。"
        ),
        reason="ローカルファイルアクセスにはユーザー確認が必要です。",
    )


def resolve_word_reader_confirmation_response(user_input, pending_confirmation=None, ask_llm_func=None):
    """Word Reader確認への返答を分類し、実行候補を作ります。

    ここでは実行せず、確認済みの実行候補（ToolRequest候補）だけを作ります。
    """
    if not pending_confirmation:
        return WordReaderConfirmationResult(
            status="no_pending",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message="",
            reason="保留中のWord Reader確認がありません。",
        )

    intent = resolve_confirmation_intent(user_input, context_type="word_reader", ask_llm_func=ask_llm_func)

    if intent.get("status") == "confirmed":
        candidate = build_word_reader_tool_request_candidate(pending_confirmation)

        return WordReaderConfirmationResult(
            status="confirmed",
            should_execute=False,
            user_confirmed=True,
            tool_request_candidate=candidate,
            message="Word Readerの実行許可を確認しました。",
            reason="ユーザーはWord Reader実行を許可しました。",
        )

    if intent.get("status") == "rejected":
        return WordReaderConfirmationResult(
            status="cancelled",
            should_execute=False,
            user_confirmed=False,
            tool_request_candidate=None,
            message=(
                "Word Readerは実行しませんでした。\n"
                "必要になったら、もう一度Wordファイルパスを送ってください。"
            ),
            reason="ユーザーがWord Reader実行をキャンセルしました。",
        )

    return WordReaderConfirmationResult(
        status="unclear",
        should_execute=False,
        user_confirmed=False,
        tool_request_candidate=None,
        message=intent.get("message", ""),
        reason="Word Reader確認待ち中の入力を確認応答として解釈できませんでした。",
    )


def build_word_reader_tool_request_candidate(pending_confirmation):
    """将来の実行に渡せる候補情報だけをdictで作ります。"""
    path = _get_value(pending_confirmation, "path")
    paths = _get_value(pending_confirmation, "paths") or ([path] if path else [])
    original_input = _get_value(pending_confirmation, "original_input", "")

    return {
        "tool_name": "word_reader",
        "action": "read_word" if len(paths) <= 1 else "read_words",
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
