#!/usr/bin/env python3
"""
LSP Server Acquisition Tool
============================
Downloads Apex and AgentScript language servers directly from the VS Code
Marketplace, eliminating the need for a VS Code installation.

The VS Code extensions are distributed as .vsix files (ZIP archives). This
script downloads them and extracts only the language server binaries:

  Apex:        extension/dist/apex-jorje-lsp.jar  → servers/apex/
  AgentScript: extension/server/**                → servers/agentscript/

Usage:
    python3 lsp-acquire.py                  # Download all servers
    python3 lsp-acquire.py apex             # Download Apex server only
    python3 lsp-acquire.py agentscript      # Download AgentScript server only
    python3 lsp-acquire.py --check          # Dry-run: show what would be downloaded
    python3 lsp-acquire.py --status         # Show current cache info
    python3 lsp-acquire.py --force          # Re-download even if cached
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
SERVERS_DIR = SCRIPT_DIR / "servers"
MANIFEST_FILE = SERVERS_DIR / "manifest.json"

MARKETPLACE_API = (
    "https://marketplace.visualstudio.com/"
    "_apis/public/gallery/extensionquery"
)

# Extension metadata — maps our server names to VS Code Marketplace IDs and
# the paths inside the .vsix we need to extract.
SERVERS = {
    "apex": {
        "extension_id": "salesforce.salesforcedx-vscode-apex",
        "extract_rules": [
            # (vsix_path_prefix, local_relative_dest)
            ("extension/dist/apex-jorje-lsp.jar", "apex-jorje-lsp.jar"),
        ],
        "verify_file": "apex-jorje-lsp.jar",  # Must exist after extraction
    },
    "agentscript": {
        "extension_id": "salesforce.agent-script-language-client",
        "extract_rules": [
            # Extract the entire server/ tree
            ("extension/server/", ""),  # prefix match → flatten into dest
        ],
        "verify_file": "server.js",  # Must exist after extraction
    },
}

# ---------------------------------------------------------------------------
# Marketplace API
# ---------------------------------------------------------------------------


def query_marketplace(extension_id: str) -> dict:
    """Query VS Code Marketplace for latest extension version + download URL.

    Uses the same POST /extensionquery pattern as check_lsp_versions.sh.
    The flags value 914 (0x392) requests:
      IncludeFiles | IncludeVersions | IncludeLatestVersionOnly |
      Unpublished | IncludeInstallationTargets

    Returns dict with keys: version, download_url (or raises on failure).
    """
    payload = json.dumps({
        "filters": [{
            "criteria": [{"filterType": 7, "value": extension_id}],
        }],
        "flags": 914,
    }).encode("utf-8")

    req = urllib.request.Request(
        MARKETPLACE_API,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json;api-version=3.0-preview.1",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError) as exc:
        raise RuntimeError(
            f"Failed to query Marketplace for {extension_id}: {exc}"
        ) from exc

    # Navigate the response: results[0].extensions[0].versions[0]
    try:
        results = data["results"]
        extensions = results[0]["extensions"]
        ext = extensions[0]
        version_info = ext["versions"][0]
        version = version_info["version"]

        # Find the VSIX download URL from the files array
        download_url = None
        for f in version_info.get("files", []):
            if f.get("assetType") == "Microsoft.VisualStudio.Services.VSIXPackage":
                download_url = f["source"]
                break

        if not download_url:
            # Fallback: construct the standard download URL
            publisher, name = extension_id.split(".", 1)
            download_url = (
                f"https://marketplace.visualstudio.com/_apis/public/gallery/"
                f"publishers/{publisher}/vsextensions/{name}/{version}/vspackage"
            )

        return {"version": version, "download_url": download_url}
    except (KeyError, IndexError) as exc:
        raise RuntimeError(
            f"Unexpected Marketplace API response for {extension_id}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Download & Extract
# ---------------------------------------------------------------------------


def download_vsix(url: str, dest_path: Path) -> str:
    """Download .vsix to dest_path with streaming SHA256. Returns hex digest."""
    sha = hashlib.sha256()
    req = urllib.request.Request(url)

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(dest_path, "wb") as fp:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    fp.write(chunk)
                    sha.update(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = int(downloaded * 100 / total)
                        mb = downloaded / (1024 * 1024)
                        print(
                            f"\r  Downloading... {mb:.1f} MB ({pct}%)",
                            end="", flush=True,
                        )
            if total > 0:
                print()  # newline after progress
    except (urllib.error.URLError, OSError) as exc:
        raise RuntimeError(f"Download failed: {exc}") from exc

    return sha.hexdigest()


def extract_server(vsix_path: Path, server_name: str, dest_dir: Path) -> int:
    """Extract relevant files from .vsix into dest_dir.

    Returns the number of files extracted.
    """
    rules = SERVERS[server_name]["extract_rules"]
    count = 0

    with zipfile.ZipFile(vsix_path, "r") as zf:
        for member in zf.namelist():
            for vsix_prefix, local_dest in rules:
                if vsix_prefix.endswith("/"):
                    # Directory prefix match — extract subtree
                    if member.startswith(vsix_prefix) and not member.endswith("/"):
                        relative = member[len(vsix_prefix):]
                        out_path = dest_dir / local_dest / relative
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(out_path, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        count += 1
                else:
                    # Exact file match
                    if member == vsix_prefix:
                        out_path = dest_dir / local_dest
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(out_path, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        count += 1

    return count


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def load_manifest() -> dict:
    """Load servers/manifest.json, returning empty structure if missing."""
    if MANIFEST_FILE.exists():
        try:
            return json.loads(MANIFEST_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"schema_version": 1, "servers": {}}


def save_manifest(manifest: dict) -> None:
    """Write servers/manifest.json atomically."""
    SERVERS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2) + "\n")
    tmp.replace(MANIFEST_FILE)


# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------


def acquire_server(server_name: str, force: bool = False, check: bool = False) -> bool:
    """Download and cache a single LSP server. Returns True on success."""
    meta = SERVERS[server_name]
    ext_id = meta["extension_id"]
    dest_dir = SERVERS_DIR / server_name

    print(f"\n{'='*60}")
    print(f"  {server_name.upper()} Language Server")
    print(f"  Extension: {ext_id}")
    print(f"{'='*60}")

    # Query marketplace for latest version
    print(f"  Querying VS Code Marketplace...")
    try:
        info = query_marketplace(ext_id)
    except RuntimeError as exc:
        print(f"  ERROR: {exc}")
        return False

    latest_version = info["version"]
    download_url = info["download_url"]
    print(f"  Latest version: {latest_version}")

    # Check if we already have this version cached
    manifest = load_manifest()
    cached = manifest.get("servers", {}).get(server_name, {})
    cached_version = cached.get("extension_version", "")

    if cached_version == latest_version and not force:
        verify_path = dest_dir / meta["verify_file"]
        if verify_path.exists():
            print(f"  Already cached (version {cached_version})")
            if check:
                print(f"  [dry-run] Would skip — already up to date")
            return True

    if check:
        print(f"  [dry-run] Would download version {latest_version}")
        print(f"  [dry-run] URL: {download_url}")
        return True

    # Download .vsix to temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        vsix_path = Path(tmpdir) / f"{server_name}.vsix"
        print(f"  Downloading .vsix...")
        try:
            sha256 = download_vsix(download_url, vsix_path)
        except RuntimeError as exc:
            print(f"  ERROR: {exc}")
            return False

        print(f"  SHA256: {sha256[:16]}...")

        # Clean destination and extract
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        print(f"  Extracting server files...")
        count = extract_server(vsix_path, server_name, dest_dir)
        print(f"  Extracted {count} files to {dest_dir.relative_to(SCRIPT_DIR)}/")

    # Verify extraction
    verify_path = dest_dir / meta["verify_file"]
    if not verify_path.exists():
        print(f"  ERROR: Expected file not found: {meta['verify_file']}")
        print(f"  The extension format may have changed.")
        return False

    # Update manifest
    manifest = load_manifest()
    manifest.setdefault("servers", {})[server_name] = {
        "extension_id": ext_id,
        "extension_version": latest_version,
        "vsix_sha256": sha256,
        "acquired_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    save_manifest(manifest)
    print(f"  SUCCESS: {server_name} {latest_version} cached")

    return True


def show_status() -> None:
    """Display current cache information."""
    manifest = load_manifest()
    servers = manifest.get("servers", {})

    print(f"\nLSP Server Cache Status")
    print(f"{'='*60}")
    print(f"  Cache directory: {SERVERS_DIR}")
    print(f"  Manifest:        {MANIFEST_FILE}")
    print()

    if not servers:
        print("  No servers cached. Run: python3 lsp-acquire.py")
        print()
        return

    for name, info in servers.items():
        dest_dir = SERVERS_DIR / name
        verify_file = SERVERS.get(name, {}).get("verify_file", "")
        exists = (dest_dir / verify_file).exists() if verify_file else dest_dir.exists()

        status = "OK" if exists else "MISSING"
        icon = "✅" if exists else "❌"

        print(f"  {icon} {name}")
        print(f"     Extension: {info.get('extension_id', 'unknown')}")
        print(f"     Version:   {info.get('extension_version', 'unknown')}")
        print(f"     Acquired:  {info.get('acquired_at', 'unknown')}")
        print(f"     SHA256:    {info.get('vsix_sha256', 'unknown')[:32]}...")
        print(f"     Status:    {status}")
        print()


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download Salesforce LSP servers from VS Code Marketplace.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "servers",
        nargs="*",
        choices=list(SERVERS.keys()) + [[]],
        default=[],
        help="Servers to acquire (default: all)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-download even if cached version matches",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Dry-run: query marketplace but don't download",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show current cache information and exit",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Minimal output (for use from install.py)",
    )

    args = parser.parse_args()

    if args.status:
        show_status()
        return 0

    targets = args.servers if args.servers else list(SERVERS.keys())

    if not args.quiet:
        print("LSP Server Acquisition")
        print(f"Cache: {SERVERS_DIR}")
        if args.check:
            print("Mode: dry-run (no downloads)")
        elif args.force:
            print("Mode: force re-download")

    success_count = 0
    for server_name in targets:
        if acquire_server(server_name, force=args.force, check=args.check):
            success_count += 1

    print(f"\n{'─'*60}")
    print(f"  Result: {success_count}/{len(targets)} servers {'checked' if args.check else 'acquired'}")
    print(f"{'─'*60}")

    return 0 if success_count == len(targets) else 1


if __name__ == "__main__":
    sys.exit(main())
