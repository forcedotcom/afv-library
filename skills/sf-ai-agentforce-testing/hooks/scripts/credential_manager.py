#!/usr/bin/env python3
"""
Credential Manager — Persistent ECA Credentials for Agentforce Testing

Manages External Client App (ECA) credentials on disk at ~/.sfagent/,
organized by org alias and ECA application name. Supports discovery,
load/save, OAuth validation, and environment export.

Directory layout:
    ~/.sfagent/
    ├── .gitignore          ("*" — prevents accidental commits)
    ├── {Org-Alias}/        (org alias — case-sensitive)
    │   └── {ECA-Name}/     (ECA app name — use `discover` to find)
    │       └── credentials.env
    └── Other-Org/
        └── ...

credentials.env format (with export prefix for shell sourcing):
    export SF_MY_DOMAIN=domain.my.salesforce.com
    export SF_CONSUMER_KEY=3MVG9...
    export SF_CONSUMER_SECRET=ABC...

Usage:
    # Discover orgs and ECAs (ALWAYS run this first to find actual names)
    python3 credential_manager.py discover
    python3 credential_manager.py discover --org-alias {org}

    # Load credentials (secrets masked in output)
    python3 credential_manager.py load --org-alias {org} --eca-name {eca}

    # Save credentials
    python3 credential_manager.py save --org-alias {org} --eca-name {eca} \\
        --domain myorg.my.salesforce.com \\
        --consumer-key 3MVG9... --consumer-secret ABC123...

    # Validate OAuth flow
    python3 credential_manager.py validate --org-alias {org} --eca-name {eca}

    # Source credentials in shell (export prefix makes vars available to subprocesses)
    source ~/.sfagent/{org}/{eca}/credentials.env

Programmatic usage:
    from credential_manager import load_credentials, validate_credentials, export_env

    creds = load_credentials("{org}", "{eca}")
    result = validate_credentials(creds)
    if result["valid"]:
        export_env(creds)

Dependencies:
    Python 3.8+ standard library only (no pip dependencies)

Author: Jag Valaiyapathy
License: MIT
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

SFAGENT_DIR_NAME = ".sfagent"
CREDENTIALS_FILE = "credentials.env"
REQUIRED_KEYS = ("SF_MY_DOMAIN", "SF_CONSUMER_KEY", "SF_CONSUMER_SECRET")

DIR_MODE = 0o700   # owner rwx only
FILE_MODE = 0o600  # owner rw only


# ═══════════════════════════════════════════════════════════════════════════
# Filesystem Helpers
# ═══════════════════════════════════════════════════════════════════════════

def get_sfagent_root() -> Path:
    """Return the ~/.sfagent root directory, creating it if needed.

    Creates the directory with 0700 permissions and writes a .gitignore
    containing "*" to prevent accidental credential commits.

    Returns:
        Path to ~/.sfagent
    """
    root = Path.home() / SFAGENT_DIR_NAME
    if not root.exists():
        root.mkdir(mode=DIR_MODE)

    # Ensure .gitignore exists
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n")
        os.chmod(gitignore, FILE_MODE)

    return root


def discover_orgs() -> List[str]:
    """List all org aliases (subdirectories) under ~/.sfagent/.

    Returns:
        Sorted list of org alias directory names.
    """
    root = get_sfagent_root()
    return sorted(
        d.name for d in root.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )


def discover_ecas(org_alias: str) -> List[str]:
    """List all ECA app directories under a given org alias.

    Args:
        org_alias: Salesforce org alias (case-sensitive).

    Returns:
        Sorted list of ECA directory names.

    Raises:
        FileNotFoundError: If the org alias directory does not exist.
    """
    org_dir = get_sfagent_root() / org_alias
    if not org_dir.is_dir():
        raise FileNotFoundError(f"Org directory not found: {org_dir}")
    return sorted(
        d.name for d in org_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )


# ═══════════════════════════════════════════════════════════════════════════
# Credential I/O
# ═══════════════════════════════════════════════════════════════════════════

def load_credentials(org_alias: str, eca_name: str) -> Dict[str, str]:
    """Parse credentials.env for a given org/ECA combination.

    Reads KEY=VALUE lines, skipping comments (#) and blank lines.

    Args:
        org_alias: Salesforce org alias (case-sensitive).
        eca_name: ECA application name.

    Returns:
        Dict with keys SF_MY_DOMAIN, SF_CONSUMER_KEY, SF_CONSUMER_SECRET.

    Raises:
        FileNotFoundError: If credentials.env does not exist.
        ValueError: If any required key is missing.
    """
    cred_file = get_sfagent_root() / org_alias / eca_name / CREDENTIALS_FILE
    if not cred_file.is_file():
        raise FileNotFoundError(f"Credentials file not found: {cred_file}")

    creds: Dict[str, str] = {}
    for line in cred_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        # Strip optional 'export ' prefix for shell-compatible credentials.env
        if line.startswith("export "):
            line = line[7:]
        key, _, value = line.partition("=")
        creds[key.strip()] = value.strip()

    missing = [k for k in REQUIRED_KEYS if not creds.get(k)]
    if missing:
        raise ValueError(f"Missing required keys in {cred_file}: {', '.join(missing)}")

    return creds


def save_credentials(
    org_alias: str,
    eca_name: str,
    domain: str,
    key: str,
    secret: str,
) -> Path:
    """Write credentials.env for a given org/ECA combination.

    Creates org and ECA directories (0700) as needed. The credentials
    file is written with 0600 permissions.

    Args:
        org_alias: Salesforce org alias (case-sensitive).
        eca_name: ECA application name.
        domain: Salesforce My Domain (e.g. myorg.my.salesforce.com).
        key: ECA Consumer Key.
        secret: ECA Consumer Secret.

    Returns:
        Path to the written credentials.env file.
    """
    root = get_sfagent_root()
    org_dir = root / org_alias
    eca_dir = org_dir / eca_name

    # Create directories with secure permissions
    for d in (org_dir, eca_dir):
        if not d.exists():
            d.mkdir(mode=DIR_MODE)

    cred_file = eca_dir / CREDENTIALS_FILE
    content = (
        f"# credentials.env — managed by credential_manager.py\n"
        f"export SF_MY_DOMAIN={domain}\n"
        f"export SF_CONSUMER_KEY={key}\n"
        f"export SF_CONSUMER_SECRET={secret}\n"
    )
    cred_file.write_text(content)
    os.chmod(cred_file, FILE_MODE)

    return cred_file


# ═══════════════════════════════════════════════════════════════════════════
# OAuth Validation
# ═══════════════════════════════════════════════════════════════════════════

def validate_credentials(creds: Dict[str, str]) -> Dict[str, Any]:
    """Test an OAuth Client Credentials flow against the Salesforce token endpoint.

    Uses the same urllib pattern as agent_api_client.py (lines 387-424).

    Args:
        creds: Dict with SF_MY_DOMAIN, SF_CONSUMER_KEY, SF_CONSUMER_SECRET.

    Returns:
        Dict with keys:
            valid (bool): Whether authentication succeeded.
            error (str | None): Error message if failed.
            token_length (int | None): Length of the access token if succeeded.
    """
    domain = creds.get("SF_MY_DOMAIN", "")
    consumer_key = creds.get("SF_CONSUMER_KEY", "")
    consumer_secret = creds.get("SF_CONSUMER_SECRET", "")

    if not all([domain, consumer_key, consumer_secret]):
        return {"valid": False, "error": "Missing required credential fields", "token_length": None}

    # Ensure domain has https:// prefix for the token URL
    if domain.startswith("https://"):
        token_url = f"{domain}/services/oauth2/token"
    elif domain.startswith("http://"):
        token_url = domain.replace("http://", "https://") + "/services/oauth2/token"
    else:
        token_url = f"https://{domain}/services/oauth2/token"

    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": consumer_key,
        "client_secret": consumer_secret,
    }).encode("utf-8")

    req = urllib.request.Request(
        token_url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            error_data = json.loads(body)
            msg = error_data.get("error_description", error_data.get("error", body))
        except json.JSONDecodeError:
            msg = body
        return {"valid": False, "error": f"HTTP {e.code}: {msg}", "token_length": None}
    except urllib.error.URLError as e:
        return {"valid": False, "error": f"Connection error: {e.reason}", "token_length": None}
    except Exception as e:
        return {"valid": False, "error": str(e), "token_length": None}

    access_token = result.get("access_token")
    if not access_token:
        return {"valid": False, "error": "No access_token in response", "token_length": None}

    return {"valid": True, "error": None, "token_length": len(access_token)}


# ═══════════════════════════════════════════════════════════════════════════
# Environment Export
# ═══════════════════════════════════════════════════════════════════════════

def export_env(creds: Dict[str, str]) -> None:
    """Set os.environ from a credentials dict.

    Useful before spawning subprocesses that read SF_MY_DOMAIN,
    SF_CONSUMER_KEY, and SF_CONSUMER_SECRET from the environment.

    Args:
        creds: Dict with credential key-value pairs.
    """
    for key, value in creds.items():
        os.environ[key] = value


# ═══════════════════════════════════════════════════════════════════════════
# Display Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _mask_secret(value: str) -> str:
    """Mask a secret value, showing only the first 3 and last 3 characters.

    Short values (≤8 chars) are fully masked.

    Args:
        value: The secret string to mask.

    Returns:
        Masked string like "ABC...XYZ".
    """
    if len(value) <= 8:
        return "***"
    return f"{value[:3]}...{value[-3:]}"


def _creds_for_display(creds: Dict[str, str]) -> Dict[str, str]:
    """Return a copy of credentials with secrets masked for safe display.

    SF_CONSUMER_SECRET is always masked. SF_CONSUMER_KEY shows first/last 3.

    Args:
        creds: Raw credentials dict.

    Returns:
        New dict with masked sensitive values.
    """
    display = dict(creds)
    if "SF_CONSUMER_SECRET" in display:
        display["SF_CONSUMER_SECRET"] = _mask_secret(display["SF_CONSUMER_SECRET"])
    if "SF_CONSUMER_KEY" in display:
        display["SF_CONSUMER_KEY"] = _mask_secret(display["SF_CONSUMER_KEY"])
    return display


# ═══════════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser with discover/load/save/validate subcommands."""
    parser = argparse.ArgumentParser(
        description="Manage persistent ECA credentials for Agentforce testing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- discover ---
    p_discover = subparsers.add_parser(
        "discover",
        help="List orgs or ECAs under an org",
    )
    p_discover.add_argument("--org-alias", help="Org alias to list ECAs for")

    # --- load ---
    p_load = subparsers.add_parser(
        "load",
        help="Load and display credentials (secrets masked)",
    )
    p_load.add_argument("--org-alias", required=True, help="Salesforce org alias")
    p_load.add_argument("--eca-name", required=True, help="ECA application name")

    # --- save ---
    p_save = subparsers.add_parser(
        "save",
        help="Save credentials to disk",
    )
    p_save.add_argument("--org-alias", required=True, help="Salesforce org alias")
    p_save.add_argument("--eca-name", required=True, help="ECA application name")
    p_save.add_argument("--domain", required=True, help="Salesforce My Domain")
    p_save.add_argument("--consumer-key", required=True, help="ECA Consumer Key")
    p_save.add_argument("--consumer-secret", required=True, help="ECA Consumer Secret")

    # --- validate ---
    p_validate = subparsers.add_parser(
        "validate",
        help="Test OAuth Client Credentials flow",
    )
    p_validate.add_argument("--org-alias", required=True, help="Salesforce org alias")
    p_validate.add_argument("--eca-name", required=True, help="ECA application name")

    return parser


def main() -> int:
    """CLI entry point. Returns 0 on success, 1 on error."""
    parser = _build_parser()
    args = parser.parse_args()

    try:
        if args.command == "discover":
            if args.org_alias:
                ecas = discover_ecas(args.org_alias)
                print(json.dumps({"org_alias": args.org_alias, "ecas": ecas}, indent=2))
            else:
                orgs = discover_orgs()
                print(json.dumps({"orgs": orgs}, indent=2))

        elif args.command == "load":
            creds = load_credentials(args.org_alias, args.eca_name)
            print(json.dumps(_creds_for_display(creds), indent=2))

        elif args.command == "save":
            path = save_credentials(
                org_alias=args.org_alias,
                eca_name=args.eca_name,
                domain=args.domain,
                key=args.consumer_key,
                secret=args.consumer_secret,
            )
            print(json.dumps({"saved": str(path)}, indent=2))

        elif args.command == "validate":
            creds = load_credentials(args.org_alias, args.eca_name)
            result = validate_credentials(creds)
            print(json.dumps(result, indent=2))

    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1
    except ValueError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {e}"}), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
