"""Tests for Data Cloud runtime installer behavior."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = ROOT / "tools" / "install.py"

_spec = importlib.util.spec_from_file_location("sf_skills_install_datacloud", INSTALLER_PATH)
_install = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_install)


def test_datacloud_runtime_repo_uses_public_fork() -> None:
    assert _install.DATACLOUD_RUNTIME_REPO == "https://github.com/Jaganpro/sf-cli-plugin-data360.git"


def test_build_finalize_install_args_keeps_datacloud_runtime_flag() -> None:
    args = _install._build_finalize_install_args(
        version="9.9.9",
        commit_sha="abc123",
        dry_run=True,
        force=True,
        called_from_bash=True,
        with_datacloud_runtime=True,
    )

    assert args[1] == str(_install.INSTALLER_FILE)
    assert "--_finalize-install" in args
    assert "--_version" in args
    assert "9.9.9" in args
    assert "--_commit-sha" in args
    assert "abc123" in args
    assert "--dry-run" in args
    assert "--force" in args
    assert "--called-from-bash" in args
    assert "--with-datacloud-runtime" in args


def test_cmd_install_defers_datacloud_runtime_until_updated_installer_restarts(
    monkeypatch, tmp_path: Path,
) -> None:
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True)
    installer_file = claude_dir / "sf-skills-install.py"

    monkeypatch.setattr(_install, "CLAUDE_DIR", claude_dir)
    monkeypatch.setattr(_install, "SKILLS_DIR", claude_dir / "skills")
    monkeypatch.setattr(_install, "HOOKS_DIR", claude_dir / "hooks")
    monkeypatch.setattr(_install, "LSP_DIR", claude_dir / "lsp-engine")
    monkeypatch.setattr(_install, "CODE_ANALYZER_DIR", claude_dir / "code_analyzer")
    monkeypatch.setattr(_install, "META_FILE", claude_dir / ".sf-skills.json")
    monkeypatch.setattr(_install, "INSTALLER_FILE", installer_file)

    def fake_download_repo_zip(target: Path) -> bool:
        source_dir = target / "sf-skills-test"
        (source_dir / "shared" / "hooks").mkdir(parents=True)
        (source_dir / "shared" / "lsp-engine").mkdir(parents=True)
        (source_dir / "shared" / "code_analyzer").mkdir(parents=True)
        (source_dir / "skills").mkdir(parents=True)
        (source_dir / "tools").mkdir(parents=True)
        (source_dir / "shared" / "hooks" / "skills-registry.json").write_text('{"version": "9.9.9"}')
        (source_dir / "tools" / "install.py").write_text("# updated installer bytes\n")
        return True

    monkeypatch.setattr(_install, "download_repo_zip", fake_download_repo_zip)
    monkeypatch.setattr(_install, "detect_state", lambda: (_install.InstallState.FRESH, None))
    monkeypatch.setattr(_install, "fetch_latest_commit_sha", lambda ref="main": "abc123def456")
    monkeypatch.setattr(_install, "cleanup_npx", lambda dry_run=False: 0)
    monkeypatch.setattr(_install, "cleanup_settings_hooks", lambda dry_run=False: 0)
    monkeypatch.setattr(_install, "cleanup_plugin_dirs", lambda dry_run=False: 0)
    monkeypatch.setattr(_install, "copy_skills", lambda source, dest, dry_run=False: 1)
    monkeypatch.setattr(_install, "copy_agents", lambda source, dest, dry_run=False: 0)
    monkeypatch.setattr(_install, "copy_hooks", lambda source, dest: 1)
    monkeypatch.setattr(_install, "copy_lsp_engine", lambda source, dest: 1)
    monkeypatch.setattr(_install, "copy_code_analyzer", lambda source, dest: 1)
    monkeypatch.setattr(_install, "_auto_acquire_lsp_servers", lambda dest: None)
    monkeypatch.setattr(_install, "ensure_code_analyzer_plugin", lambda: None)
    monkeypatch.setattr(_install, "ensure_prettier_apex", lambda: None)
    monkeypatch.setattr(_install, "install_sf_docs_runtime", lambda source_dir: (True, []))
    monkeypatch.setattr(_install, "write_metadata", lambda version, commit_sha=None: None)
    monkeypatch.setattr(_install, "touch_all_files", lambda path: None)

    datacloud_calls: list[bool] = []

    def fake_install_datacloud_runtime(dry_run: bool = False):
        datacloud_calls.append(dry_run)
        return True, ["runtime installed"]

    monkeypatch.setattr(_install, "install_datacloud_runtime", fake_install_datacloud_runtime)

    execv_calls: list[list[str]] = []

    def fake_execv(executable: str, args: list[str]) -> None:
        execv_calls.append(args)
        raise OSError("exec not available in test")

    monkeypatch.setattr(_install.os, "execv", fake_execv)

    subprocess_calls: list[list[str]] = []

    def fake_subprocess_run(args, check=False):
        subprocess_calls.append(args)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(_install.subprocess, "run", fake_subprocess_run)

    result = _install.cmd_install(dry_run=False, force=True, with_datacloud_runtime=True)

    assert result == 0
    assert datacloud_calls == []
    assert len(execv_calls) == 1
    assert "--with-datacloud-runtime" in execv_calls[0]
    assert len(subprocess_calls) == 1
    assert subprocess_calls[0] == execv_calls[0]
