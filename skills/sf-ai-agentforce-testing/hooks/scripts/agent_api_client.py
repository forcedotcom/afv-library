#!/usr/bin/env python3
"""
Agent Runtime API Client

Reusable Python client for the Salesforce Einstein Agent Runtime API v1.
Handles authentication (ECA Client Credentials), session lifecycle,
multi-turn messaging, and context variable injection.

Uses only Python standard library (urllib) — no pip dependencies.

Usage:
    from agent_api_client import AgentAPIClient

    client = AgentAPIClient(
        my_domain="your-domain.my.salesforce.com",
        consumer_key="...",
        consumer_secret="..."
    )

    # Option 1: Context manager (auto-ends session)
    with client.session(agent_id="0XxRM000...") as session:
        r1 = session.send("Hello, I need help")
        r2 = session.send("Cancel my appointment")
        print(r1.agent_text)
        print(r2.agent_text)

    # Option 2: With variables
    variables = [
        {"name": "$Context.AccountId", "type": "Text", "value": "001XXXXXXXXXXXX"},
        {"name": "$Context.EndUserLanguage", "type": "Text", "value": "en_US"},
    ]
    with client.session(agent_id="0Xx...", variables=variables) as session:
        r1 = session.send("What orders do I have?")

    # Option 3: Manual lifecycle
    session = client.start_session(agent_id="0Xx...")
    r1 = session.send("Hello")
    session.end()

Environment Variables (alternative to constructor args):
    SF_MY_DOMAIN         Salesforce My Domain URL
    SF_CONSUMER_KEY      ECA Consumer Key
    SF_CONSUMER_SECRET   ECA Consumer Secret

Author: Jag Valaiyapathy
License: MIT
"""

import json
import uuid
import urllib.request
import urllib.error
import urllib.parse
import os
import time
import sys
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class AgentMessage:
    """A single message from the agent response."""
    type: str
    id: str
    message: str
    feedback_id: str = ""
    plan_id: str = ""
    is_content_safe: bool = True
    result: list = field(default_factory=list)
    planner_surfaces: list = field(default_factory=list)
    cited_references: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.type}] {self.message[:80]}{'...' if len(self.message) > 80 else ''}"


@dataclass
class TurnResult:
    """Result of a single conversation turn (user message → agent response)."""
    sequence_id: int
    user_message: str
    agent_messages: List[AgentMessage]
    raw_response: dict
    elapsed_ms: float
    error: Optional[str] = None

    @property
    def agent_text(self) -> str:
        """Combined text from all Inform/Text agent messages."""
        return "\n".join(
            m.message for m in self.agent_messages
            if m.message and m.type in ("Inform", "Text", "Confirm")
        )

    @property
    def has_response(self) -> bool:
        """Whether the agent produced any text content."""
        return bool(self.agent_text.strip())

    @property
    def message_types(self) -> List[str]:
        """List of all message types in this turn's response."""
        return [m.type for m in self.agent_messages]

    @property
    def has_escalation(self) -> bool:
        """Whether this turn triggered an escalation or session end."""
        return any(
            m.type in ("Escalation", "SessionEnded")
            for m in self.agent_messages
        )

    @property
    def has_action_result(self) -> bool:
        """Whether any message contains action results."""
        return any(bool(m.result) for m in self.agent_messages)

    @property
    def action_results(self) -> List[dict]:
        """Collect all action result data from this turn."""
        results = []
        for m in self.agent_messages:
            if m.result:
                results.extend(m.result)
        return results

    @property
    def is_error(self) -> bool:
        """Whether this turn resulted in an error."""
        return self.error is not None

    def to_dict(self) -> dict:
        """Serialize to dict for JSON output."""
        return {
            "sequence_id": self.sequence_id,
            "user_message": self.user_message,
            "agent_text": self.agent_text,
            "message_types": self.message_types,
            "has_response": self.has_response,
            "has_escalation": self.has_escalation,
            "has_action_result": self.has_action_result,
            "action_results": self.action_results,
            "elapsed_ms": round(self.elapsed_ms, 1),
            "error": self.error,
            "raw_messages": [m.raw for m in self.agent_messages],
        }


