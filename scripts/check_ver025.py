import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.memory_forgetting import analyze_forgetting_candidates
from ai.preference_confirmation import (
    analyze_preference_confirmation,
    resolve_preference_confirmation_answer,
)
from ai.preference_memory import extract_preference_memories
from core.capability_manager import CapabilityManager
from core.personal_ai import PersonalAI


def check_imports():
    PersonalAI
    CapabilityManager
    extract_preference_memories
    analyze_preference_confirmation
    resolve_preference_confirmation_answer
    analyze_forgetting_candidates
    print("[OK] imports")
    return 0


def check_file_exists(label, path):
    if path.exists():
        print(f"[OK] {label} exists")
        return 0

    print(f"[NG] {label} missing -> {path}")
    return 1


def check_benchmark_runs():
    benchmark_path = PROJECT_ROOT / "scripts" / "benchmark_lightweight.py"
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(benchmark_path),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        print(f"[NG] benchmark exit code -> {result.returncode}")
        print(result.stdout)
        print(result.stderr)
        return 1

    required_texts = [
        "PersonalAI Lightweight Benchmark",
        "import_time_personal_ai",
        "Total",
    ]

    for required_text in required_texts:
        if required_text not in result.stdout:
            print(f"[NG] benchmark output missing -> {required_text}")
            print(result.stdout)
            return 1

    print("[OK] benchmark runs")
    return 0


def main():
    failures = 0

    failures += check_imports()
    failures += check_file_exists(
        "benchmark_lightweight.py",
        PROJECT_ROOT / "scripts" / "benchmark_lightweight.py",
    )
    failures += check_file_exists(
        "performance_benchmark.md",
        PROJECT_ROOT / "docs" / "performance_benchmark.md",
    )
    failures += check_benchmark_runs()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
