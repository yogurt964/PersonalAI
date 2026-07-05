"""画像読み取りに使うvisionバックエンドを選ぶ、最小のVision Routerです。

PersonalAIは、Qwen・OpenAI・Visionなどの機能を単独の特殊ロジックではなく、
「道具」として使い分ける設計を目指しています（ユーザーとの合意事項）。
Image Reader専用の判断ロジックをアダプタ内に埋め込まず、ここに集約することで、
将来ModelRouter/ToolRouterへ拡張する際の土台にします。

現時点ではローカルvisionモデルのみ実装されているため、常にlocalを返します。
OpenAI visionの接続にはAPIキー設定と外部への画像送信が伴うため、
実際に着手する際はユーザーへ改めて確認します（それまでOPENAIブランチは未実装のままです）。
"""

VISION_BACKEND_LOCAL = "local"
VISION_BACKEND_OPENAI = "openai"


def choose_vision_backend(image_path=None, user_request_text=""):
    """画像読み取りに使うvisionバックエンドを選びます。

    将来的には、難易度（複雑な図表・手書き・OCRなど）や安全性（個人情報を
    含む可能性が高い画像かどうか）を踏まえてlocal/openaiを使い分ける予定です。
    OpenAI visionが未接続の現時点では、常にVISION_BACKEND_LOCALを返します。
    """
    return VISION_BACKEND_LOCAL
