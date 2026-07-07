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


def needs_web_search(user_text, ask_llm_func=None):
    """この質問がWeb検索を必要としそうかを判定します。

    まずキーワード一致で判定します（今まで通り、コスト0・瞬時）。
    Ver2.68: どのキーワードにも一致しない場合のみ、ask_llm_funcが渡されていれば
    Qwenに1語（yes/no）で判定させるハイブリッド判定を追加で試します
    （confirmation_intent.pyと同じ考え方）。ask_llm_funcを渡さない場合や、
    LLMの応答が不明瞭・呼び出し失敗の場合は、安全側に倒してFalse（検索不要）を返します。
    """
    text = str(user_text or "")

    if any(phrase in text for phrase in EXPLICIT_SEARCH_PHRASES):
        return True

    if any(marker in text for marker in PRODUCT_AND_PRICING_MARKERS):
        return True

    if any(marker in text for marker in CURRENT_INFO_MARKERS):
        return True

    return _needs_web_search_via_llm(text, ask_llm_func)


def _needs_web_search_via_llm(text, ask_llm_func):
    """固定キーワードで判定できない発言だけを、Qwenにyes/noの1語で答えさせます。

    ask_llm_funcが渡されない場合（デフォルト）は、暗黙にQwenを呼び出さずFalseを返します。
    既存のtest doubleやcheckはask_llm_funcを渡さないため、この変更の影響を受けません。
    """
    if ask_llm_func is None or not text:
        return False

    prompt = (
        "次のユーザーの発言について、最新情報・実在する商品や価格・在庫など、"
        "検索エンジンで現在の情報を確認しないと正確に答えられない可能性が高いかを判定してください。\n"
        "必要なら yes、不要なら no、必ずこの2つの単語のうち1つだけで答えてください。\n\n"
        f"発言: {text}"
    )

    try:
        response = ask_llm_func([{"role": "user", "content": prompt}])
    except Exception:
        return False

    normalized = str(response or "").strip().lower()
    has_yes = "yes" in normalized
    has_no = "no" in normalized

    return has_yes and not has_no
