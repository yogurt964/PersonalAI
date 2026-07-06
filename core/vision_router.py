"""画像読み取りに使うvisionバックエンドを選ぶ、最小のVision Routerです。

PersonalAIは、Qwen・OpenAI・Visionなどの機能を単独の特殊ロジックではなく、
「道具」として使い分ける設計を目指しています（ユーザーとの合意事項）。
Image Reader専用の判断ロジックをアダプタ内に埋め込まず、ここに集約することで、
将来ModelRouter/ToolRouterへ拡張する際の土台にします。

Ver2.54でOpenAI visionへの接続口を追加しました。ただし現時点では、ユーザーが
明示的にOpenAIでの解析を求めた場合のみ選びます（画像の難易度を自動判定して
勝手にエスカレーションすることはしません。外部への画像送信と課金を伴うため、
ユーザーの明示的な意図がある場合に限定しています）。
"""

VISION_BACKEND_LOCAL = "local"
VISION_BACKEND_OPENAI = "openai"

# ユーザーが明示的にOpenAIでの解析を求めていると判断する表現。
# 画像の難易度自動判定は行わず、ここに一致した場合だけOpenAIへエスカレーションします。
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
    """画像読み取りに使うvisionバックエンドを選びます。

    デフォルトは常にローカルです。ユーザーが明示的にOpenAIでの解析を求めた
    場合のみOpenAIを選びます。画像の難易度・安全性を自動判定してのエスカレーションは
    まだ実装していません（将来の拡張候補）。
    """
    text = str(user_request_text or "")

    if any(phrase in text for phrase in OPENAI_ESCALATION_PHRASES):
        return VISION_BACKEND_OPENAI

    return VISION_BACKEND_LOCAL
