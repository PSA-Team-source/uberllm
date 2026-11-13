'use client';

// The chat screen. useChat posts to /api/chat and streams the answer in.
// https://ai-sdk.dev/docs/ai-sdk-ui/chatbot
import { useChat } from '@ai-sdk/react';
import { useState } from 'react';

export default function Chat() {
  const [input, setInput] = useState('');
  const { messages, sendMessage, status, error, stop, regenerate } = useChat();
  const busy = status === 'submitted' || status === 'streaming';

  return (
    <main>
      {messages.length === 0 && (
        <p className="hint">Ask anything. Try: &ldquo;What does GPT-5.5 cost per million tokens?&rdquo;</p>
      )}

      {messages.map((message) => (
        <div key={message.id} className={`message ${message.role}`}>
          {message.parts.map((part, i) => {
            if (part.type === 'text') return <p key={i}>{part.text}</p>;
            // A tool part is named "tool-" + the tool's key in lib/tools.ts.
            if (part.type === 'tool-modelPrice') {
              const model = (part.input as { model?: string } | undefined)?.model;
              return (
                <p key={i} className="tool">
                  {part.state === 'output-available' ? 'Looked up' : 'Looking up'} the price{model ? ` of ${model}` : ''}
                </p>
              );
            }
            return null;
          })}
        </div>
      ))}

      {status === 'submitted' && <p className="tool">Thinking&hellip;</p>}
      {error && (
        <p className="error" role="alert">
          {error.message || 'Something went wrong.'}{' '}
          <button type="button" onClick={() => regenerate()}>
            Try again
          </button>
        </p>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!input.trim() || busy) return;
          sendMessage({ text: input });
          setInput('');
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.currentTarget.value)}
          placeholder="Type a message"
          aria-label="Message"
          autoFocus
        />
        {busy ? (
          <button type="button" onClick={() => stop()}>
            Stop
          </button>
        ) : (
          <button type="submit" disabled={!input.trim()}>
            Send
          </button>
        )}
      </form>
    </main>
  );
}
