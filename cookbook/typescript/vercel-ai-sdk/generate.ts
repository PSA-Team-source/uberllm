// Vercel AI SDK on UberLLM: generateText, streamText, a tool loop and
// typed output (Output.object with a zod schema).
//   npm i ai @ai-sdk/openai-compatible zod
//   export UBERLLM_API_KEY=ull_...
//   npx tsx vercel-ai-sdk/generate.ts
import { generateText, Output, stepCountIs, streamText, tool } from "ai";
import { z } from "zod";
import { uberllm } from "./provider.js";

const model = uberllm(process.env.UBERLLM_MODEL ?? "deepseek/deepseek-v4-flash");

// 1. Text
const { text, usage } = await generateText({ model, prompt: "Say hello in one short sentence." });
console.log(text, usage.totalTokens, "tokens");

// 2. Stream
const result = streamText({ model, prompt: "Count from 1 to 5, separated by commas." });
for await (const delta of result.textStream) process.stdout.write(delta);
process.stdout.write("\n");

// 3. Tools: the SDK runs the tool and sends the result back, up to 3 steps.
const weather = await generateText({
  model,
  tools: {
    weather: tool({
      description: "Get the current temperature in a city, in Celsius",
      inputSchema: z.object({ city: z.string() }),
      execute: async ({ city }) => ({ city, celsius: 21 }),
    }),
  },
  stopWhen: stepCountIs(3),
  prompt: "What is the temperature in Paris right now?",
});
console.log(weather.text);

// 4. Typed object
const { output } = await generateText({
  model,
  output: Output.object({
    schema: z.object({ title: z.string(), year: z.number(), director: z.string() }),
  }),
  prompt: "The 1999 film where Neo takes the red pill.",
});
console.log(output);
