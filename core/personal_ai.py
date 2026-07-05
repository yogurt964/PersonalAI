import re
import textwrap

from ai.llm import SYSTEM_PROMPT, ask_llm
from ai.conversation_quality_policy import (
    build_conversation_quality_guidance,
    classify_conversation_mode,
)
from ai.memory_context import build_memory_context
from ai.memory_extract import extract_memories
from ai.memory_usage_policy import decide_memory_usage
from ai.preference_confirmation import (
    analyze_preference_confirmation,
    resolve_preference_confirmation_answer,
    save_resolved_preference_confirmation,
)
from ai.preference_memory import save_preference_memories
from core.capability_manager import CapabilityManager
from core.executor import Executor
from core.input_analyzer import InputAnalyzer
from core.memory_candidate import build_memory_candidate_from_reader_result
from core.memory_candidate_confirmation import (
    resolve_memory_candidate_confirmation_response,
    resolve_memory_candidate_edit_response,
)
from core.memory_candidate_saver import save_memory_candidate
from core.memory_search import (
    detect_memory_search_intent,
    format_memory_search_response,
    search_memories,
)
from core.permission_manager import PermissionManager
from core.planner import Planner
from core.router import Router
from core.tool_adapter import ToolRequest
from core.tool_execution_log import ToolExecutionLogger
from core.tool_registry import ToolRegistry
from core.tool_runner import run_tool_request
from core.file_reader_adapter import FileReaderAdapter
from core.file_reader_confirmation import (
    build_file_reader_confirmation,
    resolve_file_reader_confirmation_response,
)
from core.pdf_reader_adapter import PDFReaderAdapter
from core.pdf_reader_confirmation import (
    build_pdf_reader_confirmation,
    resolve_pdf_reader_confirmation_response,
)
from core.word_reader_adapter import WordReaderAdapter
from core.word_reader_confirmation import (
    build_word_reader_confirmation,
    resolve_word_reader_confirmation_response,
)
from core.web_reader_adapter import WebReaderAdapter
from core.web_reader_confirmation import (
    build_web_reader_confirmation,
    resolve_web_reader_confirmation_response,
)
from database.chat_history import get_recent_messages, save_message
from database.memory_manager import get_memories, save_memory
from database.models import create_database


WEB_READER_PREVIEW_MAX_CHARS = 360
WEB_READER_PREVIEW_LINE_WIDTH = 90
SAVED_MEMORY_PREVIEW_MAX_CHARS = 420
LAST_READ_DOCUMENT_CONTEXT_MAX_CHARS = 4000
DOCUMENT_TASK_TYPES = ("summarize", "question")
READER_SOURCE_LABELS = {
    "web_reader": "Web Reader",
    "file_reader": "File Reader",
    "pdf_reader": "PDF Reader",
    "word_reader": "Word Reader",
}
RECENT_SAVED_MEMORY_REQUEST_WORDS = [
    "今保存した記憶",
    "直近保存した記憶",
    "保存したmemory",
    "今の記憶",
]


def build_web_reader_confirmation_response(user_input, input_analysis=None, confirmation=None):
    """会話返答として出せるWeb Reader確認メッセージをdry-runで作ります。

    URLがない場合やYouTube URLの場合は、Web Reader確認メッセージにしません。
    この関数はTool実行処理を呼ばず、メッセージだけを返します。
    """
    if _get_analysis_value(input_analysis, "input_type") == "youtube":
        return None

    confirmation = confirmation or build_web_reader_confirmation(user_input)

    if not confirmation.needs_confirmation:
        return None

    return confirmation.message


def _get_analysis_value(input_analysis, key, default=None):
    """InputAnalyzerのdictや将来のモデル形式から値を取り出します。"""
    if input_analysis is None:
        return default

    if isinstance(input_analysis, dict):
        return input_analysis.get(key, default)

    return getattr(input_analysis, key, default)


def _clean_web_reader_display_text(value):
    """Web Reader表示用に、余分な空白や改行を1つの空白へ整理します。"""
    if value is None:
        return ""

    return " ".join(str(value).split())


def _shorten_web_reader_preview(text, max_chars=WEB_READER_PREVIEW_MAX_CHARS):
    """本文プレビューが長すぎる場合、読みやすい長さに切ります。"""
    text = _clean_web_reader_display_text(text)

    if len(text) <= max_chars:
        return text

    shortened = text[:max_chars].rstrip()
    last_space = shortened.rfind(" ")

    if last_space >= int(max_chars * 0.6):
        shortened = shortened[:last_space].rstrip()

    return f"{shortened}..."


def _split_web_reader_preview_lines(text):
    """句点などを目安に、本文プレビューを数行へ分けます。"""
    if not text:
        return []

    parts = re.split(r"(?<=[。！？.!?])\s+", text)
    lines = []

    for part in parts:
        part = part.strip()

        if not part:
            continue

        wrapped_lines = textwrap.wrap(
            part,
            width=WEB_READER_PREVIEW_LINE_WIDTH,
            break_long_words=False,
            break_on_hyphens=False,
        )
        lines.extend(wrapped_lines or [part])

    return lines


def _format_web_reader_preview(text, title=None):
    """本文プレビューを、会話で読みやすい複数行の表示に整えます。"""
    preview = _shorten_web_reader_preview(text)

    if not preview:
        return "(本文プレビューなし)"

    title_text = _clean_web_reader_display_text(title)
    lines = []

    if title_text and preview.startswith(f"{title_text} "):
        lines.append(title_text)
        preview = preview[len(title_text):].strip()
    elif title_text and preview == title_text:
        return title_text

    lines.extend(_split_web_reader_preview_lines(preview))

    return "\n".join(lines) if lines else "(本文プレビューなし)"


