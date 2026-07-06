import base64
import os

from database.openai_usage import get_monthly_openai_usage_total, record_openai_usage


DEFAULT_MONTHLY_CAP_USD = 5.0
DEFAULT_VISION_MODEL = "gpt-4o-mini"
DEFAULT_TEXT_MODEL = "gpt-4o-mini"

# gpt-4o-miniでの1回あたりの想定コスト（安全側に倒した概算値）。
# 実際の請求額はこれ以下になる想定です。正確な値はOpenAIのpricingページを参照してください。
ESTIMATED_COST_PER_VISION_CALL_USD = 0.01
ESTIMATED_COST_PER_TEXT_CALL_USD = 0.005


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
    client_factory=None,
    usage_total_func=None,
    usage_recorder=None,
):
    """OpenAI visionモデルで画像を解析します。

    呼び出し前に必ず月間上限をチェックし、上限に達している場合は例外を送出して
    実際の呼び出し自体を行いません。成功した場合のみ、想定利用額を記録します。
    """
    ensure_budget_available(monthly_cap_usd, usage_total_func)

    api_key = get_api_key()

    if client_factory is not None:
        response_text = client_factory(api_key, image_path, prompt, model)
    else:
        response_text = _call_real_openai_vision(api_key, image_path, prompt, model)

    recorder = usage_recorder or record_openai_usage
    recorder(
        feature="image_reader_vision",
        model=model,
        estimated_cost_usd=ESTIMATED_COST_PER_VISION_CALL_USD,
    )

    return response_text


def ask_openai_text(
    messages,
    monthly_cap_usd=DEFAULT_MONTHLY_CAP_USD,
    model=DEFAULT_TEXT_MODEL,
    client_factory=None,
    usage_total_func=None,
    usage_recorder=None,
):
    """OpenAIのテキストモデルに質問し、回答を返します。

    呼び出し前に必ず月間上限をチェックし、上限に達している場合は例外を送出して
    実際の呼び出し自体を行いません。成功した場合のみ、想定利用額を記録します。
    """
    ensure_budget_available(monthly_cap_usd, usage_total_func)

    api_key = get_api_key()

    if client_factory is not None:
        response_text = client_factory(api_key, messages, model)
    else:
        response_text = _call_real_openai_text(api_key, messages, model)

    recorder = usage_recorder or record_openai_usage
    recorder(
        feature="text_escalation",
        model=model,
        estimated_cost_usd=ESTIMATED_COST_PER_TEXT_CALL_USD,
    )

    return response_text


def _call_real_openai_text(api_key, messages, model):
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=1500,
    )

    return response.choices[0].message.content


def _call_real_openai_vision(api_key, image_path, prompt, model):
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    response = client.chat.completions.create(
        model=model,
        messages=[
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
        ],
        max_tokens=1000,
    )

    return response.choices[0].message.content
