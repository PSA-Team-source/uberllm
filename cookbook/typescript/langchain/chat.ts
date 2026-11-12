// LangChain.js on UberLLM with ChatOpenAI (@langchain/openai): invoke,
// stream, tool calls and structured output.
//   npm i @langchain/openai @langchain/core zod
//   export UBERLLM_API_KEY=ull_...
//   npx tsx langchain/chat.ts
import { tool } from "@langchain/core/tools";
import { ChatOpenAI } from "@langchain/openai";
import { z } from "zod";

const llm = new ChatOpenAI({
  model: process.env.UBERLLM_MODEL ?? "deepseek/deepseek-v4-flash",
  apiKey: process.env.UBERLLM_API_KEY,
  configuration: { baseURL: "https://api.uberllm.dev/v1" },
});

console.log((await llm.invoke("Say hello in one sentence.")).content);

for await (const chunk of await llm.stream("Count from 1 to 5, separated by commas.")) {
  process.stdout.write(String(chunk.content));
}
process.stdout.write("\n");

const getWeather = tool(async ({ city }) => `Sunny and 21C in ${city}.`, {
  name: "get_weather",
  description: "Return the current weather for a city.",
  schema: z.object({ city: z.string() }),
});
const aiMsg = await llm.bindTools([getWeather]).invoke("What's the weather in Paris?");
for (const call of aiMsg.tool_calls ?? []) {
  console.log(call.name, call.args, "->", await getWeather.invoke(call.args as { city: string }));
}

const movie = await llm
  .withStructuredOutput(z.object({ title: z.string(), year: z.number(), director: z.string() }))
  .invoke("The 1999 film where Neo takes the red pill.");
console.log(movie);
