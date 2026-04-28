"""
Authentication module for sf-permissions.

Reuses existing sf CLI authentication to connect to Salesforce orgs.
No additional credentials required - leverages the user's existing
authenticated sessions.
"""

import subprocess
import json
import sys
from typing import Optional

from simple_salesforce import Salesforce


def get_sf_connection(target_org: Optional[str] = None) -> Salesforce:
    """
    Get a Salesforce connection using sf CLI authentication.

    This function retrieves the access token from an existing sf CLI
    authenticated session, avoiding the need to manage credentials separately.

    Args:
        target_org: Optional org alias or username. If not provided,
                   uses the default target org from sf CLI.

    Returns:
        Salesforce: An authenticated simple_salesforce.Salesforce instance.

    Raises:
        RuntimeError: If sf CLI is not installed or no org is authenticated.
        ValueError: If the specified org is not found.

    Example:
        >>> sf = get_sf_connection()  # Use default org
        >>> sf = get_sf_connection('my-sandbox')  # Use specific org
        >>> accounts = sf.query("SELECT Id, Name FROM Account LIMIT 5")
    """
    # Build the sf org display command
    cmd = ['sf', 'org', 'display', '--json']
    if target_org:
        cmd.extend(['--target-org', target_org])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
    except FileNotFoundError:
        raise RuntimeError(
            "sf CLI not found. Please install it: https://developer.salesforce.com/tools/salesforcecli"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("sf CLI command timed out. Check your network connection.")

    if result.returncode != 0:
        # Parse error message from sf CLI
        try:
            error_data = json.loads(result.stdout)
            error_msg = error_data.get('message', result.stderr)
        except json.JSONDecodeError:
            error_msg = result.stderr or result.stdout

        if 'No default org' in str(error_msg) or 'no default' in str(error_msg).lower():
            raise RuntimeError(
                "No default org set. Run 'sf org login web' to authenticate, "
                "or specify --target-org."
            )
        raise RuntimeError(f"sf CLI error: {error_msg}")

    # Parse the org info
    try:
        data = json.loads(result.stdout)
        org_info = data.get('result', {})
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse sf CLI output: {e}")

    # Extract required fields
    instance_url = org_info.get('instanceUrl')
    access_token = org_info.get('accessToken')

    if not instance_url or not access_token:
        raise RuntimeError(
            "Could not retrieve org credentials. "
            "Your session may have expired. Run 'sf org login web' to re-authenticate."
        )

    # Create and return the Salesforce connection
    return Salesforce(
        instance_url=instance_url,
        session_id=access_token
    )


def list_authenticated_orgs() -> list[dict]:
    """
    List all authenticated orgs from sf CLI.

    Returns:
        List of dicts with org info (alias, username, instanceUrl, isDefaultOrg, etc.)

    Example:
        >>> orgs = list_authenticated_orgs()
        >>> for org in orgs:
        ...     print(f"{org['alias']}: {org['username']}")
    """
    cmd = ['sf', 'org', 'list', '--json']

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        raise RuntimeError("sf CLI not found.")
    except subprocess.TimeoutExpired:
        raise RuntimeError("sf CLI command timed out.")

    if result.returncode != 0:
        return []

    try:
        data = json.loads(result.stdout)
        result_data = data.get('result', {})

        # Combine scratch orgs, sandboxes, and other orgs
        orgs = []
        for org_type in ['scratchOrgs', 'sandboxes', 'nonScratchOrgs', 'other']:
            orgs.extend(result_data.get(org_type, []))

        return orgs
    except json.JSONDecodeError:
        return []


def get_org_info(target_org: Optional[str] = None) -> dict:
    """
    Get detailed information about an org.

    Args:
        target_org: Optional org alias or username.

    Returns:
        Dict with org info including username, orgId, instanceUrl, etc.
    """
    cmd = ['sf', 'org', 'display', '--json']
    if target_org:
        cmd.extend(['--target-org', target_org])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        raise RuntimeError(f"Failed to get org info: {result.stderr}")

    data = json.loads(result.stdout)
    return data.get('result', {})


if __name__ == '__main__':
    # Quick test
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else None

    print("Testing sf CLI authentication...")
    try:
        sf = get_sf_connection(target)
        print(f"✅ Connected to: {sf.sf_instance}")

        # Quick API test
        identity = sf.query("SELECT Id, Username FROM User WHERE Id = 'me' LIMIT 1")
        if identity['records']:
            print(f"✅ Authenticated as: {identity['records'][0].get('Username', 'Unknown')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
