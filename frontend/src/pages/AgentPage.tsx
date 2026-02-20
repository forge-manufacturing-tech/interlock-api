import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { DefaultService, OpenAPI } from "../api";
import { Paperclip, Send, X, FileText, Image, Lock, MessageSquare, Plus, Loader2, History } from "lucide-react";
import { useAuth } from "../lib/auth";

type ContentBlock =
  | { type: "text"; text: string }
  | { type: "image_url"; image_url: { url: string } };

interface Message {
  role: "user" | "assistant";
  content: string | ContentBlock[];
  fileName?: string;
  toolCalls?: ToolCall[];
}

interface ToolCall {
  tool: string;
  input: string;
  output?: string;
}

interface ChatSession {
  id: string;
  title?: string;
  created_at: string;
}

export default function AgentPage() {
  const { hasAiAccess, token } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (hasAiAccess) {
      loadSessions();
    }
  }, [hasAiAccess]);

  useEffect(() => {
    if (currentSessionId) {
      loadMessages(currentSessionId);
    } else {
      setMessages([]);
    }
  }, [currentSessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const loadSessions = async () => {
    try {
      const res = await DefaultService.listSessionsEndpointAgentSessionsGet();
      setSessions(res);
    } catch (err) {
      console.error("Failed to load sessions", err);
    }
  };

  const loadMessages = async (sessionId: string) => {
    try {
      const res = await DefaultService.getSessionMessagesEndpointAgentSessionsSessionIdMessagesGet(sessionId);
      setMessages(res.map((m: { role: "user" | "assistant", content: string | ContentBlock[], tool_calls?: ToolCall[] }) => ({
        role: m.role,
        content: m.content,
        toolCalls: m.tool_calls
      })));
    } catch (err) {
      console.error("Failed to load messages", err);
    }
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setInput("");
    setAttachedFile(null);
  };

  const handleSend = async () => {
    const text = input.trim();
    if ((!text && !attachedFile) || loading) return;

    let sessionId = currentSessionId;

    // Add user message to UI
    const userMessage: Message = {
      role: "user",
      content: text || (attachedFile ? `Uploaded: ${attachedFile.name}` : ""),
      fileName: attachedFile?.name,
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    const fileToSend = attachedFile;
    setAttachedFile(null);
    setLoading(true);

    try {
      if (!sessionId) {
        const session = await DefaultService.createSessionEndpointAgentSessionsPost({
          title: text ? text.slice(0, 40) : (fileToSend ? fileToSend.name : "New Chat")
        });
        sessionId = session.id;
        setCurrentSessionId(sessionId);
        setSessions(prev => [session, ...prev]);
      }

      const formData = new FormData();
      if (text) formData.append("message", text);
      if (fileToSend) formData.append("file", fileToSend);

      const response = await fetch(`${OpenAPI.BASE}/agent/sessions/${sessionId}/chat`, {
        method: "POST",
        body: formData,
        headers: {
          ...(token ? { "Authorization": `Bearer ${token}` } : {}),
        }
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      const assistantMessage: Message = { role: "assistant", content: "", toolCalls: [] };
      setMessages(prev => [...prev, assistantMessage]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            if (dataStr === "[DONE]") continue;

            try {
              const event = JSON.parse(dataStr);
              if (event.type === "content") {
                assistantMessage.content += event.content;
                setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1] = { ...assistantMessage };
                  return newMsgs;
                });
              } else if (event.type === "tool_start") {
                assistantMessage.toolCalls = [
                  ...(assistantMessage.toolCalls || []),
                  { tool: event.tool, input: event.input }
                ];
                setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1] = { ...assistantMessage };
                  return newMsgs;
                });
              } else if (event.type === "tool_end") {
                assistantMessage.toolCalls = assistantMessage.toolCalls?.map(tc =>
                  (tc.tool === event.tool && tc.output === undefined)
                    ? { ...tc, output: event.output }
                    : tc
                );
                setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1] = { ...assistantMessage };
                  return newMsgs;
                });
              } else if (event.type === "error") {
                if (typeof assistantMessage.content === 'string') {
                  assistantMessage.content += `\n\n**Error:** ${event.content}`;
                }
                setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1] = { ...assistantMessage };
                  return newMsgs;
                });
              }
            } catch {
              // Partial JSON, skip
            }
          }
        }
      }
    } catch (err) {
      console.error("Chat error", err);
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

  if (!hasAiAccess) {
    return (
      <div className="flex h-[calc(100vh-4rem)] flex-col items-center justify-center p-6">
        <div className="rounded-md border border-border bg-surface-light p-12 text-center max-w-md">
          <Lock className="mx-auto mb-4 h-12 w-12 text-text-muted" />
          <h2 className="font-mono text-xl font-bold uppercase tracking-wider text-text-primary mb-2">
            AI Access Required
          </h2>
          <p className="text-text-secondary text-sm">
            Your account does not have access to the AI manufacturing assistant.
            Contact an administrator to enable this feature.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Sidebar */}
      <div className="flex w-64 flex-col border-r border-border bg-surface-light p-4 overflow-hidden">
        <button
          onClick={handleNewChat}
          className="mb-6 flex items-center justify-center gap-2 rounded-md border border-dashed border-border p-2.5 font-mono text-xs font-bold uppercase tracking-widest text-text-muted transition-all hover:border-primary hover:bg-primary/5 hover:text-primary"
        >
          <Plus className="h-4 w-4" />
          New Session
        </button>

        <div className="mb-2 flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-widest text-text-muted">
          <History className="h-3 w-3" />
          History
        </div>

        <div className="flex-1 space-y-1 overflow-y-auto">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setCurrentSessionId(s.id)}
              className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors ${
                currentSessionId === s.id
                  ? "bg-primary/20 text-text-primary"
                  : "text-text-secondary hover:bg-surface-lighter hover:text-text-primary"
              }`}
            >
              <MessageSquare className="h-4 w-4 shrink-0 opacity-50" />
              <span className="truncate">{s.title || "Untitled Chat"}</span>
            </button>
          ))}
          {sessions.length === 0 && (
            <div className="py-8 text-center text-xs text-text-muted">
              No history found
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col p-6 overflow-hidden">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-text-primary">
              Manufacturing Assistant
            </h1>
            <p className="mt-1 text-text-secondary text-sm">
              Stream updates as the agent makes tool calls.
            </p>
          </div>
          {currentSessionId && (
            <div className="rounded-md border border-border bg-surface px-3 py-1 text-[10px] font-mono uppercase text-text-muted">
              Session: {currentSessionId.slice(0, 8)}
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto rounded-md border border-border bg-surface-light p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center gap-4">
              <p className="text-text-muted text-sm">
                How can I help with your manufacturing processes today?
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {["Search parts", "Purchase materials", "Plan assembly", "Check costs"].map(tag => (
                  <span key={tag} className="rounded-full border border-border px-3 py-1 text-xs text-text-muted">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-md px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "bg-primary/20 text-text-primary"
                    : "bg-surface text-text-secondary border border-border"
                }`}
              >
                {msg.fileName && (
                  <div className="mb-2 flex items-center gap-2 rounded border border-border bg-surface-lighter px-2 py-1 text-xs text-text-muted">
                    {getFileIcon(msg.fileName)}
                    {msg.fileName}
                  </div>
                )}
                <div className="prose prose-sm prose-invert max-w-none">
                  {typeof msg.content === 'string' ? (
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  ) : (
                    <div className="space-y-2">
                      {/* Handle multi-modal blocks from history */}
                      {msg.content.map((block: ContentBlock, j: number) => (
                        block.type === 'text' ? (
                          <ReactMarkdown key={j}>{block.text}</ReactMarkdown>
                        ) : block.type === 'image_url' ? (
                          <img key={j} src={block.image_url.url} className="max-w-xs rounded border border-border" />
                        ) : null
                      ))}
                    </div>
                  )}
                </div>

                {/* Tool Calls Display */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center gap-2 text-[10px] font-mono font-bold uppercase tracking-widest text-text-muted">
                      <div className="h-[1px] flex-1 bg-border" />
                      Agent Processing
                      <div className="h-[1px] flex-1 bg-border" />
                    </div>
                    {msg.toolCalls.map((tc, j) => (
                      <div
                        key={j}
                        className="rounded border border-border bg-surface-lighter p-2 text-xs"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <div className="font-mono font-bold text-primary">
                            {tc.tool}()
                          </div>
                          {!tc.output && (
                            <Loader2 className="h-3 w-3 animate-spin text-primary" />
                          )}
                        </div>
                        <pre className="mt-1 whitespace-pre-wrap text-[11px] text-text-muted font-mono bg-black/20 p-1.5 rounded">
                          {tc.input}
                        </pre>
                        {tc.output && (
                          <div className="mt-2 border-t border-border pt-2">
                            <pre className="whitespace-pre-wrap text-[11px] text-text-secondary font-mono">
                              {tc.output}
                            </pre>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && !messages[messages.length-1]?.content && (
            <div className="flex justify-start">
              <div className="rounded-md bg-surface px-4 py-3 border border-border">
                <div className="flex items-center gap-2 text-sm text-text-muted">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  Thinking...
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {attachedFile && (
          <div className="mt-2 flex items-center gap-2 rounded-md border border-border bg-surface-light px-3 py-2">
            {getFileIcon(attachedFile.name)}
            <span className="flex-1 truncate text-sm text-text-secondary">
              {attachedFile.name}
            </span>
            <span className="text-xs text-text-muted">
              {(attachedFile.size / 1024).toFixed(1)} KB
            </span>
            <button
              onClick={() => setAttachedFile(null)}
              className="rounded p-1 text-text-muted hover:bg-surface-lighter hover:text-text-primary"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        <div className="mt-3 flex gap-3">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".pdf,.png,.jpg,.jpeg,.gif,.webp,.csv,.txt,.json,.xlsx"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="rounded-md border border-border bg-surface-light p-2.5 text-text-muted transition-colors hover:border-primary hover:text-primary"
            title="Attach file"
          >
            <Paperclip className="h-5 w-5" />
          </button>
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
            disabled={loading || (!input.trim() && !attachedFile)}
            className="rounded-md bg-primary px-6 py-2.5 font-mono text-sm font-medium uppercase tracking-wider text-white transition-colors hover:bg-primary/90 disabled:opacity-50"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
