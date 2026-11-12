// Tool calling, the full loop, with the OpenAI Node SDK on UberLLM.
//   npm i openai
//   export UBERLLM_API_KEY=ull_...
//   npx tsx openai/tools.ts
import OpenAI from "openai";
import type { ChatCompletionMessageParam, ChatCompletionTool } from "openai/resources/chat/completions";

const client = new OpenAI({
  baseURL: "https://api.uberllm.dev/v1",
  apiKey: process.env.UBERLLM_API_KEY,
});
const model = process.env.UBERLLM_MODEL ?? "deepseek/deepseek-v4-flash";

function getWeather({ city }: { city: string }) {
  return { city, celsius: 21, sky: "clear" }; // replace with a real weather API
}

const tools: ChatCompletionTool[] = [
  {
    type: "function",
    function: {
      name: "get_weather",
      description: "Get the current weather for a city.",
      parameters: {
        type: "object",
        properties: { city: { type: "string" } },
        required: ["city"],
      },
    },
  },
];

const messages: ChatCompletionMessageParam[] = [
  { role: "user", content: "What's the weather in Paris and in Tokyo?" },
];

for (let round = 0; round < 5; round++) {
  const resp = await client.chat.completions.create({ model, messages, tools });
  const msg = resp.choices[0].message;
  if (!msg.tool_calls?.length) {
    console.log(msg.content);
    break;
  }
  // Send the assistant turn back as received (Gemini puts a signature in it).
  messages.push(msg);
  for (const call of msg.tool_calls) {
    if (call.type !== "function") continue;
    const result = getWeather(JSON.parse(call.function.arguments || "{}"));
    console.log(`-> ${call.function.name}`, result);
    messages.push({ role: "tool", tool_call_id: call.id, content: JSON.stringify(result) });
  }
}
