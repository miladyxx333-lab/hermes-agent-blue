# Paperclip Adapter for Hermes Agent Blue

A [Paperclip](https://paperclip.ing) adapter that lets you run [Hermes Agent Blue](https://github.com/NousResearch/hermes-agent) as a managed employee in a Paperclip company.

Hermes Agent Blue is a fork of Hermes Agent by [Nous Research](https://nousresearch.com) configured specifically with a blue theme and optimized for Google Gemini models.

## Why Hermes Agent?

| Feature | Claude Code | Codex | Hermes Agent |
|---------|------------|-------|-------------|
| Persistent memory | ❌ | ❌ | ✅ Remembers across sessions |
| Native tools | ~5 | ~5 | 30+ (terminal, file, web, browser, vision, git, etc.) |
| Skills system | ❌ | ❌ | ✅ 80+ loadable skills |
| Session search | ❌ | ❌ | ✅ FTS5 search over past conversations |
| Sub-agent delegation | ❌ | ❌ | ✅ Parallel sub-tasks |
| Context compression | ❌ | ❌ | ✅ Auto-compresses long conversations |
| MCP client | ❌ | ❌ | ✅ Connect to any MCP server |
| Multi-provider | Anthropic only | OpenAI only | ✅ Anthropic, OpenAI, OpenRouter, Google (Gemini) |

## Installation

```bash
npm install (local path to paperclip folder)
```

### Prerequisites

- [Hermes Agent Blue](https://github.com/NousResearch/hermes-agent) installed
- Python 3.10+
- At least one LLM API key (Google / Gemini API Key recommended for Hermes Agent Blue)

## Quick Start

### 1. Register the adapter in your Paperclip server

Add to your Paperclip server's adapter registry (`server/src/adapters/registry.ts`):

```typescript
import * as hermesLocal from "hermes-blue-paperclip-adapter";
import { execute, testEnvironment } from "hermes-blue-paperclip-adapter/server";

registry.set("hermes_blue_local", {
  ...hermesLocal,
  execute,
  testEnvironment,
});
```

### 2. Create a Hermes agent in Paperclip

In the Paperclip UI or via API, create an agent with adapter type `hermes_blue_local`:

```json
{
  "name": "Hermes Engineer",
  "adapterType": "hermes_blue_local",
  "adapterConfig": {
    "model": "gemini-2.5-flash",
    "maxIterations": 50,
    "timeoutSec": 300,
    "persistSession": true,
    "enabledToolsets": ["terminal", "file", "web"]
  }
}
```

### 3. Assign work

Create issues in Paperclip and assign them to your Hermes agent. On each heartbeat, Hermes will:

1. Receive the task instructions
2. Use its full tool suite to complete the work
3. Report results back to Paperclip
4. Persist session state for continuity

## Configuration Reference

### Core

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model` | string | `gemini-2.5-flash` | Model in `provider/model` format (or just model for auto provider) |
| `provider` | string | *(auto-detected)* | API provider override |
| `maxIterations` | number | `50` | Max tool-calling iterations per run |
| `timeoutSec` | number | `300` | Execution timeout in seconds |
| `graceSec` | number | `10` | Grace period before SIGKILL |

### Tools

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabledToolsets` | string[] | *(all)* | Toolsets to enable |
| `disabledToolsets` | string[] | `[]` | Toolsets to disable |

Available toolsets: `terminal`, `file`, `web`, `browser`, `code_execution`, `vision`, `mcp`, `creative`, `productivity`

### Session & Memory

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `persistSession` | boolean | `true` | Resume sessions across heartbeats |
| `skipMemory` | boolean | `false` | Disable persistent memory |
| `worktreeMode` | boolean | `false` | Git worktree isolation |

### Advanced

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `hermesCommand` | string | `hermes` | Custom CLI binary path |
| `contextFiles` | string[] | `[]` | Extra context files to load |
| `extraArgs` | string[] | `[]` | Additional CLI arguments |
| `env` | object | `{}` | Extra environment variables |
| `promptTemplate` | string | *(built-in)* | Custom prompt template |

### Prompt Template Variables

Use `{{variable}}` syntax in `promptTemplate`:

| Variable | Description |
|----------|-------------|
| `{{agentId}}` | Paperclip agent ID |
| `{{agentName}}` | Agent display name |
| `{{companyId}}` | Company ID |
| `{{companyName}}` | Company name |
| `{{runId}}` | Current heartbeat run ID |
| `{{taskId}}` | Assigned task/issue ID |
| `{{taskTitle}}` | Task title |
| `{{taskBody}}` | Task instructions |
| `{{projectName}}` | Project name |

Conditional sections:
- `{{#taskId}}...{{/taskId}}` — included only when a task is assigned
- `{{#noTask}}...{{/noTask}}` — included only when no task (heartbeat check)

## Architecture

```
Paperclip                          Hermes Agent
┌──────────────────┐               ┌──────────────────┐
│  Heartbeat       │               │                  │
│  Scheduler       │───execute()──▶│  hermes chat -q  │
│                  │               │                  │
│  Issue System    │               │  30+ Tools       │
│                  │◀──results─────│  Memory System   │
│  Cost Tracking   │               │  Session DB      │
│                  │               │  Skills          │
│  Org Chart       │               │  MCP Client      │
└──────────────────┘               └──────────────────┘
```

The adapter spawns Hermes Agent's CLI in single-query mode (`-q`). Hermes
processes the task using its full tool suite, then exits. The adapter
captures stdout/stderr, parses token usage and session IDs, and reports
results back to Paperclip.

Session persistence works via Hermes's `--resume` flag — each run picks
up where the last one left off, maintaining conversation context,
memories, and tool state across heartbeats.

## Development

```bash
git clone https://github.com/NousResearch/hermes-paperclip-adapter
cd hermes-paperclip-adapter
npm install
npm run build
```

## License

MIT — see [LICENSE](LICENSE)

## Links

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — The AI agent this adapter runs
- [Paperclip](https://github.com/paperclipai/paperclip) — The orchestration platform
- [Nous Research](https://nousresearch.com) — The team behind Hermes
- [Paperclip Docs](https://paperclip.ing/docs) — Paperclip documentation
