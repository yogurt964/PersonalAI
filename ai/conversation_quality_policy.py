CASUAL_KEYWORDS = [
    "こんにちは",
    "おはよう",
    "こんばんは",
    "ありがとう",
    "疲れました",
    "疲れた",
    "応援",
    "励まして",
    "雑談",
    "少しだけ話",
]

ADVICE_KEYWORDS = [
    "どうしたらいい",
    "どうすればいい",
    "おすすめ",
    "オススメ",
    "どちらがいい",
    "どっちがいい",
    "リスク",
    "提案",
    "相談",
    "選択肢",
]

DEVELOPMENT_KEYWORDS = [
    "Codex",
    "Git",
    "commit",
    "push",
    "Python",
    "VS Code",
    "PowerShell",
    "実装",
    "エラー",
    "チェック",
    "scripts",
    "docs",
    "app.py",
    "PersonalAI",
    "開発",
]


def classify_conversation_mode(user_input):
    """入力内容から、返答の雰囲気を軽く分類します。"""
    text = str(user_input or "")

    if _contains_any(text, DEVELOPMENT_KEYWORDS):
        return "development"

    if _contains_any(text, ADVICE_KEYWORDS):
        return "advice"

    if _contains_any(text, CASUAL_KEYWORDS):
        return "casual"

    return "unknown"


def build_conversation_quality_guidance(
    user_input,
    memory_usage="normal",
    input_analysis=None,
):
    """LLMへ渡す会話品質ガイダンスを作ります。

    出力を固定するのではなく、ユーザー入力に合う返答の方向だけを伝えます。
    """
    mode = classify_conversation_mode(user_input)
    task_type = _get_context_value(input_analysis, "task_type", "unknown")

    common_guidance = (
        "【会話品質方針】"
        f"\nconversation_mode: {mode}"
        f"\nmemory_usage: {memory_usage}"
        f"\ntask_type: {task_type}"
        "\n- ユーザーの入力に直接答える。"
        "\n- 不明点を断定しない。"
        "\n- 実行していないことを実行したと言わない。"
        "\n- MemoryやPreferenceを必要以上に出さない。"
        "\n- 内部機能名や実装名を必要以上に出さない。"
    )

    mode_guidance = {
        "casual": (
            "\n- 通常会話では短めで自然に返す。"
            "\n- 返答は1〜3文を目安にする。"
            "\n- ユーザーが求めていない情報へ話題を広げすぎない。"
            "\n- 好みや過去情報を無理に混ぜない。"
        ),
        "advice": (
            "\n- まず結論を出す。"
            "\n- 理由を短く説明する。"
            "\n- 必要なら現実的な選択肢を最大3つまで出す。"
            "\n- リスクがある場合は明確に伝える。"
            "\n- 関係の薄いPreference情報は出さない。"
        ),
        "development": (
            "\n- 開発補助では最初に結論を1文で出す。"
            "\n- 手順を順番に整理する。"
            "\n- 手順は最大4項目を目安にし、長くなりすぎない。"
            "\n- 変更対象、確認コマンド、注意点を明確にする。"
            "\n- 危険な操作は先に注意する。"
            "\n- 初心者にも分かるように書く。"
            "\n- 好きな食べ物などのPreference情報は、開発相談では出さない。"
        ),
        "unknown": (
            "\n- 入力に沿って自然に答える。"
            "\n- 必要なら確認質問をする。"
        ),
    }

    return common_guidance + mode_guidance.get(mode, mode_guidance["unknown"])


def _contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)


def _get_context_value(context, key, default=None):
    if context is None:
        return default

    if isinstance(context, dict):
        return context.get(key, default)

    return getattr(context, key, default)
