"""Control-plane commands shared by terminal scripts and the interactive surface."""

from __future__ import annotations

import json
from typing import Any

from .runtime import TerminalRuntime


def redact(value: Any) -> Any:
    """Recursively redact fields that commonly contain credentials."""
    secret_names = {
        "api_key", "access_key_id", "secret_access_key", "session_token",
        "service_account_json", "bedrock_api_key", "vertex_api_key",
        "password", "authorization", "bearer", "token", "client_secret",
    }
    if isinstance(value, dict):
        return {
            k: ("[redacted]" if k.lower() in secret_names else redact(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def render(value: Any, *, as_json: bool = False) -> str:
    value = redact(value)
    if as_json:
        return json.dumps(value, indent=2, default=str)
    if isinstance(value, list):
        if not value:
            return "(none)"
        if all(isinstance(row, dict) for row in value):
            keys = list(dict.fromkeys(k for row in value for k in row))
            lines = ["  ".join(keys)]
            lines.extend("  ".join(str(row.get(k, "")) for k in keys) for row in value)
            return "\n".join(lines)
        return "\n".join(str(v) for v in value)
    if isinstance(value, dict):
        return "\n".join(f"{k}: {v}" for k, v in value.items())
    return str(value)


def execute_control(runtime: TerminalRuntime, group: str, action: str | None, args: Any) -> Any:
    """Execute the safe, read/control operations that already have manager APIs."""
    manager = runtime.manager
    action = action or "list"
    if group in {"session", "sessions"}:
        if action in {"list", "ls"}:
            return manager.list_sessions(getattr(args, "workspace", None))
        if action == "show":
            sid = args.id
            return {"session": next((s for s in manager.list_sessions() if s["session_id"] == sid), None), "messages": manager.session_messages(sid)}
        if action == "rename":
            return manager.rename_session(args.id, args.title)
        if action == "delete":
            return manager.delete_session(args.id)
        if action in {"pin", "unpin", "archive", "unarchive"}:
            return manager.set_session_flags(
                args.id,
                pinned=action == "pin" if action in {"pin", "unpin"} else None,
                archived=action in {"archive", "unarchive"} if action in {"archive", "unarchive"} else None,
            )
    if group in {"provider", "providers"} and action in {"list", "ls"}:
        return manager.get_providers()
    if group in {"model", "models"}:
        if action in {"list", "ls"}:
            return manager.get_settings()
        if action in {"use", "default"}:
            return manager.set_default_model(args.model)
        if action == "add":
            return manager.add_model(args.model)
        if action == "remove":
            return manager.remove_model(args.model)
    if group in {"agent", "agents", "persona", "personas"} and action in {"list", "ls"}:
        return manager.list_agents()
    if group in {"skill", "skills"} and action in {"list", "ls"}:
        return manager.list_skills(getattr(args, "workspace", None))
    if group == "connector" and action in {"list", "ls"}:
        return manager.list_connectors()
    if group == "mcp" and action in {"list", "ls"}:
        return manager.list_mcp()
    if group in {"automation", "automations"} and action in {"list", "ls"}:
        return manager.list_automations()
    if group == "memory" and action in {"list", "ls"}:
        return manager.list_memory()
    if group == "audit" and action in {"list", "ls"}:
        return manager.list_audit()
    raise ValueError(f"unsupported control command: {group} {action}")
