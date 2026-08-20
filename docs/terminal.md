# OpenWorker Terminal Guide

OpenWorker can run entirely from a terminal. The terminal client uses the same local state, agent engine, providers, memory, sessions, connectors, MCP configuration, and Ollama installation as the desktop/server surfaces.

The configured default model is:

```text
ollama:gemma4:31b-cloud
```

## Quick start

```bash
cd ~/Downloads/openworker
ollama serve                 # only needed if Ollama is not already running
ollama pull gemma4:31b-cloud # only needed once
.venv/bin/openworker --cwd .
```

Point OpenWorker at another workspace:

```bash
.venv/bin/openworker --cwd ~/src/my-project
```

The application opens an interactive terminal UI. Type a request and press Enter. OpenWorker can inspect files, edit files, run approved commands, use web tools, use configured skills, call enabled connector/MCP tools, and maintain conversation memory.

## Interactive commands

Inside a chat session:

| Command | Purpose |
|---|---|
| `/help` | Show the interactive command list |
| `/mode plan` | Explore and propose a plan before execution |
| `/mode discuss` | Read-only discussion |
| `/mode interactive` | Ask before consequential tools (recommended) |
| `/mode auto` | Allow path-scoped actions automatically |
| `/mode custom` | Use configured automatic tools, ask for others |
| `/model` | Display/change the current model |
| `/model ollama:gemma4:31b-cloud` | Change model for the current session |
| `/clear` | Start a fresh conversation with the current workspace/model |
| `/quit`, `/exit` | Save and leave the session |

The current terminal surface preserves the original code-agent tools and approval dialog. Approvals support once, deny, always allow this tool, and always allow commands. Use `interactive` mode unless you intentionally need automation.

## CLI commands

Show help:

```bash
.venv/bin/openworker --help
.venv/bin/openworker run --help
.venv/bin/openworker session --help
```

The original invocation remains supported:

```bash
.venv/bin/openworker --cwd ~/project --model ollama:gemma4:31b-cloud
```

The explicit chat alias is equivalent:

```bash
.venv/bin/openworker chat --cwd ~/project
```

### One-shot execution

Run one prompt without opening the TUI:

```bash
.venv/bin/openworker run "List the files in this project and summarize its purpose" --cwd ~/project
```

Use a prompt file or standard input:

```bash
.venv/bin/openworker run --prompt-file task.md --cwd ~/project
cat task.md | .venv/bin/openworker run --stdin --cwd ~/project
```

The headless default denies consequential approvals. Choose an explicit policy:

```bash
.venv/bin/openworker run "Create a report.md" --approve interactive
.venv/bin/openworker run "Apply the requested edits" --approve once
.venv/bin/openworker run "Run the approved tool workflow" --approve all-tool
.venv/bin/openworker run "Run the approved command workflow" --approve all-command
```

For scripts, JSONL emits one event per line:

```bash
.venv/bin/openworker run "Inspect the repository" --jsonl --cwd ~/project
```

A session can be resumed:

```bash
.venv/bin/openworker run "Continue the previous task" --resume SESSION_ID
.venv/bin/openworker --resume SESSION_ID
```

### Sessions

```bash
.venv/bin/openworker session list
.venv/bin/openworker session show SESSION_ID
.venv/bin/openworker session rename SESSION_ID "Release preparation"
.venv/bin/openworker session pin SESSION_ID
.venv/bin/openworker session archive SESSION_ID
.venv/bin/openworker session delete SESSION_ID
```

Sessions are shared through the local state directory, so a session created by the terminal can be read by the existing server/desktop components.

### Models and providers

```bash
.venv/bin/openworker model list
.venv/bin/openworker model list --json
.venv/bin/openworker model use ollama:gemma4:31b-cloud
.venv/bin/openworker model add ollama:qwen3.5:2b
.venv/bin/openworker model remove ollama:qwen3.5:2b
.venv/bin/openworker provider list
```

Provider-qualified IDs are safest:

```text
ollama:gemma4:31b-cloud
ollama:qwen3.5:2b
openai:gpt-5.5
anthropic:claude-fable-5
```

Ollama IDs retain the model tag after the first colon. Ollama is accessed through its local OpenAI-compatible `/v1` endpoint; the default root is `http://localhost:11434`.

### Agents, skills, memory, integrations

The terminal control plane exposes read/list operations for the same registries used by the server:

```bash
.venv/bin/openworker agent list
.venv/bin/openworker persona list
.venv/bin/openworker skill list --workspace ~/project
.venv/bin/openworker memory list
.venv/bin/openworker connector list
.venv/bin/openworker mcp list
.venv/bin/openworker automation list
.venv/bin/openworker audit list
```

The Code agent can use configured skills, web search/fetch, memory, subagents, filesystem tools, shell tools, and enabled integration tools during a turn. Connector and MCP credentials remain in the existing local secret store and are never printed by JSON output; sensitive fields are redacted.

## Workspaces, permissions, and safety

`--cwd` sets the primary workspace. File operations remain scoped by the engine's roots and permission policy. In interactive mode, write, shell, connector, and other consequential operations ask for approval.

Configuration can allow command prefixes, but the built-in allowlist is intentionally empty. Workspace trust and command approvals are separate concepts. Do not use `auto` unless you understand which roots and tools are available.

Headless operation is deliberately safer than an unrestricted shell runner: its default approval policy is `deny`. Use `--approve interactive` for a script that can ask you, or use a narrowly scoped explicit policy for controlled automation.

## State and configuration

The default state directory on macOS is:

```text
~/.config/coworker/
```

Important files include:

```text
~/.config/coworker/prefs.json       # default model and UI preferences
~/.config/coworker/config.toml      # global configuration, when present
~/.config/coworker/coworker.db      # session index and memory database
~/.config/coworker/conversations/   # append-only session messages
~/.config/coworker/secrets.json     # provider/connector secrets; mode 0600
```

Workspace configuration is:

```text
<workspace>/.coworker/config.toml
```

The effective order is built-in defaults, global configuration, then workspace configuration. Existing saved preferences override a new built-in default.

## What is available in terminal versus GUI

| Area | Terminal status |
|---|---|
| Chat, code tools, approvals | Available |
| Ollama and other providers | Available through model IDs; provider listing available |
| Sessions and resume | Available; lifecycle commands available |
| Memory and skills | Available to the agent; list controls available |
| Web search/fetch | Available to the agent |
| MCP/connectors | Available during turns when configured; list controls available |
| Automations/inbox | Backend available; list/control commands are being expanded |
| Personas | Registry listing available; Code remains the default interactive builder |
| Browser OAuth and desktop file reveal | Best handled through the existing GUI/server/browser flow |
| Rich GUI settings/gallery | Not required for terminal use; local state remains shared |

The terminal surface is local-first. Features that require an OAuth browser callback, a graphical file picker, or a live remote WebSocket may still be easier to complete through the server/desktop surface, but they use the same underlying state.

## Troubleshooting

Check Ollama:

```bash
curl http://127.0.0.1:11434/api/tags
ollama list
```

Check the selected model:

```bash
.venv/bin/openworker model list --json
```

If a provider cannot be reached, verify its model prefix and endpoint. For Ollama, the model must appear in `ollama list`, and Ollama must be serving on `http://localhost:11434` unless a provider endpoint has been configured.

If a session is stuck, leave with `/quit` and resume by ID. The conversation files are append-only and can be backed up before troubleshooting.
