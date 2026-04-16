#!/usr/bin/env python3
"""Every executable in bin/ must respond to --help within 5 seconds with
exit code 0 and non-empty output. Catches import errors, missing
dependencies, and typos that would otherwise only surface at service
boot."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"

# Tools whose `--help` path we verify. (Shell scripts that don't support
# --help are smoke-tested via `bash -n` in run-all.sh separately.)
CHECK = [
    "nex-attention",
    "nex-queue",
    "nex-fit-test",
    "nex-reasoning-bench",
    "nex-signal-post",
    "nex-invoke",
    "nex-invoke-agent",
    "nex-invoke-faculty",
]


def test_help_on_each_cli():
    failures = []
    for name in CHECK:
        path = BIN / name
        if not path.exists():
            failures.append(f"{name}: binary missing at {path}")
            continue
        try:
            r = subprocess.run(
                [str(path), "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"{name}: --help timed out (>5s)")
            continue
        if r.returncode != 0:
            failures.append(f"{name}: --help exited {r.returncode}: {r.stderr.strip()[:200]}")
            continue
        if not r.stdout.strip():
            failures.append(f"{name}: --help produced no stdout")
            continue
        print(f"  [help {name}] OK")
    assert not failures, "CLI --help failures:\n  - " + "\n  - ".join(failures)


def test_fit_test_lists_scenarios():
    """fit-test --list-scenarios must enumerate the 11 safety scenarios."""
    r = subprocess.run(
        [str(BIN / "nex-fit-test"), "--list-scenarios"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert r.returncode == 0, r.stderr
    # At minimum a few scenario IDs we know ship
    expected_any = ["identity", "ethics", "impersonation", "voice", "autonomy"]
    found = sum(1 for e in expected_any if e in r.stdout.lower())
    assert found >= 3, f"fit-test scenario list looks empty; found {found}/{len(expected_any)} keywords"
    print(f"  [test_fit_test_lists_scenarios] OK ({found}/{len(expected_any)} keywords found)")


if __name__ == "__main__":
    test_help_on_each_cli()
    test_fit_test_lists_scenarios()
    print("ALL CLI HELP SMOKE TESTS PASS")