class PersonalAI:
    """PersonalAI本体の会話処理をまとめるクラスです。"""

    def __init__(self, web_reader_fetcher=None, memory_search_func=None):
        # 起動時にデータベースとテーブルを用意します。
        create_database()

        # PersonalAIが使える能力、行動計画、道具選択を担当する部品です。
        self.input_analyzer = InputAnalyzer()
        self.capability_manager = CapabilityManager()
        self.planner = Planner()
        self.router = Router()
        self.permission_manager = PermissionManager()
        self.executor = Executor()
        self.web_reader_fetcher = web_reader_fetcher
        self.memory_search_func = memory_search_func
        self.ask_llm_func = ask_llm
        self.tool_registry = self.build_tool_registry(web_reader_fetcher)
        self.tool_execution_logger = ToolExecutionLogger()

        # 直近の判断結果を保存しておく場所です。将来のデバッグやExecutor連携で使えます。
        self.last_input_analysis = None
        self.last_capability_analysis = None
        self.last_capabilities = None
        self.last_plan = None
        self.last_route = None
        self.last_permission_decision = None
        self.last_preference_confirmation = None
        self.last_memory_usage = None
        self.last_conversation_mode = None
        self.last_conversation_quality_guidance = None
        self.last_web_reader_confirmation = None
        self.last_web_reader_confirmation_result = None
        self.last_web_reader_tool_request_candidate = None
        self.last_web_reader_tool_run_result = None
        self.last_web_reader_tool_result = None
        self.last_file_reader_confirmation = None
        self.last_file_reader_confirmation_result = None
        self.last_file_reader_tool_request_candidate = None
        self.last_file_reader_tool_run_result = None
        self.last_file_reader_tool_result = None
        self.last_pdf_reader_confirmation = None
        self.last_pdf_reader_confirmation_result = None
        self.last_pdf_reader_tool_request_candidate = None
        self.last_pdf_reader_tool_run_result = None
        self.last_pdf_reader_tool_result = None
        self.last_word_reader_confirmation = None
        self.last_word_reader_confirmation_result = None
        self.last_word_reader_tool_request_candidate = None
        self.last_word_reader_tool_run_result = None
        self.last_word_reader_tool_result = None
        self.last_read_document = None
        self.last_tool_execution_record = None
        self.last_memory_candidate = None
        self.last_memory_candidate_confirmation_result = None
        self.last_memory_candidate_save_result = None
        self.last_saved_memory_candidate_result = None
        self.last_memory_search_intent = None
        self.last_memory_search_result = None
        self.pending_preference_confirmation = None
        self.pending_memory_candidate_confirmation = None
        self.pending_memory_candidate_edit = None
        self.pending_web_reader_confirmation = None
        self.pending_file_reader_confirmation = None
        self.pending_pdf_reader_confirmation = None
        self.pending_word_reader_confirmation = None
        self.last_response = None

    def build_tool_registry(self, web_reader_fetcher=None):
        """会話UIから使うToolRegistryを用意します。"""
        registry = ToolRegistry()
        registry.register(WebReaderAdapter(fetcher=web_reader_fetcher))
        registry.register(FileReaderAdapter())
        registry.register(PDFReaderAdapter())
        registry.register(WordReaderAdapter())
        return registry

    def run(self):
        """ユーザー入力を受け取り続けるメインループです。"""
        while True:
            user_input = input("あなた: ")

            if user_input.lower() == "exit":
                break

            ai_response = self.handle_user_input(user_input)

            print()
            print("AI:", ai_response)
            print()

    def handle_user_input(self, user_input):
        """ユーザーの1回分の発言を処理して、AIの返答を返します。"""
        self.save_user_message(user_input)

        pending_response = self.handle_pending_preference_confirmation(user_input)

        if pending_response:
            self.last_response = pending_response
            self.save_assistant_message(pending_response)
            return pending_response

        pending_memory_candidate_edit_response = self.handle_pending_memory_candidate_edit(user_input)

        if pending_memory_candidate_edit_response:
            self.last_response = pending_memory_candidate_edit_response
            self.save_assistant_message(pending_memory_candidate_edit_response)
            return pending_memory_candidate_edit_response

        pending_memory_candidate_response = self.handle_pending_memory_candidate_confirmation(user_input)

        if pending_memory_candidate_response:
            self.last_response = pending_memory_candidate_response
            self.save_assistant_message(pending_memory_candidate_response)
            return pending_memory_candidate_response

        pending_web_reader_response = self.handle_pending_web_reader_confirmation(user_input)

        if pending_web_reader_response:
            self.last_response = pending_web_reader_response
            self.save_assistant_message(pending_web_reader_response)
            return pending_web_reader_response

        pending_file_reader_response = self.handle_pending_file_reader_confirmation(user_input)

        if pending_file_reader_response:
            self.last_response = pending_file_reader_response
            self.save_assistant_message(pending_file_reader_response)
            return pending_file_reader_response

        pending_pdf_reader_response = self.handle_pending_pdf_reader_confirmation(user_input)

        if pending_pdf_reader_response:
            self.last_response = pending_pdf_reader_response
            self.save_assistant_message(pending_pdf_reader_response)
            return pending_pdf_reader_response

        pending_word_reader_response = self.handle_pending_word_reader_confirmation(user_input)

        if pending_word_reader_response:
            self.last_response = pending_word_reader_response
            self.save_assistant_message(pending_word_reader_response)
            return pending_word_reader_response

        recent_saved_memory_response = self.handle_recent_saved_memory_request(user_input)

        if recent_saved_memory_response:
            self.last_response = recent_saved_memory_response
            self.save_assistant_message(recent_saved_memory_response)
            return recent_saved_memory_response

        memory_search_response = self.handle_memory_search_request(user_input)

        if memory_search_response:
            self.last_response = memory_search_response
            self.save_assistant_message(memory_search_response)
            return memory_search_response

        # 入力内容を構造化して、将来のPlannerやRouterが使いやすい形にします。
        # 現時点ではWebやYouTubeを実際に読みに行く処理は行いません。
        input_analysis = self.input_analyzer.analyze(user_input)
        self.last_input_analysis = input_analysis

        # Ver2.3では、URLを含む入力に対してWeb Reader実行前の確認メッセージだけを返します。
        # ここではWebアクセスせず、許可後の実行接続もまだ行いません。
        web_reader_confirmation = build_web_reader_confirmation(user_input)
        self.last_web_reader_confirmation = web_reader_confirmation
        self.last_web_reader_confirmation_result = None
        self.last_web_reader_tool_request_candidate = None
        self.last_web_reader_tool_run_result = None
        self.last_web_reader_tool_result = None
        self.last_tool_execution_record = None
        self.last_memory_candidate = None
        self.last_memory_candidate_confirmation_result = None
        self.last_memory_candidate_save_result = None
        self.pending_memory_candidate_edit = None
        web_reader_response = build_web_reader_confirmation_response(
            user_input,
            input_analysis=input_analysis,
            confirmation=web_reader_confirmation,
        )

        if web_reader_response:
            self.pending_web_reader_confirmation = web_reader_confirmation.to_dict()
            self.pending_web_reader_confirmation["original_input"] = user_input
            self.last_response = web_reader_response
            self.save_assistant_message(web_reader_response)
            return web_reader_response

        # Ver2.29では、ユーザーが指定した単一のtxt/mdファイルに限り、確認後に読み取ります。
        # ここではファイルへ一切アクセスせず、確認メッセージだけを返します。
        file_reader_confirmation = build_file_reader_confirmation(user_input)
        self.last_file_reader_confirmation = file_reader_confirmation
        self.last_file_reader_confirmation_result = None
        self.last_file_reader_tool_request_candidate = None
        self.last_file_reader_tool_run_result = None
        self.last_file_reader_tool_result = None

        if file_reader_confirmation.needs_confirmation:
            self.pending_file_reader_confirmation = file_reader_confirmation.to_dict()
            self.pending_file_reader_confirmation["original_input"] = user_input
            self.last_response = file_reader_confirmation.message
            self.save_assistant_message(file_reader_confirmation.message)
            return file_reader_confirmation.message

        # Ver2.32では、ユーザーが指定した単一のPDFファイルに限り、確認後に読み取ります。
        pdf_reader_confirmation = build_pdf_reader_confirmation(user_input)
        self.last_pdf_reader_confirmation = pdf_reader_confirmation
        self.last_pdf_reader_confirmation_result = None
        self.last_pdf_reader_tool_request_candidate = None
        self.last_pdf_reader_tool_run_result = None
        self.last_pdf_reader_tool_result = None

        if pdf_reader_confirmation.needs_confirmation:
            self.pending_pdf_reader_confirmation = pdf_reader_confirmation.to_dict()
            self.pending_pdf_reader_confirmation["original_input"] = user_input
            self.last_response = pdf_reader_confirmation.message
            self.save_assistant_message(pdf_reader_confirmation.message)
            return pdf_reader_confirmation.message

        # Ver2.36では、ユーザーが指定した単一の.docxファイルに限り、確認後に読み取ります。
        word_reader_confirmation = build_word_reader_confirmation(user_input)
        self.last_word_reader_confirmation = word_reader_confirmation
        self.last_word_reader_confirmation_result = None
        self.last_word_reader_tool_request_candidate = None
        self.last_word_reader_tool_run_result = None
        self.last_word_reader_tool_result = None

        if word_reader_confirmation.needs_confirmation:
            self.pending_word_reader_confirmation = word_reader_confirmation.to_dict()
            self.pending_word_reader_confirmation["original_input"] = user_input
            self.last_response = word_reader_confirmation.message
            self.save_assistant_message(word_reader_confirmation.message)
            return word_reader_confirmation.message

        # 通常会話ではMemoryを控えめにし、記憶参照では詳しく使います。
        memory_usage = decide_memory_usage(user_input, input_analysis)
        self.last_memory_usage = memory_usage
        conversation_quality_guidance = build_conversation_quality_guidance(
            user_input,
            memory_usage=memory_usage,
            input_analysis=input_analysis,
        )
        conversation_mode = classify_conversation_mode(user_input)
        self.last_conversation_mode = conversation_mode
        self.last_conversation_quality_guidance = conversation_quality_guidance

        # 今のPersonalAIで対応できる入力かを先に判定します。
        # WebやPDFなど未実装の読み取りが必要な場合は、読んだふりをせずここで返答します。
        capability_analysis = self.capability_manager.analyze(user_input, input_analysis)
        self.last_capability_analysis = capability_analysis

        if not capability_analysis.get("can_handle_now"):
            ai_response = self.build_capability_unavailable_response(capability_analysis)
            self.last_response = ai_response
            self.save_assistant_message(ai_response)
            return ai_response

        memory_response = self.extract_and_save_memories(user_input)

        if memory_response:
            self.last_response = memory_response
            self.save_assistant_message(memory_response)
            return memory_response

        # ここで利用可能な能力、計画、処理先を作ります。
        # routeはExecutorへ渡し、Executorが実際のQwen呼び出しを担当します。
        capabilities = self.capability_manager.get_available_capabilities(user_input)
        plan = self.planner.create_plan(
            user_input,
            context=input_analysis,
            capabilities=capabilities,
        )
        route = self.router.route(plan)

        self.last_capabilities = capabilities
        self.last_plan = plan
        self.last_route = route

        permission_decision = self.permission_manager.evaluate(plan, route)
        self.last_permission_decision = permission_decision

        if permission_decision.get("blocked"):
            ai_response = self.build_permission_blocked_response(permission_decision)
            self.last_response = ai_response
            self.save_assistant_message(ai_response)
            return ai_response

        messages = self.build_messages(
            memory_usage,
            conversation_quality_guidance,
            conversation_mode,
        )
        ai_response = self.executor.execute(plan, route, messages)
        self.last_response = ai_response

        self.save_assistant_message(ai_response)

        return ai_response

    def build_capability_unavailable_response(self, capability_analysis):
        """必要な機能が未実装の場合に、できない理由を正直に返します。"""
        user_message = capability_analysis.get("user_message")

        if user_message:
            return user_message

        reason = capability_analysis.get("reason", "現在のPersonalAIでは対応できない入力です。")
        return f"現時点ではこの依頼を安全に実行できません。\n理由: {reason}"

    def build_permission_blocked_response(self, permission_decision):
        """許可が必要な操作を、現時点では安全に止めるための返答を作ります。"""
        reason = permission_decision.get("reason", "安全確認が必要な操作です")

        return (
            "この操作は安全確認が必要です。\n"
            f"理由: {reason}\n"
            "現時点では、許可後にこの操作を続行する仕組みは未実装です。"
        )

    def save_user_message(self, user_input):
        """ユーザー発言を会話履歴に保存します。"""
        save_message("user", user_input)

    def save_assistant_message(self, ai_response):
        """AIの返答を会話履歴に保存します。"""
        save_message("assistant", ai_response)

    def handle_pending_preference_confirmation(self, user_input):
        """保留中のPreference確認がある場合、通常処理より先に回答として扱います。"""
        if not self.pending_preference_confirmation:
            return None

        resolution = resolve_preference_confirmation_answer(
            user_input,
            self.pending_preference_confirmation,
        )

        if resolution.get("action") in ("save_primary", "save_addition", "save_change"):
            save_resolved_preference_confirmation(
                self.pending_preference_confirmation,
                resolution,
            )

        if resolution.get("should_clear_pending"):
            self.pending_preference_confirmation = None

        return resolution.get("message")

    def handle_pending_memory_candidate_confirmation(self, user_input):
        """Memory Candidate確認応答をdry-runで扱います。"""
        pending_candidate = getattr(self, "pending_memory_candidate_confirmation", None)

        if not pending_candidate:
            return None

        result = resolve_memory_candidate_confirmation_response(
            user_input,
            pending_candidate,
        )
        self.last_memory_candidate_confirmation_result = result

        if result.get("status") == "confirmed":
            save_result = save_memory_candidate(
                result.get("candidate"),
                save_memory,
            )
            self.last_memory_candidate_save_result = save_result
            if save_result.get("status") == "saved":
                self.last_saved_memory_candidate_result = dict(save_result)
            self.pending_memory_candidate_confirmation = None
            self.pending_memory_candidate_edit = None
            return self.build_memory_candidate_save_response(save_result)

        # 保存しない・後で確認はDBへ保存せず、pendingを解除します。
        if result.get("status") in ["rejected", "postponed"]:
            self.pending_memory_candidate_confirmation = None
            self.pending_memory_candidate_edit = None

        if result.get("status") == "edit_requested":
            self.pending_memory_candidate_edit = dict(pending_candidate)

        return result.get("message")

    def handle_pending_memory_candidate_edit(self, user_input):
        """Memory Candidateの編集内容をdry-runで受け取ります。"""
        pending_candidate = getattr(self, "pending_memory_candidate_edit", None)

        if not pending_candidate:
            return None

        result = resolve_memory_candidate_edit_response(
            user_input,
            pending_candidate,
        )
        self.last_memory_candidate_confirmation_result = result

        if result.get("status") == "edit_empty":
            return result.get("message")

        if result.get("status") == "edit_cancelled":
            self.pending_memory_candidate_edit = None
            self.pending_memory_candidate_confirmation = None
            return result.get("message")

        if result.get("status") == "edited_dry_run":
            edited_candidate = result.get("edited_candidate") or {}
            self.last_memory_candidate = edited_candidate
            self.pending_memory_candidate_edit = None
            self.pending_memory_candidate_confirmation = dict(edited_candidate)

            return (
                f"{result.get('message')}\n\n"
                f"{self.format_edited_memory_candidate_dry_run(result)}"
            )

        return result.get("message")

    def build_memory_candidate_save_response(self, save_result):
        """Memory Candidate保存結果を、会話で分かりやすい返答へ変換します。"""
        status = save_result.get("status")

        if status == "saved":
            return (
                f"{save_result.get('message')}\n\n"
                f"{self.format_saved_memory_candidate_preview(save_result)}\n\n"
                "保存結果:\n"
                "- 保存先: 既存の長期記憶\n"
                "- DBスキーマ変更: なし"
            )

        if status == "save_blocked_high_risk":
            return save_result.get("message")

        if status == "save_unavailable":
            return save_result.get("message")

        error = save_result.get("error")

        if error:
            return f"{save_result.get('message')}\n理由: {error}"

        return save_result.get("message", "Memory Candidateの保存結果を確認できませんでした。")

    def handle_recent_saved_memory_request(self, user_input):
        """直近保存したMemory Candidateの確認依頼に答えます。"""
        if not self.is_recent_saved_memory_request(user_input):
            return None

        if not self.last_saved_memory_candidate_result:
            return "この会話中に確認できる直近保存Memoryはまだありません。"

        return (
            "直近保存したMemoryは以下です。\n\n"
            f"{self.format_saved_memory_candidate_preview(self.last_saved_memory_candidate_result)}"
        )

    def is_recent_saved_memory_request(self, user_input):
        """ユーザーが直近保存Memoryの確認を求めているか判定します。"""
        normalized_input = str(user_input or "").lower()
        return any(word.lower() in normalized_input for word in RECENT_SAVED_MEMORY_REQUEST_WORDS)

    def handle_memory_search_request(self, user_input):
        """保存済みMemory全体から、簡易キーワード検索で探します。"""
        intent = detect_memory_search_intent(user_input)
        self.last_memory_search_intent = intent

        if not intent.get("is_memory_search"):
            return None

        result = search_memories(
            intent.get("query", ""),
            search_func=getattr(self, "memory_search_func", None),
        )
        self.last_memory_search_result = result

        return format_memory_search_response(result)

    def format_saved_memory_candidate_preview(self, save_result):
        """保存済みMemory Candidateの内容を短く見やすく表示します。"""
        candidate = save_result.get("candidate") or {}
        memory_text = save_result.get("memory_text") or ""
        title = _clean_web_reader_display_text(candidate.get("title")) or "(タイトルなし)"
        source_url = _clean_web_reader_display_text(candidate.get("source_url")) or "(URLなし)"
        summary = _clean_web_reader_display_text(candidate.get("summary")) or "(要約なし)"
        source_tool = _clean_web_reader_display_text(candidate.get("source_tool")) or "unknown"
        candidate_type = _clean_web_reader_display_text(candidate.get("candidate_type")) or "unknown"
        risk_level = _clean_web_reader_display_text(candidate.get("risk_level")) or "unknown"
        memory_text_preview = _shorten_web_reader_preview(memory_text, SAVED_MEMORY_PREVIEW_MAX_CHARS)

        return (
            "保存内容:\n"
            "タイトル:\n"
            f"{title}\n\n"
            "URL:\n"
            f"{source_url}\n\n"
            "要約:\n"
            f"{summary}\n\n"
            "保存元:\n"
            f"{source_tool}\n\n"
            "保存候補タイプ:\n"
            f"{candidate_type}\n\n"
            "リスク:\n"
            f"{risk_level}\n\n"
            "memory_text preview:\n"
            f"{memory_text_preview or '(保存テキストなし)'}"
        )

    def extract_and_save_memories(self, user_input):
        """ユーザー発言から長期記憶を抽出し、保存します。"""
        self.last_preference_confirmation = None

        # 明確な「好き・好きじゃない・嫌い」は、専用のPreference記憶として先に扱います。
        # 同じ対象はmemory_keyで更新されるため、好き嫌いの現在状態を保ちやすくなります。
        if "覚えて" in user_input:
            preference_confirmation = analyze_preference_confirmation(user_input)
            self.last_preference_confirmation = preference_confirmation

            if preference_confirmation.get("should_ask"):
                self.pending_preference_confirmation = self.build_pending_preference_confirmation(
                    user_input,
                    preference_confirmation,
                )
                return preference_confirmation.get("question")

            preference_results = save_preference_memories(user_input)

            if preference_results:
                return

        extracted_memories = extract_memories(user_input)

        for extracted_memory in extracted_memories:
            if extracted_memory.get("content"):
                save_memory(
                    extracted_memory.get("content"),
                    extracted_memory.get("memory_type", "user_profile"),
                    extracted_memory.get("category", "other"),
                    extracted_memory.get("importance", 5),
                    extracted_memory.get("source", "user"),
                    extracted_memory.get("tags", ""),
                    extracted_memory.get("memory_key"),
                    extracted_memory.get("subcategory"),
                    extracted_memory.get("scope", "global"),
                    extracted_memory.get("confidence", 80),
                    extracted_memory.get("expires_at"),
                )

    def build_pending_preference_confirmation(self, user_input, preference_confirmation):
        """Preference確認質問の保留情報を、1件だけ保存できる形にします。"""
        return {
            "type": "preference_confirmation",
            "original_text": user_input,
            "reason": preference_confirmation.get("reason"),
            "target": preference_confirmation.get("target"),
            "old_target": preference_confirmation.get("old_target"),
            "new_target": preference_confirmation.get("new_target"),
            "domain": preference_confirmation.get("domain", "food"),
            "question": preference_confirmation.get("question", ""),
        }

    def handle_pending_web_reader_confirmation(self, user_input):
        """Web Reader確認後の返答を、実行せずに安全に扱います。"""
        pending_confirmation = getattr(self, "pending_web_reader_confirmation", None)

        if not pending_confirmation:
            return None

        result = resolve_web_reader_confirmation_response(
            user_input,
            pending_confirmation,
        )
        self.last_web_reader_confirmation_result = result.to_dict()
        self.last_web_reader_tool_request_candidate = result.tool_request_candidate

        if result.status in ["confirmed", "cancelled"]:
            self.pending_web_reader_confirmation = None

        if result.status == "confirmed" and result.tool_request_candidate:
            return self.execute_web_reader_tool_request_candidate(
                result.tool_request_candidate,
            )

        return result.message or None

    def handle_pending_file_reader_confirmation(self, user_input):
        """File Reader確認後の返答を扱います。"""
        pending_confirmation = getattr(self, "pending_file_reader_confirmation", None)

        if not pending_confirmation:
            return None

        result = resolve_file_reader_confirmation_response(
            user_input,
            pending_confirmation,
        )
        self.last_file_reader_confirmation_result = result.to_dict()
        self.last_file_reader_tool_request_candidate = result.tool_request_candidate

        if result.status in ["confirmed", "cancelled"]:
            self.pending_file_reader_confirmation = None

        if result.status == "confirmed" and result.tool_request_candidate:
            return self.execute_file_reader_tool_request_candidate(
                result.tool_request_candidate,
            )

        return result.message or None

    def execute_file_reader_tool_request_candidate(self, candidate):
        """File Readerの実行候補をToolRunnerへ渡し、結果を会話返答にします。"""
        request = self.build_tool_request_from_candidate(candidate)
        user_confirmed = bool(candidate.get("user_confirmed"))
        registry = getattr(self, "tool_registry", None)

        if registry is None:
            registry = self.build_tool_registry(getattr(self, "web_reader_fetcher", None))
            self.tool_registry = registry

        logger = getattr(self, "tool_execution_logger", None)

        if logger is None:
            logger = ToolExecutionLogger()
            self.tool_execution_logger = logger

        run_result = run_tool_request(
            request,
            registry=registry,
            user_confirmed=user_confirmed,
            logger=logger,
        )

        self.last_file_reader_tool_run_result = run_result
        self.last_file_reader_tool_result = run_result.result
        self.last_tool_execution_record = run_result.execution_record

        original_input = (candidate.get("input_data") or {}).get("original_input", "")

        return self.build_file_reader_tool_response(run_result.result, original_input=original_input)

    def handle_pending_pdf_reader_confirmation(self, user_input):
        """PDF Reader確認後の返答を扱います。"""
        pending_confirmation = getattr(self, "pending_pdf_reader_confirmation", None)

        if not pending_confirmation:
            return None

        result = resolve_pdf_reader_confirmation_response(
            user_input,
            pending_confirmation,
        )
        self.last_pdf_reader_confirmation_result = result.to_dict()
        self.last_pdf_reader_tool_request_candidate = result.tool_request_candidate

        if result.status in ["confirmed", "cancelled"]:
            self.pending_pdf_reader_confirmation = None

        if result.status == "confirmed" and result.tool_request_candidate:
            return self.execute_pdf_reader_tool_request_candidate(
                result.tool_request_candidate,
            )

        return result.message or None

    def execute_pdf_reader_tool_request_candidate(self, candidate):
        """PDF Readerの実行候補をToolRunnerへ渡し、結果を会話返答にします。"""
        request = self.build_tool_request_from_candidate(candidate)
        user_confirmed = bool(candidate.get("user_confirmed"))
        registry = getattr(self, "tool_registry", None)

        if registry is None:
            registry = self.build_tool_registry(getattr(self, "web_reader_fetcher", None))
            self.tool_registry = registry

        logger = getattr(self, "tool_execution_logger", None)

        if logger is None:
            logger = ToolExecutionLogger()
            self.tool_execution_logger = logger

        run_result = run_tool_request(
            request,
            registry=registry,
            user_confirmed=user_confirmed,
            logger=logger,
        )

        self.last_pdf_reader_tool_run_result = run_result
        self.last_pdf_reader_tool_result = run_result.result
        self.last_tool_execution_record = run_result.execution_record

        original_input = (candidate.get("input_data") or {}).get("original_input", "")

        return self.build_pdf_reader_tool_response(run_result.result, original_input=original_input)

    def handle_pending_word_reader_confirmation(self, user_input):
        """Word Reader確認後の返答を扱います。"""
        pending_confirmation = getattr(self, "pending_word_reader_confirmation", None)

        if not pending_confirmation:
            return None

        result = resolve_word_reader_confirmation_response(
            user_input,
            pending_confirmation,
        )
        self.last_word_reader_confirmation_result = result.to_dict()
        self.last_word_reader_tool_request_candidate = result.tool_request_candidate

        if result.status in ["confirmed", "cancelled"]:
            self.pending_word_reader_confirmation = None

        if result.status == "confirmed" and result.tool_request_candidate:
            return self.execute_word_reader_tool_request_candidate(
                result.tool_request_candidate,
            )

        return result.message or None

    def execute_word_reader_tool_request_candidate(self, candidate):
        """Word Readerの実行候補をToolRunnerへ渡し、結果を会話返答にします。"""
        request = self.build_tool_request_from_candidate(candidate)
        user_confirmed = bool(candidate.get("user_confirmed"))
        registry = getattr(self, "tool_registry", None)

        if registry is None:
            registry = self.build_tool_registry(getattr(self, "web_reader_fetcher", None))
            self.tool_registry = registry

        logger = getattr(self, "tool_execution_logger", None)

        if logger is None:
            logger = ToolExecutionLogger()
            self.tool_execution_logger = logger

        run_result = run_tool_request(
            request,
            registry=registry,
            user_confirmed=user_confirmed,
            logger=logger,
        )

        self.last_word_reader_tool_run_result = run_result
        self.last_word_reader_tool_result = run_result.result
        self.last_tool_execution_record = run_result.execution_record

        original_input = (candidate.get("input_data") or {}).get("original_input", "")

        return self.build_word_reader_tool_response(run_result.result, original_input=original_input)

    def execute_web_reader_tool_request_candidate(self, candidate):
        """Web Readerの実行候補をToolRunnerへ渡し、結果を会話返答にします。"""
        request = self.build_tool_request_from_candidate(candidate)
        user_confirmed = bool(candidate.get("user_confirmed"))
        registry = getattr(self, "tool_registry", None)

        if registry is None:
            registry = self.build_tool_registry(getattr(self, "web_reader_fetcher", None))
            self.tool_registry = registry

        logger = getattr(self, "tool_execution_logger", None)

        if logger is None:
            logger = ToolExecutionLogger()
            self.tool_execution_logger = logger

        run_result = run_tool_request(
            request,
            registry=registry,
            user_confirmed=user_confirmed,
            logger=logger,
        )

        self.last_web_reader_tool_run_result = run_result
        self.last_web_reader_tool_result = run_result.result
        self.last_tool_execution_record = run_result.execution_record

        original_input = (candidate.get("input_data") or {}).get("original_input", "")

        return self.build_web_reader_tool_response(run_result.result, original_input=original_input)

    def build_tool_request_from_candidate(self, candidate):
        """dict形式の候補から、既存のToolRequestへ変換します。"""
        input_data = dict(candidate.get("input_data") or {})

        return ToolRequest(
            tool_name=candidate.get("tool_name", "web_reader"),
            action=candidate.get("action", "read_url"),
            input_data=input_data,
            requires_permission=bool(candidate.get("requires_permission", True)),
            risk_level=candidate.get("risk_level", "medium"),
        )

    def build_web_reader_tool_response(self, result, original_input=""):
        """ToolResultを、ユーザーに見せる短い返答へ変換します。

        Ver2.31では、読み取り依頼に要約・質問などの目的が含まれていた場合、
        読み取った本文をもとにQwenで直接答えるようにします。
        """
        if not getattr(result, "executed", False):
            self.last_memory_candidate = None
            self.pending_memory_candidate_confirmation = None
            self.pending_memory_candidate_edit = None
            reason = getattr(result, "message", "") or getattr(result, "error", "")
            return (
                "Web Readerは実行されませんでした。\n\n"
                "理由:\n"
                f"{reason or 'ユーザー確認がないため、外部Webアクセスを行いませんでした。'}"
            )

        if not getattr(result, "success", False):
            self.last_memory_candidate = None
            self.pending_memory_candidate_confirmation = None
            self.pending_memory_candidate_edit = None
            reason = getattr(result, "error", None) or getattr(result, "message", "")
            return (
                "Web Readerで読み取りを試みましたが、失敗しました。\n\n"
                "理由:\n"
                f"{reason or '原因は特定できませんでした。'}\n\n"
                "次にできること:\n"
                "- URLが正しいか確認する\n"
                "- ログや別のURLを試す"
            )

        data = getattr(result, "data", {}) or {}
        title = _clean_web_reader_display_text(data.get("title")) or "(タイトルなし)"
        final_url = _clean_web_reader_display_text(data.get("final_url") or data.get("url"))
        full_text = data.get("text") or data.get("text_preview") or ""
        self.remember_last_read_document(
            source_tool="web_reader",
            title=title,
            location=final_url,
            text=full_text,
        )
        memory_candidate = build_memory_candidate_from_reader_result(
            result,
            source_tool="web_reader",
        )
        self.last_memory_candidate = memory_candidate
        self.pending_memory_candidate_confirmation = dict(memory_candidate)
        self.pending_memory_candidate_edit = None
        memory_candidate_text = self.format_memory_candidate_dry_run(memory_candidate)

        task_response = self.build_document_task_response_if_requested(
            original_input,
            full_text,
            title,
        )

        if task_response is not None:
            return (
                "Web Readerで読み取りました。\n\n"
                f"{task_response}\n\n"
                f"{memory_candidate_text}"
            )

        text_preview = data.get("text_preview") or full_text
        formatted_preview = _format_web_reader_preview(text_preview, title=title)

        return (
            "Web Readerで読み取りました。\n\n"
            "タイトル:\n"
            f"{title}\n\n"
            "URL:\n"
            f"{final_url or '(URLなし)'}\n\n"
            "本文プレビュー:\n"
            f"{formatted_preview}\n\n"
            f"{memory_candidate_text}"
        )

    def build_file_reader_tool_response(self, result, original_input=""):
        """File ReaderのToolResultを、ユーザーに見せる短い返答へ変換します。

        Ver2.29ではMemory Candidateへの接続はまだ行いません。
        Ver2.31では、読み取り依頼に要約・質問などの目的が含まれていた場合、
        読み取った本文をもとにQwenで直接答えるようにします。
        """
        if not getattr(result, "executed", False):
            reason = getattr(result, "message", "") or getattr(result, "error", "")
            return (
                "File Readerは実行されませんでした。\n\n"
                "理由:\n"
                f"{reason or 'ユーザー確認がないため、ローカルファイルへアクセスしませんでした。'}"
            )

        if not getattr(result, "success", False):
            reason = getattr(result, "error", None) or getattr(result, "message", "")
            return (
                "File Readerで読み取りを試みましたが、失敗しました。\n\n"
                "理由:\n"
                f"{reason or '原因は特定できませんでした。'}\n\n"
                "次にできること:\n"
                "- ファイルパスが正しいか確認する\n"
                "- 対応拡張子（txt / md）のファイルか確認する"
            )

        data = getattr(result, "data", {}) or {}
        file_name = _clean_web_reader_display_text(data.get("file_name")) or "(ファイル名なし)"
        resolved_path = _clean_web_reader_display_text(data.get("resolved_path") or data.get("path"))
        full_text = data.get("text") or data.get("text_preview") or ""
        self.remember_last_read_document(
            source_tool="file_reader",
            title=file_name,
            location=resolved_path,
            text=full_text,
        )

        task_response = self.build_document_task_response_if_requested(
            original_input,
            full_text,
            file_name,
        )

        if task_response is not None:
            return f"File Readerで読み取りました。\n\n{task_response}"

        text_preview = data.get("text_preview") or full_text
        formatted_preview = _format_web_reader_preview(text_preview, title=file_name)

        return (
            "File Readerで読み取りました。\n\n"
            "ファイル名:\n"
            f"{file_name}\n\n"
            "パス:\n"
            f"{resolved_path or '(パスなし)'}\n\n"
            "本文プレビュー:\n"
            f"{formatted_preview}"
        )

    def build_pdf_reader_tool_response(self, result, original_input=""):
        """PDF ReaderのToolResultを、ユーザーに見せる短い返答へ変換します。

        Web Reader / File Readerと同じく、要約・質問などの目的が含まれていた場合は
        読み取った本文をもとにQwenで直接答えます。Memory Candidateへの接続はまだ行いません。
        """
        if not getattr(result, "executed", False):
            reason = getattr(result, "message", "") or getattr(result, "error", "")
            return (
                "PDF Readerは実行されませんでした。\n\n"
                "理由:\n"
                f"{reason or 'ユーザー確認がないため、ローカルファイルへアクセスしませんでした。'}"
            )

        if not getattr(result, "success", False):
            reason = getattr(result, "error", None) or getattr(result, "message", "")
            return (
                "PDF Readerで読み取りを試みましたが、失敗しました。\n\n"
                "理由:\n"
                f"{reason or '原因は特定できませんでした。'}\n\n"
                "次にできること:\n"
                "- ファイルパスが正しいか確認する\n"
                "- 画像だけのスキャンPDFでないか確認する"
            )

        data = getattr(result, "data", {}) or {}
        file_name = _clean_web_reader_display_text(data.get("file_name")) or "(ファイル名なし)"
        resolved_path = _clean_web_reader_display_text(data.get("resolved_path") or data.get("path"))
        full_text = data.get("text") or data.get("text_preview") or ""
        self.remember_last_read_document(
            source_tool="pdf_reader",
            title=file_name,
            location=resolved_path,
            text=full_text,
        )

        task_response = self.build_document_task_response_if_requested(
            original_input,
            full_text,
            file_name,
        )

        if task_response is not None:
            return f"PDF Readerで読み取りました。\n\n{task_response}"

        text_preview = data.get("text_preview") or full_text
        formatted_preview = _format_web_reader_preview(text_preview, title=file_name)

        return (
            "PDF Readerで読み取りました。\n\n"
            "ファイル名:\n"
            f"{file_name}\n\n"
            "パス:\n"
            f"{resolved_path or '(パスなし)'}\n\n"
            "本文プレビュー:\n"
            f"{formatted_preview}"
        )

    def build_word_reader_tool_response(self, result, original_input=""):
        """Word ReaderのToolResultを、ユーザーに見せる短い返答へ変換します。

        Web Reader / File Reader / PDF Readerと同じく、要約・質問などの目的が含まれていた場合は
        読み取った本文をもとにQwenで直接答えます。Memory Candidateへの接続はまだ行いません。
        """
        if not getattr(result, "executed", False):
            reason = getattr(result, "message", "") or getattr(result, "error", "")
            return (
                "Word Readerは実行されませんでした。\n\n"
                "理由:\n"
                f"{reason or 'ユーザー確認がないため、ローカルファイルへアクセスしませんでした。'}"
            )

        if not getattr(result, "success", False):
            reason = getattr(result, "error", None) or getattr(result, "message", "")
            return (
                "Word Readerで読み取りを試みましたが、失敗しました。\n\n"
                "理由:\n"
                f"{reason or '原因は特定できませんでした。'}\n\n"
                "次にできること:\n"
                "- ファイルパスが正しいか確認する\n"
                "- .docx形式（古い.docではない）か確認する"
            )

        data = getattr(result, "data", {}) or {}
        file_name = _clean_web_reader_display_text(data.get("file_name")) or "(ファイル名なし)"
        resolved_path = _clean_web_reader_display_text(data.get("resolved_path") or data.get("path"))
        full_text = data.get("text") or data.get("text_preview") or ""
        self.remember_last_read_document(
            source_tool="word_reader",
            title=file_name,
            location=resolved_path,
            text=full_text,
        )

        task_response = self.build_document_task_response_if_requested(
            original_input,
            full_text,
            file_name,
        )

        if task_response is not None:
            return f"Word Readerで読み取りました。\n\n{task_response}"

        text_preview = data.get("text_preview") or full_text
        formatted_preview = _format_web_reader_preview(text_preview, title=file_name)

        return (
            "Word Readerで読み取りました。\n\n"
            "ファイル名:\n"
            f"{file_name}\n\n"
            "パス:\n"
            f"{resolved_path or '(パスなし)'}\n\n"
            "本文プレビュー:\n"
            f"{formatted_preview}"
        )

    def format_memory_candidate_dry_run(self, candidate):
        """Memory Candidateを、保存しないdry-run情報として短く表示します。"""
        if not candidate:
            return (
                "Memory Candidate dry-run:\n"
                "保存候補は作成されませんでした。"
            )

        reasons = candidate.get("reasons") or []
        reason_lines = [f"- {reason}" for reason in reasons[:3]]

        if len(reasons) > 3:
            reason_lines.append("- ほかの理由は省略しました。")

        return (
            "Memory Candidate dry-run:\n"
            f"保存候補タイプ: {candidate.get('candidate_type', 'unknown')}\n"
            f"重要度: {candidate.get('importance', 'unknown')}\n"
            f"リスク: {candidate.get('risk_level', 'unknown')}\n"
            f"保存実行: {self.format_boolean_label(candidate.get('should_save'), true_label='する', false_label='しない')}\n"
            f"確認必要: {self.format_boolean_label(candidate.get('requires_user_confirmation'))}\n"
            "理由:\n"
            f"{chr(10).join(reason_lines) if reason_lines else '- 理由なし'}"
        )

    def format_edited_memory_candidate_dry_run(self, result):
        """編集済みMemory Candidateを、保存しないdry-run情報として表示します。"""
        edited_candidate = result.get("edited_candidate") or {}
        edited_summary = result.get("edited_summary") or edited_candidate.get("summary") or ""

        return (
            "編集済みMemory Candidate dry-run:\n"
            f"保存候補タイプ: {edited_candidate.get('candidate_type', 'unknown')}\n"
            f"重要度: {edited_candidate.get('importance', 'unknown')}\n"
            f"リスク: {edited_candidate.get('risk_level', 'unknown')}\n"
            "編集後要約:\n"
            f"{edited_summary or '(編集後要約なし)'}\n"
            f"保存実行: {self.format_boolean_label(edited_candidate.get('should_save'), true_label='する', false_label='しない')}\n"
            f"確認必要: {self.format_boolean_label(edited_candidate.get('requires_user_confirmation'))}"
        )

    def format_boolean_label(self, value, true_label="はい", false_label="いいえ"):
        """True/Falseを、ユーザーに見せやすい日本語へ変換します。"""
        return true_label if bool(value) else false_label

    def remember_last_read_document(self, source_tool, title, location, text):
        """Web Reader / File Readerで読み取った本文を、後続の会話で使えるように保持します。"""
        cleaned_text = _clean_web_reader_display_text(text)

        if not cleaned_text:
            return

        self.last_read_document = {
            "source_tool": source_tool,
            "title": title,
            "location": location,
            "text": cleaned_text,
        }

    def build_last_read_document_context(self):
        """直近に読み取ったReader結果を、LLMが参照できるsystem messageにします。

        フォローアップの質問や要約依頼に、本文プレビューだけでなく
        読み取った本文（上限あり）をもとに答えられるようにします。
        """
        document = getattr(self, "last_read_document", None)

        if not document:
            return None

        text = str(document.get("text") or "")[:LAST_READ_DOCUMENT_CONTEXT_MAX_CHARS]

        if not text:
            return None

        source_label = READER_SOURCE_LABELS.get(document.get("source_tool"), "File Reader")
        title = document.get("title") or "(タイトルなし)"
        location = document.get("location") or "(場所不明)"

        return (
            f"直近{source_label}で読み取った資料が1件だけあります。\n"
            "これより前に読み取った別のファイルの内容は、この会話ではもう保持していません。\n"
            f"タイトル/ファイル名: {title}\n"
            f"場所: {location}\n"
            "本文（長い場合は途中までです）:\n"
            f"{text}\n\n"
            "この資料について聞かれた場合は、この本文をもとに答えてください。"
            "本文に書かれていないことは推測せず、書かれていないと伝えてください。\n"
            "ここに書かれている資料とは別のファイルについて聞かれた場合は、"
            "その資料の内容はもう保持していないため分からないと正直に伝えてください。"
            "この資料に書かれていないからといって、別のファイルにも書かれていないと断定しないでください。"
        )

    def build_document_task_messages(self, original_input, document_text, title):
        """読み取った本文をもとに、ユーザーの依頼へ直接答えるためのmessagesを作ります。"""
        return [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "system",
                "content": (
                    "直前に読み取った資料をもとに、ユーザーの依頼に答えてください。\n"
                    f"タイトル/ファイル名: {title}\n"
                    "本文:\n"
                    f"{document_text}\n\n"
                    "資料に書かれていないことは推測せず、書かれていないと正直に伝えてください。"
                ),
            },
            {
                "role": "user",
                "content": original_input,
            },
        ]

    def build_document_task_response_if_requested(self, original_input, document_text, title):
        """読み取り依頼に要約・質問などの目的が含まれる場合、Qwenで直接答えます。

        目的が読み取りだけの場合はNoneを返し、呼び出し側は従来のプレビュー表示にします。
        """
        original_input = str(original_input or "").strip()

        if not original_input or not document_text:
            return None

        task_type = self.input_analyzer.analyze(original_input).get("task_type")

        if task_type not in DOCUMENT_TASK_TYPES:
            return None

        ask_llm_func = getattr(self, "ask_llm_func", None) or ask_llm
        messages = self.build_document_task_messages(original_input, document_text, title)

        return ask_llm_func(messages)

    def build_messages(
        self,
        memory_usage=None,
        conversation_quality_guidance=None,
        conversation_mode=None,
    ):
        """長期記憶と会話履歴を使って、LLMに渡すmessagesを作ります。"""
        if memory_usage is None:
            memory_usage = self.last_memory_usage or "normal"

        if conversation_quality_guidance is None:
            conversation_quality_guidance = self.last_conversation_quality_guidance

        if conversation_mode is None:
            conversation_mode = self.last_conversation_mode or "unknown"

        memories = get_memories()
        memory_context = build_memory_context(memories, memory_usage=memory_usage)
        # 通常会話や開発相談では、古いPreference混入を避けるため現在入力中心にします。
        recent_limit = self.get_recent_message_limit(memory_usage, conversation_mode)
        recent_messages = get_recent_messages(recent_limit)

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "system",
                "content": memory_context,
            },
        ]

        last_read_document_context = self.build_last_read_document_context()

        if last_read_document_context:
            messages.append(
                {
                    "role": "system",
                    "content": last_read_document_context,
                }
            )

        for message in recent_messages:
            messages.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        runtime_instruction = self.build_memory_usage_runtime_instruction(memory_usage)

        if runtime_instruction:
            messages.append(
                {
                    "role": "system",
                    "content": runtime_instruction,
                }
            )

        if conversation_quality_guidance:
            messages.append(
                {
                    "role": "system",
                    "content": conversation_quality_guidance,
                }
            )

        return messages

    def get_recent_message_limit(self, memory_usage, conversation_mode):
        """会話モードに応じて、LLMへ渡す直近履歴の量を調整します。"""
        if memory_usage == "detailed":
            return 20

        if conversation_mode in ("casual", "development"):
            return 1

        if conversation_mode == "advice":
            return 4

        return 8

    def build_memory_usage_runtime_instruction(self, memory_usage):
        """今回の入力に対するMemory利用の強さを、最後にもう一度伝えます。"""
        if memory_usage == "minimal":
            return (
                "今回の入力は通常会話です。会話履歴や長期記憶に好きな食べ物などの"
                "Preference情報があっても、直接関係がなければ話題に出さないでください。"
                "挨拶、応援、雑談として自然に短く返してください。"
            )

        if memory_usage == "detailed":
            return (
                "今回の入力は明示的な記憶参照です。保存済みMemoryを分かる範囲で整理して答え、"
                "記憶にないことは作らないでください。"
            )

        return (
            "今回の入力では、関連が強いMemoryだけを使ってください。"
            "関係の薄いPreference情報は無理に出さないでください。"
        )
