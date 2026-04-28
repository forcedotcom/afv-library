#!/usr/bin/env python3
"""
LSP Client for Language Server Protocol
========================================

This module provides a Python interface to LSP servers
for use in Claude Code hooks.

Features:
- Works with any LSP server (Agent Script, Apex, etc.)
- Communicates via JSON-RPC over stdio
- Returns parsed diagnostics for validation hooks
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any


# Language ID mapping based on file extension
EXTENSION_TO_LANGUAGE = {
    ".agent": "agentscript",
    ".cls": "apex",
    ".trigger": "apex",
    ".apex": "apex",
    ".js": "javascript",
    ".html": "html",
    ".css": "css",
}

# Wrapper script mapping based on language
LANGUAGE_TO_WRAPPER = {
    "agentscript": "agentscript_wrapper.sh",
    "apex": "apex_wrapper.sh",
    "javascript": "lwc_wrapper.sh",
    "html": "lwc_wrapper.sh",
    "css": "lwc_wrapper.sh",
}


class LSPClient:
    """Client for communicating with an LSP server."""

    def __init__(self, wrapper_path: Optional[str] = None, language_id: Optional[str] = None):
        """
        Initialize the LSP client.

        Args:
            wrapper_path: Path to the LSP wrapper script. If None, auto-discovers.
            language_id: Language ID for the LSP server. If None, auto-detects from file extension.
        """
        self.language_id = language_id
        self.wrapper_path = wrapper_path or self._find_wrapper(language_id)
        self._server_process: Optional[subprocess.Popen] = None
        self._request_id = 0

    def _detect_language_id(self, file_path: str) -> str:
        """Detect language ID from file extension."""
        ext = Path(file_path).suffix.lower()
        return EXTENSION_TO_LANGUAGE.get(ext, "apex")

    def _find_project_root(self, file_path: str) -> str:
        """
        Find the project root directory by looking for project markers.

        Walks up the directory tree looking for:
        - sfdx-project.json (Salesforce DX projects)
        - .git (git repository root)
        - package.json (Node.js projects)

        Falls back to the file's parent directory if no markers found.
        """
        current = Path(file_path).resolve().parent

        # Project markers in order of priority
        markers = ["sfdx-project.json", ".git", "package.json"]

        while current != current.parent:  # Stop at filesystem root
            for marker in markers:
                if (current / marker).exists():
                    return str(current)
            current = current.parent

        # Fallback: use file's parent directory
        return str(Path(file_path).parent)

    def _find_wrapper(self, language_id: Optional[str] = None) -> str:
        """Find the LSP wrapper script relative to this module."""
        module_dir = Path(__file__).parent

        # Determine which wrapper to use based on language
        wrapper_name = "agentscript_wrapper.sh"  # default
        if language_id and language_id in LANGUAGE_TO_WRAPPER:
            wrapper_name = LANGUAGE_TO_WRAPPER[language_id]

        wrapper = module_dir / wrapper_name
        if wrapper.exists():
            return str(wrapper)

        # Fallback: check common locations
        fallbacks = [
            Path.home() / ".claude" / "lsp" / wrapper_name,
            Path.home() / ".claude" / "plugins" / "marketplaces" / "sf-skills" / "shared" / "lsp-engine" / wrapper_name,
        ]
        for fallback in fallbacks:
            if fallback.exists():
                return str(fallback)

        raise FileNotFoundError(
            f"LSP wrapper script '{wrapper_name}' not found. Ensure the required VS Code extension is installed."
        )

    def is_available(self) -> bool:
        """Check if the LSP server is available."""
        try:
            # Quick check: can we find the wrapper?
            if not os.path.exists(self.wrapper_path):
                return False

            # Quick check: is it executable?
            if not os.access(self.wrapper_path, os.X_OK):
                return False

            return True
        except Exception:
            return False

    def _next_request_id(self) -> int:
        """Generate the next request ID."""
        self._request_id += 1
        return self._request_id

    def _create_message(self, method: str, params: Dict[str, Any]) -> str:
        """Create a JSON-RPC message with Content-Length header."""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method,
            "params": params,
        }
        content = json.dumps(request)
        return f"Content-Length: {len(content)}\r\n\r\n{content}"

    def validate_file(self, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a file using the LSP server.

        Args:
            file_path: Path to the file to validate
            content: Optional file content (if None, reads from disk)

        Returns:
            Dict with 'success' boolean and 'diagnostics' list
        """
        import select
        import time

        if content is None:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Could not read file: {e}",
                    "diagnostics": [],
                }

        try:
            # Determine language ID and wrapper
            lang_id = self.language_id or self._detect_language_id(file_path)
            wrapper = self.wrapper_path

            # If no explicit wrapper was set and we have a language, find the right wrapper
            if not self.language_id and lang_id in LANGUAGE_TO_WRAPPER:
                wrapper = self._find_wrapper(lang_id)

            # Start the LSP server with unbuffered I/O
            process = subprocess.Popen(
                [wrapper, "--stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )

            def send_message(method: str, params: Dict, req_id: Optional[int] = None):
                """Send a JSON-RPC message to the LSP server."""
                msg = {"jsonrpc": "2.0", "method": method, "params": params}
                if req_id is not None:
                    msg["id"] = req_id
                content_bytes = json.dumps(msg).encode("utf-8")
                header = f"Content-Length: {len(content_bytes)}\r\n\r\n".encode("utf-8")
                process.stdin.write(header + content_bytes)
                process.stdin.flush()

            def send_response(req_id: int, result: Any):
                """Send a JSON-RPC response to the LSP server."""
                msg = {"jsonrpc": "2.0", "id": req_id, "result": result}
                content_bytes = json.dumps(msg).encode("utf-8")
                header = f"Content-Length: {len(content_bytes)}\r\n\r\n".encode("utf-8")
                process.stdin.write(header + content_bytes)
                process.stdin.flush()

            def handle_server_request(msg: Dict) -> bool:
                """
                Handle requests FROM the server that require a response.
                Returns True if the message was a request that was handled.
                """
                # Server requests have both 'id' and 'method' (no 'result')
                if "id" in msg and "method" in msg and "result" not in msg:
                    method = msg.get("method", "")
                    req_id = msg["id"]

                    if method == "workspace/configuration":
                        # LWC Language Server asks for TypeScript support config
                        # Return empty/default config for each requested item
                        items = msg.get("params", {}).get("items", [])
                        # Return null (default) for each config item requested
                        result = [None] * len(items)
                        send_response(req_id, result)
                        return True

                    elif method == "client/registerCapability":
                        # Server wants to register dynamic capabilities
                        send_response(req_id, None)
                        return True

                    elif method == "window/workDoneProgress/create":
                        # Server wants to create a progress indicator
                        send_response(req_id, None)
                        return True

                return False

            def read_responses(timeout: float = 3.0) -> List[Dict]:
                """Read LSP responses with Content-Length header parsing."""
                responses = []
                buffer = b""
                start = time.time()

                while time.time() - start < timeout:
                    ready, _, _ = select.select([process.stdout], [], [], 0.1)
                    if ready:
                        chunk = process.stdout.read(4096)
                        if not chunk:
                            break
                        buffer += chunk

                        # Parse complete messages
                        while b"Content-Length:" in buffer:
                            header_end = buffer.find(b"\r\n\r\n")
                            if header_end == -1:
                                break
                            header = buffer[:header_end].decode("utf-8")
                            try:
                                content_length = int(header.split(":")[1].strip())
                            except (ValueError, IndexError):
                                break
                            msg_start = header_end + 4
                            msg_end = msg_start + content_length
                            if len(buffer) < msg_end:
                                break
                            msg = buffer[msg_start:msg_end].decode("utf-8")
                            try:
                                parsed = json.loads(msg)
                                # Handle server requests that need responses
                                if not handle_server_request(parsed):
                                    # Not a handled request, add to responses
                                    responses.append(parsed)
                            except json.JSONDecodeError:
                                pass
                            buffer = buffer[msg_end:]
                    time.sleep(0.05)
                return responses

            # Initialize LSP
            # Note: LWC Language Server requires workspaceFolders pointing to project root
            # (where sfdx-project.json lives), not just the file's parent directory
            workspace_root = self._find_project_root(file_path)
            root_uri = f"file://{workspace_root}"
            init_params = {
                "processId": os.getpid(),
                "rootUri": root_uri,
                "rootPath": workspace_root,
                "workspaceFolders": [
                    {"uri": root_uri, "name": os.path.basename(workspace_root)}
                ],
                "capabilities": {
                    "textDocument": {
                        "publishDiagnostics": {"relatedInformation": True},
                    },
                    "workspace": {
                        "workspaceFolders": True,
                        "configuration": True,  # Support workspace/configuration requests
                    }
                },
            }
            send_message("initialize", init_params, self._next_request_id())
            time.sleep(0.3)
            read_responses(timeout=1)  # Read initialize response

            # Send initialized notification
            send_message("initialized", {})

            # Open document
            file_uri = f"file://{os.path.abspath(file_path)}"
            did_open_params = {
                "textDocument": {
                    "uri": file_uri,
                    "languageId": lang_id,
                    "version": 1,
                    "text": content,
                }
            }
            send_message("textDocument/didOpen", did_open_params)

            # Wait for diagnostics (async from server)
            # LWC Language Server needs more time than Apex LSP
            time.sleep(0.5)
            responses = read_responses(timeout=5)

            # Extract diagnostics from responses
            diagnostics = []
            for resp in responses:
                if resp.get("method") == "textDocument/publishDiagnostics":
                    params = resp.get("params", {})
                    for diag in params.get("diagnostics", []):
                        diagnostics.append({
                            "severity": diag.get("severity", 1),
                            "message": diag.get("message", "Unknown error"),
                            "range": diag.get("range", {}),
                            "source": diag.get("source", lang_id),
                            "code": diag.get("code", ""),
                        })

            # Clean shutdown
            send_message("shutdown", {}, self._next_request_id())
            send_message("exit", {})
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()

            return {
                "success": len(diagnostics) == 0,
                "diagnostics": diagnostics,
                "file_path": file_path,
            }

        except FileNotFoundError:
            return {
                "success": False,
                "error": "LSP wrapper script not found. Install VS Code Agent Script extension.",
                "diagnostics": [],
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "diagnostics": [],
            }

    def _parse_diagnostics(self, response: str) -> List[Dict[str, Any]]:
        """Parse diagnostics from LSP response."""
        diagnostics = []

        # Look for JSON-RPC responses
        try:
            # Split by Content-Length headers
            parts = response.split("Content-Length:")
            for part in parts:
                if not part.strip():
                    continue

                # Find JSON content after headers
                json_start = part.find("{")
                if json_start == -1:
                    continue

                json_content = part[json_start:]

                # Handle multiple JSON objects
                decoder = json.JSONDecoder()
                pos = 0
                while pos < len(json_content):
                    try:
                        obj, end_pos = decoder.raw_decode(json_content[pos:])
                        pos += end_pos

                        # Check for diagnostics notification
                        if obj.get("method") == "textDocument/publishDiagnostics":
                            params = obj.get("params", {})
                            for diag in params.get("diagnostics", []):
                                diagnostics.append({
                                    "severity": diag.get("severity", 1),
                                    "message": diag.get("message", "Unknown error"),
                                    "range": diag.get("range", {}),
                                    "source": diag.get("source", "agentscript"),
                                })
                    except json.JSONDecodeError:
                        break

        except Exception:
            pass  # Ignore parsing errors

        return diagnostics


def is_lsp_available() -> bool:
    """Check if the Agent Script LSP is available."""
    try:
        client = LSPClient()
        return client.is_available()
    except Exception:
        return False


def get_diagnostics(file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get diagnostics for a file.

    Args:
        file_path: Path to the .agent file
        content: Optional file content

    Returns:
        Dict with validation results
    """
    try:
        client = LSPClient()
        return client.validate_file(file_path, content)
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "diagnostics": [],
        }


if __name__ == "__main__":
    # CLI usage for testing
    if len(sys.argv) < 2:
        print("Usage: python lsp_client.py <file.agent>")
        sys.exit(1)

    result = get_diagnostics(sys.argv[1])
    print(json.dumps(result, indent=2))
