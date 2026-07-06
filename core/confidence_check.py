"""Qwen（ローカルモデル）の回答が低信頼そうかどうかを判定する共通の仕組みです。

vision_router（画像解析）とテキスト応答（Reader経由の要約・質問など）の
両方で同じ判定ロジックを再利用します。
"""

LOW_CONFIDENCE_MARKERS = [
    "わかりません",
    "分かりません",
    "判断できません",
    "確信が持てません",
    "不明瞭",
    "読み取れません",
    "断定できません",
    "特定できません",
]


def seems_low_confidence(text):
    """テキストに低信頼のサインとなる表現が含まれるかを判定します。"""
    text = str(text or "")
    return any(marker in text for marker in LOW_CONFIDENCE_MARKERS)
