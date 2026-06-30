import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHECK_SCRIPTS = [
    "scripts/check_ver011.py",
    "scripts/check_ver012.py",
    "scripts/check_ver013.py",
    "scripts/check_ver014.py",
    "scripts/check_ver015.py",
    "scripts/check_ver016.py",
    "scripts/check_ver017.py",
    "scripts/check_ver018.py",
    "scripts/check_ver019.py",
    "scripts/check_ver020.py",
    "scripts/check_ver021.py",
    "scripts/check_ver022.py",
    "scripts/check_ver023.py",
    "scripts/check_ver024.py",
    "scripts/check_ver025.py",
    "scripts/check_ver026.py",
    "scripts/benchmark_lightweight.py",
]


def run_script(script_path):
    log(f"[RUN] {script_path}")

    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(PROJECT_ROOT / script_path),
        ],
        cwd=PROJECT_ROOT,
        text=True,
    )

    if result.returncode == 0:
        log(f"[OK] {script_path}")
        log()
        return True

    log(f"[NG] {script_path} exit code={result.returncode}")
    log()
    return False


def main():
    log("PersonalAI Pre-Ver1.0 Check Runner")
    log("=================================")
    log()
    log("Some checks create and clean up test-only Memory records.")
    log("They must not delete existing user Memory or change is_active outside test data.")
    log()

    passed = []
    failed = []

    for script_path in CHECK_SCRIPTS:
        if run_script(script_path):
            passed.append(script_path)
        else:
            failed.append(script_path)

    log("Summary")
    log("-------")
    log(f"Passed: {len(passed)}")
    log(f"Failed: {len(failed)}")

    if failed:
        log()
        log("Failed scripts:")

        for script_path in failed:
            log(f"- {script_path}")

        raise SystemExit(1)

    log()
    log("All pre-Ver1.0 checks passed.")


def log(message=""):
    print(message, flush=True)


if __name__ == "__main__":
    main()
