"""ユーザーの質問が「Web検索が必要そうか」を判定する、最小の仕組みです。

Qwen（ローカルモデル）は学習時点までの知識しか持たず、OpenAIの通常モデルも同様に
静的な知識しか持ちません。最新情報・時事的な質問は、低信頼を検知してから
遡ってエスカレーションするのではなく、質問の時点で「検索が要る」と判定し、
最初からOpenAIの検索機能つきモデルへ直接渡します（confidence_check.pyの
低信頼判定とは別の、独立した判定です）。
"""

import re

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


def needs_web_search(user_text, ask_llm_func=None, openai_client_factory=None):
    """この質問がWeb検索を必要としそうかを判定します。

    まずキーワード一致で判定します（今まで通り、コスト0・瞬時）。
    Ver2.68/2.71: どのキーワードにも一致しない場合のみ、4段階のフォールバックで
    追加判定を試します（Qwenの自己申告確信度には一切頼らない設計、
    docs/llm_intent_resolver_design.md参照）。
    1. ask_llm_funcが渡されていればQwenにyes/noの1語で判定させる
    2. Qwenの応答がyes/noのどちらでもない（不明瞭・呼び出し失敗）場合、
       OpenAIに同じ判定を依頼する
    3. OpenAIの応答も不明瞭なら、安全側に倒してFalse（検索不要）を返す
    ask_llm_funcを渡さない場合（デフォルト、既存のtest double含む）は、この
    フォールバック自体を行わず、Qwen・OpenAIのどちらも呼び出しません。
    """
    text = str(user_text or "")

    if any(phrase in text for phrase in EXPLICIT_SEARCH_PHRASES):
        return True

    if any(marker in text for marker in PRODUCT_AND_PRICING_MARKERS):
        return True

    if any(marker in text for marker in CURRENT_INFO_MARKERS):
        return True

    if ask_llm_func is None or not text:
        return False

    qwen_verdict = _ask_llm_needs_web_search(text, ask_llm_func)

    if qwen_verdict is not None:
        return qwen_verdict

    openai_verdict = _ask_openai_needs_web_search(text, openai_client_factory)

    return bool(openai_verdict)


_WEB_SEARCH_JUDGEMENT_PROMPT_TEMPLATE = (
    "次のユーザーの発言について、最新情報・実在する商品や価格・在庫など、"
    "検索エンジンで現在の情報を確認しないと正確に答えられない可能性が高いかを判定してください。\n"
    "必要なら yes、不要なら no、必ずこの2つの単語のうち1つだけで答えてください。\n\n"
    "発言: {text}"
)


def _parse_yes_no(response):
    """応答からyes/noを単語境界つきで判定します。

    単純な部分文字列一致（"no" in text）は、"not"や"know"のような無関係な単語にも
    誤って一致してしまうため、単語単位（記号除去後の完全一致）で判定します。
    """
    normalized = str(response or "").strip().lower()
    tokens = re.findall(r"[a-z]+", normalized)

    has_yes = "yes" in tokens
    has_no = "no" in tokens

    if has_yes and not has_no:
        return True

    if has_no and not has_yes:
        return False

    return None


def _ask_llm_needs_web_search(text, ask_llm_func):
    """固定キーワードで判定できない発言だけを、Qwenにyes/noの1語で答えさせます。

    応答がyes/noのどちらか一方に明確に一致しない場合（不明瞭・呼び出し失敗）はNoneを
    返し、呼び出し元でOpenAIへのフォールバックを判断できるようにします。
    """
    prompt = _WEB_SEARCH_JUDGEMENT_PROMPT_TEMPLATE.format(text=text)

    try:
        response = ask_llm_func([{"role": "user", "content": prompt}])
    except Exception:
        return None

    return _parse_yes_no(response)


def _ask_openai_needs_web_search(text, openai_client_factory):
    """Qwenでは判定できなかった発言について、OpenAIに同じ判定を依頼します（Ver2.71）。

    予算超過・キー未設定などでOpenAIが使えない場合は、安全側に倒してNoneを返します
    （呼び出し元がFalse＝検索不要にフォールバックします）。
    """
    from ai.openai_client import ask_openai_text

    prompt = _WEB_SEARCH_JUDGEMENT_PROMPT_TEMPLATE.format(text=text)

    try:
        response = ask_openai_text(
            [{"role": "user", "content": prompt}],
            feature="web_search_need_classification_fallback",
            client_factory=openai_client_factory,
        )
    except Exception:
        return None

    return _parse_yes_no(response)
