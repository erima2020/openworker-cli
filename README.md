# OpenWorker-CLI

OpenWorker-CLI is an AI coworker that runs from the terminal. It can work with files, shell commands, web tools, memory, skills, MCP servers, connectors, and scheduled automations while asking for approval before consequential actions.

The GUI has been replaced by a CLI in this version (see https://github.com/andrewyng/openworker for the original with a GUI). The supported surfaces are the terminal CLI and the optional local API server.

> **Development note:** The changes in this checkout were made mostly autonomously by the Claude Code CLI using GPT-5.6 Luna by OpenAI. AI-assisted software can contain mistakes, omissions, or security issues. This experimental version is not aimed for use in production.

## Default model

The default model is:

```text
ollama:gemma4:31b-cloud
```

The model is accessed through Ollama's OpenAI-compatible local API. Other provider-qualified model IDs remain supported, for example `openai:gpt-5.5` or `anthropic:claude-fable-5`.

## Run from source

Prerequisites: Python 3.10+ and [Ollama](https://ollama.com/).

```shell
cd /Users/Username/Downloads/openworker
bash packaging/setup_dev_env.sh
ollama serve
ollama pull gemma4:31b-cloud
.venv/bin/openworker --cwd /Users/Username/Downloads
```

From another directory:

```shell
/Users/Username/Downloads/openworker/.venv/bin/openworker \
  --cwd /Users/Username/Downloads
```

Override the model:

```shell
.venv/bin/openworker \
  --cwd ~/project \
  --model ollama:gemma4:31b-cloud
```

The optional API server remains available:

```shell
.venv/bin/openworker-server --cwd ~/project --port 8765
```

## One-shot CLI

```shell
.venv/bin/openworker run \
  "Inspect this project and summarize its structure" \
  --cwd ~/project
```

Prompt files, standard input, JSONL events, approval policies, and session resume are documented in [`docs/terminal.md`](docs/terminal.md).

## Interactive commands

Inside the terminal client:

```text
/help
/status
/model ollama:gemma4:31b-cloud
/persona code
/mode discuss
/mode plan
/mode interactive
/mode auto
/mode custom
/clear
/interrupt
/quit
```

## What it can do

- Produce documents, reports, scripts, and other workspace deliverables.
- Inspect and modify files under approved workspace roots.
- Run shell commands subject to permission and approval rules.
- Search the web and fetch web pages.
- Use configured MCP servers and connector tools.
- Use persistent memory and reusable skills.
- Run subagents and scheduled automations.
- Keep durable conversation sessions that can be resumed.
- Use multiple model providers through explicit provider-qualified model IDs.

## Privacy and safety

OpenWorker stores conversations, preferences, memory, and provider/connector configuration locally. Credentials are kept in the local secret store rather than the project configuration. Consequential tools are approval-gated in interactive mode, and headless `run` defaults to denying approvals.

## Documentation

See [`docs/terminal.md`](docs/terminal.md) for the complete terminal guide, including:

- Installation and Ollama setup
- Interactive and one-shot operation
- Sessions and resume
- Models and providers
- Personas, skills, memory, MCP, and connectors
- Automations and unattended approvals
- Workspace roots and trust
- JSON/JSONL scripting
- State paths and troubleshooting

## Repository layout

| Directory | Purpose |
|---|---|
| `coworker/` | Python engine, terminal CLI, providers, connectors, MCP, memory, and automations |
| `stt/` | Optional speech-to-text sidecar |
| `packaging/` | Server packaging and development bootstrap |
| `docs/` | Terminal guide and project documentation |
| `tests/` | Python backend and terminal tests |

## Tests

```shell
.venv/bin/pytest
```

## License

MIT - see [LICENSE](LICENSE).
