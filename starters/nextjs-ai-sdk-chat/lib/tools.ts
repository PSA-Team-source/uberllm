import { tool } from 'ai';
import { z } from 'zod';
import { UBERLLM_PRICES_URL } from './uberllm';

// Tools the model may call. Each one runs on the server.
// https://ai-sdk.dev/docs/ai-sdk-core/tools-and-tool-calling
export const tools = {
  // Live price of a model, from UberLLM's public price list (no key needed).
  // It is the price the model's page and the README badge show:
  // https://uberllm.dev/docs/price-api
  modelPrice: tool({
    description:
      'Look up the current price of an AI model on UberLLM, in US dollars ' +
      '(text models: per 1M input and output tokens). ' +
      'Takes a model id such as "openai/gpt-5.5" or "deepseek/deepseek-v4-flash".',
    inputSchema: z.object({ model: z.string().min(1).max(200).describe('The model id, as "maker/name"') }),
    execute: async ({ model }) => {
      // The id goes in the query string, so it cannot change the path that is called.
      const res = await fetch(`${UBERLLM_PRICES_URL}?${new URLSearchParams({ model })}`).catch(() => null);
      const body = res?.ok ? await res.json().catch(() => null) : null;
      if (!Array.isArray(body?.models)) return { error: 'Could not reach the price list. Try again.' };
      // An unknown id, or a model nobody serves right now, is an empty list.
      const m = body.models[0];
      if (!m) return { error: `There is no model called ${model} on UberLLM right now.` };
      // Fields with no value are left out by the API (a text model has no "price", an image model no "input_per_m").
      return {
        id: m.id as string,
        name: m.name as string,
        unit: m.unit as string | undefined,
        input_per_m: m.input_per_m as number | undefined,
        output_per_m: m.output_per_m as number | undefined,
        list_input_per_m: m.list_input_per_m as number | undefined,
        list_output_per_m: m.list_output_per_m as number | undefined,
        price: m.price as number | undefined,
        list_price: m.list_price as number | undefined,
        discount_pct: m.discount_pct as number | undefined,
      };
    },
  }),
};
