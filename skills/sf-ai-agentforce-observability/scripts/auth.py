"""
JWT Bearer authentication for Salesforce Data 360.

Uses certificate patterns from sf-connected-apps skill for secure
server-to-server authentication without user interaction.

Prerequisites (via sf-connected-apps skill):
1. Generate certificate: openssl req -x509 -sha256 -nodes ...
2. Create External Client App with JWT Bearer flow
3. Upload certificate to Salesforce
4. Store private key at ~/.sf/jwt/{org_alias}-agentforce-observability.key

Key Path Resolution (in order):
1. Explicit key_path parameter
2. App-specific: ~/.sf/jwt/{org_alias}-agentforce-observability.key
3. Generic fallback: ~/.sf/jwt/{org_alias}.key

Usage:
    # With app-specific key (recommended)
    auth = Data360Auth(org_alias="myorg", consumer_key="3MVG9...")

    # With explicit key path
    auth = Data360Auth(
        org_alias="myorg",
        consumer_key="3MVG9...",
        key_path=Path("~/.sf/jwt/custom.key").expanduser()
    )

    token = auth.get_token()
    # Use token for Data 360 API requests
"""

import json
import time
import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import jwt
import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


# Default paths for JWT keys
DEFAULT_KEY_DIR = Path.home() / ".sf" / "jwt"

# Salesforce OAuth endpoints
LOGIN_URL = "https://login.salesforce.com"
TEST_LOGIN_URL = "https://test.salesforce.com"

# Token refresh buffer (refresh 5 minutes before expiry)
TOKEN_REFRESH_BUFFER = 300


@dataclass
class OrgInfo:
    """Salesforce org connection information."""

    instance_url: str
    username: str
    access_token: Optional[str] = None
    is_sandbox: bool = False

    @property
    def login_url(self) -> str:
        """Get the appropriate login URL based on org type."""
        return TEST_LOGIN_URL if self.is_sandbox else LOGIN_URL


