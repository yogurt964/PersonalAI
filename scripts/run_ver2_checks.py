import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHECK_SCRIPTS = [
    "scripts/check_ver2430.py",
    "scripts/check_ver2420.py",
    "scripts/check_ver2410.py",
    "scripts/check_ver2400.py",
    "scripts/check_ver2390.py",
    "scripts/check_ver2380.py",
    "scripts/check_ver2370.py",
    "scripts/check_ver2360.py",
    "scripts/check_ver2350.py",
    "scripts/check_ver2340.py",
    "scripts/check_ver2330.py",
    "scripts/check_ver2320.py",
    "scripts/check_ver2310.py",
    "scripts/check_ver2300.py",
    "scripts/check_ver2290.py",
    "scripts/check_ver2280.py",
    "scripts/check_ver2270.py",
    "scripts/check_ver2260.py",
    "scripts/check_ver2250.py",
    "scripts/check_ver2240.py",
    "scripts/check_ver2230.py",
    "scripts/check_ver2220.py",
    "scripts/check_ver2210.py",
    "scripts/check_ver2200.py",
    "scripts/check_ver2190.py",
    "scripts/check_ver2180.py",
    "scripts/check_ver2170.py",
    "scripts/check_ver2160.py",
    "scripts/check_ver2150.py",
    "scripts/check_ver2140.py",
    "scripts/check_ver2130.py",
    "scripts/check_ver2120.py",
    "scripts/check_ver2110.py",
    "scripts/check_ver2100.py",
    "scripts/check_ver290.py",
    "scripts/check_ver280.py",
    "scripts/check_ver270.py",
    "scripts/check_ver260.py",
    "scripts/check_ver250.py",
    "scripts/check_ver240.py",
    "scripts/check_ver230.py",
    "scripts/check_ver220.py",
    "scripts/check_ver210.py",
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
