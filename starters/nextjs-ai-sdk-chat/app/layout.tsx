import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Chat',
  description: 'A streaming chat app on Next.js and the Vercel AI SDK, using UberLLM.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
