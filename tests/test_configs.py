#!/usr/bin/env python3
"""Validate shipped config files parse correctly and satisfy schema requirements.

These are structural tests: YAML must parse, required fields must be present,
systemd units must have the hard-stop `ExecStartPre=nex-reasoning-bench`
gating in place. A regression here silently breaks the boot contract.
"""
import configparser
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pyyaml not installed; skipping config tests", file=sys.stderr)
    sys.exit(77)  # skip code

ROOT = Path(__file__).resolve().parent.parent


def test_reasoning_benchmarks_yaml():
    cfg = yaml.safe_load((ROOT / "config/reasoning-benchmarks.example.yaml").read_text())
    assert "reasoning_gates" in cfg, "missing reasoning_gates"
    gates = cfg["reasoning_gates"]
    assert len(gates) >= 3, f"expected at least 3 gates, got {len(gates)}"

    names = {g["name"] for g in gates}
    required = {"hle", "gpqa-diamond", "mmlu-pro"}
    assert required.issubset(names), f"missing gates: {required - names}"

    # HLE must be text-only
    hle = next(g for g in gates if g["name"] == "hle")
    assert hle.get("filter") == "text-only", "HLE gate must filter to text-only"
    assert hle.get("weight") == "critical", "HLE must be critical weight"
    assert hle.get("threshold_pct", 0) >= 10, "HLE threshold should be at least 10%"

    # Every gate must have a numeric threshold and a weight
    for g in gates:
        assert isinstance(g.get("threshold_pct"), (int, float)), f"{g['name']}: threshold_pct missing/non-numeric"
        assert g.get("weight") in ("critical", "high", "medium"), f"{g['name']}: weight must be one of critical/high/medium"

    # kernel_baseline must reference only valid gate names
    kb = cfg.get("kernel_baseline", {})
    required_gates = set(kb.get("required_gates", []))
    assert required_gates, "kernel_baseline.required_gates must be non-empty"
    assert required_gates.issubset(names), f"kernel_baseline references unknown gates: {required_gates - names}"

    # revalidation_triggers must include agent_backend_change and a stamp_age_days entry
    rv = cfg.get("revalidation_triggers", [])
    str_triggers = {t for t in rv if isinstance(t, str)}
    assert "agent_backend_change" in str_triggers, "must trigger on agent_backend_change"
    assert "kernel_backend_change" in str_triggers, "must trigger on kernel_backend_change"
    assert any(isinstance(t, dict) and "stamp_age_days" in t for t in rv), "must have stamp_age_days trigger"

    # Cost cap must be present and reasonable
    assert "max_cost_per_fit_test_usd" in cfg, "missing cost cap"
    assert 0 < cfg["max_cost_per_fit_test_usd"] <= 10.0, "cost cap must be in (0, 10] USD"

    print("  [test_reasoning_benchmarks_yaml] OK")


def test_hitl_yaml():
    path = ROOT / "config/hitl.example.yaml"
    assert path.exists(), "hitl.example.yaml missing"
    cfg = yaml.safe_load(path.read_text())
    assert isinstance(cfg, dict), "hitl config must be a dict"
    # Consultation-domain presence check — HITL's core contract
    expected_any = {"principal", "consultation_domains", "hitl"}
    assert any(k in cfg for k in expected_any), \
        f"hitl config must define one of {expected_any}; got {list(cfg.keys())}"
    print("  [test_hitl_yaml] OK")


def test_persona_yamls():
    for persona in (ROOT / "templates/personas").glob("*.yaml"):
        cfg = yaml.safe_load(persona.read_text())
        assert isinstance(cfg, dict), f"{persona.name} must be a dict"
        print(f"  [test_persona_yaml {persona.name}] OK")


def test_systemd_units_gate_on_reasoning_bench():
    """Each unit must declare ExecStartPre=nex-reasoning-bench so an agent
    whose reasoning gate fails literally cannot boot."""
    units = list((ROOT / "systemd").glob("*.service"))
    assert units, "no systemd units found"

    for unit in units:
        text = unit.read_text()
        # Required sections
        for section in ("[Unit]", "[Service]", "[Install]"):
            assert section in text, f"{unit.name}: missing {section}"
        assert "ExecStart=" in text, f"{unit.name}: missing ExecStart"

        # Hard-stop pre-check — both baseline AND agent stamp must be verified
        assert "ExecStartPre=" in text, f"{unit.name}: no ExecStartPre"
        pre_lines = [ln for ln in text.splitlines() if ln.startswith("ExecStartPre=")]
        pre_blob = "\n".join(pre_lines)
        assert "nex-reasoning-bench" in pre_blob, \
            f"{unit.name}: ExecStartPre must invoke nex-reasoning-bench"
        assert "--baseline" in pre_blob, \
            f"{unit.name}: must gate on kernel baseline (--baseline)"
        # Agent stamp check must reference the instance name %i
        assert "%i" in pre_blob, \
            f"{unit.name}: must validate the specific agent (%i)"

        # Also parse structurally via configparser
        c = configparser.ConfigParser(strict=False)
        c.read(unit)
        assert "Unit" in c.sections()
        assert "Service" in c.sections()
        assert "Install" in c.sections()

        print(f"  [test_systemd_unit {unit.name}] OK")


def test_claude_md_template_has_placeholders():
    """The identity template must contain {{AGENT_NAME}} and {{PRINCIPAL_NAME}}
    placeholders so nex-init's sed-substitution works."""
    tmpl = ROOT / "templates/identity/CLAUDE.md.template"
    if not tmpl.exists():
        # Alternate path
        candidates = list((ROOT / "templates/identity").glob("*.template"))
        assert candidates, "no CLAUDE.md.template found under templates/identity/"
        tmpl = candidates[0]

    text = tmpl.read_text()
    assert "{{AGENT_NAME}}" in text, "template missing {{AGENT_NAME}} placeholder"
    # Principal name placeholder is also common; accept either name
    has_principal = "{{PRINCIPAL_NAME}}" in text or "{{PRINCIPAL}}" in text
    assert has_principal, "template missing {{PRINCIPAL_NAME}} or {{PRINCIPAL}} placeholder"
    print("  [test_claude_md_template_has_placeholders] OK")


if __name__ == "__main__":
    test_reasoning_benchmarks_yaml()
    test_hitl_yaml()
    test_persona_yamls()
    test_systemd_units_gate_on_reasoning_bench()
    test_claude_md_template_has_placeholders()
    print("ALL CONFIG TESTS PASS")
