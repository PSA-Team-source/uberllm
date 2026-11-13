// The chat endpoint. The page posts the conversation here and reads the
// answer as a stream. Follows the AI SDK guide for the Next.js App Router:
// https://ai-sdk.dev/docs/getting-started/nextjs-app-router
import {
  convertToModelMessages,
  createUIMessageStreamResponse,
  isStepCount,
  streamText,
  toUIMessageStream,
  type UIMessage,
} from 'ai';
import { tools } from '@/lib/tools';
import { MODEL, uberllm } from '@/lib/uberllm';

export const maxDuration = 60; // seconds a streamed answer may take on Vercel

export async function POST(req: Request) {
  if (!process.env.UBERLLM_API_KEY) {
    // Plain text: the chat screen shows the body of a failed answer as it is.
    return new Response(
      'UBERLLM_API_KEY is not set. Copy .env.example to .env.local, add your key and restart npm run dev.',
      { status: 500 },
    );
  }
  const body = await req.json().catch(() => null);
  if (!Array.isArray(body?.messages)) return new Response('Send { "messages": [...] }.', { status: 400 });
  const messages = body.messages as UIMessage[];

  const result = streamText({
    model: uberllm(MODEL),
    instructions: 'You are a helpful assistant. Use the modelPrice tool for any question about model prices; never quote a price from memory.',
    messages: await convertToModelMessages(messages),
    tools,
    stopWhen: isStepCount(5), // the model may call tools, then answer, in up to 5 steps
  });

  return createUIMessageStreamResponse({
    stream: toUIMessageStream({
      stream: result.stream,
      // What the page shows when a call fails. UberLLM error messages say what
      // to do ("Your credit balance is too low..."), so pass them on.
      onError: (error) => (error instanceof Error ? error.message : 'Something went wrong. Please try again.'),
    }),
  });
}
