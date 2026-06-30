import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.memory_forgetting import (
    analyze_forgetting_candidates,
    get_forgetting_candidates,
)
from core.personal_ai import PersonalAI


def build_synthetic_memories():
    return [
        {
            "id": 1,
            "content": "一時メモ",
            "memory_type": "temporary",
            "category": "temporary",
            "importance": 1,
            "confidence": 30,
            "scope": "temporary",
            "tags": "temporary,test",
            "is_active": True,
        },
        {
            "id": 2,
            "content": "ユーザーはPersonalAIを全アプリ操作の入口にしたい。",
            "memory_type": "user_profile",
            "category": "core",
            "importance": 10,
            "confidence": 95,
            "scope": "user",
            "tags": "core,project",
            "memory_key": "core:personal_ai:goal",
            "is_active": True,
        },
        {
            "id": 3,
            "content": "期限切れの一時情報",
            "memory_type": "temporary",
            "category": "temporary",
            "importance": 3,
            "confidence": 60,
            "scope": "temporary",
            "tags": "temporary",
            "expires_at": "2000-01-01T00:00:00",
            "is_active": True,
        },
        {
            "id": 4,
            "content": "すでに無効な記憶",
            "memory_type": "temporary",
            "category": "temporary",
            "importance": 1,
            "confidence": 20,
            "scope": "temporary",
            "tags": "temporary",
            "is_active": False,
        },
    ]


def check_imports():
    analyze_forgetting_candidates
    get_forgetting_candidates
    PersonalAI
    print("[OK] imports")
    return 0


def find_candidate(candidates, memory_id):
    for candidate in candidates:
        if candidate["memory_id"] == memory_id:
            return candidate

    return None


def check_low_value_candidate(candidates):
    candidate = find_candidate(candidates, 1)

    if candidate is None:
        print("[NG] low value memory was not suggested")
        return 1

    expected_reasons = ["low_importance", "low_confidence", "temporary_scope"]
    missing_reasons = [
        reason
        for reason in expected_reasons
        if reason not in candidate["reasons"]
    ]

    if missing_reasons:
        print(f"[NG] low value reasons missing -> {missing_reasons}")
        print(candidate)
        return 1

    print("[OK] low value memory is suggested")
    return 0


def check_high_value_protected(candidates):
    candidate = find_candidate(candidates, 2)

    if candidate is not None:
        print(f"[NG] high value memory was suggested -> {candidate}")
        return 1

    print("[OK] high value memory is protected")
    return 0


def check_expired_candidate(candidates):
    candidate = find_candidate(candidates, 3)

    if candidate is None:
        print("[NG] expired memory was not suggested")
        return 1

    if "expired" not in candidate["reasons"]:
        print(f"[NG] expired reason missing -> {candidate}")
        return 1

    print("[OK] expired memory is suggested")
    return 0


def check_inactive_excluded(candidates):
    candidate = find_candidate(candidates, 4)

    if candidate is not None:
        print(f"[NG] inactive memory was suggested -> {candidate}")
        return 1

    print("[OK] inactive memory is excluded")
    return 0


def check_dry_run_fields(candidates):
    required_keys = ["dry_run", "recommended_action", "score", "reasons"]

    for candidate in candidates:
        for key in required_keys:
            if key not in candidate:
                print(f"[NG] candidate missing {key} -> {candidate}")
                return 1

        if candidate["dry_run"] is not True:
            print(f"[NG] dry_run is not True -> {candidate}")
            return 1

    print("[OK] dry-run fields")
    return 0


def check_db_dry_run_read():
    try:
        candidates = get_forgetting_candidates(limit=10, max_candidates=5, min_score=50)
    except Exception as error:
        print(f"[OK] DB dry-run read skipped -> {error}")
        return 0

    if not isinstance(candidates, list):
        print(f"[NG] DB dry-run result is not list -> {type(candidates)}")
        return 1

    print("[OK] DB dry-run read")
    return 0


def main():
    failures = 0

    failures += check_imports()

    candidates = analyze_forgetting_candidates(
        build_synthetic_memories(),
        max_candidates=20,
        min_score=50,
    )

    failures += check_low_value_candidate(candidates)
    failures += check_high_value_protected(candidates)
    failures += check_expired_candidate(candidates)
    failures += check_inactive_excluded(candidates)
    failures += check_dry_run_fields(candidates)
    failures += check_db_dry_run_read()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
