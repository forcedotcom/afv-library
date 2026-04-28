"""
LSP Engine for sf-skills
========================

This module provides Language Server Protocol (LSP) integration for
Salesforce development skills in Claude Code.

Currently supports:
- Agent Script (.agent files) via Salesforce VS Code extension

Usage:
    from shared.lsp_engine import LSPClient, get_diagnostics

    # Get diagnostics for a file
    diagnostics = get_diagnostics('/path/to/file.agent')

    # Or use the client directly
    client = LSPClient()
    if client.is_available():
        result = client.validate_file('/path/to/file.agent')
"""

from .lsp_client import LSPClient, get_diagnostics, is_lsp_available
from .diagnostics import DiagnosticParser, format_diagnostics_for_claude

__version__ = "1.0.0"
__all__ = [
    "LSPClient",
    "get_diagnostics",
    "is_lsp_available",
    "DiagnosticParser",
    "format_diagnostics_for_claude",
]
