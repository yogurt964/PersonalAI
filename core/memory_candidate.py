import re


SUMMARY_MAX_CHARS = 320
LONG_TEXT_THRESHOLD = 1000

PERSONAL_INFO_KEYWORDS = [
    "個人情報",
    "住所",
    "電話番号",
    "メールアドレス",
    "氏名",
    "生年月日",
    "マイナンバー",
    "email",
    "address",
    "phone",
]

SECRET_KEYWORDS = [
    "api key",
    "api_key",
    "apikey",
    "password",
    "passwd",
    "secret",
    "token",
    "パスワード",
    "apiキー",
    "認証情報",
]

HIGH_RISK_KEYWORDS = [
    "契約",
    "法律",
    "訴訟",
    "医療",
    "診断",
    "治療",
    "薬",
    "金銭",
    "請求",
    "支払い",
    "銀行",
    "投資",
    "税金",
    "legal",
    "medical",
    "contract",
    "payment",
    "invoice",
]


def build_memory_candidate_from_reader_result(reader_result, source_tool="web_reader"):
    """Reader結果からMemory保存候補を作るdry-run関数です。

    この関数はDBへ保存せず、LLMも呼ばず、候補dictだけを返します。
    """
    data = _extract_reader_data(reader_result)
    title = _clean_text(data.get("title"))
    source_url = _clean_text(data.get("final_url") or data.get("url") or data.get("source_url"))
    text = _clean_text(data.get("text") or data.get("text_preview") or data.get("summary"))
    summary = _shorten_text(data.get("text_preview") or text)
    reasons = []

    if not summary and title:
        summary = title
        reasons.append("本文が空のため、titleをsummary候補にしました。")

    risk_level = "low"

    if not summary:
        reasons.append("本文プレビューがないため、保存価値を判断できません。")

    if _contains_any(text, PERSONAL_INFO_KEYWORDS):
        risk_level = _max_risk(risk_level, "medium")
        reasons.append("個人情報を含む可能性があります。")

    if _contains_any(text, SECRET_KEYWORDS):
        risk_level = _max_risk(risk_level, "high")
        reasons.append("APIキー・パスワード・認証情報を含む可能性があります。")

    if _contains_any(text, HIGH_RISK_KEYWORDS):
        risk_level = _max_risk(risk_level, "high")
        reasons.append("金銭・契約・法律・医療など高リスク領域を含む可能性があります。")

    if len(text) > LONG_TEXT_THRESHOLD:
        risk_level = _max_risk(risk_level, "medium")
        reasons.append("本文が長いため、保存前に要約や確認が必要です。")

    if not reasons:
        reasons.append("保存すべきか迷うため、dry-runでは候補提示に留めます。")

    requires_user_confirmation = True

    return {
        "source_tool": source_tool,
        "source_url": source_url,
        "title": title,
        "summary": summary,
        "candidate_type": _decide_candidate_type(risk_level, source_url),
        "importance": _decide_importance(title, summary, risk_level),
        "risk_level": risk_level,
        "requires_user_confirmation": requires_user_confirmation,
        "reasons": reasons,
        "should_save": False,
    }


def _extract_reader_data(reader_result):
    if reader_result is None:
        return {}

    if isinstance(reader_result, dict):
        data = reader_result.get("data")

        if isinstance(data, dict):
            merged = dict(reader_result)
            merged.update(data)
            return merged

        return dict(reader_result)

    data = getattr(reader_result, "data", None)

    if isinstance(data, dict):
        return dict(data)

    return {}


def _clean_text(value):
    if value is None:
        return ""

    return " ".join(str(value).split())


def _shorten_text(value, max_chars=SUMMARY_MAX_CHARS):
    text = _clean_text(value)

    if len(text) <= max_chars:
        return text

    shortened = text[:max_chars].rstrip()
    last_space = shortened.rfind(" ")

    if last_space >= int(max_chars * 0.6):
        shortened = shortened[:last_space].rstrip()

    return f"{shortened}..."


def _contains_any(text, keywords):
    normalized = _normalize_for_search(text)
    return any(_normalize_for_search(keyword) in normalized for keyword in keywords)


def _normalize_for_search(text):
    return re.sub(r"\s+", " ", str(text or "").lower())


def _max_risk(current, candidate):
    order = {"low": 0, "medium": 1, "high": 2}
    return candidate if order[candidate] > order[current] else current


def _decide_candidate_type(risk_level, source_url):
    if risk_level == "high":
        return "review_required"

    if source_url:
        return "reader_summary"

    return "memory_candidate"


def _decide_importance(title, summary, risk_level):
    if risk_level == "high":
        return "review"

    if title and summary:
        return "medium"

    return "low"
