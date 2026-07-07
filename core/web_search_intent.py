"""ユーザーの質問が「Web検索が必要そうか」を判定する、最小の仕組みです。

Qwen（ローカルモデル）は学習時点までの知識しか持たず、OpenAIの通常モデルも同様に
静的な知識しか持ちません。最新情報・時事的な質問は、低信頼を検知してから
遡ってエスカレーションするのではなく、質問の時点で「検索が要る」と判定し、
最初からOpenAIの検索機能つきモデルへ直接渡します（confidence_check.pyの
低信頼判定とは別の、独立した判定です）。
"""

# 現在・最新情報が必要だと判断する表現。
CURRENT_INFO_MARKERS = [
    "最新",
    "今日の",
    "今日は",
    "現在の",
    "今の",
    "今何時",
    "今何日",
    "リアルタイム",
    "速報",
    "ニュース",
    "天気",
    "為替",
    "株価",
]

# ユーザーが明示的に検索を求めていると判断する表現。
EXPLICIT_SEARCH_PHRASES = [
    "検索して",
    "調べて",
    "ググって",
    "Web検索して",
    "web検索して",
    "ネットで調べて",
    "インターネットで調べて",
]

# Ver2.63: 実機テストで、商品・価格・在庫・比較のような「答えの時点で現在情報が
# 必要な相談」がこの判定に一切引っかからず、Qwenが実在しない価格・商品・リンクを
# 断定してしまう問題が見つかった。これらもWeb検索が必要な質問として扱う。
PRODUCT_AND_PRICING_MARKERS = [
    "実際の商品",
    "具体的な商品",
    "おすすめ商品",
    "お勧め商品",
    "価格",
    "値段",
    "予算",
    "在庫",
    "リンク",
    "BTO",
    "bto",
    "今買うなら",
    "比較",
    "ランキング",
    "セール",
]


def needs_web_search(user_text):
    """この質問がWeb検索を必要としそうかを判定します。

    キーワード一致による簡易判定です。誤検知・見逃しはあり得るため、
    将来的にはconfirmation_intentと同様のハイブリッド判定への拡張も検討します。
    """
    text = str(user_text or "")

    if any(phrase in text for phrase in EXPLICIT_SEARCH_PHRASES):
        return True

    if any(marker in text for marker in PRODUCT_AND_PRICING_MARKERS):
        return True

    return any(marker in text for marker in CURRENT_INFO_MARKERS)
