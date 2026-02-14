import { useState, useRef, useEffect } from "react";
import { DefaultService } from "../api";
import { Paperclip, Send, X, FileText, Image, Lock } from "lucide-react";
import { useAuth } from "../lib/auth";

interface Message {
  role: "user" | "assistant";
  content: string;
  fileName?: string;
}

export default function AgentPage() {
  const { hasAiAccess } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
      const formData: Record<string, any> = {};
      if (text) formData.message = text;
      if (fileToSend) formData.file = fileToSend;
      const res = await DefaultService.chatAgentAgentChatPost(formData);
      const content =
        typeof res === "string"
          ? res
          : typeof res?.response === "string"
            ? res.response
            : JSON.stringify(res, null, 2);
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
    <div className="flex h-[calc(100vh-4rem)] flex-col p-6">
      <div className="mb-4">
        <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-text-primary">
          Manufacturing Assistant
        </h1>
        <p className="mt-1 text-text-secondary">
          Chat with the tech transfer agent. Attach PDFs or images for
          multimodal analysis.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto rounded-md border border-border bg-surface-light p-4 space-y-3">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4">
            <p className="text-text-muted text-sm">
              Send a message to start the conversation.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              <span className="rounded-full border border-border px-3 py-1 text-xs text-text-muted">
                PDF analysis
              </span>
              <span className="rounded-full border border-border px-3 py-1 text-xs text-text-muted">
                Image recognition
              </span>
              <span className="rounded-full border border-border px-3 py-1 text-xs text-text-muted">
                BOM extraction
              </span>
              <span className="rounded-full border border-border px-3 py-1 text-xs text-text-muted">
                Manufacturing queries
              </span>
            </div>
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
              {msg.fileName && (
                <div className="mb-2 flex items-center gap-2 rounded border border-border bg-surface-lighter px-2 py-1 text-xs text-text-muted">
                  {getFileIcon(msg.fileName)}
                  {msg.fileName}
                </div>
              )}
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
  );
}
