import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHECK_SCRIPTS = [
    "scripts/check_ver200.py",
    "scripts/run_ver1_checks.py",
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
    log("PersonalAI Ver2 Check Runner")
    log("============================")
    log()
    log("This runner is for standard Ver2.x checks.")
    log("It must not run Web access in automatic checks, delete DB files, create tags, or push commits.")
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
        log(f"Failed checks: {len(failed)}")

        for script_path in failed:
            log(f"- {script_path}")

        raise SystemExit(1)

    log()
    log("All Ver2 checks passed.")


def log(message=""):
    print(message, flush=True)


if __name__ == "__main__":
    main()
