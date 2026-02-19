import { useState, useRef, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import { DefaultService } from "../api";
import { Paperclip, Send, X, FileText, Image, Trash2 } from "lucide-react";

const STORAGE_KEY = "agent-chat-messages";

// Type for content blocks from multimodal messages
type ContentBlock =
  | { type: "text"; text: string }
  | { type: "image_url"; image_url: { url: string } };

// Helper to normalize content (handles both string and content block arrays)
function normalizeContent(content: string | ContentBlock[]): string {
  if (typeof content === "string") {
    return content;
  }
  if (Array.isArray(content)) {
    return content
      .filter(
        (block): block is { type: "text"; text: string } =>
          block.type === "text",
      )
      .map((block) => block.text)
      .join("\n");
  }
  return String(content);
}

interface Message {
  role: "user" | "assistant";
  content: string;
  fileName?: string;
  toolCalls?: ToolCall[];
}

interface ToolCall {
  tool: string;
  input: string;
  output?: string;
}

interface ChatFormData {
  message?: string;
  file?: File;
  history?: string;
}

interface AgentChatProps {
  className?: string;
}

function loadMessages(): Message[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored) as Message[];
    }
  } catch {
    // Ignore parse errors
  }
  return [];
}

function saveMessages(messages: Message[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  } catch {
    // Ignore storage errors
  }
}

export default function AgentChat({ className = "" }: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>(loadMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Save messages to localStorage whenever they change
  useEffect(() => {
    saveMessages(messages);
  }, [messages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleClear = () => {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  const refetchQueries = () => {
    // Invalidate and refetch parts and trees queries
    queryClient.invalidateQueries({ queryKey: ["trees"] });
    queryClient.invalidateQueries({ queryKey: ["tree"] });
    queryClient.invalidateQueries({ queryKey: ["parts-all"] });
    queryClient.invalidateQueries({ queryKey: ["part"] });
    queryClient.invalidateQueries({ queryKey: ["labor"] });
    queryClient.invalidateQueries({ queryKey: ["tools"] });
  };

  const handleSend = async () => {
    const text = input.trim();
    if ((!text && !attachedFile) || loading) return;

    const userMessage: Message = {
      role: "user",
      content: text || (attachedFile ? `Uploaded: ${attachedFile.name}` : ""),
      fileName: attachedFile?.name,
    };

    setInput("");
    const fileToSend = attachedFile;
    setAttachedFile(null);
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const formData: ChatFormData = {};
      if (text) formData.message = text;
      if (fileToSend) formData.file = fileToSend;
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));
      formData.history = JSON.stringify(history);

      const res = await DefaultService.chatAgentAgentChatPost(formData);
      const responseData =
        typeof res === "string"
          ? { response: res, history: [], tool_calls: [] }
          : res;

      const newHistory: Message[] = (responseData.history || []).map(
        (m: { role: string; content: string | ContentBlock[] }) => ({
          role: m.role as "user" | "assistant",
          content: normalizeContent(m.content as string | ContentBlock[]),
          toolCalls:
            m.role === "assistant" ? responseData.tool_calls : undefined,
        }),
      );
      setMessages(newHistory);

      // Refetch queries after agent responds (agent may update parts/trees)
      refetchQueries();
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

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setAttachedFile(file);
    e.target.value = "";
  };

  const getFileIcon = (name: string) => {
    const ext = name.split(".").pop()?.toLowerCase();
    if (ext === "pdf") return <FileText className="h-4 w-4" />;
    if (["png", "jpg", "jpeg", "gif", "webp"].includes(ext || ""))
      return <Image className="h-4 w-4" />;
    return <FileText className="h-4 w-4" />;
  };

  return (
    <div className={`flex flex-col ${className}`}>
      <div className="border-b border-border bg-surface-light px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-mono text-sm font-semibold uppercase tracking-wider text-text-primary">
              Manufacturing Assistant
            </h2>
            <p className="text-xs text-text-muted mt-0.5">
              Attach PDFs or images for analysis
            </p>
          </div>
          {messages.length > 0 && (
            <button
              onClick={handleClear}
              className="rounded-md border border-border bg-surface-light p-2 text-text-muted transition-colors hover:border-red-500 hover:text-red-500"
              title="Clear chat"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
            <p className="text-xs text-text-muted">
              Ask about your manufacturing data
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-md px-3 py-2 text-xs ${
                msg.role === "user"
                  ? "bg-primary/20 text-text-primary"
                  : "bg-surface text-text-secondary"
              }`}
            >
              {msg.fileName && (
                <div className="mb-2 flex items-center gap-2 rounded border border-border bg-surface-lighter px-2 py-1 text-[10px] text-text-muted">
                  {getFileIcon(msg.fileName)}
                  {msg.fileName}
                </div>
              )}
              <div className="prose prose-xs prose-invert max-w-none">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>

              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <div className="mt-2 space-y-1">
                  <div className="text-[10px] font-mono uppercase text-text-muted">
                    Tool Calls:
                  </div>
                  {msg.toolCalls.map((tc, j) => (
                    <div
                      key={j}
                      className="rounded border border-border bg-surface-lighter p-1.5 text-[10px]"
                    >
                      <div className="font-mono font-semibold text-primary">
                        {tc.tool}
                      </div>
                      <pre className="mt-1 whitespace-pre-wrap text-text-muted">
                        {tc.input}
                      </pre>
                      {tc.output && (
                        <pre className="mt-1 whitespace-pre-wrap text-text-secondary">
                          → {tc.output}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-md bg-surface px-3 py-2">
              <div className="flex items-center gap-2 text-xs text-text-muted">
                <div className="h-3 w-3 animate-spin rounded-full border border-primary border-t-transparent" />
                Thinking...
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {attachedFile && (
        <div className="mx-3 mb-2 flex items-center gap-2 rounded border border-border bg-surface-light px-2 py-1.5">
          {getFileIcon(attachedFile.name)}
          <span className="flex-1 truncate text-xs text-text-secondary">
            {attachedFile.name}
          </span>
          <span className="text-[10px] text-text-muted">
            {(attachedFile.size / 1024).toFixed(1)} KB
          </span>
          <button
            onClick={() => setAttachedFile(null)}
            className="rounded p-0.5 text-text-muted hover:bg-surface-lighter hover:text-text-primary"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      )}

      <div className="border-t border-border p-3">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept=".pdf,.png,.jpg,.jpeg,.gif,.webp,.csv,.txt,.json,.xlsx"
          className="hidden"
        />
        <div className="flex gap-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="rounded-md border border-border bg-surface-light p-2 text-text-muted transition-colors hover:border-primary hover:text-primary"
            title="Attach file"
          >
            <Paperclip className="h-4 w-4" />
          </button>
          <input
            type="text"
            placeholder="Ask..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 rounded-md border border-border bg-surface px-3 py-2 text-xs text-text-primary placeholder-text-muted outline-none focus:border-primary"
          />
          <button
            onClick={handleSend}
            disabled={loading || (!input.trim() && !attachedFile)}
            className="rounded-md bg-primary p-2 text-white transition-colors hover:bg-primary/90 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
