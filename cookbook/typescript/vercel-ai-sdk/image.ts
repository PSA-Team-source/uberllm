// Make an image with the Vercel AI SDK on UberLLM and save it.
//   npm i ai @ai-sdk/openai-compatible
//   export UBERLLM_API_KEY=ull_...
//   npx tsx vercel-ai-sdk/image.ts
import { writeFile } from "node:fs/promises";
import { generateImage } from "ai";
import { uberllm } from "./provider.js";

const { image } = await generateImage({
  model: uberllm.imageModel(process.env.UBERLLM_IMAGE_MODEL ?? "black-forest-labs/flux.2-klein-4b"),
  prompt: "A red bicycle on a white background, studio photo",
  size: "1024x1024",
});
await writeFile("image.png", image.uint8Array);
console.log(`saved image.png (${image.uint8Array.length} bytes)`);
