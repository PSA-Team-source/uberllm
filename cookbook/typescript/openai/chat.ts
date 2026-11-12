// Chat and streaming with the official OpenAI Node SDK on UberLLM.
//   npm i openai
//   export UBERLLM_API_KEY=ull_...
//   npx tsx openai/chat.ts
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://api.uberllm.dev/v1",
  apiKey: process.env.UBERLLM_API_KEY,
});
const model = process.env.UBERLLM_MODEL ?? "deepseek/deepseek-v4-flash";

const resp = await client.chat.completions.create({
  model,
  messages: [{ role: "user", content: "What is a context window? One sentence." }],
});
console.log(resp.choices[0].message.content);
// UberLLM adds usage.cost_usd: what the call cost, in US dollars.
console.log("cost:", (resp.usage as { cost_usd?: number } | undefined)?.cost_usd);

const stream = await client.chat.completions.create({
  model,
  messages: [{ role: "user", content: "Count from 1 to 5, separated by commas." }],
  stream: true,
});
for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? "");
}
process.stdout.write("\n");
