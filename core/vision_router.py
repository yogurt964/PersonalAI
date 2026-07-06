"""画像読み取りに使うvisionバックエンドを選ぶ、最小のVision Routerです。

PersonalAIは、Qwen・OpenAI・Visionなどの機能を単独の特殊ロジックではなく、
「道具」として使い分ける設計を目指しています（ユーザーとの合意事項）。
Image Reader専用の判断ロジックをアダプタ内に埋め込まず、ここに集約することで、
将来ModelRouter/ToolRouterへ拡張する際の土台にします。

Ver2.54でOpenAI visionへの接続口を追加しました。
Ver2.55で、ユーザーから「明示的に求めなくても、必要なタイミングをPersonalAIが判断して
OpenAIを呼び出してよい」との合意を得たため、ローカルモデルの解析結果が低信頼そうな場合に
自動でOpenAIへエスカレーションする判定を追加しました（判定ロジックはcore/confidence_check.pyを
テキスト応答の自動エスカレーションと共有しています）。
月間予算ガード（ai/openai_client.py）は自動エスカレーション時も必ずかかるため、
上限に達している場合はエスカレーションされず、ローカルの結果がそのまま使われます。
"""

from core.confidence_check import seems_low_confidence

VISION_BACKEND_LOCAL = "local"
VISION_BACKEND_OPENAI = "openai"

# ユーザーが明示的にOpenAIでの解析を求めていると判断する表現。
# これが一致した場合は、ローカルを試さず直接OpenAIを使います（ユーザーの明示的な指定を優先）。
OPENAI_ESCALATION_PHRASES = [
    "OpenAIで解析して",
    "openaiで解析して",
    "OpenAIで見て",
    "openaiで見て",
    "OpenAIで読んで",
    "もっと正確に解析して",
    "もっと詳しく解析して",
    "高精度で解析して",
]


def choose_vision_backend(image_path=None, user_request_text=""):
    """最初にどちらのバックエンドを試すかを選びます。

    デフォルトは常にローカルです。ユーザーが明示的にOpenAIでの解析を求めた
    場合のみ、最初からOpenAIを選びます。
    """
    text = str(user_request_text or "")

    if any(phrase in text for phrase in OPENAI_ESCALATION_PHRASES):
        return VISION_BACKEND_OPENAI

    return VISION_BACKEND_LOCAL


def should_escalate_after_local_result(local_result_text):
    """ローカルでの解析結果を見て、OpenAIへの自動エスカレーションを試す価値があるか判定します。

    ユーザーの明示的な指定がない通常の読み取りでも、ローカルモデルが
    「わからない」「判断できません」のように低信頼な答えを返した場合は、
    PersonalAIの判断で自動的にOpenAIへ再解析を試みます。
    月間予算ガード自体はai/openai_client.py側で別途かかるため、ここでは
    「試す価値があるかどうか」だけを判定します。
    """
    return seems_low_confidence(local_result_text)
