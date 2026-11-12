// A Mastra agent with a tool, running on an UberLLM model. Mastra takes
// any OpenAI-compatible endpoint as { providerId, modelId, url, apiKey }.
//   npm i @mastra/core zod
//   export UBERLLM_API_KEY=ull_...
//   npx tsx mastra/agent.ts
import { Agent } from "@mastra/core/agent";
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

const convert = createTool({
  id: "convert-currency",
  description: "Convert an amount between currencies at today's rate.",
  inputSchema: z.object({ amount: z.number(), from: z.string(), to: z.string() }),
  outputSchema: z.object({ result: z.number(), rate: z.number() }),
  execute: async ({ amount, from, to }) => {
    // Replace with a real rates API.
    const rates: Record<string, number> = { "USD-EUR": 0.92, "EUR-USD": 1.09 };
    const rate = rates[`${from.toUpperCase()}-${to.toUpperCase()}`] ?? 1;
    return { result: Math.round(amount * rate * 100) / 100, rate };
  },
});

const agent = new Agent({
  id: "travel-helper",
  name: "Travel helper",
  instructions: "You help with travel money questions. Use the tool for every conversion.",
  model: {
    providerId: "uberllm",
    modelId: process.env.UBERLLM_MODEL ?? "deepseek/deepseek-v4-flash",
    url: "https://api.uberllm.dev/v1",
    apiKey: process.env.UBERLLM_API_KEY,
  },
  tools: { convert },
});

const res = await agent.generate("How many euros is 250 US dollars?");
console.log(res.text);
