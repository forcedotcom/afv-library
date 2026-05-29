"""Canonical path helpers for investigating-agentforce-architecture.

Layout:

    ~/.claude/data/investigating-agentforce-architecture/
    └── <org_id_15>/
        └── <agent_api_name>__<agent_version>/
            ├── <agent>_<ver>_metadata_tree.json     ← rendered tree
            └── .emit_ctx.json                       ← per-run shell ctx

Validation strategy
-------------------
The three "agent-identity" segments (org_id_15, agent_api_name, agent_version)
are validated by the regex helpers in the sibling ``fs_guard`` module. Any
segment containing ``..``, ``/``, or characters outside its regex charclass
raises ``PathValidationError`` — direct ``Path`` composition from unvalidated
input would be a path-traversal vulnerability and is prohibited.
"""
from __future__ import annotations

from pathlib import Path

from . import fs_guard


# -----------------------------------------------------------------------------
# Roots
# -----------------------------------------------------------------------------

DATA_ROOT: Path = (
    Path.home() / ".claude" / "data" / "investigating-agentforce-architecture"
)
CACHE_ROOT: Path = (
    Path.home() / ".claude" / "cache" / "investigating-agentforce-architecture"
)


class PathValidationError(ValueError):
    """Raised when a path segment fails validation.

    Wraps fs_guard's ``ValidationError`` so callers have a single exception
    type to catch.
    """

    def __init__(self, label: str, reason: str) -> None:
        self.label = label
        self.reason = reason
        super().__init__(f"{label}: {reason}")


# -----------------------------------------------------------------------------
# Validation helpers
# -----------------------------------------------------------------------------


def _validate_agent_triple(
    org_id_15: str, agent_api_name: str, agent_version: str
) -> None:
    """Validate the three identity segments. Raises PathValidationError on
    failure, wrapping fs_guard's ValidationError so callers don't need to
    know about fs_guard internals."""
    try:
        fs_guard.validate_org_id_15(org_id_15, label="org_id_15")
        fs_guard.validate_api_name(agent_api_name, label="agent_api_name")
        fs_guard.validate_agent_version(agent_version, label="agent_version")
    except fs_guard.ValidationError as e:
        raise PathValidationError(e.label, e.reason) from e


# -----------------------------------------------------------------------------
# Path builders
# -----------------------------------------------------------------------------


def agent_dir(
    org_id_15: str, agent_api_name: str, agent_version: str
) -> Path:
    """Return ``DATA_ROOT/<org_id_15>/<agent_api_name>__<agent_version>/``.

    All three segments are regex-validated before being joined.
    """
    _validate_agent_triple(org_id_15, agent_api_name, agent_version)
    return DATA_ROOT / org_id_15 / f"{agent_api_name}__{agent_version}"


def architecture_tree_path(
    org_id_15: str, agent_api_name: str, agent_version: str
) -> Path:
    """Return the path to the rendered metadata tree JSON.

    Filename convention: ``<agent_api_name>_<agent_version>_metadata_tree.json``.
    """
    base = agent_dir(org_id_15, agent_api_name, agent_version)
    return base / f"{agent_api_name}_{agent_version}_metadata_tree.json"


def architecture_emit_ctx_path(
    org_id_15: str, agent_api_name: str, agent_version: str
) -> Path:
    """Return the path to the per-run ``.emit_ctx.json``.

    The file is dotfile-named to signal per-run shell state.
    """
    base = agent_dir(org_id_15, agent_api_name, agent_version)
    return base / ".emit_ctx.json"
