// UberLLM as a Vercel AI SDK provider, through @ai-sdk/openai-compatible.
//   npm i ai @ai-sdk/openai-compatible zod
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";

export const uberllm = createOpenAICompatible({
  name: "uberllm",
  apiKey: process.env.UBERLLM_API_KEY,
  baseURL: "https://api.uberllm.dev/v1",
  includeUsage: true, // token usage (and cost) on streamed answers too
  supportsStructuredOutputs: true, // send JSON schemas as response_format json_schema
});
