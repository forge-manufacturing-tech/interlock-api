import { useState, Fragment } from "react";
import { useQuery } from "@tanstack/react-query";
import { DefaultService } from "../api";

export default function PartsPage() {
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data: parts, isLoading } = useQuery({
    queryKey: ["parts"],
    queryFn: () => DefaultService.readPartsPartsGet(),
  });

  const filtered = parts?.filter((p) => {
    const q = search.toLowerCase();
    return (
      !q ||
      p.name?.toLowerCase().includes(q) ||
      p.description?.toLowerCase().includes(q) ||
      p.status?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-text-primary">
          Parts Explorer
        </h1>
        <p className="mt-1 text-text-secondary">
          Browse and manage manufacturing parts.
        </p>
      </div>

      <input
        type="text"
        placeholder="Search parts by name, description, or status..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full max-w-md rounded-md border border-border bg-surface px-4 py-2.5 text-text-primary placeholder-text-muted outline-none focus:border-primary"
      />

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : !filtered || filtered.length === 0 ? (
        <div className="rounded-md border border-border bg-surface-light p-12 text-center">
          <p className="text-text-muted">
            No parts found. Use the BOM Ingest to add parts.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-md border border-border">
          <table className="w-full divide-y divide-border">
            <thead>
              <tr className="bg-surface-light">
                <th className="px-4 py-3 text-left text-xs font-mono uppercase tracking-wider text-text-secondary">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-mono uppercase tracking-wider text-text-secondary">
                  Description
                </th>
                <th className="px-4 py-3 text-left text-xs font-mono uppercase tracking-wider text-text-secondary">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-mono uppercase tracking-wider text-text-secondary">
                  Unit of Measure
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((part) => (
                <Fragment key={part.id}>
                  <tr
                    onClick={() =>
                      setExpandedId(expandedId === part.id ? null : part.id ?? null)
                    }
                    className="cursor-pointer bg-surface transition-colors hover:bg-surface-light"
                  >
                    <td className="px-4 py-3 text-sm text-text-primary">
                      {part.name || "—"}
                    </td>
                    <td className="px-4 py-3 text-sm text-text-secondary max-w-xs truncate">
                      {part.description || "—"}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <StatusBadge status={part.status} />
                    </td>
                    <td className="px-4 py-3 text-sm text-text-secondary">
                      {part.unit_of_measure || "—"}
                    </td>
                  </tr>
                  {expandedId === part.id && (
                    <tr>
                      <td colSpan={4} className="bg-surface-light px-4 py-4">
                        <pre className="overflow-x-auto rounded-md bg-surface p-4 text-xs text-text-secondary font-mono">
                          {JSON.stringify(part, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status?: string }) {
  const colors: Record<string, string> = {
    APPROVED: "bg-green-500/20 text-green-400",
    PENDING: "bg-yellow-500/20 text-yellow-400",
    REJECTED: "bg-red-500/20 text-red-400",
  };
  const cls = status ? colors[status] || "bg-surface text-text-muted" : "bg-surface text-text-muted";
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {status || "—"}
    </span>
  );
}
