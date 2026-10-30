<p align="center"><img src="logo.svg" width="64" height="64" alt="UberLLM"></p>

# UberLLM

[UberLLM](https://uberllm.dev) is an API marketplace for AI models: chat,
image, video, music and speech. You call one OpenAI- and Anthropic-compatible
API with one key. Each request is served by a third-party inference provider
for that model, and costs what that provider charged for it.

- No UberLLM fee on requests. Adding credit by card costs 5.5% + $0.50.
- Prepaid. Accounts start at $0; a request that fails is not billed.
- Base URL: `https://api.uberllm.dev/v1` (OpenAI) or `https://api.uberllm.dev` (Anthropic).
- Models and live prices: <https://uberllm.dev/models>
- Docs: <https://uberllm.dev/docs>

This repository holds the public tooling: plugins for Claude Code and Codex,
the `uberllm` agent skill, the Claude Code installer with its checksums, and
copy-paste setup for SDKs and MCP clients.

## Get a key

Sign in at <https://uberllm.dev> with your email (a code is sent, no password),
add credit, and create a key in **Dashboard → Keys**. Keys start with `ull_`.

## Install in your coding agent

This repository is a Claude Code plugin, a Codex plugin and an Agent Skill.
Each one adds UberLLM's hosted MCP server (`https://api.uberllm.dev/mcp`,
Streamable HTTP) and/or the `uberllm` skill, which knows how to set UberLLM up,
pick a model and make images and videos. Nothing to build or run locally: the
server is hosted, and it authenticates with your key as
`Authorization: Bearer ull_...`.

MCP tools: `list_models`, `get_model`, `quote`, `generate_image`, `edit_image`,
`start_video`, `get_job`, `wait_job`, `balance`. A tool call is billed exactly
like the same API request. Full reference: <https://uberllm.dev/docs/mcp>

**Claude Code plugin** (MCP server + skill). Inside Claude Code:

```
/plugin marketplace add PSA-Team-source/uberllm
/plugin install uberllm@uberllm
```

Claude Code asks for your API key when the plugin is enabled and keeps it in
your system's credential store. Set or change it later with
`claude plugin configure uberllm`.

**Codex plugin** (MCP server + skill):

```sh
codex plugin marketplace add PSA-Team-source/uberllm
codex plugin add uberllm@uberllm
export UBERLLM_API_KEY=ull_...   # the MCP server reads the key from here
```

**Skill only** (Claude Code, Codex, Cursor, OpenCode and other agents that read
Agent Skills), via [skills.sh](https://skills.sh):

```sh
npx skills add PSA-Team-source/uberllm
```

**MCP server only, Claude Code:**

```sh
claude mcp add --transport http uberllm https://api.uberllm.dev/mcp --header "Authorization: Bearer ull_..."
```

**Cursor** (`~/.cursor/mcp.json`) and other clients that take a URL:

```json
{
  "mcpServers": {
    "uberllm": {
      "url": "https://api.uberllm.dev/mcp",
      "headers": { "Authorization": "Bearer ull_..." }
    }
  }
}
```

**VS Code** (`.vscode/mcp.json`; VS Code asks for the key once and stores it):

```json
{
  "inputs": [
    { "type": "promptString", "id": "uberllm-key", "description": "UberLLM API key (ull_...)", "password": true }
  ],
  "servers": {
    "uberllm": {
      "type": "http",
      "url": "https://api.uberllm.dev/mcp",
      "headers": { "Authorization": "Bearer ${input:uberllm-key}" }
    }
  }
}
```

**Claude Desktop** (Settings → Developer → Edit Config), through
[`mcp-remote`](https://www.npmjs.com/package/mcp-remote):

```json
{
  "mcpServers": {
    "uberllm": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://api.uberllm.dev/mcp", "--header", "Authorization:${UBERLLM_AUTH}"],
      "env": { "UBERLLM_AUTH": "Bearer ull_..." }
    }
  }
}
```

The server is listed in the [official MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=dev.uberllm)
as `dev.uberllm/mcp` ([`server.json`](server.json)).

## OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(base_url="https://api.uberllm.dev/v1", api_key="ull_...")
r = client.chat.completions.create(
    model="deepseek/deepseek-v4-flash",
    messages=[{"role": "user", "content": "Say hello in five words."}],
)
print(r.choices[0].message.content)
```

## Anthropic SDK

```python
from anthropic import Anthropic

client = Anthropic(base_url="https://api.uberllm.dev", api_key="ull_...")
m = client.messages.create(
    model="anthropic/claude-haiku-4.5",
    max_tokens=100,
    messages=[{"role": "user", "content": "Say hello in five words."}],
)
print(m.content[0].text)
```

Any chat model in the catalog works on both APIs. Model ids are the ids on
<https://uberllm.dev/models>.

## Vercel AI SDK

```ts
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import { generateText } from "ai";

const uberllm = createOpenAICompatible({
  name: "uberllm",
  apiKey: process.env.UBERLLM_API_KEY,
  baseURL: "https://api.uberllm.dev/v1",
  includeUsage: true,
});

const { text } = await generateText({
  model: uberllm("deepseek/deepseek-v4-flash"),
  prompt: "Say hello in five words.",
});
```

Streaming, tool calls and images: <https://uberllm.dev/docs/ai-sdk>

## Claude Code

### By hand (3 steps)

1. Create a key in **Dashboard → Keys**.
2. Save it to a file only you can read:

   ```sh
   mkdir -p ~/.uberllm && chmod 700 ~/.uberllm
   printf '%s\n' 'ull_your_key' > ~/.uberllm/key && chmod 600 ~/.uberllm/key
   ```

3. Add this to `~/.claude/settings.json` (every project) or
   `<project>/.claude/settings.local.json` (one project):

   ```json
   {
     "apiKeyHelper": "cat ~/.uberllm/key",
     "env": {
       "ANTHROPIC_BASE_URL": "https://api.uberllm.dev",
       "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1"
     }
   }
   ```

### With the installer

[`install/claude-code.sh`](install/claude-code.sh) (macOS, Linux) and
[`install/claude-code.ps1`](install/claude-code.ps1) (Windows) are byte-for-byte
the files served at `https://uberllm.dev/install/`. They sign you in through
the browser, save the key to a mode-600 file, merge `ANTHROPIC_BASE_URL` and an
`apiKeyHelper` into your Claude Code settings (backing the file up first), and
make one test request. `--uninstall` reverts it.

Read it, check it, then run it:

```sh
curl -fsSL https://uberllm.dev/install/claude-code.sh -o claude-code.sh
shasum -a 256 claude-code.sh   # compare with install/SHA256SUMS
less claude-code.sh
sh claude-code.sh              # add --project for this project only
```

| File | SHA-256 |
|---|---|
| `claude-code.sh` | `f5aa1c4610992d8f4ecc1b1cd777bc731c5fad9da6a38cac46989834b194d66c` |
| `claude-code.ps1` | `60d631b48e60a2e3f17e5eee19136d47a255f143627986e86b6ceb379858a3b9` |

If the file you downloaded does not match the sum above, do not run it, and
tell us at support@uberllm.dev.

Details: <https://uberllm.dev/docs/claude-code>

## Support

support@uberllm.dev · [Privacy](https://uberllm.dev/privacy) · [Terms](https://uberllm.dev/terms)

## License

MIT
