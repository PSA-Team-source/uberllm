#!/usr/bin/env node
// A tool-calling agent in one file, with no framework and no dependencies.
// It answers questions about the folder you run it in: the model may list
// files, read a file and ask for the time, as many rounds as it needs.
//
//   node agent.ts "What does this project do?"     one question
//   node agent.ts                                  chat (keeps the conversation)
//
// Needs Node 22.18 or newer, which runs TypeScript files directly:
// https://nodejs.org/api/typescript.html#type-stripping
// Wire format: OpenAI chat completions with tools,
// https://uberllm.dev/docs/openai-sdk and https://uberllm.dev/openapi.json
import { readdir, readFile, realpath, stat } from "node:fs/promises";
import { realpathSync } from "node:fs";
import path from "node:path";
import { createInterface } from "node:readline/promises";

// The key is only ever sent here. It is a constant on purpose: an
// OPENAI_BASE_URL in your shell cannot redirect it.
export const BASE_URL = "https://api.uberllm.dev/v1";
export const DEFAULT_MODEL = "deepseek/deepseek-v4-flash";
const MAX_ROUNDS = 8; // model turns per question, so a confused model cannot loop forever
const MAX_FILE_BYTES = 64 * 1024;
const MAX_ENTRIES = 200;

type ToolCall = { id: string; type: string; function: { name: string; arguments: string } };
export type Message =
  | { role: "system" | "user"; content: string }
  | { role: "assistant"; content: string | null; tool_calls?: ToolCall[]; [extra: string]: unknown }
  | { role: "tool"; tool_call_id: string; content: string };
export type Usage = { prompt_tokens: number; completion_tokens: number; cost_usd: number };

// ---- Tools -----------------------------------------------------------------
// What the model is told it can call (JSON Schema), then the code that runs.

