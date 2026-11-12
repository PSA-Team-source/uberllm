// The official Anthropic TypeScript SDK on UberLLM (/v1/messages).
// Base URL has no /v1: the SDK adds /v1/messages itself.
//   npm i @anthropic-ai/sdk
//   export UBERLLM_API_KEY=ull_...
//   npx tsx anthropic/messages.ts
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic({
  baseURL: "https://api.uberllm.dev",
  apiKey: process.env.UBERLLM_API_KEY,
});
const model = process.env.UBERLLM_MODEL ?? "anthropic/claude-haiku-4.5";

const msg = await client.messages.create({
  model,
  max_tokens: 300,
  system: "You answer in one sentence.",
  messages: [{ role: "user", content: "Why is the sky blue?" }],
});
for (const block of msg.content) if (block.type === "text") console.log(block.text);

const stream = client.messages.stream({
  model,
  max_tokens: 300,
  messages: [{ role: "user", content: "Count from 1 to 5, separated by commas." }],
});
stream.on("text", (text) => process.stdout.write(text));
await stream.finalMessage();
process.stdout.write("\n");
