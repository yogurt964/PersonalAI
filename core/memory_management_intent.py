import re


MEMORY_LIST_PATTERNS = [
    "覚えていることを見せて",
    "覚えていることを一覧",
    "記憶一覧",
    "Memory一覧",
    "memory一覧",
    "何を覚えている",
    "何を覚えていますか",
    "保存した記憶を見せて",
    "保存したMemoryを見せて",
    "保存したmemoryを見せて",
]

MEMORY_DELETE_VERBS = [
    "削除して",
    "消して",
    "忘れて",
]

MEMORY_REFERENCE_WORDS = [
    "記憶",
    "Memory",
    "memory",
]

_ID_PATTERN = re.compile(r"(?:id\s*[:：]?\s*)?(\d+)\s*番?", re.IGNORECASE)


def detect_memory_list_request(user_input):
    """ユーザー入力が保存済みMemoryの一覧表示を求めているか判定します。"""
    text = _clean_text(user_input)
    return any(pattern in text for pattern in MEMORY_LIST_PATTERNS)


def detect_memory_delete_request(user_input):
    """ユーザー入力が特定Memoryの削除を求めているか判定します。

    「記憶」「Memory」のような言及と、削除を示す動詞の両方が含まれる場合のみ
    削除意図として扱います（「このファイルを削除して」のような無関係な削除依頼と
    衝突しないようにするためです）。
    """
    text = _clean_text(user_input)

    has_delete_verb = any(verb in text for verb in MEMORY_DELETE_VERBS)
    has_memory_reference = any(word in text for word in MEMORY_REFERENCE_WORDS)

    if not (has_delete_verb and has_memory_reference):
        return {"is_delete_request": False, "memory_id": None}

    memory_id = _extract_memory_id(text)

    return {"is_delete_request": True, "memory_id": memory_id}


def _extract_memory_id(text):
    match = _ID_PATTERN.search(text)

    if not match:
        return None

    return int(match.group(1))


def _clean_text(value):
    if value is None:
        return ""

    return " ".join(str(value).split())
