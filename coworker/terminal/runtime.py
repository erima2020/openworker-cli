"""Shared in-process runtime for the terminal surface."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from ..config import load_config
from ..conversations import ConversationStore
from ..memory import MemorySettingsStore, SQLiteMemoryStore
from ..permissions import Mode
from ..secrets import SecretStore, state_dir
from ..server.manager import SessionManager


DEFAULT_MODEL = "ollama:gemma4:31b-cloud"


class TerminalRuntime:
    """Own the same durable stores used by the GUI/server, without HTTP."""

    def __init__(
        self,
        *,
        workspace: str | Path = ".",
        model: Optional[str] = None,
        mode: Optional[str] = None,
        data_dir: Optional[str | Path] = None,
    ) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        self.data_dir = Path(data_dir).expanduser() if data_dir else state_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config = load_config(self.workspace)
        self.model = model or self.config.model or DEFAULT_MODEL
        self.mode = Mode(mode or self.config.mode)
        self.secrets = SecretStore()
        self.sessions = ConversationStore(self.data_dir)
        self.sessions.touch_workspace(os.path.realpath(str(self.workspace)))
        self.memory_settings = MemorySettingsStore(self.data_dir / "memory-settings.json")
        self.memory_store = SQLiteMemoryStore(self.data_dir / "coworker.db")
        self.manager = SessionManager(
            workspace=self.workspace,
            data_dir=self.data_dir,
            model=self.model,
            mode=self.mode,
        )

    def new_session_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def load_session(self, session_id: str):
        return self.sessions.load(session_id)
