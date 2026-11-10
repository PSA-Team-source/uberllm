# Installing the UberLLM MCP server (for AI agents such as Cline)

UberLLM's MCP server is hosted. There is nothing to clone, build, install or run
locally: you only add one entry to the client's MCP settings.

- URL: `https://api.uberllm.dev/mcp`
- Transport: Streamable HTTP (not SSE)
- Auth: header `Authorization: Bearer <key>`. Keys start with `ull_`.

## 1. Get the user's API key

Ask the user for their UberLLM API key. If they have none: sign in at
<https://uberllm.dev> (email code, no password), add credit, then create a key
in **Dashboard → Keys** (<https://uberllm.dev/dashboard/keys>). Never print the
key back in chat or logs.

## 2. Add the server

**Cline**: open `cline_mcp_settings.json` (MCP Servers → Configure MCP Servers)
and add this entry under `mcpServers`, keeping any servers already there.
`"type": "streamableHttp"` is required; without it Cline uses SSE and the
connection fails.

```json
{
  "mcpServers": {
    "uberllm": {
      "type": "streamableHttp",
      "url": "https://api.uberllm.dev/mcp",
      "headers": { "Authorization": "Bearer ull_..." },
      "disabled": false
    }
  }
}
```

Other clients: see the "Install in your coding agent" section of
[README.md](README.md) (Claude Code, Codex, Gemini CLI, Cursor, VS Code, Claude
Desktop).

## 3. Check it

Call the `balance` tool. It answers with `available_usd`. Then `list_models`
with `{"type": "image"}` lists the image models with their prices.

If a call answers "Missing API key", the `Authorization` header is not being
sent; if it answers that the key is not valid, ask the user to check it in
**Dashboard → Keys**.

## Tools

`list_models`, `get_model`, `quote` (prices a request, spends nothing),
`generate_image`, `edit_image`, `start_video`, `get_job`, `wait_job`,
`balance`. A tool call is billed exactly like the same API request; a request
that fails costs nothing. Reference: <https://uberllm.dev/docs/mcp>
