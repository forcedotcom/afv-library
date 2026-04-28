#!/usr/bin/env python3
"""
Agent Script Syntax Validator
=============================

PostToolUse hook that validates .agent files for common syntax errors and
high-value production gotchas documented in the sf-ai-agentscript skill.

Issue messages include stable rule IDs (ASV-*) so the validator output can be
cross-referenced with the validator rule catalog documentation.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class AgentScriptValidator:
    """Validates Agent Script syntax and common production gotchas."""

    NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,79}$")
    VARIABLE_DECL_PATTERN = re.compile(
        r"^([A-Za-z][A-Za-z0-9_]*)\s*:\s*(mutable|linked)\s+([A-Za-z][A-Za-z0-9_\[\]]*)(?:\s*=\s*(.+?))?\s*$",
        re.IGNORECASE,
    )
    BLOCK_NAME_PATTERN = re.compile(r"^(topic|start_agent)\s+([A-Za-z][A-Za-z0-9_]*)\s*:")
    ACTION_DECL_PATTERN = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)\s*:\s*(.*)$")
    IO_FIELD_PATTERN = re.compile(r'^(?:"([^"]+)"|([A-Za-z_][A-Za-z0-9_]*))\s*:\s*([A-Za-z][A-Za-z0-9_\[\]]*)\s*$')
    CONNECTION_BLOCK_PATTERN = re.compile(r"^connection\s+([A-Za-z_][A-Za-z0-9_]*)\s*:")
    KEY_VALUE_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_:]*)\s*:\s*(.*)$")

    RESERVED_CONTEXT_VARIABLE_NAMES = {
        "Locale",
        "Channel",
        "Status",
        "Origin",
    }

    RESERVED_FIELD_NAMES = {
        "description",
        "label",
        "is_required",
        "is_displayable",
        "is_used_by_planner",
        "model",
    }

    INVALID_TRANSITION_PROPERTIES = {
        "label",
        "require_user_confirmation",
        "include_in_progress_indicator",
        "progress_indicator_message",
        "is_required",
        "is_user_input",
        "is_displayable",
        "is_used_by_planner",
    }

    TOP_LEVEL_ENDERS = (
        "config:",
        "variables:",
        "system:",
        "knowledge:",
        "language:",
        "connection ",
        "connections:",
        "topic ",
        "start_agent ",
        "actions:",
    )

    CONDITIONAL_EXECUTABLE_PREFIXES = (
        "|",
        "if ",
        "else:",
        "run ",
        "set ",
        "transition to ",
        "with ",
    )

    SENSITIVE_ACTION_TOKENS = (
        "delete",
        "refund",
        "charge",
        "cancel",
        "escalate",
        "transfer",
        "close",
        "disable",
        "update_profile",
        "update_customer",
        "reset_password",
        "change_owner",
    )

    LARGE_FILE_LIMITS = {
        "lines": 450,
        "topics": 18,
        "actions": 40,
    }

    def __init__(self, content: str, file_path: str):
        self.content = content
        self.file_path = file_path
        self.lines = content.split("\n")
        self.errors: List[Tuple[int, str, str]] = []
        self.warnings: List[Tuple[int, str, str]] = []

        self.config_fields: Dict[str, Tuple[str, int]] = {}
        self.config_raw_fields: Dict[str, Tuple[str, int]] = {}
        self.topic_names: Dict[str, int] = {}
        self.start_agent_names: Dict[str, int] = {}
        self.variable_names: Dict[str, int] = {}
        self.variable_definitions: List[Dict] = []
        self.variable_by_name: Dict[str, Dict] = {}
        self.defined_topics: Set[str] = set()
        self.connection_blocks: List[Dict] = []
        self.connection_messaging_lines: List[int] = []
        self.messaging_linked_var_lines: List[int] = []
        self.context_linked_var_lines: List[int] = []
        self.action_definitions: List[Dict] = []
        self.block_descriptions: List[Dict] = []
        self.multiline_description_issues: List[Tuple[int, str]] = []
        self.lifecycle_instruction_wrappers: List[Tuple[int, str]] = []
        self.lifecycle_pipe_lines: List[Tuple[int, str]] = []
        self.lifecycle_run_lines: List[Tuple[int, str, str]] = []
        self.lifecycle_arithmetic_lines: List[Tuple[int, str, str, str]] = []  # (line, lifecycle_name, var_name, owner)
        self.lifecycle_null_guards: List[Tuple[int, str, str, str]] = []  # (line, lifecycle_name, var_name, owner)
        self.topic_inline_system_lines: List[Tuple[int, str]] = []
        self.line_owner: Dict[int, str] = {}
        self.welcome_error_inline_interpolation_lines: List[Tuple[int, str]] = []
        self.welcome_error_folded_scalar_lines: List[Tuple[int, str]] = []
        self.default_agent_user_comment_lines: List[int] = []
        self.top_level_actions_lines: List[int] = []

        self.validation_org = self._resolve_validation_org()
        self._query_cache: Dict[str, Dict] = {}
        self._user_query_cache: Dict[str, Dict] = {}

        self._parse_structure()

    @staticmethod
    def _indent(raw_line: str) -> int:
        expanded = raw_line.expandtabs(4)
        return len(expanded) - len(expanded.lstrip(" "))

    @staticmethod
    def _strip_quotes(value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")):
            return value[1:-1]
        return value

    def _strip_inline_comment(self, value: str) -> str:
        in_single = False
        in_double = False
        escaped = False
        out: List[str] = []
        for char in value:
            if char == "\\" and (in_single or in_double):
                escaped = not escaped
                out.append(char)
                continue
            if char == "'" and not in_double and not escaped:
                in_single = not in_single
            elif char == '"' and not in_single and not escaped:
                in_double = not in_double
            elif char == "#" and not in_single and not in_double:
                break
            out.append(char)
            escaped = False
        return "".join(out).rstrip()

    def _clean_scalar_value(self, value: str) -> str:
        commentless = self._strip_inline_comment(value).strip()
        return self._strip_quotes(commentless)

    @staticmethod
    def _sql_quote(value: str) -> str:
        return value.replace("'", "\\'")

    @staticmethod
    def _is_placeholder_value(value: Optional[str]) -> bool:
        return bool(value and "{{" in value and "}}" in value)

    @staticmethod
    def _is_demo_user_value(value: Optional[str]) -> bool:
        if not value:
            return False
        lowered = value.lower()
        demo_domains = ("yourorg.com", "company.com", "company.salesforce.com", "example.com")
        return AgentScriptValidator._is_placeholder_value(value) or any(lowered.endswith(f"@{domain}") for domain in demo_domains)

    def _issue_message(self, rule_id: Optional[str], message: str) -> str:
        return f"[{rule_id}] {message}" if rule_id else message

    def _add_error(self, line_num: int, message: str, rule_id: Optional[str] = None):
        self.errors.append((line_num, "error", self._issue_message(rule_id, message)))

    def _add_warning(self, line_num: int, message: str, rule_id: Optional[str] = None):
        self.warnings.append((line_num, "warning", self._issue_message(rule_id, message)))

    def _project_root_for_file(self) -> Path:
        current = Path(self.file_path).resolve().parent
        for candidate in [current, *current.parents]:
            if (candidate / "sfdx-project.json").exists():
                return candidate
        return current

    def _resolve_sf_target_org(self, cwd: Path) -> Optional[str]:
        try:
            proc = subprocess.run(
                ["sf", "config", "get", "target-org", "--json"],
                text=True,
                capture_output=True,
                timeout=15,
                cwd=str(cwd),
            )
        except Exception:
            return None

        if proc.returncode != 0:
            return None

        try:
            payload = json.loads(proc.stdout or "{}")
        except Exception:
            return None

        results = payload.get("result") or []
        if not isinstance(results, list):
            return None

        for entry in results:
            value = (entry or {}).get("value")
            if value:
                return str(value).strip()
        return None

    def _resolve_validation_org(self) -> Optional[str]:
        for env_name in ("AGENTSCRIPT_VALIDATION_ORG", "SF_TARGET_ORG", "TARGET_ORG"):
            value = os.environ.get(env_name)
            if value:
                return value.strip()
        return self._resolve_sf_target_org(self._project_root_for_file())

    def _effective_agent_type(self) -> Optional[str]:
        agent_type = self.config_fields.get("agent_type")
        default_agent_user = self.config_fields.get("default_agent_user")
        if agent_type:
            return agent_type[0]
        if default_agent_user:
            return "AgentforceServiceAgent"
        return None

    def _run_soql_query(self, soql: str) -> Dict:
        if soql in self._query_cache:
            return self._query_cache[soql]

        if not self.validation_org:
            result = {"ok": False, "reason": "no_validation_org"}
            self._query_cache[soql] = result
            return result

        try:
            proc = subprocess.run(
                ["sf", "data", "query", "--query", soql, "-o", self.validation_org, "--json"],
                text=True,
                capture_output=True,
                timeout=30,
            )
        except Exception as exc:
            result = {"ok": False, "reason": "query_failed", "detail": str(exc)}
            self._query_cache[soql] = result
            return result

        if proc.returncode != 0:
            detail = (proc.stdout or proc.stderr or "sf data query failed").strip()
            result = {"ok": False, "reason": "query_failed", "detail": detail}
            self._query_cache[soql] = result
            return result

        try:
            payload = json.loads(proc.stdout or "{}")
        except Exception:
            result = {"ok": False, "reason": "query_failed", "detail": "Could not parse sf data query JSON output."}
            self._query_cache[soql] = result
            return result

        result = {
            "ok": True,
            "payload": payload,
            "records": ((payload.get("result") or {}).get("records") or []) if isinstance(payload, dict) else [],
        }
        self._query_cache[soql] = result
        return result

    def _query_user_in_org(self, username: str) -> Dict:
        if username in self._user_query_cache:
            return self._user_query_cache[username]

        soql = (
            "SELECT Username, IsActive, UserType, Profile.Name "
            f"FROM User WHERE Username = '{self._sql_quote(username)}' LIMIT 1"
        )
        query = self._run_soql_query(soql)
        if not query.get("ok"):
            result = {"ok": False, "reason": query.get("reason"), "detail": query.get("detail")}
            self._user_query_cache[username] = result
            return result

        records = query.get("records") or []
        if not records:
            result = {"ok": False, "reason": "missing"}
            self._user_query_cache[username] = result
            return result

        record = records[0]
        is_active = record.get("IsActive") is True
        user_type = record.get("UserType")
        profile_name = ((record.get("Profile") or {}).get("Name"))

        if not is_active:
            result = {"ok": False, "reason": "inactive", "record": record}
        elif user_type == "AutomatedProcess":
            result = {"ok": False, "reason": "automated_process", "record": record}
        elif profile_name != "Einstein Agent User":
            result = {"ok": False, "reason": "wrong_profile", "record": record}
        else:
            result = {"ok": True, "reason": "valid", "record": record}

        self._user_query_cache[username] = result
        return result

    def _query_permission_set_assignments(self, username: str) -> Dict:
        soql = (
            "SELECT PermissionSetId, PermissionSet.Name "
            f"FROM PermissionSetAssignment WHERE Assignee.Username = '{self._sql_quote(username)}'"
        )
        return self._run_soql_query(soql)

    def _query_permission_set(self, permset_name: str) -> Dict:
        soql = f"SELECT Id, Name FROM PermissionSet WHERE Name = '{self._sql_quote(permset_name)}' LIMIT 1"
        return self._run_soql_query(soql)

    def _query_apex_classes(self, class_names: List[str]) -> Dict:
        names = sorted({name for name in class_names if name})
        if not names:
            return {"ok": True, "records": []}
        quoted = ", ".join(f"'{self._sql_quote(name)}'" for name in names)
        return self._run_soql_query(f"SELECT Id, Name FROM ApexClass WHERE Name IN ({quoted})")

    def _query_setup_entity_access(self, parent_id: str, setup_entity_ids: List[str], setup_entity_type: str = "ApexClass") -> Dict:
        ids = sorted({entity_id for entity_id in setup_entity_ids if entity_id})
        if not ids:
            return {"ok": True, "records": []}
        quoted = ", ".join(f"'{entity_id}'" for entity_id in ids)
        soql = (
            "SELECT SetupEntityId, SetupEntityType "
            f"FROM SetupEntityAccess WHERE ParentId = '{parent_id}' "
            f"AND SetupEntityType = '{setup_entity_type}' AND SetupEntityId IN ({quoted})"
        )
        return self._run_soql_query(soql)

    def _query_active_flows(self, flow_names: List[str]) -> Dict:
        names = sorted({name for name in flow_names if name})
        if not names:
            return {"ok": True, "records": []}
        quoted = ", ".join(f"'{self._sql_quote(name)}'" for name in names)
        soql = f"SELECT ApiName, ActiveVersionId FROM FlowDefinitionView WHERE ApiName IN ({quoted})"
        return self._run_soql_query(soql)

    def _agent_identifier(self) -> Optional[str]:
        if "developer_name" in self.config_fields:
            return self.config_fields["developer_name"][0]
        if "agent_name" in self.config_fields:
            return self.config_fields["agent_name"][0]
        return None

    def _collect_targets(self) -> Dict[str, List[Tuple[str, int, str]]]:
        apex_targets: List[Tuple[str, int, str]] = []
        flow_targets: List[Tuple[str, int, str]] = []
        other_targets: List[Tuple[str, int, str]] = []

        for action in self.action_definitions:
            if action.get("scope") != "definition":
                continue
            target = action.get("target")
            if not target:
                continue
            line = action.get("target_line") or action.get("line") or 1
            if target.startswith("apex://"):
                apex_ref = target[len("apex://"):].strip()
                apex_class_name = apex_ref.split(".", 1)[0]
                apex_targets.append((apex_class_name, line, target))
            elif target.startswith("flow://"):
                flow_name = target[len("flow://"):].strip()
                flow_targets.append((flow_name, line, target))
            else:
                other_targets.append((target, line, target))

        return {"apex": apex_targets, "flow": flow_targets, "other": other_targets}

    def _collect_connection_route_targets(self) -> List[Tuple[str, int, str]]:
        flows: List[Tuple[str, int, str]] = []
        for block in self.connection_blocks:
            route_name = (block.get("fields") or {}).get("outbound_route_name")
            if not route_name:
                continue
            value, line = route_name
            if value.startswith("flow://"):
                flows.append((value[len("flow://"):].strip(), line, value))
        return flows

    def _flush_action(self, current_action: Optional[Dict]):
        if current_action:
            self.action_definitions.append(current_action)

    def _parse_structure(self):
        current_top: Optional[str] = None
        current_block_name: Optional[str] = None
        current_action: Optional[Dict] = None
        current_variable: Optional[Dict] = None
        current_connection: Optional[Dict] = None
        actions_mode: Optional[str] = None
        actions_indent: Optional[int] = None
        reasoning_indent: Optional[int] = None
        current_io: Optional[Dict] = None
        current_io_field: Optional[Dict] = None
        lifecycle_block: Optional[Dict] = None

        for i, raw_line in enumerate(self.lines, 1):
            indent = self._indent(raw_line)
            stripped = raw_line.strip()

            if current_top in {"topic", "start_agent"} and current_block_name:
                self.line_owner[i] = current_block_name

            if not stripped:
                continue

            if stripped.startswith("#"):
                continue

            # Close nested contexts when indentation decreases
            if lifecycle_block and indent <= lifecycle_block["indent"]:
                lifecycle_block = None

            if current_io_field and indent <= current_io_field["indent"]:
                # Check filter_from_agent + is_used_by_planner conflict before closing
                if current_io_field.get("has_filter_from_agent") and current_io_field.get("has_is_used_by_planner") and current_action:
                    current_action["filter_planner_conflict_lines"].append(
                        (current_io_field["is_used_by_planner_line"], current_io_field["name"], current_io_field["section"])
                    )
                current_io_field = None

            if current_io and indent <= current_io["indent"]:
                current_io = None

            if current_action and indent <= current_action["indent"]:
                self._flush_action(current_action)
                current_action = None
                current_io = None
                current_io_field = None

            if current_variable and (current_top != "variables" or indent <= current_variable["indent"]):
                current_variable = None

            if actions_mode and actions_indent is not None and indent <= actions_indent:
                actions_mode = None
                actions_indent = None

            if reasoning_indent is not None and indent <= reasoning_indent:
                reasoning_indent = None

            if indent == 0 and current_connection and not stripped.startswith("connection "):
                self.connection_blocks.append(current_connection)
                current_connection = None

            # Top-level blocks
            if indent == 0:
                current_top = None
                current_block_name = None
                lifecycle_block = None

                if stripped == "config:":
                    current_top = "config"
                    continue
                if stripped == "variables:":
                    current_top = "variables"
                    continue
                if stripped == "knowledge:":
                    current_top = "knowledge"
                    continue
                if stripped == "language:":
                    current_top = "language"
                    continue
                if stripped == "system:":
                    current_top = "system"
                    continue
                if stripped == "connections:":
                    current_top = "connections"
                    continue
                if stripped == "actions:":
                    self.top_level_actions_lines.append(i)
                    current_top = "actions"
                    continue

                connection_match = self.CONNECTION_BLOCK_PATTERN.match(stripped)
                if connection_match:
                    if current_connection:
                        self.connection_blocks.append(current_connection)
                    channel = connection_match.group(1)
                    current_top = "connection"
                    current_connection = {"channel": channel, "line": i, "fields": {}}
                    if channel == "messaging":
                        self.connection_messaging_lines.append(i)
                    continue

                block_match = self.BLOCK_NAME_PATTERN.match(stripped)
                if block_match:
                    kind, name = block_match.groups()
                    current_top = kind
                    current_block_name = name
                    self.line_owner[i] = name
                    if kind == "topic":
                        self.topic_names.setdefault(name, i)
                    else:
                        self.start_agent_names.setdefault(name, i)
                    self.defined_topics.add(name)
                    continue

            # config block
            if current_top == "config" and indent > 0:
                field_match = self.KEY_VALUE_PATTERN.match(stripped)
                if field_match:
                    field, raw_value = field_match.groups()
                    self.config_raw_fields[field] = (raw_value, i)
                    cleaned = self._clean_scalar_value(raw_value)
                    self.config_fields[field] = (cleaned, i)
                    if field == "default_agent_user" and self._strip_inline_comment(raw_value).strip() != raw_value.strip():
                        self.default_agent_user_comment_lines.append(i)
                continue

            # variables block
            if current_top == "variables" and indent > 0:
                commentless = self._strip_inline_comment(stripped)
                var_match = self.VARIABLE_DECL_PATTERN.match(commentless)
                if var_match:
                    name, modifier, var_type, default_value = var_match.groups()
                    definition = {
                        "name": name,
                        "modifier": modifier.lower(),
                        "type": var_type,
                        "line": i,
                        "indent": indent,
                        "default": default_value.strip() if default_value else None,
                        "source": None,
                        "source_line": None,
                    }
                    self.variable_names.setdefault(name, i)
                    self.variable_definitions.append(definition)
                    self.variable_by_name[name] = definition
                    current_variable = definition
                    if name in self.RESERVED_FIELD_NAMES:
                        # Report later in dedicated rule.
                        pass
                    continue

                # Multi-line variable declaration: "Name:" on its own line,
                # with type/modifier/default on subsequent indented lines.
                # This captures the variable name for reserved-name checks
                # even when the full single-line pattern doesn't match.
                multiline_var_match = re.match(r"^([A-Za-z][A-Za-z0-9_]*)\s*:\s*$", commentless)
                if multiline_var_match:
                    name = multiline_var_match.group(1)
                    definition = {
                        "name": name,
                        "modifier": "",
                        "type": "",
                        "line": i,
                        "indent": indent,
                        "default": None,
                        "source": None,
                        "source_line": None,
                    }
                    self.variable_names.setdefault(name, i)
                    self.variable_definitions.append(definition)
                    self.variable_by_name[name] = definition
                    current_variable = definition
                    continue

                if current_variable and indent > current_variable["indent"]:
                    field_match = self.KEY_VALUE_PATTERN.match(stripped)
                    if field_match:
                        field, raw_value = field_match.groups()
                        cleaned = self._clean_scalar_value(raw_value)
                        if field == "type" and not current_variable.get("type"):
                            current_variable["type"] = cleaned
                        elif field == "default" and current_variable.get("default") is None:
                            current_variable["default"] = cleaned
                        elif field == "source":
                            current_variable["source"] = cleaned
                            current_variable["source_line"] = i
                            if "@MessagingSession." in cleaned or "@MessagingEndUser." in cleaned:
                                self.messaging_linked_var_lines.append(i)
                            if cleaned.startswith("@context."):
                                self.context_linked_var_lines.append(i)
                    continue

            # connection block
            if current_top == "connection" and current_connection and indent > 0:
                field_match = self.KEY_VALUE_PATTERN.match(stripped)
                if field_match:
                    field, raw_value = field_match.groups()
                    current_connection["fields"][field] = (self._clean_scalar_value(raw_value), i)
                continue

            # system block (simple heuristics for welcome/error message guidance)
            if current_top == "system" and indent > 0:
                lower = stripped.lower()
                if "welcome" in lower or "error" in lower:
                    kind = "welcome" if "welcome" in lower else "error"
                    if "{!" in stripped:
                        self.welcome_error_inline_interpolation_lines.append((i, kind))
                    if re.search(r":\s*>[-+]?\s*$", stripped):
                        self.welcome_error_folded_scalar_lines.append((i, kind))
                continue

            # topic/start_agent internals
            if current_top in {"topic", "start_agent"} and indent > 0:
                # lifecycle tracking
                if stripped in {"before_reasoning:", "after_reasoning:"}:
                    lifecycle_block = {"name": stripped[:-1], "indent": indent, "owner": current_block_name}
                    continue

                if lifecycle_block and indent > lifecycle_block["indent"]:
                    if stripped.startswith("instructions:"):
                        self.lifecycle_instruction_wrappers.append((i, lifecycle_block["name"]))
                    if stripped.startswith("|"):
                        self.lifecycle_pipe_lines.append((i, lifecycle_block["name"]))
                    run_match = re.match(r"^run\s+@actions\.([A-Za-z_][A-Za-z0-9_]*)\b", stripped)
                    if run_match:
                        self.lifecycle_run_lines.append((i, lifecycle_block["name"], run_match.group(1)))
                    # Detect arithmetic on variables: set @variables.X = @variables.X + N
                    arith_match = re.match(
                        r"^set\s+@variables\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*@variables\.\1\s*[+\-]\s*\d+",
                        stripped,
                    )
                    if arith_match:
                        self.lifecycle_arithmetic_lines.append((i, lifecycle_block["name"], arith_match.group(1), lifecycle_block.get("owner") or ""))
                    # Detect null guards: if @variables.X is None:
                    null_match = re.match(r"^if\s+@variables\.([A-Za-z_][A-Za-z0-9_]*)\s+is\s+None\s*:", stripped)
                    if null_match:
                        self.lifecycle_null_guards.append((i, lifecycle_block["name"], null_match.group(1), lifecycle_block.get("owner") or ""))
                    # keep parsing deeper structures too

                if stripped == "reasoning:":
                    reasoning_indent = indent
                    continue

                if stripped == "actions:":
                    if reasoning_indent is not None and indent > reasoning_indent:
                        actions_mode = "reasoning"
                    else:
                        actions_mode = "definition"
                    actions_indent = indent
                    continue

                if actions_mode in {"definition", "reasoning"} and actions_indent is not None and indent > actions_indent:
                    if current_action is None or indent == current_action["indent"]:
                        action_match = self.ACTION_DECL_PATTERN.match(stripped)
                        if action_match:
                            name, remainder = action_match.groups()
                            if name not in {"inputs", "outputs", "target", "description", "label", "source", "system", "reasoning"}:
                                current_action = {
                                    "name": name,
                                    "line": i,
                                    "indent": indent,
                                    "owner": current_block_name,
                                    "scope": actions_mode,
                                    "kind": "definition" if actions_mode == "definition" else "reasoning",
                                    "inline": remainder.strip(),
                                    "target": None,
                                    "target_line": None,
                                    "description": None,
                                    "description_line": None,
                                    "has_available_when": False,
                                    "available_when_count": 0,
                                    "has_inputs_block": False,
                                    "has_outputs_block": False,
                                    "io_fields": [],
                                    "invalid_transition_properties": [],
                                    "required_input_lines": [],
                                    "prompt_output_display_lines": [],
                                    "date_io_lines": [],
                                    "require_user_confirmation_lines": [],
                                    "reserved_io_field_lines": [],
                                    "filter_planner_conflict_lines": [],
                                }
                                inline = remainder.strip()
                                if inline.startswith("@utils.transition"):
                                    current_action["kind"] = "utility_transition"
                                elif inline.startswith("@topic."):
                                    current_action["kind"] = "delegation"
                                elif inline.startswith("@utils."):
                                    current_action["kind"] = "utility"
                                elif inline.startswith("target:"):
                                    target_value = self._clean_scalar_value(inline.split(":", 1)[1].strip())
                                    current_action["target"] = target_value
                                    current_action["target_line"] = i
                                continue

                    if current_action is not None and indent > current_action["indent"]:
                        if stripped.startswith("target:"):
                            target = self._clean_scalar_value(stripped.split(":", 1)[1].strip())
                            current_action["target"] = target
                            current_action["target_line"] = i
                            continue

                        if stripped.startswith("description:"):
                            current_action["description"] = self._clean_scalar_value(stripped.split(":", 1)[1].strip())
                            current_action["description_line"] = i
                            continue

                        if stripped.startswith("available when"):
                            current_action["has_available_when"] = True
                            current_action["available_when_count"] += 1
                            continue

                        if stripped == "inputs:":
                            current_action["has_inputs_block"] = True
                            current_io = {"name": "inputs", "indent": indent}
                            current_io_field = None
                            continue

                        if stripped == "outputs:":
                            current_action["has_outputs_block"] = True
                            current_io = {"name": "outputs", "indent": indent}
                            current_io_field = None
                            continue

                        if stripped.startswith("require_user_confirmation:"):
                            value = self._clean_scalar_value(stripped.split(":", 1)[1].strip())
                            if value == "True":
                                current_action["require_user_confirmation_lines"].append(i)
                            continue

                        if current_io and indent > current_io["indent"]:
                            if current_io_field is None or indent == current_io_field["indent"]:
                                field_match = self.IO_FIELD_PATTERN.match(self._strip_inline_comment(stripped))
                                if field_match:
                                    quoted_field_name, plain_field_name, field_type = field_match.groups()
                                    field_name = quoted_field_name or plain_field_name
                                    current_io_field = {
                                        "name": field_name,
                                        "type": field_type,
                                        "indent": indent,
                                        "section": current_io["name"],
                                        "line": i,
                                        "has_filter_from_agent": False,
                                        "filter_from_agent_value": None,
                                        "has_is_displayable": False,
                                        "is_displayable_value": None,
                                        "has_is_used_by_planner": False,
                                        "is_used_by_planner_value": None,
                                        "filter_from_agent_line": None,
                                        "is_displayable_line": None,
                                        "is_used_by_planner_line": None,
                                    }
                                    current_action["io_fields"].append(current_io_field)
                                    if field_type == "date":
                                        current_action["date_io_lines"].append((i, field_name, current_io["name"]))
                                    if field_name in self.RESERVED_FIELD_NAMES:
                                        current_action["reserved_io_field_lines"].append((i, field_name, current_io["name"]))
                                    continue

                            if current_io_field and indent > current_io_field["indent"]:
                                if stripped.startswith("is_displayable:"):
                                    value = self._clean_scalar_value(stripped.split(":", 1)[1].strip())
                                    current_io_field["has_is_displayable"] = True
                                    current_io_field["is_displayable_value"] = value
                                    current_io_field["is_displayable_line"] = i
                                    if value == "True":
                                        current_action["prompt_output_display_lines"].append((i, current_io_field["name"]))
                                if stripped.startswith("is_required:") and self._clean_scalar_value(stripped.split(":", 1)[1].strip()) == "True":
                                    current_action["required_input_lines"].append((i, current_io_field["name"]))
                                if stripped.startswith("filter_from_agent:"):
                                    value = self._clean_scalar_value(stripped.split(":", 1)[1].strip())
                                    current_io_field["has_filter_from_agent"] = True
                                    current_io_field["filter_from_agent_value"] = value
                                    current_io_field["filter_from_agent_line"] = i
                                if stripped.startswith("is_used_by_planner:"):
                                    value = self._clean_scalar_value(stripped.split(":", 1)[1].strip())
                                    current_io_field["has_is_used_by_planner"] = True
                                    current_io_field["is_used_by_planner_value"] = value
                                    current_io_field["is_used_by_planner_line"] = i
                                continue

                        if current_action["kind"] == "utility_transition":
                            property_name = stripped.split(":", 1)[0].strip()
                            if property_name in self.INVALID_TRANSITION_PROPERTIES:
                                current_action["invalid_transition_properties"].append((i, property_name))
                            continue

                # topic/start-level descriptions/system overrides outside action contexts
                if actions_mode is None and current_action is None:
                    if stripped.startswith("description:"):
                        desc_value = stripped.split(":", 1)[1].strip()
                        if desc_value in {"", "|", ">", "|-", ">-", "|+", ">+"}:
                            self.multiline_description_issues.append((i, current_top))
                        else:
                            self.block_descriptions.append(
                                {
                                    "name": current_block_name,
                                    "kind": current_top,
                                    "line": i,
                                    "description": self._clean_scalar_value(desc_value),
                                }
                            )
                        continue

                    if stripped.startswith("system:") and stripped != "system:":
                        self.topic_inline_system_lines.append((i, current_block_name or current_top))
                        continue

        # Check last IO field for filter/planner conflict before flush
        if current_io_field and current_io_field.get("has_filter_from_agent") and current_io_field.get("has_is_used_by_planner") and current_action:
            current_action["filter_planner_conflict_lines"].append(
                (current_io_field["is_used_by_planner_line"], current_io_field["name"], current_io_field["section"])
            )
        self._flush_action(current_action)
        if current_connection:
            self.connection_blocks.append(current_connection)

    def validate(self) -> dict:
        self._check_mixed_indentation()
        self._check_boolean_case()
        self._check_required_blocks()
        self._check_config_fields()
        self._check_start_agent_count()
        self._check_name_collisions()
        self._check_naming_rules()
        self._check_invalid_connections_wrapper()
        self._check_invalid_top_level_actions()
        self._check_mutable_linked_conflict()
        self._check_reserved_variable_names()
        self._check_reserved_field_names()
        self._check_linked_variable_defaults()
        self._check_linked_variable_types()
        self._check_undefined_variables()
        self._check_undefined_topics()
        self._check_multiline_descriptions()
        self._check_topic_system_override_syntax()
        self._check_lifecycle_instruction_wrappers()
        self._check_lifecycle_pipe_content()
        self._check_lifecycle_run_portability()
        self._check_lifecycle_arithmetic_null_guard()
        self._check_post_action_position()
        self._check_empty_list_literals()
        self._check_inputs_in_set()
        self._check_bare_run_actions()
        self._check_run_resolution_to_definition_scope()
        self._check_action_metadata_context()
        self._check_target_action_io_completeness()
        self._check_multiple_available_when()
        self._check_confirmation_runtime_gap()
        self._check_prompt_output_displayability()
        self._check_prompt_hidden_outputs_need_planner()
        self._check_date_type_in_action_io()
        self._check_filter_planner_conflict()
        self._check_is_required_advisories()
        self._check_user_input_string_matching()
        self._check_string_method_portability()
        self._check_structured_output_scalar_assignment()
        self._check_invalid_else_if()
        self._check_nested_if_blocks()
        self._check_empty_conditional_bodies()
        self._check_ellipsis_misuse()
        self._check_connection_block_completeness()
        self._check_agent_type_specific_patterns()
        self._check_service_agent_user_in_org()
        self._check_apex_target_existence()
        self._check_service_agent_target_permissions()
        self._check_connection_route_flow_readiness()
        self._check_large_file_risk()
        self._check_duplicate_descriptions()
        self._check_transition_naming_conventions()
        self._check_sensitive_actions_without_guards()
        self._check_welcome_error_patterns()
        self._check_escalation_fallback_heuristic()
        self._check_platform_guardrail_topic_conflict()

        return {
            "success": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "file_path": self.file_path,
            "checklist": self._build_checklist(),
        }

    def _check_mixed_indentation(self):
        has_tabs = False
        has_spaces = False
        tab_line = None
        space_line = None

        for i, line in enumerate(self.lines, 1):
            leading = len(line) - len(line.lstrip())
            if leading <= 0:
                continue
            leading_chars = line[:leading]
            if "\t" in leading_chars:
                has_tabs = True
                if tab_line is None:
                    tab_line = i
            if " " in leading_chars:
                has_spaces = True
                if space_line is None:
                    space_line = i

        if has_tabs and has_spaces:
            self._add_error(
                tab_line or 1,
                f"Mixed tabs and spaces detected. Tabs first seen on line {tab_line}, spaces first seen on line {space_line}. Use consistent indentation (all tabs OR all spaces).",
                "ASV-STR-001",
            )

    def _check_boolean_case(self):
        assignment_pattern = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_:\- ]*\s*[:=]\s*(true|false)\s*(?:#.*)?$", re.IGNORECASE)
        for i, line in enumerate(self.lines, 1):
            match = assignment_pattern.match(line)
            if not match:
                continue
            value = match.group(1)
            if value.lower() == "true" and value != "True":
                self._add_error(i, f"Boolean must be capitalized: use 'True' instead of '{value}'.", "ASV-STR-002")
            elif value.lower() == "false" and value != "False":
                self._add_error(i, f"Boolean must be capitalized: use 'False' instead of '{value}'.", "ASV-STR-002")

    def _check_required_blocks(self):
        required = {"system": False, "config": False, "start_agent": False}
        for line in self.lines:
            stripped = line.strip()
            if stripped.startswith("system:"):
                required["system"] = True
            elif stripped.startswith("config:"):
                required["config"] = True
            elif stripped.startswith("start_agent "):
                required["start_agent"] = True
        missing = [name for name, present in required.items() if not present]
        if missing:
            self._add_error(
                1,
                f"Missing required blocks: {', '.join(missing)}. Every agent needs config, system, and exactly one start_agent.",
                "ASV-STR-003",
            )

    def _check_config_fields(self):
        developer_name = self.config_fields.get("developer_name")
        legacy_agent_name = self.config_fields.get("agent_name")
        compatibility_agent_description = self.config_fields.get("agent_description")
        config_description = self.config_fields.get("description")
        agent_type = self.config_fields.get("agent_type")
        default_agent_user = self.config_fields.get("default_agent_user")

        if not developer_name and not legacy_agent_name:
            self._add_error(1, "Missing agent identifier in config block. Use either 'developer_name' or legacy 'agent_name'.", "ASV-CFG-001")
        if not compatibility_agent_description and not config_description:
            self._add_error(1, "Missing agent description in config block. Use either 'description' or compatibility 'agent_description'.", "ASV-CFG-001")

        if compatibility_agent_description and config_description:
            self._add_warning(compatibility_agent_description[1], "Config defines both 'description:' and 'agent_description:'. Use one field; public docs/examples prefer 'description:'.", "ASV-CFG-003")

        for line in self.default_agent_user_comment_lines:
            self._add_warning(
                line,
                "default_agent_user should contain only the username literal. Remove inline comments or trailing text so org-aware validation and publish-time resolution stay reliable.",
                "ASV-CFG-004",
            )

        enable_logs = self.config_fields.get("enable_enhanced_event_logs")
        if enable_logs and enable_logs[0] not in {"True", "False"}:
            self._add_warning(
                enable_logs[1],
                "enable_enhanced_event_logs should be a boolean literal (True/False).",
                "ASV-CFG-005",
            )

        user_locale = self.config_fields.get("user_locale")
        if user_locale and not user_locale[0]:
            self._add_warning(user_locale[1], "user_locale is present but empty. Provide a locale string or remove the field.", "ASV-CFG-005")

        for optional_name in ("company", "role", "agent_version"):
            optional_field = self.config_fields.get(optional_name)
            if optional_field and not optional_field[0]:
                self._add_warning(optional_field[1], f"{optional_name} is present but empty. Remove it or provide a string value.", "ASV-CFG-005")

        for field_name in ("developer_name", "agent_name", "default_agent_user", "agent_label"):
            field = self.config_fields.get(field_name)
            if field and self._is_placeholder_value(field[0]):
                self._add_warning(field[1], f"Config field '{field_name}' still contains a template placeholder ('{field[0]}'). Replace it before preview/publish.", "ASV-CFG-007")

        if not agent_type:
            if not default_agent_user:
                self._add_error(
                    1,
                    "Missing both 'agent_type' and 'default_agent_user'. Without agent_type the compiler defaults to a Service Agent, which requires default_agent_user.",
                    "ASV-CFG-002",
                )
            else:
                self._add_warning(
                    1,
                    "Missing 'agent_type'. This compiles when 'default_agent_user' is present because the compiler defaults to a Service Agent, but setting agent_type explicitly is safer.",
                    "ASV-CFG-002",
                )
            return

        agent_type_value, agent_type_line = agent_type
        if agent_type_value not in {"AgentforceServiceAgent", "AgentforceEmployeeAgent"}:
            self._add_error(
                agent_type_line,
                f"Invalid agent_type '{agent_type_value}'. Use 'AgentforceServiceAgent' or 'AgentforceEmployeeAgent'.",
                "ASV-CFG-002",
            )
            return

        if agent_type_value == "AgentforceServiceAgent" and not default_agent_user:
            self._add_error(
                agent_type_line,
                "Service Agents require 'default_agent_user' in config. Set it to a valid Einstein Agent User.",
                "ASV-CFG-002",
            )

        if agent_type_value == "AgentforceEmployeeAgent" and default_agent_user:
            self._add_error(
                default_agent_user[1],
                "Employee Agents must NOT include 'default_agent_user'. Remove it entirely; Employee Agents run as the logged-in user.",
                "ASV-CFG-002",
            )

    def _check_start_agent_count(self):
        count = len(self.start_agent_names)
        if count == 0:
            self._add_error(1, "Missing start_agent block. Every agent needs exactly one start_agent.", "ASV-STR-004")
        elif count > 1:
            first_line = sorted(self.start_agent_names.values())[1]
            self._add_error(first_line, f"Found {count} start_agent blocks. Exactly one start_agent is allowed.", "ASV-STR-004")

    def _check_name_collisions(self):
        for name, line in self.start_agent_names.items():
            if name in self.topic_names:
                self._add_error(
                    line,
                    f"Name collision: start_agent '{name}' has the same API name as a topic. This is a proven publish blocker because generated GenAiPluginDefinition metadata collides; use unique names.",
                    "ASV-STR-005",
                )

    def _check_name_rules(self, name: str, line: int, kind: str):
        if self._is_placeholder_value(name):
            self._add_warning(
                line,
                f"{kind} '{name}' looks like an unresolved template placeholder. Replace it with a concrete API-safe name before publish.",
                "ASV-CFG-007",
            )
            return
        if not self.NAME_PATTERN.match(name):
            self._add_error(
                line,
                f"Invalid {kind} '{name}'. Names must start with a letter and contain only letters, numbers, and underscores (max 80 chars).",
                "ASV-STR-006",
            )
            return
        if "__" in name:
            self._add_error(line, f"Invalid {kind} '{name}'. Consecutive underscores are not allowed.", "ASV-STR-006")
        if name.endswith("_"):
            self._add_error(line, f"Invalid {kind} '{name}'. Names cannot end with an underscore.", "ASV-STR-006")

    def _check_naming_rules(self):
        if "developer_name" in self.config_fields:
            name, line = self.config_fields["developer_name"]
            self._check_name_rules(name, line, "developer_name")
        elif "agent_name" in self.config_fields:
            name, line = self.config_fields["agent_name"]
            self._check_name_rules(name, line, "agent_name")

        for name, line in self.topic_names.items():
            self._check_name_rules(name, line, "topic name")
        for name, line in self.start_agent_names.items():
            self._check_name_rules(name, line, "start_agent name")
        for name, line in self.variable_names.items():
            self._check_name_rules(name, line, "variable name")

    def _check_invalid_connections_wrapper(self):
        for i, line in enumerate(self.lines, 1):
            if line.strip() == "connections:":
                self._add_error(i, "Invalid top-level block 'connections:'. Use 'connection messaging:' (singular) instead.", "ASV-STR-007")

    def _check_invalid_top_level_actions(self):
        for line in self.top_level_actions_lines:
            self._add_error(line, "Top-level 'actions:' blocks are not valid. Define actions inside a topic or start_agent block only.", "ASV-STR-017")

    def _check_mutable_linked_conflict(self):
        pattern = re.compile(r"mutable\s+linked|linked\s+mutable", re.IGNORECASE)
        for i, line in enumerate(self.lines, 1):
            if pattern.search(line):
                self._add_error(
                    i,
                    "Variable cannot be both 'mutable' AND 'linked'. Use 'mutable' for changeable state and 'linked' for external read-only data.",
                    "ASV-STR-008",
                )

    def _check_reserved_variable_names(self):
        for name, line in self.variable_names.items():
            if name in self.RESERVED_CONTEXT_VARIABLE_NAMES:
                self._add_warning(
                    line,
                    f"Variable name '{name}' may conflict with platform context mappings. Prefer a prefixed name like 'customer_{name.lower()}'.",
                    "ASV-STR-009",
                )

    def _check_reserved_field_names(self):
        for variable in self.variable_definitions:
            if variable["name"] in self.RESERVED_FIELD_NAMES:
                self._add_error(
                    variable["line"],
                    f"Variable name '{variable['name']}' is reserved in recent Agent Script / invocable parsing paths. Rename it (for example '{variable['name']}_field' or '{variable['name']}_text').",
                    "ASV-STR-021",
                )

        for action in self.action_definitions:
            for line, field_name, section in action.get("reserved_io_field_lines", []):
                self._add_error(
                    line,
                    f"Field name '{field_name}' in action {section} is reserved in recent Agent Script / invocable parsing paths. Rename the field to avoid parser failures.",
                    "ASV-STR-021",
                )

    def _check_linked_variable_defaults(self):
        for variable in self.variable_definitions:
            if variable["modifier"] == "linked" and variable.get("default") is not None:
                self._add_error(
                    variable["line"],
                    f"Linked variable '{variable['name']}' cannot declare a default value. Remove '= ...' and populate it via 'source:'.",
                    "ASV-STR-018",
                )

    def _check_linked_variable_types(self):
        for variable in self.variable_definitions:
            if variable["modifier"] != "linked":
                continue
            var_type = variable["type"]
            if var_type == "object" or var_type.startswith("list["):
                self._add_error(
                    variable["line"],
                    f"Linked variable '{variable['name']}' uses unsupported type '{var_type}'. Linked variables should use scalar types and be parsed downstream if needed.",
                    "ASV-STR-019",
                )

    def _check_undefined_variables(self):
        ref_pattern = re.compile(r"@variables\.([A-Za-z_][A-Za-z0-9_]*)")
        executable_prefixes = ("|", "if ", "set ", "run ", "with ", "available when", "transition to ")
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if not stripped.startswith(executable_prefixes):
                continue
            for name in ref_pattern.findall(stripped):
                if name not in self.variable_names:
                    self._add_error(i, f"Reference to undefined variable '@variables.{name}'. Declare it in the variables block first.", "ASV-STR-010")

    def _check_undefined_topics(self):
        ref_pattern = re.compile(r"@topic\.([A-Za-z][A-Za-z0-9_]*)")
        for i, line in enumerate(self.lines, 1):
            for name in ref_pattern.findall(line):
                if name not in self.defined_topics:
                    self._add_error(i, f"Reference to undefined topic '@topic.{name}'. Define the topic or fix the reference.", "ASV-STR-011")

    def _check_multiline_descriptions(self):
        for line, block_kind in self.multiline_description_issues:
            self._add_warning(
                line,
                f"{block_kind} description appears multiline or block-scalar based. Keep topic/start_agent description on a single line; multiline descriptions are a known parser gotcha.",
                "ASV-STR-012",
            )

    def _check_topic_system_override_syntax(self):
        for line, owner in self.topic_inline_system_lines:
            self._add_error(
                line,
                f"Topic '{owner}' uses shorthand 'system: ...'. Prefer the documented nested form: 'system:' followed by 'instructions:'.",
                "ASV-CFG-006",
            )

    def _check_lifecycle_instruction_wrappers(self):
        for line, lifecycle_name in self.lifecycle_instruction_wrappers:
            self._add_warning(
                line,
                f"{lifecycle_name} should contain direct content, not an 'instructions:' wrapper. Put procedural lines directly under {lifecycle_name}:.",
                "ASV-STR-013",
            )

    def _check_lifecycle_pipe_content(self):
        for line, lifecycle_name in self.lifecycle_pipe_lines:
            self._add_error(
                line,
                f"{lifecycle_name} contains a pipe-style prompt line. Lifecycle hooks should use deterministic statements like 'set', 'if', 'run', or 'transition to' rather than '|'.",
                "ASV-RUN-009",
            )

    def _check_lifecycle_run_portability(self):
        for line, lifecycle_name, action_name in self.lifecycle_run_lines:
            self._add_warning(
                line,
                f"{lifecycle_name} runs '@actions.{action_name}'. Lifecycle-hook 'run' syntax is valid but not portable enough to treat as universally reliable across bundle types and org states.",
                "ASV-RUN-010",
            )

    def _check_lifecycle_arithmetic_null_guard(self):
        # Build a set of (lifecycle_name, var_name, owner) tuples that have null guards
        guarded = set()
        for _, lifecycle_name, var_name, owner in self.lifecycle_null_guards:
            guarded.add((lifecycle_name, var_name, owner))

        for line, lifecycle_name, var_name, owner in self.lifecycle_arithmetic_lines:
            if (lifecycle_name, var_name, owner) not in guarded:
                var_def = self.variable_by_name.get(var_name)
                var_type = var_def["type"] if var_def else "unknown"
                if var_type in ("number", "integer"):
                    self._add_warning(
                        line,
                        f"{lifecycle_name} in '{owner}' does arithmetic on '@variables.{var_name}' without a null guard. "
                        f"Mutable number variables can be None at runtime (e.g., Eval API state injection, Testing Center). "
                        f"Add 'if @variables.{var_name} is None: set @variables.{var_name} = 0' before the arithmetic to prevent silent crashes.",
                        "ASV-RUN-021",
                    )

    def _check_post_action_position(self):
        in_instructions = False
        seen_pipe_text = False
        warned_in_block = False
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith("instructions:"):
                in_instructions = True
                seen_pipe_text = False
                warned_in_block = False
                continue
            if in_instructions:
                if stripped.startswith(("actions:", "topic ", "start_agent ", "before_reasoning:", "after_reasoning:")):
                    in_instructions = False
                    warned_in_block = False
                    continue
                if stripped.startswith("|"):
                    seen_pipe_text = True
                if not warned_in_block and seen_pipe_text and stripped.startswith("if ") and "@variables." in stripped:
                    if any(token in stripped for token in ["_status", "_done", "_complete", "_processed"]):
                        self._add_warning(
                            i,
                            "Post-action check appears after LLM instructions. Consider moving it to the top of instructions so it triggers on topic re-entry after action completion.",
                            "ASV-QLT-005",
                        )
                        warned_in_block = True

    def _check_empty_list_literals(self):
        compare_pattern = re.compile(r"^\s*if\s+.*(?:==|!=)\s*\[\]\s*:?\s*(?:#.*)?$")
        set_pattern = re.compile(r"^\s*set\s+.+?=\s*\[\]\s*(?:#.*)?$")
        for i, line in enumerate(self.lines, 1):
            if compare_pattern.search(line):
                self._add_error(i, "Empty list literal '[]' is not supported in expressions. Use len(@variables.list) == 0 instead.", "ASV-RUN-001")
            elif set_pattern.search(line):
                self._add_error(i, "Resetting with 'set ... = []' is a known parser gotcha. Use a temporary empty variable workaround instead.", "ASV-RUN-001")

    def _check_inputs_in_set(self):
        pattern = re.compile(r"^\s*set\s+@variables\.[^=]+\s*=\s*@inputs\.")
        for i, line in enumerate(self.lines, 1):
            if pattern.search(line):
                self._add_warning(i, "Using @inputs in set is a deploy-breaking anti-pattern. Capture input with @utils.setVariables or bind from @variables instead.", "ASV-RUN-002")

    def _check_bare_run_actions(self):
        pattern = re.compile(r"^\s*run\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:#.*)?$")
        for i, line in enumerate(self.lines, 1):
            match = pattern.search(line)
            if match:
                self._add_error(i, f"Bare action name '{match.group(1)}' in run. Use '@actions.{match.group(1)}' explicitly.", "ASV-RUN-003")

    def _check_run_resolution_to_definition_scope(self):
        definition_actions: Dict[str, Dict[str, Dict]] = {}
        reasoning_actions: Dict[str, Dict[str, Dict]] = {}
        for action in self.action_definitions:
            owner = action.get("owner") or ""
            if action.get("scope") == "definition":
                definition_actions.setdefault(owner, {})[action["name"]] = action
            elif action.get("scope") == "reasoning":
                reasoning_actions.setdefault(owner, {})[action["name"]] = action

        pattern = re.compile(r"^\s*run\s+@actions\.([A-Za-z_][A-Za-z0-9_]*)\b")
        for i, line in enumerate(self.lines, 1):
            match = pattern.match(line.strip())
            if not match:
                continue
            action_name = match.group(1)
            owner = self.line_owner.get(i)
            if not owner:
                continue

            definition_action = definition_actions.get(owner, {}).get(action_name)
            reasoning_action = reasoning_actions.get(owner, {}).get(action_name)

            if definition_action:
                if not definition_action.get("target"):
                    kind = definition_action.get("kind") or "action"
                    self._add_error(
                        i,
                        f"run @actions.{action_name} resolves to a non-target-backed '{kind}' action in '{owner}'. Deterministic 'run' only works for topic-level action definitions that declare 'target:'. Use direct 'set' / 'transition to', or let reasoning.actions invoke the utility/delegation instead.",
                        "ASV-RUN-014",
                    )
                continue

            if reasoning_action:
                self._add_error(
                    i,
                    f"run @actions.{action_name} resolves to a reasoning-only utility/delegation in '{owner}'. Deterministic 'run' only works for topic-level action definitions that declare 'target:'.",
                    "ASV-RUN-014",
                )
                continue

            available_targets = sorted(
                action["name"]
                for action in definition_actions.get(owner, {}).values()
                if action.get("target")
            )
            available_suffix = (
                f" Available deterministic targets in '{owner}': {', '.join(available_targets)}."
                if available_targets
                else ""
            )
            self._add_error(
                i,
                f"run @actions.{action_name} does not resolve to a topic-level target-backed action definition in '{owner}'. Deterministic 'run' requires a topic-level action with 'target:'.{available_suffix}",
                "ASV-RUN-014",
            )

    def _check_action_metadata_context(self):
        for action in self.action_definitions:
            if action["kind"] != "utility_transition":
                continue
            for line, property_name in action["invalid_transition_properties"]:
                self._add_error(
                    line,
                    f"'{property_name}' is not valid on @utils.transition actions. Use it only on target-backed action definitions with 'target:'.",
                    "ASV-RUN-004",
                )

    def _check_target_action_io_completeness(self):
        for action in self.action_definitions:
            if action.get("scope") != "definition" or not action.get("target"):
                continue
            if not action.get("has_outputs_block"):
                self._add_error(
                    action.get("target_line") or action["line"],
                    f"Target-backed action '{action['name']}' is missing an outputs: block. Server-side publish is known to fail when target actions omit outputs.",
                    "ASV-RUN-011",
                )

    def _check_multiple_available_when(self):
        for action in self.action_definitions:
            if action.get("available_when_count", 0) > 1:
                self._add_warning(
                    action["line"],
                    f"Action '{action['name']}' declares multiple 'available when' clauses. This can be org-dependent; prefer one compound condition for portability.",
                    "ASV-RUN-012",
                )

    def _check_confirmation_runtime_gap(self):
        for action in self.action_definitions:
            for line in action.get("require_user_confirmation_lines", []):
                self._add_warning(
                    line,
                    f"Action '{action['name']}' uses require_user_confirmation: True. This compiles, but runtime confirmation dialogs are unreliable; prefer an explicit two-step confirmation pattern plus an available-when guard.",
                    "ASV-RUN-013",
                )

    def _check_prompt_output_displayability(self):
        for action in self.action_definitions:
            target = action.get("target") or ""
            if not (target.startswith("prompt://") or target.startswith("generatePromptResponse://")):
                continue
            for line, field_name in action["prompt_output_display_lines"]:
                self._add_warning(
                    line,
                    f"Output '{field_name}' uses 'is_displayable: True' on a prompt target. This can cause blank agent responses; prefer 'is_displayable: False' with 'is_used_by_planner: True'.",
                    "ASV-RUN-005",
                )

    def _check_prompt_hidden_outputs_need_planner(self):
        for action in self.action_definitions:
            target = action.get("target") or ""
            if not (target.startswith("prompt://") or target.startswith("generatePromptResponse://")):
                continue
            for field in action.get("io_fields", []):
                if field.get("section") != "outputs":
                    continue

                hidden_via_display = field.get("has_is_displayable") and field.get("is_displayable_value") == "False"
                hidden_via_filter = field.get("has_filter_from_agent") and field.get("filter_from_agent_value") == "True"
                planner_visible = field.get("has_is_used_by_planner") and field.get("is_used_by_planner_value") == "True"

                if hidden_via_display and not planner_visible:
                    self._add_warning(
                        field.get("is_displayable_line") or field.get("line") or action.get("line") or 1,
                        f"Prompt output '{field['name']}' is hidden with 'is_displayable: False' but is not marked 'is_used_by_planner: True'. If this output should influence the reply or routing, make it planner-visible as well.",
                        "ASV-RUN-025",
                    )

                if hidden_via_filter and not planner_visible:
                    self._add_warning(
                        field.get("filter_from_agent_line") or field.get("line") or action.get("line") or 1,
                        f"Prompt output '{field['name']}' uses 'filter_from_agent: True'. That hides the field from direct display, but prompt outputs often also need planner visibility to influence the reply. If the planner needs this value, prefer 'is_displayable: False' + 'is_used_by_planner: True' on the prompt output instead of 'filter_from_agent'.",
                        "ASV-RUN-025",
                    )

    def _check_date_type_in_action_io(self):
        for action in self.action_definitions:
            for line, field_name, section in action["date_io_lines"]:
                self._add_warning(
                    line,
                    f"Field '{field_name}' uses 'date' in action {section}. Runtime support is unreliable; prefer 'object' with complex_data_type_name: \"lightning__dateType\" for action I/O.",
                    "ASV-RUN-006",
                )

    def _check_filter_planner_conflict(self):
        for action in self.action_definitions:
            for line, field_name, section in action.get("filter_planner_conflict_lines", []):
                self._add_error(
                    line,
                    f"Output '{field_name}' in action '{action['name']}' has both 'filter_from_agent' and 'is_used_by_planner'. These are mutually exclusive — remove 'is_used_by_planner' and use only 'filter_from_agent'. This causes InvalidFormatError and cascading ACTION_NOT_IN_SCOPE failures.",
                    "ASV-RUN-020",
                )

    def _check_is_required_advisories(self):
        for action in self.action_definitions:
            if action["has_available_when"]:
                continue
            for line, field_name in action["required_input_lines"]:
                self._add_warning(
                    line,
                    f"Input '{field_name}' uses 'is_required: True', but that is only a planner hint. Add an 'available when' guard if this input must gate execution.",
                    "ASV-RUN-007",
                )

    def _check_user_input_string_matching(self):
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if not (stripped.startswith("if ") or stripped.startswith("available when")):
                continue
            if "@system_variables.user_input" not in stripped:
                continue
            if re.search(r"\b(contains|startswith|endswith)\b", stripped):
                self._add_warning(
                    i,
                    "Raw '@system_variables.user_input' substring/prefix matching is brittle for deterministic routing. Normalize the utterance with Flow/Apex/classifier logic first, then branch on an explicit boolean or enum.",
                    "ASV-RUN-023",
                )

    def _check_string_method_portability(self):
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if not (stripped.startswith("if ") or stripped.startswith("available when")):
                continue
            if "@system_variables.user_input" in stripped:
                continue
            if re.search(r"\b(contains|startswith|endswith)\b", stripped):
                self._add_warning(
                    i,
                    "String-method guards (`contains` / `startswith` / `endswith`) are not portable enough for control-flow-critical validation. Prefer a Flow/Apex/classifier action that returns an explicit scalar when routing or policy depends on the result.",
                    "ASV-RUN-024",
                )

    def _check_structured_output_scalar_assignment(self):
        structured_outputs_by_owner: Dict[str, Dict[str, List[Dict]]] = {}
        for action in self.action_definitions:
            if action.get("scope") != "definition":
                continue
            owner = action.get("owner") or ""
            for field in action.get("io_fields", []):
                if field.get("section") != "outputs":
                    continue
                field_type = (field.get("type") or "").lower()
                if field_type == "object" or field_type.startswith("list["):
                    structured_outputs_by_owner.setdefault(owner, {}).setdefault(field.get("name") or "", []).append(field)

        assignment_pattern = re.compile(
            r"^\s*set\s+@variables\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*@outputs\.([A-Za-z_][A-Za-z0-9_]*)(?![\.\[])",
        )

        for i, line in enumerate(self.lines, 1):
            match = assignment_pattern.match(line)
            if not match:
                continue
            variable_name, output_name = match.groups()
            owner = self.line_owner.get(i)
            if not owner:
                continue

            structured_fields = structured_outputs_by_owner.get(owner, {}).get(output_name, [])
            if not structured_fields:
                continue

            variable_def = self.variable_by_name.get(variable_name)
            if not variable_def:
                continue
            variable_type = (variable_def.get("type") or "").lower()
            if variable_type == "object" or variable_type.startswith("list["):
                continue

            structured_type = structured_fields[0].get("type") or "object"
            self._add_warning(
                i,
                f"@outputs.{output_name} is declared as '{structured_type}' in '{owner}', but it is being assigned directly to scalar variable '@variables.{variable_name}' ({variable_type}). Do not assume structured outputs are scalars; access a concrete field (for example '@outputs.{output_name}.value' only if the schema exposes 'value') or flatten the output in Flow/Apex first.",
                "ASV-RUN-026",
            )

    def _check_invalid_else_if(self):
        pattern = re.compile(r"^\s*else\s+if\b")
        for i, line in enumerate(self.lines, 1):
            if pattern.search(line):
                self._add_error(i, "'else if' is not supported. Use a compound condition or flatten the logic into sequential if blocks.", "ASV-STR-015")

    def _check_nested_if_blocks(self):
        stack: List[Dict] = []
        conditional_start = re.compile(r"^\s*(if\b.*:|else:)\s*(?:#.*)?$")
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = self._indent(line)
            while stack and indent <= stack[-1]["indent"]:
                stack.pop()
            if conditional_start.match(line):
                if stack and indent > stack[-1]["indent"]:
                    self._add_error(i, "Nested 'if' blocks are not supported in Agent Script. Use compound predicates or flatten the logic.", "ASV-STR-016")
                stack.append({"indent": indent, "line": i})

    def _check_empty_conditional_bodies(self):
        blocks: List[Dict] = []
        conditional_start = re.compile(r"^\s*(if\b.*:|else:)\s*(?:#.*)?$")
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            indent = self._indent(line)

            while blocks and indent <= blocks[-1]["indent"] and stripped:
                block = blocks.pop()
                if not block["has_body"]:
                    self._add_error(
                        block["line"],
                        f"{block['kind']} block has no executable body. Add '|' text, 'set', 'run', or 'transition to' under the block.",
                        "ASV-STR-014",
                    )

            if not stripped or stripped.startswith("#"):
                continue

            if conditional_start.match(line):
                kind = "else" if stripped.startswith("else:") else "if"
                blocks.append({"line": i, "indent": indent, "kind": kind, "has_body": False})
                continue

            for block in blocks:
                if indent > block["indent"]:
                    block["has_body"] = True

        while blocks:
            block = blocks.pop()
            if not block["has_body"]:
                self._add_error(
                    block["line"],
                    f"{block['kind']} block has no executable body. Add '|' text, 'set', 'run', or 'transition to' under the block.",
                    "ASV-STR-014",
                )

    def _check_ellipsis_misuse(self):
        valid_with_pattern = re.compile(r"^\s*with\s+(?:\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_]*)\s*=\s*\.\.\.\s*(?:#.*)?$")
        invalid_pattern = re.compile(r"(?:=|:)\s*\.\.\.\s*(?:#.*)?$")
        for i, line in enumerate(self.lines, 1):
            if "..." not in line:
                continue
            stripped = line.strip()
            if valid_with_pattern.match(stripped):
                continue
            if invalid_pattern.search(stripped):
                self._add_error(i, "'...' is slot-filling syntax only. Use it in 'with param=...' bindings, not in variable declarations or general expressions.", "ASV-STR-020")

    def _check_connection_block_completeness(self):
        for block in self.connection_blocks:
            channel = block.get("channel")
            line = block.get("line") or 1
            fields = block.get("fields") or {}
            if channel not in {"messaging", "voice", "web"}:
                continue

            route_type = fields.get("outbound_route_type")
            route_name = fields.get("outbound_route_name")
            escalation_message = fields.get("escalation_message")

            if route_type or route_name or escalation_message:
                missing = []
                if not route_type:
                    missing.append("outbound_route_type")
                if not route_name:
                    missing.append("outbound_route_name")
                if not escalation_message:
                    missing.append("escalation_message")
                if missing:
                    self._add_error(
                        line,
                        f"connection {channel}: uses route configuration but is missing required field(s): {', '.join(missing)}. Route properties are all-or-nothing.",
                        "ASV-CON-001",
                    )

            if route_name:
                route_value, route_line = route_name
                if not route_value.startswith("flow://"):
                    self._add_error(
                        route_line,
                        f"connection {channel}: outbound_route_name must use a flow:// target. Found '{route_value}'.",
                        "ASV-CON-002",
                    )

            if route_type:
                route_type_value, route_type_line = route_type
                if route_type_value != "OmniChannelFlow":
                    self._add_warning(
                        route_type_line,
                        f"connection {channel}: outbound_route_type '{route_type_value}' is not the TDD-validated value 'OmniChannelFlow'. Verify it in the target org before publish.",
                        "ASV-CON-003",
                    )

    def _check_agent_type_specific_patterns(self):
        agent_type = self._effective_agent_type()
        if agent_type == "AgentforceEmployeeAgent":
            for line in self.connection_messaging_lines:
                self._add_warning(
                    line,
                    "Employee Agents typically should not include 'connection messaging:'. That block is generally for Service Agents / Messaging flows.",
                    "ASV-RUN-008",
                )
            for line in self.messaging_linked_var_lines:
                self._add_warning(
                    line,
                    "Messaging-linked variables are usually unnecessary for Employee Agents and may cause configuration issues if Messaging is not set up.",
                    "ASV-RUN-008",
                )

        if agent_type == "AgentforceServiceAgent":
            for line in self.context_linked_var_lines:
                self._add_warning(
                    line,
                    "Service Agent linked variable uses an @context.* source. These sources are not portable across NGA Service Agent configurations; verify the runtime surface carefully.",
                    "ASV-RUN-017",
                )

    def _check_service_agent_user_in_org(self):
        default_agent_user = self.config_fields.get("default_agent_user")
        effective_agent_type = self._effective_agent_type()
        if effective_agent_type != "AgentforceServiceAgent" or not default_agent_user:
            return

        username, line = default_agent_user
        if self._is_demo_user_value(username):
            self._add_warning(
                line,
                f"default_agent_user '{username}' looks like a template/demo value. Replace it with a real Einstein Agent User before preview/publish in a target org.",
                "ASV-CFG-007",
            )
            return

        if not self.validation_org:
            self._add_warning(line, "Could not run org-aware default_agent_user validation because no target org could be resolved.", "ASV-ORG-001")
            return

        query_result = self._query_user_in_org(username)
        if query_result.get("ok"):
            return

        reason = query_result.get("reason")
        record = query_result.get("record") or {}
        if reason == "missing":
            self._add_error(line, f"Service Agent default_agent_user '{username}' was not found in org '{self.validation_org}'.", "ASV-ORG-001")
        elif reason == "inactive":
            self._add_error(line, f"Service Agent default_agent_user '{username}' exists in '{self.validation_org}' but IsActive is false.", "ASV-ORG-001")
        elif reason == "automated_process":
            self._add_error(line, f"Service Agent default_agent_user '{username}' resolves to UserType=AutomatedProcess in '{self.validation_org}'. That is not a valid Einstein Agent User for Service Agent publishing.", "ASV-ORG-001")
        elif reason == "wrong_profile":
            profile_name = ((record.get("Profile") or {}).get("Name")) or "null"
            self._add_error(line, f"Service Agent default_agent_user '{username}' exists in '{self.validation_org}' but Profile.Name is '{profile_name}', not 'Einstein Agent User'.", "ASV-ORG-001")
        elif reason == "query_failed":
            detail = query_result.get("detail", "sf data query failed")
            self._add_warning(line, f"Could not verify default_agent_user '{username}' against org '{self.validation_org}'. sf data query failed: {detail}", "ASV-ORG-001")

    def _check_apex_target_existence(self):
        targets = self._collect_targets()
        apex_targets = targets["apex"]
        if not apex_targets or not self.validation_org:
            return

        query = self._query_apex_classes([name for name, _, _ in apex_targets])
        if not query.get("ok"):
            detail = query.get("detail", "sf data query failed")
            self._add_warning(1, f"Could not verify Apex target existence in '{self.validation_org}'. sf data query failed: {detail}", "ASV-ORG-006")
            return

        found_by_name = {record.get("Name"): record for record in (query.get("records") or [])}
        for apex_name, line, raw_target in apex_targets:
            if apex_name not in found_by_name:
                self._add_error(line, f"Apex target '{raw_target}' was not found in org '{self.validation_org}'. Deploy the class before publish.", "ASV-ORG-006")

    def _check_service_agent_target_permissions(self):
        default_agent_user = self.config_fields.get("default_agent_user")
        effective_agent_type = self._effective_agent_type()
        if effective_agent_type != "AgentforceServiceAgent" or not default_agent_user:
            return

        username, user_line = default_agent_user
        if not self.validation_org:
            return

        user_result = self._query_user_in_org(username)
        if not user_result.get("ok"):
            return

        targets = self._collect_targets()
        apex_targets = targets["apex"]
        flow_targets = targets["flow"]
        other_targets = targets["other"]
        if not apex_targets and not flow_targets and not other_targets:
            return

        assignments = self._query_permission_set_assignments(username)
        if not assignments.get("ok"):
            detail = assignments.get("detail", "sf data query failed")
            self._add_warning(user_line, f"Could not verify permission set assignments for Service Agent user '{username}' in '{self.validation_org}'. sf data query failed: {detail}", "ASV-ORG-002")
            return

        assigned_names = {((record.get("PermissionSet") or {}).get("Name")) for record in (assignments.get("records") or [])}
        assigned_names.discard(None)

        if not any(name == "AgentforceServiceAgentUser" or "AgentforceServiceAgentUser" in name for name in assigned_names):
            self._add_warning(
                user_line,
                f"Service Agent user '{username}' is missing a verified AgentforceServiceAgentUser permission set/group assignment in '{self.validation_org}'. Recommend assigning it before publish to avoid runtime/publish surprises.",
                "ASV-ORG-002",
            )

        agent_identifier = self._agent_identifier()
        custom_permset_name = f"{agent_identifier}_Access" if agent_identifier else None
        custom_assigned = bool(custom_permset_name and custom_permset_name in assigned_names)

        if apex_targets and not custom_assigned:
            first_line = apex_targets[0][1]
            self._add_warning(
                first_line,
                f"This Service Agent uses apex:// targets but user '{username}' is not assigned custom permission set '{custom_permset_name}'. Recommend creating/assigning '{custom_permset_name}' with <classAccesses> for every Apex class target.",
                "ASV-ORG-002",
            )

        if flow_targets and not custom_assigned:
            first_line = flow_targets[0][1]
            self._add_warning(
                first_line,
                f"This Service Agent uses flow:// targets but user '{username}' is not assigned custom permission set '{custom_permset_name}'. Flow internals still need object/field/Apex access; verify permissions explicitly.",
                "ASV-ORG-002",
            )

        if custom_assigned and custom_permset_name:
            permset_query = self._query_permission_set(custom_permset_name)
            permset_records = permset_query.get("records") if permset_query.get("ok") else []
            permset_id = permset_records[0].get("Id") if permset_records else None

            if apex_targets and permset_id:
                apex_query = self._query_apex_classes([name for name, _, _ in apex_targets])
                apex_by_name = {record.get("Name"): record for record in (apex_query.get("records") or [])} if apex_query.get("ok") else {}
                access_query = self._query_setup_entity_access(permset_id, [record.get("Id") for record in apex_by_name.values()], "ApexClass") if apex_by_name else {"ok": True, "records": []}
                access_by_id = {record.get("SetupEntityId"): record for record in (access_query.get("records") or [])} if access_query.get("ok") else {}
                for apex_name, line, raw_target in apex_targets:
                    apex_record = apex_by_name.get(apex_name)
                    if not apex_record:
                        self._add_warning(
                            line,
                            f"Could not verify Apex target '{raw_target}' in org '{self.validation_org}'. If this is namespaced or packaged, verify '{custom_permset_name}' includes explicit class access for it.",
                            "ASV-ORG-003",
                        )
                        continue
                    if apex_record.get("Id") not in access_by_id:
                        self._add_warning(
                            line,
                            f"Apex target '{raw_target}' is not granted in permission set '{custom_permset_name}'. Recommend adding <classAccesses><apexClass>{apex_name}</apexClass><enabled>true</enabled></classAccesses> and reassigning if needed.",
                            "ASV-ORG-003",
                        )
            elif apex_targets and not permset_id:
                first_line = apex_targets[0][1]
                self._add_warning(
                    first_line,
                    f"User '{username}' appears assigned to '{custom_permset_name}', but the permission set record could not be resolved in '{self.validation_org}'. Verify the permission set exists and includes class access entries.",
                    "ASV-ORG-003",
                )

        active_flows_query = self._query_active_flows([name for name, _, _ in flow_targets]) if flow_targets else {"ok": True, "records": []}
        active_flows = {record.get("ApiName"): record for record in (active_flows_query.get("records") or [])} if active_flows_query.get("ok") else {}
        for flow_name, line, raw_target in flow_targets:
            record = active_flows.get(flow_name)
            if not active_flows_query.get("ok"):
                detail = active_flows_query.get("detail", "sf data query failed")
                self._add_warning(line, f"Could not verify Flow target '{raw_target}' in '{self.validation_org}'. sf data query failed: {detail}", "ASV-ORG-004")
                continue
            if not record:
                self._add_error(line, f"Flow target '{raw_target}' was not found in org '{self.validation_org}'. Deploy the FlowDefinition before publish.", "ASV-ORG-004")
                continue
            if not record.get("ActiveVersionId"):
                self._add_error(line, f"Flow target '{raw_target}' exists in '{self.validation_org}' but has no active version. Activate the Flow before publish.", "ASV-ORG-004")

        for raw_target, line, _ in other_targets:
            self._add_warning(
                line,
                f"Target '{raw_target}' uses a protocol the validator cannot permission-check automatically. Verify the Service Agent user '{username}' has all required access before publish.",
                "ASV-ORG-005",
            )

    def _check_connection_route_flow_readiness(self):
        route_targets = self._collect_connection_route_targets()
        if not route_targets or not self.validation_org:
            return

        concrete_targets = []
        for flow_name, line, raw_target in route_targets:
            if self._is_placeholder_value(flow_name) or self._is_placeholder_value(raw_target):
                self._add_warning(
                    line,
                    f"Connection route Flow '{raw_target}' still contains a template placeholder. Replace it with a real Flow API name before publish.",
                    "ASV-CFG-007",
                )
                continue
            concrete_targets.append((flow_name, line, raw_target))

        if not concrete_targets:
            return

        query = self._query_active_flows([name for name, _, _ in concrete_targets])
        if not query.get("ok"):
            detail = query.get("detail", "sf data query failed")
            self._add_warning(1, f"Could not verify connection route Flows in '{self.validation_org}'. sf data query failed: {detail}", "ASV-ORG-007")
            return

        flows_by_name = {record.get("ApiName"): record for record in (query.get("records") or [])}
        for flow_name, line, raw_target in concrete_targets:
            record = flows_by_name.get(flow_name)
            if not record:
                self._add_error(line, f"Connection route Flow '{raw_target}' was not found in org '{self.validation_org}'. Deploy it before publish.", "ASV-ORG-007")
            elif not record.get("ActiveVersionId"):
                self._add_error(line, f"Connection route Flow '{raw_target}' exists in '{self.validation_org}' but has no active version. Activate it before publish.", "ASV-ORG-007")

    def _check_large_file_risk(self):
        if len(self.lines) > self.LARGE_FILE_LIMITS["lines"] or len(self.topic_names) > self.LARGE_FILE_LIMITS["topics"] or len(self.action_definitions) > self.LARGE_FILE_LIMITS["actions"]:
            self._add_warning(
                1,
                f"Agent size is high ({len(self.lines)} lines, {len(self.topic_names)} topics, {len(self.action_definitions)} actions). Large/complex .agent files are more likely to hit parser instability or authoring drift.",
                "ASV-RUN-019",
            )

    def _normalized_description(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def _check_duplicate_descriptions(self):
        topic_seen: Dict[str, Dict] = {}
        action_seen: Dict[Tuple[str, str], Dict] = {}

        for block in self.block_descriptions:
            normalized = self._normalized_description(block.get("description") or "")
            if not normalized:
                continue
            if normalized in topic_seen:
                first = topic_seen[normalized]
                self._add_warning(
                    block["line"],
                    f"Topic/start description duplicates '{first['name']}' almost exactly. Distinct descriptions improve planner/topic selection quality.",
                    "ASV-QLT-003",
                )
            else:
                topic_seen[normalized] = block

        for action in self.action_definitions:
            description = action.get("description") or ""
            normalized = self._normalized_description(description)
            if not normalized:
                continue
            key = (action.get("owner") or "", normalized)
            if key in action_seen:
                first = action_seen[key]
                self._add_warning(
                    action.get("description_line") or action["line"],
                    f"Action '{action['name']}' has a near-duplicate description of '{first['name']}' in the same block. Distinct descriptions improve action selection.",
                    "ASV-QLT-002",
                )
            else:
                action_seen[key] = action

    def _check_transition_naming_conventions(self):
        accepted_prefixes = ("go_to_", "go_", "back", "begin", "end_", "new_", "start_")
        for action in self.action_definitions:
            if action.get("kind") != "utility_transition":
                continue
            if action["name"].startswith(accepted_prefixes):
                continue
            self._add_warning(
                action["line"],
                f"Transition action '{action['name']}' does not use the recommended navigation naming prefixes ('go_to_', 'go_', 'back', 'start_'). Consistent naming makes routing graphs easier to read.",
                "ASV-QLT-001",
            )

    def _check_sensitive_actions_without_guards(self):
        for action in self.action_definitions:
            if action.get("scope") != "definition" or not action.get("target"):
                continue
            haystack = f"{action['name']} {action.get('description') or ''}".lower()
            if any(token in haystack for token in self.SENSITIVE_ACTION_TOKENS) and not action.get("has_available_when"):
                self._add_warning(
                    action.get("description_line") or action.get("target_line") or action["line"],
                    f"Sensitive action '{action['name']}' has no 'available when' guard. Consider adding deterministic gating for safety and policy control.",
                    "ASV-QLT-004",
                )

    def _check_welcome_error_patterns(self):
        for line, kind in self.welcome_error_inline_interpolation_lines:
            self._add_warning(line, f"{kind.title()} message uses `{{!...}}` interpolation in quoted string form. For dynamic system messages, switch to template/block form with `|`.", "ASV-RUN-015")
        for line, kind in self.welcome_error_folded_scalar_lines:
            self._add_warning(line, f"{kind.title()} message uses folded scalar style (`>`). Prefer literal block style (`|`) for dynamic or multiline system messages.", "ASV-RUN-016")

    def _check_escalation_fallback_heuristic(self):
        if "@utils.escalate" not in self.content or not self.connection_blocks:
            return
        fallback_tokens = ["leave_message", "escalation_attempted", "handoff_failed", "human_available", "before_reasoning:"]
        if not any(token in self.content for token in fallback_tokens):
            self._add_warning(
                1,
                "Agent uses @utils.escalate with connection routing but no obvious fallback/latch pattern was detected. Consider adding a before_reasoning guard or fallback topic to avoid escalation loops.",
                "ASV-RUN-018",
            )

    def _check_platform_guardrail_topic_conflict(self):
        """Warn when custom topics duplicate the 3 platform-injected guardrail tools.

        The platform auto-injects these tools into every topic's EnabledToolsStep:
          - Inappropriate Content Guardrail  (tool name: Inappropriate_Content)
          - Prompt Injection Guardrail       (tool name: Prompt_Injection)
          - Reverse Engineering Guardrail    (tool name: Reverse_Engineering)

        Custom AgentScript topics with the same or similar names create 3+3 tool
        duplication in the LLM tool set, confusing the planner and causing
        "unexpected error" crashes when both the platform tool and the custom
        topic fire on the same input. The platform tools cannot be disabled.

        Recommended fix: Remove the custom guardrail topics and let the platform's
        built-in guardrail tools handle content moderation.
        """
        platform_guardrail_patterns = {
            "inappropriate": "Inappropriate Content Guardrail",
            "prompt_injection": "Prompt Injection Guardrail",
            "reverse_engineering": "Reverse Engineering Guardrail",
        }

        conflicting_topics = []
        for topic_name, line_num in self.topic_names.items():
            topic_lower = topic_name.lower()
            for pattern, platform_name in platform_guardrail_patterns.items():
                if pattern in topic_lower:
                    conflicting_topics.append((topic_name, line_num, platform_name))

        # Also check for transition actions in start_agent that route to guardrail topics
        guardrail_transitions = []
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            for pattern in platform_guardrail_patterns:
                if f"@topic." in stripped and pattern in stripped.lower() and "transition" in stripped.lower():
                    guardrail_transitions.append((i, stripped))

        if conflicting_topics:
            topic_list = ", ".join(f"'{t[0]}' (line {t[1]}, conflicts with {t[2]})" for t in conflicting_topics)
            self._add_warning(
                conflicting_topics[0][1],
                f"Custom guardrail topic(s) {topic_list} duplicate the platform's built-in guardrail tools. "
                f"The platform auto-injects 'Inappropriate Content Guardrail', 'Prompt Injection Guardrail', and "
                f"'Reverse Engineering Guardrail' into every topic's tool set. Custom topics with similar names create "
                f"3+3 tool duplication, confusing the LLM planner and causing 'unexpected error' crashes. "
                f"Consider removing custom guardrail topics and relying on the platform's built-in guardrail tools.",
                "ASV-RUN-022",
            )

    def _issue_texts(self, severity: str) -> List[str]:
        issues = self.errors if severity == "error" else self.warnings
        return [message for _, _, message in issues]

    def _checklist_entry(self, section: str, label: str, error_terms: List[str], warning_terms: Optional[List[str]] = None, success_detail: str = "No issues found.", na_detail: Optional[str] = None, applicable: bool = True, confidence: Optional[str] = None) -> Dict[str, str]:
        if not applicable:
            return {"section": section, "status": "info", "icon": "ℹ️", "label": label, "detail": na_detail or "Not applicable.", "confidence": confidence or "Informational"}

        warning_terms = warning_terms or error_terms
        error_matches = [msg for msg in self._issue_texts("error") if any(term in msg for term in error_terms)]
        if error_matches:
            return {"section": section, "status": "error", "icon": "❌", "label": label, "detail": error_matches[0], "confidence": confidence or "Blocking"}

        warning_matches = [msg for msg in self._issue_texts("warning") if any(term in msg for term in warning_terms)]
        if warning_matches:
            return {"section": section, "status": "warning", "icon": "⚠️", "label": label, "detail": warning_matches[0], "confidence": confidence or "Warning"}

        return {"section": section, "status": "ok", "icon": "✅", "label": label, "detail": success_detail, "confidence": confidence or "Check"}

    def _build_checklist(self) -> List[Dict[str, str]]:
        effective_agent_type = self._effective_agent_type()
        targets = self._collect_targets()
        route_targets = self._collect_connection_route_targets()
        has_targets = bool(targets["apex"] or targets["flow"] or targets["other"])
        service_agent = effective_agent_type == "AgentforceServiceAgent"
        employee_agent = effective_agent_type == "AgentforceEmployeeAgent"
        prompt_targets_present = any((action.get("target") or "").startswith(("prompt://", "generatePromptResponse://")) for action in self.action_definitions)

        return [
            self._checklist_entry("Structure", "Indentation consistency", ["ASV-STR-001"], success_detail="Tabs/spaces usage is consistent.", confidence="Compiler rule"),
            self._checklist_entry("Structure", "Boolean capitalization", ["ASV-STR-002"], success_detail="Boolean literals use True/False correctly.", confidence="Compiler rule"),
            self._checklist_entry("Structure", "Required top-level blocks", ["ASV-STR-003"], success_detail="config, system, and start_agent blocks are present.", confidence="Compiler rule"),
            self._checklist_entry("Structure", "Exactly one start_agent", ["ASV-STR-004"], success_detail="Exactly one start_agent block is defined.", confidence="Compiler rule"),
            self._checklist_entry("Structure", "Topic/start_agent naming collisions", ["ASV-STR-005"], success_detail="No topic/start_agent API-name collisions detected.", confidence="Proven publish blocker"),
            self._checklist_entry("Structure", "Naming rule compliance", ["ASV-STR-006"], success_detail="Names follow Agent Script naming rules."),
            self._checklist_entry("Structure", "Connections/actions top-level blocks", ["ASV-STR-007", "ASV-STR-017"], success_detail="No invalid top-level connections/actions wrappers detected."),
            self._checklist_entry("Structure", "Variable and field safety", ["ASV-STR-008", "ASV-STR-009", "ASV-STR-010", "ASV-STR-018", "ASV-STR-019", "ASV-STR-020", "ASV-STR-021"], success_detail="Variable declarations, field names, and executable references look consistent."),
            self._checklist_entry("Structure", "Topic references", ["ASV-STR-011"], success_detail="All @topic references resolve to defined topics."),
            self._checklist_entry("Structure", "Description formatting", ["ASV-STR-012"], success_detail="Topic/start_agent descriptions stay on a single safe line."),
            self._checklist_entry("Structure", "Conditional block structure", ["ASV-STR-014", "ASV-STR-015", "ASV-STR-016"], success_detail="Conditional blocks avoid unsupported else-if/nested/empty-body patterns."),
            self._checklist_entry("Structure", "Lifecycle hook formatting", ["ASV-STR-013", "ASV-RUN-009", "ASV-RUN-010"], success_detail="Lifecycle hooks use direct deterministic content."),
            self._checklist_entry("Structure", "Lifecycle arithmetic null guards", ["ASV-RUN-021"], success_detail="Lifecycle arithmetic operations have null guards.", na_detail="No lifecycle arithmetic operations detected.", applicable=bool(self.lifecycle_arithmetic_lines), confidence="Runtime crash risk"),
            self._checklist_entry("Agent identity", "Config field completeness", ["ASV-CFG-001", "ASV-CFG-003", "ASV-CFG-004", "ASV-CFG-005", "ASV-CFG-007"], success_detail="Config fields are present and shaped safely.", confidence="Compiler / authoring rule"),
            self._checklist_entry("Agent identity", "Service vs Employee agent semantics", ["ASV-CFG-002"], success_detail="Agent type and default_agent_user relationship is valid.", confidence="Compiler / platform rule"),
            self._checklist_entry("Agent identity", "Topic system override syntax", ["ASV-CFG-006"], success_detail="Topic-level system overrides use the documented nested form.", na_detail="No topic-level system override shorthand detected.", applicable=bool(self.topic_inline_system_lines), confidence="Docs alignment / future-proofing"),
            self._checklist_entry("Connections", "Connection routing completeness", ["ASV-CON-001", "ASV-CON-002", "ASV-CON-003"], success_detail="Connection routing fields are complete and use validated shapes.", na_detail="No connection routing blocks detected.", applicable=bool(self.connection_blocks), confidence="Publish / runtime rule"),
            self._checklist_entry("Targets & permissions", "Service Agent user exists in target org", ["ASV-ORG-001"], success_detail="default_agent_user resolves to an active Einstein Agent User.", na_detail="Not applicable to Employee Agents or agents without default_agent_user.", applicable=service_agent and bool(self.config_fields.get("default_agent_user")), confidence="Configuration drift / publish risk"),
            self._checklist_entry("Targets & permissions", "Apex target existence", ["ASV-ORG-006"], success_detail="All apex:// targets exist in the resolved org.", na_detail="No apex:// targets detected.", applicable=bool(targets["apex"]), confidence="Publish rule"),
            self._checklist_entry("Targets & permissions", "Required Service Agent permission assignments", ["ASV-ORG-002"], success_detail="Required system/custom permission assignments are present for the detected targets.", na_detail="No Service Agent target-backed actions require permission assignment checks.", applicable=service_agent and has_targets, confidence="Likely runtime risk"),
            self._checklist_entry("Targets & permissions", "Apex target permission coverage", ["ASV-ORG-003"], success_detail="All apex:// targets are covered by the assigned custom permission set.", na_detail="No apex:// targets detected.", applicable=service_agent and bool(targets["apex"]), confidence="Likely runtime risk"),
            self._checklist_entry("Targets & permissions", "Flow target readiness", ["ASV-ORG-004"], success_detail="All flow:// targets exist and have an active version.", na_detail="No flow:// targets detected.", applicable=bool(targets["flow"]), confidence="Proven publish blocker"),
            self._checklist_entry("Targets & permissions", "Connection route flow readiness", ["ASV-ORG-007"], success_detail="All connection route Flows exist and have an active version.", na_detail="No outbound connection route Flows detected.", applicable=bool(route_targets), confidence="Proven publish blocker"),
            self._checklist_entry("Targets & permissions", "Other target protocol review", ["ASV-ORG-005"], success_detail="All detected target protocols are fully supported by automatic checks.", na_detail="No non-apex/non-flow targets detected.", applicable=bool(targets["other"]), confidence="Manual review"),
            self._checklist_entry("Runtime gotchas", "Collection / set gotchas", ["ASV-RUN-001", "ASV-RUN-002"], success_detail="No known collection/set gotchas detected.", confidence="Compiler / deploy rule"),
            self._checklist_entry("Runtime gotchas", "Action invocation syntax", ["ASV-RUN-003", "ASV-RUN-014"], success_detail="run statements resolve only to topic-level target-backed @actions definitions.", confidence="Compiler / resolution rule"),
            self._checklist_entry("Runtime gotchas", "Utility action metadata", ["ASV-RUN-004"], success_detail="@utils.transition metadata usage is valid.", confidence="Compiler rule"),
            self._checklist_entry("Runtime gotchas", "Target action schema completeness", ["ASV-RUN-011"], success_detail="Target-backed actions declare outputs: blocks for publish safety.", na_detail="No target-backed action definitions detected.", applicable=has_targets, confidence="Publish blocker"),
            self._checklist_entry("Runtime gotchas", "Multiple available-when portability", ["ASV-RUN-012"], success_detail="Actions avoid duplicate available-when clauses.", na_detail="No actions detected.", applicable=bool(self.action_definitions), confidence="Org-dependent behavior"),
            self._checklist_entry("Runtime gotchas", "Confirmation dialog reliability", ["ASV-RUN-013"], success_detail="No risky require_user_confirmation usage detected.", na_detail="No target-backed action definitions detected.", applicable=bool(self.action_definitions), confidence="Runtime gap"),
            self._checklist_entry("Runtime gotchas", "Prompt output displayability", ["ASV-RUN-005", "ASV-RUN-025"], success_detail="Prompt outputs use safe display/planner visibility settings.", na_detail="No prompt targets detected.", applicable=prompt_targets_present, confidence="Runtime gotcha"),
            self._checklist_entry("Runtime gotchas", "Action I/O date typing", ["ASV-RUN-006"], success_detail="No risky 'date' action I/O declarations detected.", na_detail="No action I/O declarations detected.", applicable=bool(self.action_definitions), confidence="Runtime gotcha"),
            self._checklist_entry("Runtime gotchas", "Output visibility conflict", ["ASV-RUN-020"], success_detail="No filter_from_agent + is_used_by_planner conflicts detected.", na_detail="No action output declarations detected.", applicable=bool(self.action_definitions), confidence="Blocking / cascade risk"),
            self._checklist_entry("Runtime gotchas", "Planner-required input hints", ["ASV-RUN-007"], success_detail="Required inputs are either guarded or not using the risky planner-only hint.", na_detail="No action inputs detected.", applicable=bool(self.action_definitions), confidence="Planner behavior"),
            self._checklist_entry("Runtime gotchas", "Deterministic string-guard portability", ["ASV-RUN-023", "ASV-RUN-024"], success_detail="No brittle raw-user-input or string-method guards detected.", confidence="Portability warning"),
            self._checklist_entry("Runtime gotchas", "Structured output access", ["ASV-RUN-026"], success_detail="Structured outputs are not being assigned directly into scalar variables.", na_detail="No structured-output direct assignments detected.", applicable=bool(self.action_definitions), confidence="Schema / runtime warning"),
            self._checklist_entry("Runtime gotchas", "Agent-type-specific messaging/context patterns", ["ASV-RUN-008", "ASV-RUN-017"], success_detail="No agent-type-specific Messaging/context issues detected.", na_detail="No employee/service-agent-only Messaging/context checks apply.", applicable=employee_agent or service_agent, confidence="Runtime / portability"),
            self._checklist_entry("Runtime gotchas", "Welcome/error message stability", ["ASV-RUN-015", "ASV-RUN-016"], success_detail="System welcome/error messages avoid inline interpolation and folded-scalar pitfalls.", na_detail="No obvious welcome/error message patterns detected.", applicable=bool(self.welcome_error_inline_interpolation_lines or self.welcome_error_folded_scalar_lines), confidence="Authoring guidance"),
            self._checklist_entry("Runtime gotchas", "Escalation fallback resilience", ["ASV-RUN-018"], success_detail="Escalation usage includes an obvious fallback or latch pattern.", na_detail="No @utils.escalate usage detected.", applicable="@utils.escalate" in self.content, confidence="Heuristic warning"),
            self._checklist_entry("Runtime gotchas", "Large file parser risk", ["ASV-RUN-019"], success_detail="File size/complexity stays below the configured parser-risk thresholds.", confidence="Heuristic warning"),
            self._checklist_entry("Runtime gotchas", "Platform guardrail topic conflict", ["ASV-RUN-022"], success_detail="No custom topics duplicate the platform's built-in guardrail tools.", na_detail="No guardrail-related topic names detected.", applicable=any(p in n.lower() for n in self.topic_names for p in ("inappropriate", "prompt_injection", "reverse_engineering")), confidence="Runtime crash risk"),
            self._checklist_entry("Quality", "Transition naming conventions", ["ASV-QLT-001"], success_detail="Transition actions follow the recommended go_to_ naming pattern.", na_detail="No utility transitions detected.", applicable=any(action.get("kind") == "utility_transition" for action in self.action_definitions), confidence="Style / maintainability"),
            self._checklist_entry("Quality", "Action description distinctness", ["ASV-QLT-002"], success_detail="Action descriptions are distinct enough to guide planner selection.", na_detail="No repeated action descriptions detected.", applicable=bool(self.action_definitions), confidence="LLM routing quality"),
            self._checklist_entry("Quality", "Topic description distinctness", ["ASV-QLT-003"], success_detail="Topic descriptions are distinct enough to guide topic selection.", na_detail="No repeated topic/start descriptions detected.", applicable=bool(self.block_descriptions), confidence="LLM routing quality"),
            self._checklist_entry("Quality", "Sensitive action guard suggestions", ["ASV-QLT-004"], success_detail="Sensitive actions use deterministic gating or avoid risky verbs.", na_detail="No obviously sensitive target-backed actions detected.", applicable=bool(self.action_definitions), confidence="Best practice"),
        ]


def format_output(result: dict) -> str:
    lines = []
    file_name = Path(result["file_path"]).name
    checklist = result.get("checklist") or []

    if result["success"]:
        lines.append(f"✅ Agent Script Validation Passed: {file_name}")
    else:
        lines.append(f"❌ Agent Script validation found blocking issues in {file_name}")

    error_count = sum(1 for item in checklist if item.get("status") == "error")
    warning_count = sum(1 for item in checklist if item.get("status") == "warning")
    info_count = sum(1 for item in checklist if item.get("status") == "info")
    ok_count = sum(1 for item in checklist if item.get("status") == "ok")

    lines.append(f"📊 Summary: {error_count} blocking, {warning_count} warnings, {info_count} informational, {ok_count} passing checks")

    if result["errors"]:
        recommendation = "Fix blocking issues before preview/publish."
    elif result["warnings"]:
        recommendation = "Safe to preview. Review warnings before publish."
    else:
        recommendation = "Safe to preview and publish."

    lines.append(f"➡️ Recommended next step: {recommendation}")
    lines.append("")
    lines.append("Validation checklist")
    lines.append("--------------------")

    current_section = None
    for item in checklist:
        section = item.get("section", "General")
        if section != current_section:
            if current_section is not None:
                lines.append("")
            lines.append(f"{section}:")
            current_section = section
        confidence = item.get("confidence")
        confidence_text = f" [{confidence}]" if confidence else ""
        lines.append(f"  {item['icon']} {item['label']}{confidence_text} — {item['detail']}")

    if result["errors"]:
        lines.append("")
        lines.append("Blocking issues")
        lines.append("---------------")
        for line_num, _, message in result["errors"]:
            lines.append(f"❌ Line {line_num}: {message}")
        lines.append("")
        lines.append("Fix the blocking issues above before validate/preview/publish.")

    if result["warnings"]:
        lines.append("")
        lines.append("Warnings")
        lines.append("--------")
        for line_num, _, message in result["warnings"]:
            lines.append(f"⚠️ Line {line_num}: {message}")

    return "\n".join(lines)


def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path.endswith(".agent"):
        sys.exit(0)
    if not os.path.exists(file_path):
        sys.exit(0)

    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            content = handle.read()
    except Exception as exc:
        print(f"⚠️ Could not read {file_path}: {exc}")
        sys.exit(0)

    validator = AgentScriptValidator(content, file_path)
    result = validator.validate()
    output = format_output(result)
    if output:
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