export const TOOLS = [
  {
    type: "function",
    function: {
      name: "list_files",
      description: "List the files and folders in a folder of the project.",
      parameters: {
        type: "object",
        properties: { dir: { type: "string", description: "Folder, relative to the project. Default: the project itself." } },
      },
    },
  },
  {
    type: "function",
    function: {
      name: "read_file",
      description: "Read a text file of the project (first 64 KB).",
      parameters: {
        type: "object",
        properties: { path: { type: "string", description: "File path, relative to the project." } },
        required: ["path"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "current_time",
      description: "The current date and time (ISO 8601, UTC).",
      parameters: { type: "object", properties: {} },
    },
  },
] as const;

// The model chooses the path, so it is checked: it must stay inside the project,
// and hidden names (.env, .git, .ssh) are refused so a key never reaches the model.
export async function safePath(root: string, rel: string): Promise<string> {
  if (rel.split(/[\\/]/).some((part) => part.startsWith(".") && part !== "." && part !== "..")) {
    throw new Error("hidden files and folders are off limits");
  }
  const base = await realpath(root);
  // realpath follows symlinks, so a link out of the project is caught too. Its own
  // error carries the full path on your disk, which the model must not see.
  const full = await realpath(path.resolve(base, rel)).catch(() => {
    throw new Error("no such file or folder");
  });
  if (full !== base && !full.startsWith(base + path.sep)) throw new Error("path is outside the project");
  // Again on the real path: a link named "notes" that points at .env is still .env.
  if (path.relative(base, full).split(path.sep).some((part) => part.startsWith("."))) {
    throw new Error("hidden files and folders are off limits");
  }
  return full;
}

export async function runTool(name: string, args: Record<string, unknown>, root: string): Promise<string> {
  if (name === "current_time") return new Date().toISOString();
  if (name === "list_files") {
    const dir = await safePath(root, typeof args.dir === "string" && args.dir ? args.dir : ".");
    const entries = (await readdir(dir, { withFileTypes: true }))
      .filter((e) => !e.name.startsWith(".") && e.name !== "node_modules")
      .map((e) => (e.isDirectory() ? e.name + "/" : e.name))
      .sort();
    const shown = entries.slice(0, MAX_ENTRIES);
    return shown.join("\n") + (entries.length > shown.length ? `\n(${entries.length - shown.length} more not shown)` : "");
  }
  if (name === "read_file") {
    if (typeof args.path !== "string" || !args.path) throw new Error("path is required");
    const file = await safePath(root, args.path);
    const info = await stat(file);
    if (!info.isFile()) throw new Error("not a file");
    const bytes = (await readFile(file)).subarray(0, MAX_FILE_BYTES);
    if (bytes.includes(0)) throw new Error("not a text file");
    return bytes.toString("utf8") + (info.size > MAX_FILE_BYTES ? "\n(cut at 64 KB)" : "");
  }
  throw new Error(`unknown tool ${name}`);
}

// ---- The loop --------------------------------------------------------------

export type AgentOptions = {
  apiKey: string;
  model?: string;
  root?: string; // the project folder the tools may read
  fetch?: typeof fetch; // for tests
  onToolCall?: (name: string, args: unknown) => void;
};

// Adds the model's turns to `messages` and returns its final answer.
export async function runAgent(messages: Message[], opts: AgentOptions): Promise<{ text: string; usage: Usage }> {
  const send = opts.fetch ?? fetch;
  const root = opts.root ?? process.cwd();
  const usage: Usage = { prompt_tokens: 0, completion_tokens: 0, cost_usd: 0 };

  for (let round = 0; round < MAX_ROUNDS; round++) {
    const res = await send(`${BASE_URL}/chat/completions`, {
      method: "POST",
      headers: { Authorization: `Bearer ${opts.apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model: opts.model ?? DEFAULT_MODEL, messages, tools: TOOLS }),
    });
    const body = (await res.json().catch(() => null)) as any;
    if (!res.ok || !body) {
      // UberLLM errors are { error: { code, message } } and the message says what to do.
      throw new Error(body?.error?.message ?? `UberLLM answered HTTP ${res.status}${res.ok ? " with a body that is not JSON" : ""}`);
    }
    usage.prompt_tokens += body.usage?.prompt_tokens ?? 0;
    usage.completion_tokens += body.usage?.completion_tokens ?? 0;
    usage.cost_usd += body.usage?.cost_usd ?? 0; // what this call cost, in US dollars

    const reply = body.choices?.[0]?.message;
    if (!reply) throw new Error("UberLLM sent an answer with no message");
    // Send the assistant turn back exactly as received: some models put
    // extra fields in it that they need to see again.
    messages.push(reply);
    if (!reply.tool_calls?.length) return { text: reply.content ?? "", usage };

    for (const call of reply.tool_calls as ToolCall[]) {
      let result: string;
      try {
        const args = JSON.parse(call.function.arguments || "{}");
        opts.onToolCall?.(call.function.name, args);
        result = await runTool(call.function.name, args, root);
      } catch (err) {
        // The model gets the error as the tool result and can try something else.
        result = `Error: ${err instanceof Error ? err.message : String(err)}`;
      }
      messages.push({ role: "tool", tool_call_id: call.id, content: result });
    }
  }
  throw new Error(`No answer after ${MAX_ROUNDS} rounds of tool calls`);
}

// ---- Command line ----------------------------------------------------------

const SYSTEM =
  "You answer questions about the project in the current folder. " +
  "Use the tools to look at files before you answer; do not guess what a file contains.";

async function main() {
  try {
    process.loadEnvFile(); // reads .env when there is one
  } catch {}
  const apiKey = process.env.UBERLLM_API_KEY;
  if (!apiKey) {
    console.error("Set UBERLLM_API_KEY first (copy .env.example to .env). Create a key at https://uberllm.dev/dashboard/keys");
    process.exit(1);
  }
  const opts: AgentOptions = {
    apiKey,
    model: process.env.UBERLLM_MODEL || DEFAULT_MODEL,
    onToolCall: (name, args) => console.error(`-> ${name} ${JSON.stringify(args)}`),
  };
  const messages: Message[] = [{ role: "system", content: SYSTEM }];

  const ask = async (question: string) => {
    messages.push({ role: "user", content: question });
    const { text, usage } = await runAgent(messages, opts);
    console.log(text);
    console.error(`(${usage.prompt_tokens} tokens in, ${usage.completion_tokens} out, $${usage.cost_usd.toFixed(6)})`);
  };

  const question = process.argv.slice(2).join(" ").trim();
  if (question) return ask(question);

  const rl = createInterface({ input: process.stdin, output: process.stderr });
  console.error(`Model ${opts.model}. Ask about this folder. Ctrl+C to quit.`);
  for (;;) {
    let line: string;
    try {
      line = (await rl.question("> ")).trim();
    } catch {
      break; // input closed
    }
    if (!line) continue;
    try {
      await ask(line);
    } catch (err) {
      console.error(err instanceof Error ? err.message : err);
      // Drop the unanswered turns so the conversation stays valid for the next question.
      while (messages.length > 1 && messages[messages.length - 1].role !== "user") messages.pop();
      messages.pop();
    }
  }
  rl.close();
}

// Run only when started as a program, not when a test imports this file.
if (process.argv[1] && realpathSync(process.argv[1]) === import.meta.filename) {
  main().catch((err) => {
    console.error(err instanceof Error ? err.message : err);
    process.exit(1);
  });
}
