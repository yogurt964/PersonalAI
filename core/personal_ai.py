from ai.llm import SYSTEM_PROMPT
from ai.memory_context import build_memory_context
from ai.memory_extract import extract_memories
from ai.preference_confirmation import (
    analyze_preference_confirmation,
    resolve_preference_confirmation_answer,
    save_resolved_preference_confirmation,
)
from ai.preference_memory import save_preference_memories
from core.capability_manager import CapabilityManager
from core.executor import Executor
from core.input_analyzer import InputAnalyzer
from core.permission_manager import PermissionManager
from core.planner import Planner
from core.router import Router
from database.chat_history import get_recent_messages, save_message
from database.memory_manager import get_memories, save_memory
from database.models import create_database


class PersonalAI:
    """PersonalAI本体の会話処理をまとめるクラスです。"""

    def __init__(self):
        # 起動時にデータベースとテーブルを用意します。
        create_database()

        # PersonalAIが使える能力、行動計画、道具選択を担当する部品です。
        self.input_analyzer = InputAnalyzer()
        self.capability_manager = CapabilityManager()
        self.planner = Planner()
        self.router = Router()
        self.permission_manager = PermissionManager()
        self.executor = Executor()

        # 直近の判断結果を保存しておく場所です。将来のデバッグやExecutor連携で使えます。
        self.last_input_analysis = None
        self.last_capability_analysis = None
        self.last_capabilities = None
        self.last_plan = None
        self.last_route = None
        self.last_permission_decision = None
        self.last_preference_confirmation = None
        self.pending_preference_confirmation = None
        self.last_response = None

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

        # 入力内容を構造化して、将来のPlannerやRouterが使いやすい形にします。
        # 現時点ではWebやYouTubeを実際に読みに行く処理は行いません。
        input_analysis = self.input_analyzer.analyze(user_input)
        self.last_input_analysis = input_analysis

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

        messages = self.build_messages()
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

    def build_messages(self):
        """長期記憶と会話履歴を使って、LLMに渡すmessagesを作ります。"""
        memories = get_memories()
        memory_context = build_memory_context(memories)
        recent_messages = get_recent_messages(20)

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

        for message in recent_messages:
            messages.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        return messages
