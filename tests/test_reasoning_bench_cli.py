#!/usr/bin/env python3
"""Smoke-test nex-reasoning-bench CLI entry points.

Scope: we exercise CLI paths that don't call a real LLM (--list, --help,
--dry-run) to verify argument parsing, config loading, and the hard-stop
contract. Real benchmark execution is v0.2 scope.

Why: every `ExecStartPre=%h/agent-kernel/bin/nex-reasoning-bench ...`
line in the shipped systemd units runs this CLI at service-boot time.
If the CLI doesn't even parse its arguments correctly, no agent boots.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "bin" / "nex-reasoning-bench"


def run(args, env=None, cwd=None):
    r = subprocess.run(
        [str(BENCH), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd or str(ROOT),
        timeout=30,
    )
    return r.returncode, r.stdout, r.stderr


def test_help():
    rc, out, err = run(["--help"])
    assert rc == 0, f"--help exited {rc}: {err}"
    for flag in ("--baseline", "--dry-run", "--gate", "--list", "--force"):
        assert flag in out, f"help missing {flag}"
    print("  [test_help] OK")


def test_list_shows_required_gates():
    rc, out, err = run(["--list"])
    assert rc == 0, err
    # Exact gate names must appear
    for name in ("hle", "gpqa-diamond", "mmlu-pro"):
        assert name in out, f"--list missing {name}"
    # Surface-level visibility of text-only filter
    assert "text-only" in out, "HLE text-only filter not surfaced in --list"
    # Kernel baseline reference must be visible
    assert "Kernel baseline" in out or "kernel" in out.lower()
    print("  [test_list_shows_required_gates] OK")


def test_baseline_dry_run_succeeds():
    rc, out, err = run(["--baseline", "--dry-run"])
    assert rc == 0, f"baseline --dry-run exited {rc}: {err}"
    assert "kernel baseline" in out.lower()
    # All three required gates must be reported
    for g in ("hle", "gpqa-diamond", "mmlu-pro"):
        assert g in out, f"baseline dry-run missing {g}"
    assert "text-only" in out, "HLE text-only filter not reported on dry-run"
    print("  [test_baseline_dry_run_succeeds] OK")


def test_agent_requires_name():
    rc, out, err = run([])
    assert rc != 0, "empty invocation must fail"
    assert "agent" in (out + err).lower() or "required" in (out + err).lower()
    print("  [test_agent_requires_name] OK")


def test_unknown_gate_errors():
    rc, out, err = run(["somebody", "--gate", "bogus-gate-name", "--dry-run"])
    assert rc != 0, "unknown gate must exit non-zero"
    combined = out + err
    assert "no gate named" in combined.lower() or "bogus" in combined.lower()
    print("  [test_unknown_gate_errors] OK")


def test_agent_dry_run_names_filter():
    rc, out, err = run(["alice", "--dry-run"])
    # dry-run of agent gates should report each with its config
    # In dry-run we don't require stamps, so this should succeed
    assert rc == 0, f"agent --dry-run exited {rc}: {err}"
    assert "hle" in out
    assert "text-only" in out
    print("  [test_agent_dry_run_names_filter] OK")


def test_v01_scaffold_blocks_boot():
    """A real (non-dry-run) invocation in v0.1 MUST fail the boot gate —
    benchmark execution is v0.2 scope; until then, unproven capacity is
    unfit capacity. A regression that accidentally returns success here
    would let untested agents boot."""
    # Use a sandboxed HOME so we don't touch any real stamps
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "HOME": td}
        rc, out, err = run(["--baseline"], env=env)
        assert rc != 0, (
            "v0.1 scaffold must fail baseline — otherwise untested "
            "backends would be admitted. Got rc=0.\n" + out + err
        )
        assert "scaffold" in (out + err).lower() or "unproven" in (out + err).lower() \
            or "failed" in (out + err).lower(), \
            "failure mode must be named, not silent"
    print("  [test_v01_scaffold_blocks_boot] OK")


if __name__ == "__main__":
    test_help()
    test_list_shows_required_gates()
    test_baseline_dry_run_succeeds()
    test_agent_requires_name()
    test_unknown_gate_errors()
    test_agent_dry_run_names_filter()
    test_v01_scaffold_blocks_boot()
    print("ALL REASONING-BENCH CLI TESTS PASS")
