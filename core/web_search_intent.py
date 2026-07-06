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


def needs_web_search(user_text):
    """この質問がWeb検索を必要としそうかを判定します。

    キーワード一致による簡易判定です。誤検知・見逃しはあり得るため、
    将来的にはconfirmation_intentと同様のハイブリッド判定への拡張も検討します。
    """
    text = str(user_text or "")

    if any(phrase in text for phrase in EXPLICIT_SEARCH_PHRASES):
        return True

    return any(marker in text for marker in CURRENT_INFO_MARKERS)
