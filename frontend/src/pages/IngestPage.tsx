import { useState, useRef, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { DefaultService } from "../api";

export default function IngestPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const mutation = useMutation({
    mutationFn: (f: File) => DefaultService.ingestBomIngestBomPost({ file: f }),
    onSuccess: (data) => setResult(data),
  });

  const handleFile = (f: File) => {
    setFile(f);
    setResult(null);
    mutation.reset();
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, []);

  const handleUpload = () => {
    if (file) mutation.mutate(file);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-text-primary">
          BOM Ingestion
        </h1>
        <p className="mt-1 text-text-secondary">
          Upload and process bills of materials.
        </p>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-md border-2 border-dashed p-12 text-center transition-colors ${
          dragOver
            ? "border-primary bg-primary/5"
            : "border-border bg-surface-light hover:border-text-muted"
        }`}
      >
        <div className="space-y-2">
          <div className="text-4xl text-text-muted">↑</div>
          <p className="text-text-primary font-medium">
            Drop your file here or click to browse
          </p>
          <p className="text-sm text-text-muted">
            Supported formats: CSV, Excel, JSON
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls,.json"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
      </div>

      {file && (
        <div className="rounded-md border border-border bg-surface-light p-4 flex items-center justify-between">
          <div>
            <p className="text-sm text-text-primary font-medium">{file.name}</p>
            <p className="text-xs text-text-muted">{formatSize(file.size)}</p>
          </div>
          <button
            onClick={handleUpload}
            disabled={mutation.isPending}
            className="rounded-md bg-primary px-4 py-2.5 font-mono text-sm font-medium uppercase tracking-wider text-white transition-colors hover:bg-primary/90 disabled:opacity-50"
          >
            {mutation.isPending ? "Uploading..." : "UPLOAD"}
          </button>
        </div>
      )}

      {mutation.isError && (
        <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          Upload failed. Please check your file format and try again.
        </div>
      )}

      {result && (
        <div className="rounded-md border border-border bg-surface-light p-6">
          <h3 className="font-mono text-sm uppercase tracking-wider text-text-secondary mb-3">
            Result
          </h3>
          <pre className="overflow-x-auto rounded-md bg-surface p-4 text-xs text-text-secondary font-mono">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
