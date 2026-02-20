import { useState, useRef, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import { DefaultService, OpenAPI } from "../api";
import { Paperclip, Send, X, FileText, Image, Loader2, Plus, History, MessageSquare } from "lucide-react";
import { useAuth } from "../lib/auth";

const STORAGE_SESSION_KEY = "agent-chat-current-session-id";

// Type for content blocks from multimodal messages
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

interface AgentChatProps {
  className?: string;
}

export default function AgentChat({ className = "" }: AgentChatProps) {
  const { token, hasAiAccess } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(() => localStorage.getItem(STORAGE_SESSION_KEY));
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isSendingRef = useRef(false);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (hasAiAccess) {
      loadSessions();
    }
  }, [hasAiAccess]);

  useEffect(() => {
    if (currentSessionId) {
      localStorage.setItem(STORAGE_SESSION_KEY, currentSessionId);
      if (!isSendingRef.current) {
        loadMessages(currentSessionId);
      }
    } else {
      localStorage.removeItem(STORAGE_SESSION_KEY);
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
    setShowHistory(false);
  };

  const refetchQueries = () => {
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

    let sessionId = currentSessionId;

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
    isSendingRef.current = true;

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
                if (typeof assistantMessage.content === 'string') {
                  assistantMessage.content += event.content;
                }
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
      refetchQueries();
    } catch (err) {
      console.error("Chat error", err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "An error occurred. Please try again." },
      ]);
    } finally {
      setLoading(false);
      isSendingRef.current = false;
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
    <div className={`flex flex-col bg-surface-light ${className}`}>
      <div className="border-b border-border bg-surface-lighter px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-mono text-sm font-semibold uppercase tracking-wider text-text-primary">
              Manufacturing Assistant
            </h2>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className={`rounded-md p-2 transition-colors ${showHistory ? "bg-primary/20 text-primary" : "text-text-muted hover:bg-white/5"}`}
              title="History"
            >
              <History className="h-4 w-4" />
            </button>
            <button
              onClick={handleNewChat}
              className="rounded-md p-2 text-text-muted hover:bg-white/5"
              title="New chat"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden relative flex flex-col">
        {showHistory ? (
          <div className="flex-1 overflow-y-auto p-2 space-y-1 bg-surface">
            <div className="px-2 py-1 mb-2 text-[10px] font-mono font-bold uppercase tracking-widest text-text-muted">
              Recent Sessions
            </div>
            {sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  setCurrentSessionId(s.id);
                  setShowHistory(false);
                }}
                className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-xs transition-colors ${
                  currentSessionId === s.id
                    ? "bg-primary/20 text-text-primary"
                    : "text-text-secondary hover:bg-white/5 hover:text-text-primary"
                }`}
              >
                <MessageSquare className="h-3.5 w-3.5 shrink-0 opacity-50" />
                <span className="truncate">{s.title || "Untitled Chat"}</span>
              </button>
            ))}
            {sessions.length === 0 && (
              <div className="py-8 text-center text-xs text-text-muted">
                No history found
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {messages.length === 0 && (
              <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
                <p className="text-xs text-text-muted">
                  How can I help you today?
                </p>
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[90%] rounded-md px-3 py-2 text-xs ${
                    msg.role === "user"
                      ? "bg-primary/20 text-text-primary border border-primary/20"
                      : "bg-surface text-text-secondary border border-border"
                  }`}
                >
                  {msg.fileName && (
                    <div className="mb-2 flex items-center gap-2 rounded border border-border bg-surface-lighter px-2 py-1 text-[10px] text-text-muted">
                      {getFileIcon(msg.fileName)}
                      {msg.fileName}
                    </div>
                  )}
                  <div className="prose prose-invert prose-xs max-w-none">
                    {typeof msg.content === 'string' ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      <div className="space-y-2">
                        {msg.content.map((block: ContentBlock, j: number) => (
                          block.type === 'text' ? (
                            <ReactMarkdown key={j}>{block.text}</ReactMarkdown>
                          ) : block.type === 'image_url' ? (
                            <img key={j} src={block.image_url.url} className="max-w-full rounded border border-border" />
                          ) : null
                        ))}
                      </div>
                    )}
                  </div>

                  {msg.toolCalls && msg.toolCalls.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <div className="flex items-center gap-2 text-[9px] font-mono font-bold uppercase tracking-widest text-text-muted opacity-60">
                        <div className="h-[1px] flex-1 bg-border" />
                        Processing
                        <div className="h-[1px] flex-1 bg-border" />
                      </div>
                      {msg.toolCalls.map((tc, j) => (
                        <div
                          key={j}
                          className="rounded border border-border bg-surface-lighter p-1.5 text-[10px]"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="font-mono font-bold text-primary">
                              {tc.tool}()
                            </div>
                            {!tc.output && (
                              <Loader2 className="h-2.5 w-2.5 animate-spin text-primary" />
                            )}
                          </div>
                          <pre className="mt-1 whitespace-pre-wrap text-[10px] text-text-muted font-mono bg-black/20 p-1 rounded">
                            {tc.input}
                          </pre>
                          {tc.output && (
                            <div className="mt-1.5 border-t border-border pt-1.5">
                              <pre className="whitespace-pre-wrap text-[10px] text-text-secondary font-mono">
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
                <div className="rounded-md bg-surface px-3 py-2 border border-border">
                  <div className="flex items-center gap-2 text-xs text-text-muted">
                    <Loader2 className="h-3 w-3 animate-spin text-primary" />
                    Thinking...
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="border-t border-border p-3 bg-surface-lighter">
        {attachedFile && (
          <div className="mb-2 flex items-center gap-2 rounded border border-border bg-surface-light px-2 py-1">
            {getFileIcon(attachedFile.name)}
            <span className="flex-1 truncate text-[10px] text-text-secondary">
              {attachedFile.name}
            </span>
            <button
              onClick={() => setAttachedFile(null)}
              className="rounded p-0.5 text-text-muted hover:text-text-primary"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        )}
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
            className="rounded-md border border-border bg-surface p-2 text-text-muted transition-colors hover:border-primary hover:text-primary"
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
            className="rounded-md bg-primary p-2 text-white transition-colors hover:bg-primary/90 disabled:opacity-50 shadow-sm"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