# ═══════════════════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════════════════

class AgentAPIError(Exception):
    """Error from Agent Runtime API."""
    def __init__(self, status_code: int, message: str, raw: dict = None):
        self.status_code = status_code
        self.message = message
        self.raw = raw or {}
        super().__init__(f"HTTP {status_code}: {message}")


# ═══════════════════════════════════════════════════════════════════════════
# Agent Session
# ═══════════════════════════════════════════════════════════════════════════

class AgentSession:
    """
    Manages a single agent conversation session.

    Tracks all turns, handles sequenceId auto-increment, and ensures
    proper session cleanup.
    """

    def __init__(self, client: 'AgentAPIClient', session_id: str,
                 initial_messages: List[AgentMessage] = None):
        self.client = client
        self.session_id = session_id
        self.initial_messages = initial_messages or []
        self._sequence_id = 0
        self._turns: List[TurnResult] = []
        self._ended = False

    @property
    def turns(self) -> List[TurnResult]:
        """All turns executed in this session."""
        return list(self._turns)

    @property
    def turn_count(self) -> int:
        """Number of turns executed."""
        return len(self._turns)

    @property
    def initial_greeting(self) -> str:
        """The agent's initial greeting message (from session start)."""
        return "\n".join(
            m.message for m in self.initial_messages
            if m.message and m.type in ("Inform", "Text")
        )

    def send(self, text: str, variables: List[Dict] = None) -> TurnResult:
        """
        Send a user message and return the agent's response.

        Args:
            text: The user's message text
            variables: Optional variables to send with this message
                       (only editable variables can be set mid-session)

        Returns:
            TurnResult with agent's response and metadata
        """
        if self._ended:
            raise AgentAPIError(400, "Session already ended")

        self._sequence_id += 1

        body: Dict[str, Any] = {
            "message": {
                "sequenceId": self._sequence_id,
                "type": "Text",
                "text": text,
            }
        }

        if variables:
            body["variables"] = variables

        start_time = time.time()

        try:
            response = self.client._api_request(
                "POST",
                f"https://api.salesforce.com/einstein/ai-agent/v1"
                f"/sessions/{self.session_id}/messages",
                body=body,
            )
        except AgentAPIError as e:
            elapsed = (time.time() - start_time) * 1000
            turn = TurnResult(
                sequence_id=self._sequence_id,
                user_message=text,
                agent_messages=[],
                raw_response=e.raw,
                elapsed_ms=elapsed,
                error=str(e),
            )
            self._turns.append(turn)
            return turn

        elapsed = (time.time() - start_time) * 1000
        messages = _parse_messages(response.get("messages", []))

        turn = TurnResult(
            sequence_id=self._sequence_id,
            user_message=text,
            agent_messages=messages,
            raw_response=response,
            elapsed_ms=elapsed,
        )
        self._turns.append(turn)
        return turn

    def end(self) -> dict:
        """
        End the session and release server resources.

        Returns:
            Response dict (contains SessionEnded message)
        """
        if self._ended:
            return {}

        try:
            response = self.client._api_request(
                "DELETE",
                f"https://api.salesforce.com/einstein/ai-agent/v1"
                f"/sessions/{self.session_id}",
                headers={"x-session-end-reason": "UserRequest"},
            )
            self._ended = True
            return response
        except AgentAPIError:
            self._ended = True
            return {}

    def to_dict(self) -> dict:
        """Serialize full session data for JSON output."""
        return {
            "session_id": self.session_id,
            "turn_count": self.turn_count,
            "initial_greeting": self.initial_greeting,
            "turns": [t.to_dict() for t in self._turns],
            "ended": self._ended,
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()
        return False

    def __repr__(self) -> str:
        return f"AgentSession(id={self.session_id}, turns={self.turn_count})"


# ═══════════════════════════════════════════════════════════════════════════
# Agent API Client
# ═══════════════════════════════════════════════════════════════════════════

class AgentAPIClient:
    """
    Client for Salesforce Einstein Agent Runtime API v1.

    Handles authentication (ECA Client Credentials flow), session lifecycle,
    and message sending. Uses only Python standard library.

    NOTE: Agent API is NOT supported for agents of type "Agentforce (Default)".
    """

    API_BASE = "https://api.salesforce.com/einstein/ai-agent/v1"

    def __init__(
        self,
        my_domain: str = None,
        consumer_key: str = None,
        consumer_secret: str = None,
        timeout: int = 120,
        retry_count: int = 1,
        verbose: bool = False,
        log_callback=None,
    ):
        """
        Initialize the Agent API client.

        Args:
            my_domain: Salesforce My Domain URL (e.g., "your-domain.my.salesforce.com")
                       Falls back to SF_MY_DOMAIN env var.
            consumer_key: ECA Consumer Key. Falls back to SF_CONSUMER_KEY env var.
            consumer_secret: ECA Consumer Secret. Falls back to SF_CONSUMER_SECRET env var.
            timeout: Request timeout in seconds (API max is 120).
            retry_count: Number of retries on transient failures (429, 500+).
            verbose: Print debug info to stderr.
            log_callback: Optional callable(msg: str) to route log messages through
                          (e.g., StreamingConsole.api_log). If None, prints to stderr.
        """
        self.my_domain = (my_domain or os.environ.get("SF_MY_DOMAIN", "")).strip().rstrip("/")
        self._consumer_key = consumer_key or os.environ.get("SF_CONSUMER_KEY", "")
        self._consumer_secret = consumer_secret or os.environ.get("SF_CONSUMER_SECRET", "")
        self._timeout = min(timeout, 120)  # API max is 120s
        self._retry_count = retry_count
        self._verbose = verbose
        self._log_callback = log_callback
        self._access_token: Optional[str] = None
        self._token_issued_at: float = 0

        # Normalize domain
        if self.my_domain and not self.my_domain.startswith("https://"):
            self.my_domain = f"https://{self.my_domain}"

    def _log(self, msg: str):
        """Print debug message to stderr if verbose."""
        if self._verbose:
            if self._log_callback:
                self._log_callback(msg)
            else:
                print(f"  [api] {msg}", file=sys.stderr)

    # ─── Authentication ────────────────────────────────────────────────

    def authenticate(self) -> str:
        """
        Obtain access token via Client Credentials flow.

        Returns:
            The access token string.

        Raises:
            AgentAPIError: If authentication fails.
        """
        if not self.my_domain:
            raise AgentAPIError(0, "my_domain is required (set SF_MY_DOMAIN env var)")
        if not self._consumer_key:
            raise AgentAPIError(0, "consumer_key is required (set SF_CONSUMER_KEY env var)")
        if not self._consumer_secret:
            raise AgentAPIError(0, "consumer_secret is required (set SF_CONSUMER_SECRET env var)")

        token_url = f"{self.my_domain}/services/oauth2/token"
        self._log(f"Authenticating to {token_url}")

        data = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": self._consumer_key,
            "client_secret": self._consumer_secret,
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
            raise AgentAPIError(e.code, f"Authentication failed: {msg}")
        except urllib.error.URLError as e:
            raise AgentAPIError(0, f"Connection error during auth: {e.reason}")

        self._access_token = result.get("access_token")
        self._token_issued_at = time.time()

        if not self._access_token:
            raise AgentAPIError(401, f"No access_token in response: {json.dumps(result)[:200]}")

        self._log("Authentication successful")
        return self._access_token

    def _ensure_authenticated(self):
        """Authenticate if no valid token exists (tokens expire ~60 min)."""
        if not self._access_token or (time.time() - self._token_issued_at) > 3300:
            self.authenticate()

    # ─── Session Management ────────────────────────────────────────────

    def start_session(
        self,
        agent_id: str,
        variables: List[Dict] = None,
        bypass_user: bool = True,
    ) -> AgentSession:
        """
        Start a new agent conversation session.

        Args:
            agent_id: BotDefinition ID (e.g., "0XxRM0000004ABC").
                      Query with: SELECT Id FROM BotDefinition WHERE DeveloperName='X'
            variables: Optional list of session variables. Each dict should have:
                       {"name": "$Context.AccountId", "type": "Text", "value": "001XX"}
                       Supported types: Text, Number, Boolean, Object, Date, DateTime,
                       Currency, Id.
            bypass_user: If True, use the agent-assigned user (from ECA Run As).
                         If False, use the user associated with the token.

        Returns:
            AgentSession instance for sending messages.

        Raises:
            AgentAPIError: If session creation fails.
        """
        self._ensure_authenticated()

        session_key = str(uuid.uuid4())
        self._log(f"Starting session for agent {agent_id} (key: {session_key[:8]}...)")

        body: Dict[str, Any] = {
            "externalSessionKey": session_key,
            "instanceConfig": {
                "endpoint": self.my_domain,
            },
            "streamingCapabilities": {
                "chunkTypes": ["Text"],
            },
            "bypassUser": bypass_user,
        }

        if variables:
            body["variables"] = variables
            self._log(f"Session variables: {[v['name'] for v in variables]}")

        response = self._api_request(
            "POST",
            f"{self.API_BASE}/agents/{agent_id}/sessions",
            body=body,
        )

        session_id = response.get("sessionId")
        if not session_id:
            raise AgentAPIError(500, "No sessionId in response", response)

        initial_messages = _parse_messages(response.get("messages", []))

        self._log(f"Session started: {session_id[:12]}...")
        if initial_messages:
            self._log(f"Initial greeting: {initial_messages[0].message[:60]}...")

        return AgentSession(self, session_id, initial_messages)

    def session(
        self,
        agent_id: str,
        variables: List[Dict] = None,
        bypass_user: bool = True,
    ) -> AgentSession:
        """
        Start a session (alias for start_session, for use with `with` statement).

        Usage:
            with client.session(agent_id="0Xx...") as s:
                s.send("Hello")
        """
        return self.start_session(agent_id, variables, bypass_user)

    # ─── Internal HTTP ─────────────────────────────────────────────────

    def _api_request(
        self,
        method: str,
        url: str,
        body: dict = None,
        headers: dict = None,
    ) -> dict:
        """
        Make an authenticated API request with retry logic.

        Retries on:
        - 429 (Rate Limit) with exponential backoff
        - 500+ (Server Error) with linear backoff
        - 401 (Unauthorized) with re-authentication
        """
        self._ensure_authenticated()

        req_headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if headers:
            req_headers.update(headers)

        data = json.dumps(body).encode("utf-8") if body else None

        last_error = None
        for attempt in range(self._retry_count + 1):
            req = urllib.request.Request(
                url, data=data, headers=req_headers, method=method
            )

            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    resp_body = resp.read().decode("utf-8")
                    if resp_body:
                        return json.loads(resp_body)
                    return {}

            except urllib.error.HTTPError as e:
                resp_body = e.read().decode("utf-8", errors="replace")
                try:
                    error_data = json.loads(resp_body)
                except json.JSONDecodeError:
                    error_data = {"raw": resp_body}

                last_error = AgentAPIError(e.code, resp_body[:300], error_data)
                self._log(f"HTTP {e.code} on {method} {url[:60]}... (attempt {attempt + 1})")

                # Retry on 429 (rate limit) with exponential backoff
                if e.code == 429 and attempt < self._retry_count:
                    wait = 2 ** (attempt + 1)
                    self._log(f"Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue

                # Retry on 500+ (server error)
                if e.code >= 500 and attempt < self._retry_count:
                    self._log("Server error, retrying in 2s...")
                    time.sleep(2)
                    continue

                # Re-authenticate on 401
                if e.code == 401 and attempt < self._retry_count:
                    self._log("Token expired, re-authenticating...")
                    self._access_token = None
                    self._ensure_authenticated()
                    req_headers["Authorization"] = f"Bearer {self._access_token}"
                    continue

                raise last_error

            except urllib.error.URLError as e:
                last_error = AgentAPIError(0, f"Connection error: {e.reason}")
                if attempt < self._retry_count:
                    self._log(f"Connection error, retrying in 1s: {e.reason}")
                    time.sleep(1)
                    continue
                raise last_error

        raise last_error


# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

def _parse_messages(messages_data: list) -> List[AgentMessage]:
    """Parse raw message dicts into AgentMessage objects."""
    messages = []
    for msg in messages_data:
        messages.append(AgentMessage(
            type=msg.get("type", "Unknown"),
            id=msg.get("id", ""),
            message=msg.get("message", ""),
            feedback_id=msg.get("feedbackId", ""),
            plan_id=msg.get("planId", ""),
            is_content_safe=msg.get("isContentSafe", True),
            result=msg.get("result", []),
            planner_surfaces=msg.get("plannerSurfaces", []),
            cited_references=msg.get("citedReferences", []),
            raw=msg,
        ))
    return messages


def parse_variables(var_strings: List[str]) -> List[Dict[str, str]]:
    """
    Parse variable strings into API-format dicts.

    Accepts formats:
        "name=value"              → {"name": "name", "type": "Text", "value": "value"}
        "name:Type=value"         → {"name": "name", "type": "Type", "value": "value"}
        "$Context.Field=value"    → {"name": "$Context.Field", "type": "Text", "value": "value"}

    Args:
        var_strings: List of "name=value" or "name:type=value" strings.

    Returns:
        List of variable dicts suitable for the API.
    """
    variables = []
    for vs in var_strings:
        if "=" not in vs:
            raise ValueError(f"Invalid variable format (expected name=value): {vs}")

        name_part, value = vs.split("=", 1)

        if ":" in name_part:
            name, var_type = name_part.rsplit(":", 1)
        else:
            name = name_part
            var_type = "Text"

        variables.append({
            "name": name.strip(),
            "type": var_type.strip(),
            "value": value.strip(),
        })

    return variables


# ═══════════════════════════════════════════════════════════════════════════
# CLI Quick Test
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Quick connectivity test — verifies token and lists the agent greeting."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Agent API Client — quick connectivity test"
    )
    parser.add_argument("--my-domain", default=os.environ.get("SF_MY_DOMAIN", ""),
                        help="Salesforce My Domain URL")
    parser.add_argument("--consumer-key", default=os.environ.get("SF_CONSUMER_KEY", ""),
                        help="ECA Consumer Key")
    parser.add_argument("--consumer-secret", default=os.environ.get("SF_CONSUMER_SECRET", ""),
                        help="ECA Consumer Secret")
    parser.add_argument("--agent-id", default=os.environ.get("SF_AGENT_ID", ""),
                        help="BotDefinition ID")
    parser.add_argument("--message", default="Hello",
                        help="Test message to send")
    parser.add_argument("--var", action="append", default=[],
                        help="Variable: 'name=value' or '$Context.Field=value'")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable debug output")

    args = parser.parse_args()

    if not args.agent_id:
        print("ERROR: --agent-id required (or set SF_AGENT_ID env var)", file=sys.stderr)
        sys.exit(1)

    client = AgentAPIClient(
        my_domain=args.my_domain,
        consumer_key=args.consumer_key,
        consumer_secret=args.consumer_secret,
        verbose=args.verbose,
    )

    variables = parse_variables(args.var) if args.var else None

    print("=" * 60)
    print("AGENT API CONNECTIVITY TEST")
    print("=" * 60)

    try:
        token = client.authenticate()
        print(f"✅ Authentication: OK (token length: {len(token)})")
    except AgentAPIError as e:
        print(f"❌ Authentication: FAILED — {e.message}")
        sys.exit(1)

    try:
        with client.session(agent_id=args.agent_id, variables=variables) as session:
            print(f"✅ Session created: {session.session_id[:16]}...")

            if session.initial_greeting:
                print(f"   Greeting: {session.initial_greeting[:80]}...")

            result = session.send(args.message)
            if result.has_response:
                print(f"✅ Message sent: \"{args.message}\"")
                print(f"   Response: {result.agent_text[:120]}...")
                print(f"   Types: {result.message_types}")
                print(f"   Elapsed: {result.elapsed_ms:.0f}ms")
            elif result.is_error:
                print(f"❌ Message failed: {result.error}")
            else:
                print(f"⚠️  Message sent but no text response")
                print(f"   Types: {result.message_types}")

        print(f"✅ Session ended cleanly")
    except AgentAPIError as e:
        print(f"❌ API error: {e}")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()
