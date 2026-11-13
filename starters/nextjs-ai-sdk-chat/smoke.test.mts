// Smoke test.  npm test
// The offline tests call the real /api/chat handler and the provider with a
// stand-in for the API. The live ones call the real API and run only when
// UBERLLM_API_KEY is set (they cost a fraction of a cent).
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { generateText, Output } from 'ai';
import { z } from 'zod';

const live = process.env.UBERLLM_API_KEY ? false : 'UBERLLM_API_KEY is not set';
process.env.UBERLLM_API_KEY ||= 'offline-test-key';
const { POST } = await import('./app/api/chat/route');
const { MODEL, UBERLLM_BASE_URL, uberllm } = await import('./lib/uberllm');

const capital = z.object({ city: z.string(), country: z.string() });

const userMessage = (text: string) => ({
  messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text }] }],
});
const ask = (text: string) =>
  POST(new Request('http://localhost/api/chat', { method: 'POST', body: JSON.stringify(userMessage(text)) }));

// One streamed chat completion, as the API sends it (server-sent events).
const sse = (chunks: object[]) =>
  new Response(chunks.map((c) => `data: ${JSON.stringify(c)}\n\n`).join('') + 'data: [DONE]\n\n', {
    headers: { 'content-type': 'text/event-stream' },
  });
const chunk = (delta: object, finish_reason: string | null = null) => ({
  id: 'c1',
  object: 'chat.completion.chunk',
  created: 0,
  model: MODEL,
  choices: [{ index: 0, delta, finish_reason }],
});

test('the key only goes to api.uberllm.dev', () => {
  assert.equal(new URL(UBERLLM_BASE_URL).origin, 'https://api.uberllm.dev');
});

test('offline: /api/chat calls the tool, then streams the answer', async () => {
  const realFetch = globalThis.fetch;
  const calls: { url: string; auth: string | null; body: any }[] = [];
  globalThis.fetch = (async (input: any, init: any) => {
    const url = String(input instanceof Request ? input.url : input);
    if (url === 'https://api.uberllm.dev/api/v1/public/prices?model=openai%2Fgpt-5.5') {
      return Response.json({
        updated_at: '2026-01-01T00:00:00Z',
        models: [{ id: 'openai/gpt-5.5', name: 'GPT-5.5', type: 'text', unit: '1M tokens', input_per_m: 2.85, output_per_m: 17.1 }],
      });
    }
    calls.push({ url, auth: new Headers(init.headers).get('authorization'), body: JSON.parse(init.body) });
    if (calls.length === 1) {
      return sse([
        chunk({ role: 'assistant', tool_calls: [{ index: 0, id: 'call_1', type: 'function', function: { name: 'modelPrice', arguments: '{"model":"openai/gpt-5.5"}' } }] }),
        chunk({}, 'tool_calls'),
      ]);
    }
    return sse([chunk({ role: 'assistant', content: 'Input costs ' }), chunk({ content: '$2.85 per 1M tokens.' }), chunk({}, 'stop')]);
  }) as typeof fetch;

  try {
    const res = await ask('What does GPT-5.5 cost?');
    assert.equal(res.status, 200);
    const stream = await res.text();
    assert.match(stream, /"type":"tool-output-available"/);
    assert.match(stream, /Input costs /);
    assert.match(stream, /\$2\.85 per 1M tokens\./);
  } finally {
    globalThis.fetch = realFetch;
  }

  assert.equal(calls.length, 2);
  for (const c of calls) {
    assert.equal(c.url, 'https://api.uberllm.dev/v1/chat/completions');
    assert.equal(c.auth, `Bearer ${process.env.UBERLLM_API_KEY}`);
  }
  assert.equal(calls[0].body.tools[0].function.name, 'modelPrice');
  const toolResult = calls[1].body.messages.at(-1);
  assert.equal(toolResult.role, 'tool');
  assert.match(toolResult.content, /17\.1/); // the live price went back to the model
});