@dataclass
class Data360Auth:
    """
    JWT Bearer authentication for Data 360 Query API.

    This class handles:
    - JWT assertion generation using X.509 certificates
    - Token exchange with Salesforce OAuth endpoint
    - Token caching and automatic refresh
    - Integration with sf CLI for org discovery

    Attributes:
        org_alias: Salesforce CLI org alias
        consumer_key: Connected App consumer key (client ID)
        key_path: Path to private key file (default: ~/.sf/jwt/{org_alias}.key)

    Example:
        >>> auth = Data360Auth("prod", "3MVG9...")
        >>> token = auth.get_token()
        >>> headers = {"Authorization": f"Bearer {token}"}
    """

    org_alias: str
    consumer_key: Optional[str] = None
    key_path: Optional[Path] = None
    _token: Optional[str] = field(default=None, repr=False)
    _token_expiry: float = field(default=0, repr=False)
    _org_info: Optional[OrgInfo] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize key path and consumer key if not provided.

        Key path resolution order:
        1. Explicit key_path parameter (already set)
        2. App-specific: ~/.sf/jwt/{org_alias}-agentforce-observability.key
        3. Generic fallback: ~/.sf/jwt/{org_alias}.key

        Consumer key resolution order:
        1. Explicit consumer_key parameter (already set)
        2. App-specific file: ~/.sf/jwt/{org_alias}-agentforce-observability.consumer-key
        3. Generic file: ~/.sf/jwt/{org_alias}.consumer-key
        4. Environment variable: SF_{ORG_ALIAS}_CONSUMER_KEY or SF_CONSUMER_KEY
        """
        # Resolve key path
        if self.key_path is None:
            # Try app-specific key first
            app_specific_key = DEFAULT_KEY_DIR / f"{self.org_alias}-agentforce-observability.key"
            if app_specific_key.exists():
                self.key_path = app_specific_key
            else:
                # Fall back to generic org key
                self.key_path = DEFAULT_KEY_DIR / f"{self.org_alias}.key"

        # Resolve consumer key
        if self.consumer_key is None:
            self.consumer_key = self._load_consumer_key()

    def _load_consumer_key(self) -> str:
        """
        Load consumer key from file or environment.

        Resolution order:
        1. App-specific file: ~/.sf/jwt/{org_alias}-agentforce-observability.consumer-key
        2. Generic file: ~/.sf/jwt/{org_alias}.consumer-key
        3. Environment: SF_{ORG_ALIAS}_CONSUMER_KEY (uppercase, hyphens to underscores)
        4. Environment: SF_CONSUMER_KEY

        Returns:
            Consumer key string

        Raises:
            ValueError: If consumer key not found
        """
        import os

        # Try app-specific consumer key file
        app_specific = DEFAULT_KEY_DIR / f"{self.org_alias}-agentforce-observability.consumer-key"
        if app_specific.exists():
            return app_specific.read_text().strip()

        # Try generic consumer key file
        generic = DEFAULT_KEY_DIR / f"{self.org_alias}.consumer-key"
        if generic.exists():
            return generic.read_text().strip()

        # Try org-specific environment variable
        env_key = f"SF_{self.org_alias.upper().replace('-', '_')}_CONSUMER_KEY"
        if os.environ.get(env_key):
            return os.environ[env_key]

        # Try generic environment variable
        if os.environ.get("SF_CONSUMER_KEY"):
            return os.environ["SF_CONSUMER_KEY"]

        raise ValueError(
            f"Consumer key not found for {self.org_alias}. Provide via:\n"
            f"  1. File: {app_specific}\n"
            f"  2. Env: {env_key} or SF_CONSUMER_KEY\n"
            f"  3. Parameter: consumer_key='...'"
        )

    @property
    def org_info(self) -> OrgInfo:
        """Get org information from sf CLI (cached)."""
        if self._org_info is None:
            self._org_info = self._get_org_info()
        return self._org_info

    def _get_org_info(self) -> OrgInfo:
        """
        Retrieve org information using sf CLI.

        Returns:
            OrgInfo with instance URL and username

        Raises:
            RuntimeError: If sf CLI command fails
        """
        try:
            result = subprocess.run(
                ["sf", "org", "display", "--target-org", self.org_alias, "--json"],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)

            if data.get("status") != 0:
                raise RuntimeError(f"sf org display failed: {data.get('message', 'Unknown error')}")

            result_data = data.get("result", {})
            instance_url = result_data.get("instanceUrl", "")
            username = result_data.get("username", "")
            is_sandbox = result_data.get("isSandbox", False) or "sandbox" in instance_url.lower()

            return OrgInfo(
                instance_url=instance_url,
                username=username,
                is_sandbox=is_sandbox
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get org info: {e.stderr}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse sf CLI output: {e}")

    def _load_private_key(self) -> bytes:
        """
        Load private key from file.

        Returns:
            Private key bytes

        Raises:
            FileNotFoundError: If key file doesn't exist
        """
        if not self.key_path.exists():
            raise FileNotFoundError(
                f"Private key not found at {self.key_path}\n"
                f"Generate with: openssl req -x509 -sha256 -nodes -days 365 "
                f"-newkey rsa:2048 -keyout {self.key_path} -out {self.key_path.with_suffix('.crt')}"
            )

        return self.key_path.read_bytes()

    def _create_jwt_assertion(self) -> str:
        """
        Create a signed JWT assertion for the OAuth flow.

        The JWT includes:
        - iss: Consumer key (client ID)
        - sub: Salesforce username
        - aud: Login URL
        - exp: Expiration time (5 minutes from now)

        Returns:
            Signed JWT string
        """
        private_key_bytes = self._load_private_key()

        # Load the private key
        private_key = serialization.load_pem_private_key(
            private_key_bytes,
            password=None,
            backend=default_backend()
        )

        # Create JWT payload
        now = int(time.time())
        payload = {
            "iss": self.consumer_key,
            "sub": self.org_info.username,
            "aud": self.org_info.login_url,
            "exp": now + 300,  # 5 minute expiry
        }

        # Sign and return
        return jwt.encode(payload, private_key, algorithm="RS256")

    def _exchange_token(self, assertion: str) -> dict:
        """
        Exchange JWT assertion for access token.

        Args:
            assertion: Signed JWT assertion

        Returns:
            Token response dict with access_token, instance_url, etc.

        Raises:
            RuntimeError: If token exchange fails
        """
        token_url = f"{self.org_info.login_url}/services/oauth2/token"

        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        }

        with httpx.Client() as client:
            response = client.post(token_url, data=data)

            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("error_description", response.text)
                raise RuntimeError(f"Token exchange failed: {error_msg}")

            return response.json()

    def get_token(self, force_refresh: bool = False) -> str:
        """
        Get or refresh the access token.

        Tokens are cached and automatically refreshed before expiry.

        Args:
            force_refresh: Force token refresh even if current token is valid

        Returns:
            Valid access token string

        Example:
            >>> auth = Data360Auth("prod", "3MVG9...")
            >>> token = auth.get_token()
            >>> # Token is cached, subsequent calls are fast
            >>> token = auth.get_token()  # Returns cached token
        """
        # Check if current token is still valid
        if not force_refresh and self._token and time.time() < self._token_expiry:
            return self._token

        # Generate new JWT assertion
        assertion = self._create_jwt_assertion()

        # Exchange for access token
        token_response = self._exchange_token(assertion)

        self._token = token_response["access_token"]
        # Salesforce tokens typically expire in 1-2 hours; refresh 5 min early
        self._token_expiry = time.time() + 3600 - TOKEN_REFRESH_BUFFER

        # Update instance URL if different
        if token_response.get("instance_url"):
            self._org_info = OrgInfo(
                instance_url=token_response["instance_url"],
                username=self.org_info.username,
                is_sandbox=self.org_info.is_sandbox
            )

        return self._token

    def get_headers(self) -> dict:
        """
        Get HTTP headers with valid authorization.

        Returns:
            Dict with Authorization header

        Example:
            >>> auth = Data360Auth("prod", "3MVG9...")
            >>> headers = auth.get_headers()
            >>> response = httpx.get(url, headers=headers)
        """
        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
        }

    @property
    def instance_url(self) -> str:
        """Get the Salesforce instance URL."""
        return self.org_info.instance_url

    def test_connection(self) -> bool:
        """
        Test the authentication by making a simple Data 360 Query API call.

        Uses the v66.0 Query SQL endpoint to verify:
        1. Token is valid
        2. Data 360 is accessible
        3. User has cdp_query_api permissions

        Returns:
            True if authentication is successful

        Raises:
            RuntimeError: If authentication fails
        """
        token = self.get_token()

        # Test with a simple Data 360 Query API call (v66.0)
        url = f"{self.instance_url}/services/data/v66.0/ssot/query-sql"

        # Minimal query to test connectivity - just check if STDM DMO exists
        test_query = {
            "sql": "SELECT ssot__Id__c FROM ssot__AIAgentSession__dlm LIMIT 1"
        }

        with httpx.Client() as client:
            response = client.post(url, headers=self.get_headers(), json=test_query)

            if response.status_code in [200, 201]:
                return True
            elif response.status_code == 401:
                raise RuntimeError("Authentication failed: Invalid or expired token")
            elif response.status_code == 403:
                raise RuntimeError(
                    "Access denied: Ensure ECA has cdp_query_api scope and user has Data 360 permissions"
                )
            elif response.status_code == 400:
                # 400 might mean DMO doesn't exist (no Agentforce data) but API works
                error_text = response.text
                if "does not exist" in error_text.lower():
                    raise RuntimeError(
                        "Data 360 accessible but AIAgentSession DMO not found. "
                        "Ensure Agentforce Session Tracing is enabled."
                    )
                raise RuntimeError(f"Query error: {response.text}")
            else:
                raise RuntimeError(f"Connection test failed: {response.status_code} - {response.text}")


def get_auth_from_env(org_alias: str) -> Data360Auth:
    """
    Create Data360Auth from environment variables.

    Expects:
    - SF_CONSUMER_KEY or SF_{ORG_ALIAS}_CONSUMER_KEY environment variable
    - Private key at ~/.sf/jwt/{org_alias}.key

    Args:
        org_alias: Salesforce org alias

    Returns:
        Configured Data360Auth instance
    """
    import os

    # Try org-specific key first, then generic
    consumer_key = os.environ.get(f"SF_{org_alias.upper()}_CONSUMER_KEY")
    if not consumer_key:
        consumer_key = os.environ.get("SF_CONSUMER_KEY")

    if not consumer_key:
        raise ValueError(
            f"Consumer key not found. Set SF_CONSUMER_KEY or SF_{org_alias.upper()}_CONSUMER_KEY"
        )

    return Data360Auth(org_alias=org_alias, consumer_key=consumer_key)


# Backwards compatibility alias (Data Cloud → Data 360 rebrand, Oct 2025)
DataCloudAuth = Data360Auth
