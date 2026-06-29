import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from database.memory_manager import get_memories


def check_imports():
    get_memories
    print("[OK] imports")
    return 0


def check_list_script_exists():
    script_path = PROJECT_ROOT / "scripts" / "list_memories.py"

    if not script_path.exists():
        print("[NG] scripts/list_memories.py does not exist")
        return 1

    print("[OK] list_memories.py exists")
    return 0


def run_list_memories(args):
    script_path = PROJECT_ROOT / "scripts" / "list_memories.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(script_path),
            *args,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def check_list_command(label, args):
    result = run_list_memories(args)

    if result.returncode != 0:
        print(f"[NG] {label} failed")
        print(result.stderr)
        return 1

    output = result.stdout

    if not isinstance(output, str):
        print(f"[NG] {label} output type -> {type(output)}")
        return 1

    if "=== Memories ===" not in output:
        print(f"[NG] {label} missing title")
        return 1

    if not has_expected_memory_output(output):
        print(f"[NG] {label} unexpected output")
        print(output)
        return 1

    print(f"[OK] {label}")
    return 0


def has_expected_memory_output(output):
    if "保存されている記憶はありません。" in output:
        return True

    expected_labels = [
        "content:",
        "memory_type:",
        "category:",
        "scope:",
        "confidence:",
    ]

    return any(label in output for label in expected_labels)


def main():
    failures = 0

    failures += check_imports()
    failures += check_list_script_exists()
    failures += check_list_command("list --limit", ["--limit", "5"])
    failures += check_list_command("list --category", ["--category", "name", "--limit", "5"])
    failures += check_list_command(
        "list --include-inactive",
        ["--include-inactive", "--limit", "5"],
    )
    failures += check_list_command("list --search", ["--search", "test", "--limit", "5"])

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
