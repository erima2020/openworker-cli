"""Headless single-turn execution for scripts and CI."""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from typing import Any

from ..agent import build_code_engine
from ..events import Event, EventType
from ..permissions import Mode
from ..sessions import SessionRecord
from .runtime import TerminalRuntime


class HeadlessApprover:
    def __init__(self, policy: str) -> None:
        self.policy = policy

    async def __call__(self, request: Any):
        from ..engine import ApprovalOutcome

        if self.policy == "once":
            return ApprovalOutcome("once")
        if self.policy == "all-tool":
            return ApprovalOutcome("always_tool")
        if self.policy == "all-command":
            return ApprovalOutcome("always_command")
        if self.policy == "interactive":
            answer = await asyncio.to_thread(input, f"Approve {request.tool_name}? [y/N] ")
            return ApprovalOutcome("once" if answer.strip().lower() in {"y", "yes"} else "deny")
        return ApprovalOutcome("deny")


def event_dict(event: Event) -> dict[str, Any]:
    return {"event": event.type.value, "data": event.data}


async def run_once(runtime: TerminalRuntime, prompt: str, *, session_id: str | None, policy: str, jsonl: bool) -> int:
    sid = session_id or runtime.new_session_id()
    record = runtime.load_session(sid) if session_id else None
    messages = record.messages if record else None
    model = record.model if record else runtime.model
    mode = Mode(record.mode) if record else runtime.mode
    engine = build_code_engine(
        workspace=runtime.workspace,
        model=model,
        mode=mode,
        approver=HeadlessApprover(policy),
        memory_store=runtime.memory_store,
        memory_off=not runtime.memory_settings.enabled,
        user_rules=runtime.memory_settings.user_rules,
        messages=messages,
        session_id=sid,
        secrets=runtime.secrets,
    )
    last_text = ""
    try:
        async for event in engine.run(prompt):
            if jsonl:
                print(json.dumps({"session_id": sid, **event_dict(event)}, default=str), flush=True)
            elif event.type is EventType.ASSISTANT_MESSAGE and event.data.get("text"):
                last_text = str(event.data["text"])
                print(last_text, flush=True)
            elif event.type is EventType.TOOL_PROPOSED:
                print(f"tool: {event.data.get('name')} {event.data.get('arguments', '')}", flush=True)
            elif event.type is EventType.TOOL_FINISHED:
                print(f"tool finished: {event.data.get('name')} ({event.data.get('status')})", flush=True)
            elif event.type in {EventType.ERROR, EventType.INTERRUPTED}:
                print(f"{event.type.value}: {event.data}", file=sys.stderr, flush=True)
    finally:
        runtime.sessions.save(SessionRecord(session_id=sid, workspace=str(runtime.workspace), model=model, mode=mode.value, messages=engine.messages, agent="code"))
    return 0


def run_sync(runtime: TerminalRuntime, prompt: str, **kwargs: Any) -> int:
    return asyncio.run(run_once(runtime, prompt, **kwargs))
