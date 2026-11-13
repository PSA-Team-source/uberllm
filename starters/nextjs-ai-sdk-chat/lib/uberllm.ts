// UberLLM as a Vercel AI SDK provider, through the official OpenAI-compatible
// package: https://ai-sdk.dev/providers/openai-compatible-providers
import { createOpenAICompatible } from '@ai-sdk/openai-compatible';

// The key is only ever sent here.
export const UBERLLM_BASE_URL = 'https://api.uberllm.dev/v1';
// Public price list, no key needed: https://uberllm.dev/docs/price-api
export const UBERLLM_PRICES_URL = 'https://api.uberllm.dev/api/v1/public/prices';

export const uberllm = createOpenAICompatible({
  name: 'uberllm',
  baseURL: UBERLLM_BASE_URL,
  apiKey: process.env.UBERLLM_API_KEY, // sent as "Authorization: Bearer <key>"
  includeUsage: true, // token counts on streamed answers too
  // Needed for typed output (Output.object): without it the SDK does not send
  // your JSON schema to the model and the answer may not match it.
  supportsStructuredOutputs: true,
});

// Any chat model id from https://uberllm.dev/models. It must take tools.
export const MODEL = process.env.UBERLLM_MODEL || 'deepseek/deepseek-v4-flash';
