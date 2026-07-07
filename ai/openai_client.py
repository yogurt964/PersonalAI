import base64
import os

from database.openai_usage import get_monthly_openai_usage_total, record_openai_usage


DEFAULT_MONTHLY_CAP_USD = 5.0
DEFAULT_VISION_MODEL = "gpt-4o-mini"
DEFAULT_TEXT_MODEL = "gpt-4o-mini"

# Tier3（最上位モデル）用。Ver2.58でテキスト、Ver2.59でvisionの実APIによる
# 存在・動作（max_completion_tokensフォールバック含む）を確認済み。
DEFAULT_POWERFUL_VISION_MODEL = "gpt-5.5"
DEFAULT_POWERFUL_TEXT_MODEL = "gpt-5.5"

# gpt-4o-miniでの1回あたりの想定コスト（安全側に倒した概算値）。
# 実際の請求額はこれ以下になる想定です。正確な値はOpenAIのpricingページを参照してください。
ESTIMATED_COST_PER_VISION_CALL_USD = 0.01
ESTIMATED_COST_PER_TEXT_CALL_USD = 0.005

# Tier3（より高性能・高コストなモデル）での1回あたりの想定コスト（安全側に倒した概算値）。
# gpt-5.5はgpt-4oより高価な想定のため、引き続き安全側の概算値のまま運用する。
ESTIMATED_COST_PER_POWERFUL_VISION_CALL_USD = 0.03
ESTIMATED_COST_PER_POWERFUL_TEXT_CALL_USD = 0.02

# Web検索機能つきモデル用。Ver2.58で実APIにより動作確認済み（tool_choice強制が必須）。
DEFAULT_WEB_SEARCH_MODEL = "gpt-4o-mini"
ESTIMATED_COST_PER_WEB_SEARCH_CALL_USD = 0.015


class OpenAIKeyMissingError(Exception):
    """OPENAI_API_KEY環境変数が設定されていない場合の例外です。"""


class OpenAIBudgetExceededError(Exception):
    """今月の想定利用額が上限に達している場合の例外です。"""


def get_api_key():
    """環境変数からAPIキーを読み取ります。

    キーの値自体はログに出力せず、保存もしません。
    """
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise OpenAIKeyMissingError(
            "OPENAI_API_KEY環境変数が設定されていません。"
            "設定後は新しいターミナルを開き直す必要があります。"
        )

    return api_key


def ensure_budget_available(monthly_cap_usd=DEFAULT_MONTHLY_CAP_USD, usage_total_func=None):
    """今月の想定利用額が上限未満かを確認します。

    上限に達している場合は例外を送出し、呼び出し自体を行わせません
    （予算超過での実行を防ぐためのガードです）。
    """
    usage_total_func = usage_total_func or get_monthly_openai_usage_total
    current_usage = usage_total_func()

    if current_usage >= monthly_cap_usd:
        raise OpenAIBudgetExceededError(
            f"今月の想定利用額（${current_usage:.2f}）が上限（${monthly_cap_usd:.2f}）に達しているため、"
            "OpenAI呼び出しをブロックしました。上限を上げる場合はユーザーに確認してください。"
        )


def describe_image_with_openai(
    image_path,
    prompt,
    monthly_cap_usd=DEFAULT_MONTHLY_CAP_USD,
    model=DEFAULT_VISION_MODEL,
    feature="image_reader_vision",
    estimated_cost_usd=ESTIMATED_COST_PER_VISION_CALL_USD,
    client_factory=None,
    usage_total_func=None,
    usage_recorder=None,
):
    """OpenAI visionモデルで画像を解析します。

    呼び出し前に必ず月間上限をチェックし、上限に達している場合は例外を送出して
    実際の呼び出し自体を行いません。成功した場合のみ、想定利用額を記録します。
    Tier3（より高性能なモデル）から呼ぶ場合は、model/feature/estimated_cost_usdを
    差し替えて使います。
    """
    ensure_budget_available(monthly_cap_usd, usage_total_func)

    api_key = get_api_key()

    if client_factory is not None:
        response_text = client_factory(api_key, image_path, prompt, model)
    else:
        response_text = _call_real_openai_vision(api_key, image_path, prompt, model)

    recorder = usage_recorder or record_openai_usage
    recorder(
        feature=feature,
        model=model,
        estimated_cost_usd=estimated_cost_usd,
    )

    return response_text


