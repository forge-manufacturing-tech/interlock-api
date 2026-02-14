import { useState, useRef, useEffect } from "react";
import { DefaultService } from "../api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function AgentPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const res = await DefaultService.chatAgentAgentChatPost(text);
      const content =
        typeof res === "string" ? res : JSON.stringify(res, null, 2);
      setMessages((prev) => [...prev, { role: "assistant", content }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "An error occurred. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col p-6">
      <div className="mb-4">
        <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-text-primary">
          Manufacturing Assistant
        </h1>
        <p className="mt-1 text-text-secondary">
          Chat with the tech transfer agent.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto rounded-md border border-border bg-surface-light p-4 space-y-3">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <p className="text-text-muted text-sm">
              Send a message to start the conversation.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[75%] rounded-md px-4 py-3 text-sm ${
                msg.role === "user"
                  ? "bg-primary/20 text-text-primary"
                  : "bg-surface text-text-secondary"
              }`}
            >
              <pre className="whitespace-pre-wrap break-words font-sans">
                {msg.content}
              </pre>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-md bg-surface px-4 py-3">
              <div className="flex items-center gap-2 text-sm text-text-muted">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                Thinking...
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="mt-4 flex gap-3">
        <input
          type="text"
          placeholder="Ask about your manufacturing data..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 rounded-md border border-border bg-surface px-4 py-2.5 text-text-primary placeholder-text-muted outline-none focus:border-primary"
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="rounded-md bg-primary px-6 py-2.5 font-mono text-sm font-medium uppercase tracking-wider text-white transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
