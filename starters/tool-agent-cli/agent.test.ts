// Smoke test.  node --test agent.test.ts
// The first tests run offline with a stand-in for the API. The last one calls
// the real API and runs only when UBERLLM_API_KEY is set (it costs a fraction of a cent).
import assert from "node:assert/strict";
import { mkdtemp, mkdir, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { BASE_URL, runAgent, runTool, safePath, type Message } from "./agent.ts";

async function project() {
  const root = await mkdtemp(path.join(tmpdir(), "agent-test-"));
  await writeFile(path.join(root, "notes.txt"), "The launch code word is PINEAPPLE.");
  await writeFile(path.join(root, ".env"), "SECRET=1");
  await mkdir(path.join(root, "src"));
  await symlink(tmpdir(), path.join(root, "out"));
  await symlink(".env", path.join(root, "env-link"));
  return root;
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

test("the tools stay inside the project and never read hidden files", async () => {
  const root = await project();
  assert.equal(await runTool("list_files", {}, root), "env-link\nnotes.txt\nout\nsrc/"); // .env is not listed
  assert.match(await runTool("read_file", { path: "notes.txt" }, root), /PINEAPPLE/);
  await assert.rejects(safePath(root, ".env"), /hidden/);
  await assert.rejects(safePath(root, "src/../.env"), /hidden/);
  await assert.rejects(safePath(root, "../"), /outside/);
  await assert.rejects(safePath(root, "/etc/hosts"), /outside/);
  await assert.rejects(safePath(root, "out"), /outside/); // a symlink that leaves the project
  await assert.rejects(safePath(root, "env-link"), /hidden/); // a symlink to a hidden file
  // A missing file does not put the full path on your disk in the error the model sees.
  await assert.rejects(safePath(root, "nope.txt"), (err: Error) => err.message === "no such file or folder");
});

test("the loop runs the tool, sends the result back and returns the answer", async () => {
  const root = await project();
  const sent: any[] = [];
  const assistantTurn = {
    role: "assistant",
    content: null,
    signature: "keep-me", // an extra field the model needs back
    tool_calls: [{ id: "call_1", type: "function", function: { name: "read_file", arguments: '{"path":"notes.txt"}' } }],
  };
  const fake = (async (url: any, init: any) => {
    assert.equal(String(url), "https://api.uberllm.dev/v1/chat/completions");
    assert.equal(init.headers.Authorization, "Bearer test-key");
    sent.push(JSON.parse(init.body));
    return sent.length === 1
      ? json({ choices: [{ message: assistantTurn }], usage: { prompt_tokens: 10, completion_tokens: 5, cost_usd: 0.000001 } })
      : json({ choices: [{ message: { role: "assistant", content: "PINEAPPLE" } }], usage: { prompt_tokens: 30, completion_tokens: 2, cost_usd: 0.000002 } });
  }) as typeof fetch;

  const messages: Message[] = [{ role: "user", content: "What is the code word?" }];
  const called: string[] = [];
  const out = await runAgent(messages, { apiKey: "test-key", root, fetch: fake, onToolCall: (n) => called.push(n) });

  assert.equal(out.text, "PINEAPPLE");
  assert.deepEqual(called, ["read_file"]);
  assert.deepEqual(out.usage, { prompt_tokens: 40, completion_tokens: 7, cost_usd: 0.000003 });
  assert.equal(sent[0].tools.length, 3);
  assert.deepEqual(sent[1].messages[1], assistantTurn); // sent back as received
  assert.deepEqual(sent[1].messages[2], { role: "tool", tool_call_id: "call_1", content: "The launch code word is PINEAPPLE." });
});

test("a failing tool is reported to the model, an API error to the caller", async () => {
  const root = await project();
  let n = 0;
  const fake = (async (_url: any, init: any) => {
    n++;
    if (n === 1) {
      return json({ choices: [{ message: { role: "assistant", content: null, tool_calls: [{ id: "c", type: "function", function: { name: "read_file", arguments: '{"path":".env"}' } }] } }] });
    }
    assert.match(JSON.parse(init.body).messages.at(-1).content, /^Error: hidden files/);
    return json({ error: { code: "insufficient_credits", message: "Your credit balance is too low to serve this request." } }, 402);
  }) as typeof fetch;
  await assert.rejects(runAgent([{ role: "user", content: "read .env" }], { apiKey: "k", root, fetch: fake }), /credit balance is too low/);
});

test("an answer that is not JSON is a readable error", async () => {
  const fake = (async () => new Response("<html>bad gateway</html>", { status: 200 })) as typeof fetch;
  await assert.rejects(runAgent([{ role: "user", content: "hi" }], { apiKey: "k", fetch: fake }), /HTTP 200 with a body that is not JSON/);
});

test("live: the real API answers from a file", { skip: !process.env.UBERLLM_API_KEY && "UBERLLM_API_KEY is not set" }, async () => {
  assert.equal(new URL(BASE_URL).host, "api.uberllm.dev");
  const root = await project();
  const called: string[] = [];
  const out = await runAgent(
    [{ role: "user", content: "Read notes.txt and reply with only the code word in it." }],
    { apiKey: process.env.UBERLLM_API_KEY!, model: process.env.UBERLLM_MODEL || undefined, root, onToolCall: (n) => called.push(n) },
  );
  assert.ok(called.includes("read_file"), "the model called read_file");
  assert.match(out.text, /PINEAPPLE/);
  assert.ok(out.usage.cost_usd > 0, "the answer carries its cost");
});