def ask_openai_text(
    messages,
    monthly_cap_usd=DEFAULT_MONTHLY_CAP_USD,
    model=DEFAULT_TEXT_MODEL,
    feature="text_escalation",
    estimated_cost_usd=ESTIMATED_COST_PER_TEXT_CALL_USD,
    client_factory=None,
    usage_total_func=None,
    usage_recorder=None,
):
    """OpenAIのテキストモデルに質問し、回答を返します。

    呼び出し前に必ず月間上限をチェックし、上限に達している場合は例外を送出して
    実際の呼び出し自体を行いません。成功した場合のみ、想定利用額を記録します。
    Tier3（より高性能なモデル）から呼ぶ場合は、model/feature/estimated_cost_usdを
    差し替えて使います。
    """
    ensure_budget_available(monthly_cap_usd, usage_total_func)

    api_key = get_api_key()

    if client_factory is not None:
        response_text = client_factory(api_key, messages, model)
    else:
        response_text = _call_real_openai_text(api_key, messages, model)

    recorder = usage_recorder or record_openai_usage
    recorder(
        feature=feature,
        model=model,
        estimated_cost_usd=estimated_cost_usd,
    )

    return response_text


def ask_openai_with_web_search(
    query,
    monthly_cap_usd=DEFAULT_MONTHLY_CAP_USD,
    model=DEFAULT_WEB_SEARCH_MODEL,
    feature="web_search",
    estimated_cost_usd=ESTIMATED_COST_PER_WEB_SEARCH_CALL_USD,
    client_factory=None,
    usage_total_func=None,
    usage_recorder=None,
):
    """OpenAIのWeb検索機能つきモデルに質問し、回答を返します。

    Qwen・通常のOpenAIモデルは学習時点までの知識しか持たないため、最新情報が
    必要な質問はTierエスカレーションとは別に、最初からこの関数を使います。
    呼び出し前に必ず月間上限をチェックし、上限に達している場合は例外を送出して
    実際の呼び出し自体を行いません。成功した場合のみ、想定利用額を記録します。

    Ver2.58で実APIによる検証済み（課金設定完了後）。tool_choiceで明示的にweb_searchを
    強制しないと、曖昧な短い質問ではモデルが検索を省略し、学習時点の古い情報で
    答えてしまうことがあると判明したため、_call_real_openai_web_searchでは常に
    tool_choice={"type": "web_search"}を指定しています。

    ユーザーから「検索はOpenAI、回答生成はQwenに分離してコストを抑えられないか」という
    提案があり、Ver2.67で実APIのresponse.outputの中身を詳しく調査した。
    web_search_call項目には検索クエリのみが含まれ、sourcesは常にnullで、
    生の検索結果（参照ページの本文・スニペット）は含まれていなかった。
    実質的な回答内容と引用元URLは、message項目のtext/annotations(url_citation)に
    合成済みの形でしか存在せず、Qwenが再構成できるだけの生データを取り出す方法が
    このAPIには用意されていないことを確認した。そのためこの分離は実現不可能と判断し、
    一括呼び出しのまま維持する（Ver2.58時点の設計を継続）。
    """
    ensure_budget_available(monthly_cap_usd, usage_total_func)

    api_key = get_api_key()

    if client_factory is not None:
        response_text = client_factory(api_key, query, model)
    else:
        response_text = _call_real_openai_web_search(api_key, query, model)

    recorder = usage_recorder or record_openai_usage
    recorder(
        feature=feature,
        model=model,
        estimated_cost_usd=estimated_cost_usd,
    )

    return response_text


def _call_real_openai_web_search(api_key, query, model):
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model,
        tools=[{"type": "web_search"}],
        tool_choice={"type": "web_search"},
        input=query,
    )

    return response.output_text


def _call_real_openai_text(api_key, messages, model):
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1500,
        )
    except Exception as error:
        # gpt-5.5などの新しいモデルはmax_tokensではなくmax_completion_tokensを要求します
        # （Ver2.58の実API検証で判明。実際にAPIを叩けるようになるまで気づけなかった問題です）。
        if "max_completion_tokens" not in str(error):
            raise

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=1500,
        )

    return response.choices[0].message.content


def _call_real_openai_vision(api_key, image_path, prompt, model):
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    request_messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                },
            ],
        }
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=request_messages,
            max_tokens=1000,
        )
    except Exception as error:
        # gpt-5.5などの新しいモデルはmax_tokensではなくmax_completion_tokensを要求します
        # （Ver2.58の実API検証で判明。実際にAPIを叩けるようになるまで気づけなかった問題です）。
        if "max_completion_tokens" not in str(error):
            raise

        response = client.chat.completions.create(
            model=model,
            messages=request_messages,
            max_completion_tokens=1000,
        )

    return response.choices[0].message.content