test('offline: a bad request body is a 400, a missing key says what to do', async () => {
  const post = (body: string) => POST(new Request('http://localhost/api/chat', { method: 'POST', body }));
  for (const body of ['not json', '{}', '{"messages":"x"}']) assert.equal((await post(body)).status, 400, body);

  const key = process.env.UBERLLM_API_KEY;
  delete process.env.UBERLLM_API_KEY;
  try {
    const res = await ask('hi');
    assert.equal(res.status, 500);
    assert.match(await res.text(), /^UBERLLM_API_KEY is not set\. Copy \.env\.example/); // plain text, not JSON
  } finally {
    process.env.UBERLLM_API_KEY = key;
  }
});

test('offline: the price tool reads the public price list', async () => {
  const { tools } = await import('./lib/tools');
  const realFetch = globalThis.fetch;
  const urls: string[] = [];
  let answer: () => Response = () => Response.json({ models: [] });
  globalThis.fetch = (async (input: any) => {
    urls.push(String(input));
    return answer();
  }) as typeof fetch;
  const run = (model: string) => tools.modelPrice.execute!({ model }, { toolCallId: 't', messages: [] } as any) as Promise<any>;
  try {
    // A path trick stays in the query string, on the price list address.
    assert.match((await run('../../health')).error, /no model called/);
    assert.equal(urls[0], 'https://api.uberllm.dev/api/v1/public/prices?model=..%2F..%2Fhealth');
    answer = () => new Response('<html>bad gateway</html>', { status: 502 });
    assert.match((await run('openai/gpt-5.5')).error, /Could not reach/);
    answer = () => Response.json({ models: [{ id: 'a/b', name: 'B', type: 'image', unit: 'image', price: 0.03, list_price: 0.04, discount_pct: 25 }] });
    assert.deepEqual(JSON.parse(JSON.stringify(await run('a/b'))), { id: 'a/b', name: 'B', unit: 'image', price: 0.03, list_price: 0.04, discount_pct: 25 });
  } finally {
    globalThis.fetch = realFetch;
  }
});

test('offline: typed output sends the JSON schema to the model', async () => {
  const realFetch = globalThis.fetch;
  let body: any;
  globalThis.fetch = (async (_input: any, init: any) => {
    body = JSON.parse(init.body);
    return Response.json({
      id: 'c1',
      object: 'chat.completion',
      created: 0,
      model: MODEL,
      choices: [{ index: 0, message: { role: 'assistant', content: '{"city":"Paris","country":"France"}' }, finish_reason: 'stop' }],
      usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
    });
  }) as typeof fetch;
  try {
    const { output } = await generateText({ model: uberllm(MODEL), output: Output.object({ schema: capital }), prompt: 'The capital of France.' });
    assert.deepEqual(output, { city: 'Paris', country: 'France' });
  } finally {
    globalThis.fetch = realFetch;
  }
  // This is what supportsStructuredOutputs: true in lib/uberllm.ts turns on.
  assert.equal(body.response_format.type, 'json_schema');
  assert.deepEqual(Object.keys(body.response_format.json_schema.schema.properties), ['city', 'country']);
});

test('live: /api/chat streams an answer that used the price tool', { skip: live }, async () => {
  const res = await ask('What does deepseek/deepseek-v4-flash cost per 1M input tokens? Look it up.');
  assert.equal(res.status, 200);
  const stream = await res.text();
  assert.match(stream, /"type":"tool-output-available"/, 'the model called modelPrice');
  assert.match(stream, /"type":"text-delta"/, 'the answer streamed');
  assert.match(stream, /"input_per_m":/, 'the tool returned a price');
  assert.doesNotMatch(stream, /"type":"error"/);
});

test('live: typed output follows the schema', { skip: live }, async () => {
  const { output } = await generateText({
    model: uberllm(MODEL),
    output: Output.object({ schema: capital }),
    prompt: 'The capital of France.',
  });
  assert.equal(output.city, 'Paris');
  assert.equal(output.country, 'France');
});
