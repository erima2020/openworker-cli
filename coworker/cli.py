"""OpenWorker terminal CLI: interactive chat plus control-plane commands."""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path
from typing import Optional

from .config import load_config
from .conversations import ConversationStore
from .memory import MemorySettingsStore, SQLiteMemoryStore
from .permissions import Mode
from .secrets import state_dir
from .terminal.commands import execute_control, render
from .terminal.run import run_sync
from .terminal.runtime import DEFAULT_MODEL, TerminalRuntime

COMMANDS = {
    "chat", "run", "session", "sessions", "provider", "providers", "model", "models",
    "agent", "agents", "persona", "personas", "skill", "skills", "connector", "mcp",
    "automation", "automations", "memory", "audit", "workspace", "config",
}


def _legacy_parser() -> argparse.ArgumentParser:
    cfg = load_config()
    parser = argparse.ArgumentParser(
        prog="openworker", description="OpenWorker terminal chat (Ollama by default)."
    )
    parser.add_argument("skill", nargs="?", default="code", help="legacy agent name (default: code)")
    parser.add_argument("--cwd", default=".", help="workspace directory")
    parser.add_argument("--model", default=cfg.model or DEFAULT_MODEL, help=f"model id (default: {cfg.model or DEFAULT_MODEL})")
    parser.add_argument("--mode", default=cfg.mode, choices=[m.value for m in Mode], help="permission mode")
    parser.add_argument("--resume", default=None, help="resume a session id")
    parser.add_argument("--persona", default=None, help="agent/persona name")
    return parser


def _command_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openworker", description="OpenWorker terminal control plane")
    parser.add_argument("--json", action="store_true", help="format control output as JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    chat = sub.add_parser("chat", help="launch interactive terminal chat")
    _add_runtime_flags(chat)
    run = sub.add_parser("run", help="run one prompt without the TUI")
    run.add_argument("prompt", nargs="?", help="prompt text")
    run.add_argument("--prompt-file")
    run.add_argument("--stdin", action="store_true")
    run.add_argument("--cwd", default=".")
    run.add_argument("--model", default=None)
    run.add_argument("--mode", choices=[m.value for m in Mode], default=None)
    run.add_argument("--session", "--resume", dest="session")
    run.add_argument("--approve", choices=["deny", "interactive", "once", "all-tool", "all-command"], default="deny")
    run.add_argument("--jsonl", action="store_true")
    for group in sorted(COMMANDS - {"chat", "run"}):
        p = sub.add_parser(group, help=f"manage {group}")
        p.add_argument("action", nargs="?", default="list")
        p.add_argument("id", nargs="?")
        p.add_argument("title", nargs="?")
        p.add_argument("--model", dest="model")
        p.add_argument("--workspace")
        p.add_argument("--json", action="store_true")
    return parser


def _add_runtime_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--model", default=None)
    parser.add_argument("--mode", choices=[m.value for m in Mode], default=None)
    parser.add_argument("--resume")
    parser.add_argument("--persona")


def _launch_chat(args: argparse.Namespace) -> None:
    cfg = load_config()
    workspace = Path(args.cwd).expanduser().resolve()
    data_dir = state_dir()
    memory_settings = MemorySettingsStore(data_dir / "memory-settings.json")
    memory_store = SQLiteMemoryStore(data_dir / "coworker.db")
    session_store = ConversationStore(data_dir)
    session_store.touch_workspace(os.path.realpath(str(workspace)))
    resume_messages = None
    session_id = args.resume or uuid.uuid4().hex[:12]
    model = args.model or cfg.model or DEFAULT_MODEL
    mode = args.mode or cfg.mode
    if args.resume:
        record = session_store.load(args.resume)
        if record is None:
            raise SystemExit(f"session not found: {args.resume}")
        resume_messages, model, mode = record.messages, record.model, record.mode
    from .tui.app import CoworkerApp
    app = CoworkerApp(
        workspace=workspace, model=model, mode=Mode(mode), memory_store=memory_store,
        memory_off=not memory_settings.enabled, user_rules=memory_settings.user_rules,
        session_store=session_store, session_id=session_id, resume_messages=resume_messages,
    )
    app.run()


def main(argv: Optional[list[str]] = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in COMMANDS:
        parser = _command_parser()
        args = parser.parse_args(argv)
        if args.command == "chat":
            _launch_chat(args)
            return
        if args.command == "run":
            prompt = args.prompt
            if args.prompt_file:
                prompt = Path(args.prompt_file).read_text(encoding="utf-8")
            if args.stdin:
                prompt = sys.stdin.read()
            if not prompt:
                parser.error("run requires a prompt, --prompt-file, or --stdin")
            runtime = TerminalRuntime(workspace=args.cwd, model=args.model, mode=args.mode)
            raise SystemExit(run_sync(runtime, prompt, session_id=args.session, policy=args.approve, jsonl=args.jsonl))
        runtime = TerminalRuntime(workspace=getattr(args, "workspace", None) or ".")
        try:
            result = execute_control(runtime, args.command, args.action, args)
        except ValueError as exc:
            parser.error(str(exc))
        print(render(result, as_json=getattr(args, "json", False)))
        return
    args = _legacy_parser().parse_args(argv)
    _launch_chat(args)


if __name__ == "__main__":
    main()
