"""Tests for installer-generated hook configuration."""
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = ROOT / "tools" / "install.py"

_spec = importlib.util.spec_from_file_location("sf_skills_install", INSTALLER_PATH)
_install = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_install)


def get_guardrail_prompt() -> str:
    """Return the PreToolUse prompt hook text."""
    hooks = _install.get_hooks_config()["PreToolUse"]
    prompt_hooks = [
        hook
        for hook_group in hooks
        for hook in hook_group.get("hooks", [])
        if hook.get("type") == "prompt"
    ]
    assert len(prompt_hooks) == 1
    return prompt_hooks[0]["prompt"]


def test_guardrail_prompt_is_advisory_only() -> None:
    prompt = get_guardrail_prompt()

    assert "Always ALLOW the command" in prompt
    assert "Never block, deny, or stop continuation" in prompt
    assert "advisory context only" in prompt


def test_guardrail_prompt_keeps_only_sfdx_and_api_version_checks() -> None:
    prompt = get_guardrail_prompt()

    assert "the command uses 'sfdx' instead of 'sf'" in prompt
    assert "API version below v56" in prompt

    assert "hardcoded credentials" not in prompt
    assert "API keys" not in prompt
    assert "secrets" not in prompt
    assert "hardcoded 15 or 18-character Salesforce record IDs" not in prompt
    assert "Hardcoded record ID detected" not in prompt


def test_prompt_hook_still_counts_as_sf_skills_hook() -> None:
    guardrail_hook_group = _install.get_hooks_config()["PreToolUse"][0]
    assert _install.is_sf_skills_hook(guardrail_hook_group) is True
