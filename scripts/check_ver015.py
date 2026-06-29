import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.memory_context import build_memory_context
from database.memory_manager import get_memories


def check_imports():
    build_memory_context
    get_memories
    print("[OK] imports")
    return 0


def check_show_script_exists():
    script_path = PROJECT_ROOT / "scripts" / "show_memory_context.py"

    if not script_path.exists():
        print("[NG] scripts/show_memory_context.py does not exist")
        return 1

    print("[OK] show_memory_context.py exists")
    return 0


def check_build_memory_context_with_db_memories():
    memories = get_memories(limit=20)
    context = build_memory_context(memories)

    if not isinstance(context, str):
        print(f"[NG] build_memory_context return type -> {type(context)}")
        return 1

    if "長期記憶" not in context:
        print("[NG] build_memory_context output does not include 長期記憶")
        return 1

    print("[OK] build_memory_context works with current DB memories")
    return 0


def check_show_script_runs():
    script_path = PROJECT_ROOT / "scripts" / "show_memory_context.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(script_path),
            "--limit",
            "5",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )

    if result.returncode != 0:
        print("[NG] show_memory_context.py failed")
        print(result.stderr)
        return 1

    if "MemoryContext Preview" not in result.stdout:
        print("[NG] show_memory_context.py output missing preview header")
        return 1

    if "長期記憶" not in result.stdout:
        print("[NG] show_memory_context.py output missing 長期記憶")
        return 1

    print("[OK] show_memory_context.py runs")
    return 0


def main():
    failures = 0

    failures += check_imports()
    failures += check_show_script_exists()
    failures += check_build_memory_context_with_db_memories()
    failures += check_show_script_runs()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
