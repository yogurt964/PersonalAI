import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.preference_confirmation import analyze_preference_confirmation
from ai.preference_memory import extract_preference_memories, save_preference_memories


def check_imports():
    analyze_preference_confirmation
    save_preference_memories
    print("[OK] imports")
    return 0


def check_decision(label, text, expected_should_ask, expected_reason, expected_question_text=""):
    decision = analyze_preference_confirmation(text)

    if decision["should_ask"] != expected_should_ask:
        print(
            f"[NG] {label} should_ask -> expected {expected_should_ask}, "
            f"got {decision['should_ask']}"
        )
        return 1

    if decision["reason"] != expected_reason:
        print(f"[NG] {label} reason -> expected {expected_reason}, got {decision['reason']}")
        return 1

    if expected_question_text and expected_question_text not in decision["question"]:
        print(f"[NG] {label} question -> {decision['question']}")
        return 1

    print(f"[OK] {label}")
    return 0


def check_ver019_extract(label, text, expected_target, expected_polarity):
    preferences = extract_preference_memories(text)

    if len(preferences) != 1:
        print(f"[NG] {label} extract count -> expected 1, got {len(preferences)}")
        return 1

    preference = preferences[0]

    if preference["target"] != expected_target:
        print(f"[NG] {label} target -> {preference['target']}")
        return 1

    if preference["polarity"] != expected_polarity:
        print(f"[NG] {label} polarity -> {preference['polarity']}")
        return 1

    print(f"[OK] {label} extract")
    return 0


def main():
    failures = 0

    failures += check_imports()
    failures += check_decision(
        "simple addition",
        "焼き肉が好きです。覚えて",
        False,
        "simple_addition",
    )
    failures += check_decision(
        "explicit negative",
        "ラーメンは好きじゃないです。覚えて\n寿司は嫌いです。覚えて",
        False,
        "explicit_negative_preference",
    )
    failures += check_decision(
        "primary preference",
        "一番好きな食べ物は焼き肉です。覚えて",
        True,
        "primary_preference_update",
        "一番",
    )
    failures += check_decision(
        "temporal preference change",
        "前はカレーが好きだったけど、今は焼き肉が好きです。覚えて",
        True,
        "temporal_preference_change",
    )
    failures += check_decision(
        "preference change request",
        "好きな食べ物をカレーから焼き肉に変更して。覚えて",
        True,
        "preference_change_request",
    )

    failures += check_ver019_extract(
        "ramen like",
        "ラーメンが好きです。覚えて",
        "ラーメン",
        "like",
    )
    failures += check_ver019_extract(
        "sushi like",
        "寿司が好きです。覚えて",
        "寿司",
        "like",
    )
    failures += check_ver019_extract(
        "ramen not_like",
        "ラーメンは好きじゃないです。覚えて",
        "ラーメン",
        "not_like",
    )
    failures += check_ver019_extract(
        "sushi dislike",
        "寿司は嫌いです。覚えて",
        "寿司",
        "dislike",
    )

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
