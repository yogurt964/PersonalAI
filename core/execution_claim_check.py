"""通常会話（Executor経由のQwen生成）が、実際には実行していない記憶操作
（削除・編集・保存など）を実行したかのように主張していないかを判定する、
最小の検証層です（Ver2.70、docs/llm_intent_resolver_design.mdの検証層B）。

通常会話（core/personal_ai.pyのhandle_user_input()でExecutorが生成する自由回答）は、
記憶の削除・編集・保存を直接実行する仕組みを一切持ちません。これらは専用の確認フロー
（memory_delete_confirmation / memory_edit_confirmation / memory_candidate_confirmation）
またはextract_and_save_memories()（真の結果を返した場合は早期returnし、通常会話には
到達しない）でのみ実行されます。

そのため、通常会話の回答に「記憶」への言及と、操作を完了したという表現の両方が
含まれる場合、実際にその操作を実行した保証がないことを、正直に注記します
（Ver2.62で見つかった、Qwenが削除操作を捏造して回答した事象への構造的な対策）。

完全一致の言い換え検知には限界があり、過去に実行済みの操作を正しく振り返って
説明しているだけの発言にも注記が付く場合があります。ただしその場合も、
「この会話の中で今実行する仕組みは動いていない」という注記自体は常に事実であるため、
誤りにはなりません。
"""

MEMORY_REFERENCE_WORDS = [
    "記憶",
    "Memory",
    "memory",
]

ACTION_COMPLETION_MARKERS = [
    "削除しました",
    "削除いたしました",
    "編集しました",
    "編集いたしました",
    "保存しました",
    "保存いたしました",
    "保存が完了",
    "無効化しました",
    "更新しました",
    "書き換えました",
]


def contains_unverified_action_claim(text):
    """通常会話の回答に、記憶操作を実行したという未検証の主張が含まれるかを判定します。"""
    text = str(text or "")

    has_memory_reference = any(word in text for word in MEMORY_REFERENCE_WORDS)
    has_completion_marker = any(marker in text for marker in ACTION_COMPLETION_MARKERS)

    return has_memory_reference and has_completion_marker
