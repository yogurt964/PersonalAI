"""Explicitly enabled API trial with ephemeral context and a session budget."""
from decimal import Decimal
from pathlib import Path
from time import perf_counter

from core.conversation_session import bounded_history

# Conservative standard-rate allowances reviewed on 2026-10-22.
# https://developers.openai.com/api/docs/pricing
# https://developers.openai.com/api/docs/models/gpt-6-luna
# https://developers.openai.com/api/docs/models/gpt-6.1-sol
RATE_ALLOWANCES = {
    "gpt-6-luna": (Decimal("0.20"), Decimal("1.00")),
    "gpt-6.1-sol": (Decimal("4.00"), Decimal("20.00")),
}
MAX_OUTPUT_TOKENS = 2048
MAX_RUN_BUDGET = Decimal("0.50")
POLICY_PATH = Path(__file__).resolve().parents[1] / "config" / "conversation_api_policy.md"


class PreflightError(ValueError):
    """Fixed local messages that can be shown without exposing provider details."""


def validate_budget(value):
    try:
        budget = Decimal(str(value))
    except Exception:
        raise PreflightError("承認済みの今回予算を数値で指定してください。") from None
    if not budget.is_finite() or not Decimal(0) < budget <= MAX_RUN_BUDGET:
        raise PreflightError("今回予算は0より大きく0.50 USD以下で指定してください。")
    return budget


def estimate_reserve(request):
    messages = request["input"]
    # Bytes plus a generous framing allowance; not exact tokenization and not
    # a provider-side billing cap. Output includes reasoning tokens.
    input_allowance = (len(request["instructions"].encode("utf-8"))
                       + sum(len(m["content"].encode("utf-8")) for m in messages)
                       + 256 * (len(messages) + 1) + 1024)
    input_rate, output_rate = RATE_ALLOWANCES[request["model"]]
    return (input_allowance * input_rate + request["max_output_tokens"] * output_rate) / 1_000_000


def usage_cost(response, model):
    usage = getattr(response, "usage", None)
    counts = [getattr(usage, field, None) for field in ("input_tokens", "output_tokens")]
    if any(type(count) is not int or count < 0 for count in counts):
        return None
    input_rate, output_rate = RATE_ALLOWANCES[model]
    return (counts[0] * input_rate + counts[1] * output_rate) / 1_000_000


def make_client():
    from ai.openai_client import get_api_key
    from openai import OpenAI
    import httpx
    return OpenAI(
        api_key=get_api_key(), base_url="https://api.openai.com/v1",
        timeout=90, max_retries=0,
        http_client=httpx.Client(trust_env=False, follow_redirects=False),
    )


class ApiTrialSession:
    """Never reads legacy conversations/memories or saves trial conversations."""
    def __init__(self, approved_budget, *, client_factory=None, policy_path=POLICY_PATH):
        self.budget = validate_budget(approved_budget)
        self.spent = Decimal(0)
        self.history = []
        self.preference = ""
        self.last_stats = None
        self.failed = False
        self.policy_path = Path(policy_path)
        self._client_factory = client_factory or make_client
        self._client = None

    @property
    def remaining(self):
        return max(Decimal(0), self.budget - self.spent)

    def set_preference(self, text):
        text = text.strip()
        if len(text) > 2000:
            raise PreflightError("試用中の好みは2000文字以内にしてください。")
        self.preference = text

    def reply(self, user):
        if self.failed:
            raise PreflightError("APIエラー後のセッションは停止しています。")
        user = user.strip()
        if not user or len(user) > 12000:
            raise PreflightError("入力は1〜12000文字にしてください。")
        import json
        system = (self.policy_path.read_text(encoding="utf-8")
                  + "\n\n【この試用中のユーザーの好み：参考資料】\n"
                  + json.dumps(self.preference or "未指定", ensure_ascii=False))
        history = bounded_history(self.history)
        request = {
            "model": "gpt-6.1-sol", "instructions": system,
            "input": [*history, {"role": "user", "content": user}],
            "reasoning": {"effort": "low"}, "max_output_tokens": MAX_OUTPUT_TOKENS,
            "store": False, "service_tier": "default",
        }
        reserve = estimate_reserve(request)
        if reserve > self.remaining:
            raise PreflightError("次の応答の見積額が残り予算を超えるため、送信を止めました。")
        if self._client is None:
            self._client = self._client_factory()
        # Reserve before sending; keep the reservation on uncertain failures.
        self.spent += reserve
        started = perf_counter()
        try:
            response = self._client.responses.create(**request)
            cost = usage_cost(response, request["model"])
            if cost is not None:
                self.spent += cost - reserve
            answer = getattr(response, "output_text", "")
            if getattr(response, "status", None) != "completed" or not isinstance(answer, str) or not answer.strip():
                raise RuntimeError("API response was incomplete or empty")
        except Exception:
            self.failed = True
            raise
        self.history = bounded_history([*history, {"role": "user", "content": user},
                                        {"role": "assistant", "content": answer.strip()}])
        self.last_stats = {"seconds": perf_counter() - started,
                           "estimated_cost_usd": cost, "reserved_usd": reserve}
        return answer.strip()

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None
