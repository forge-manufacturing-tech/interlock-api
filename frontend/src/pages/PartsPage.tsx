import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { DefaultService } from "../api";
import type { PartNode } from "../api";
import { ChevronRight, ChevronDown, Search } from "lucide-react";

interface NodeData extends PartNode {
  children?: NodeData[];
  type?: string;
  quantity?: number;
  unit?: string;
  unit_cost?: number;
  [key: string]: unknown;
}

export default function PartsPage() {
  const [search, setSearch] = useState("");
  const [expandedTrees, setExpandedTrees] = useState<Set<string>>(new Set());

  const { data: roots, isLoading: rootsLoading } = useQuery({
    queryKey: ["trees"],
    queryFn: () => DefaultService.readTreesTreesGet(),
  });

  const toggleTree = (id: string) => {
    setExpandedTrees((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const expandAll = () => {
    if (roots) {
      setExpandedTrees(new Set(roots.map((r) => r.id).filter(Boolean) as string[]));
    }
  };

  const collapseAll = () => {
    setExpandedTrees(new Set());
  };

  const filteredRoots = roots?.filter((r) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      r.name?.toLowerCase().includes(q) ||
      r.description?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-text-primary">
          Parts Explorer
        </h1>
        <p className="mt-1 text-text-secondary">
          Manufacturing parts organized by product tree.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search trees..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-md border border-border bg-surface pl-10 pr-4 py-2.5 text-text-primary placeholder-text-muted outline-none focus:border-primary"
          />
        </div>
        <button
          onClick={expandAll}
          className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text-secondary hover:border-primary hover:text-primary transition-colors"
        >
          Expand All
        </button>
        <button
          onClick={collapseAll}
          className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text-secondary hover:border-primary hover:text-primary transition-colors"
        >
          Collapse All
        </button>
      </div>

      {rootsLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : !filteredRoots || filteredRoots.length === 0 ? (
        <div className="rounded-md border border-border bg-surface-light p-12 text-center">
          <p className="text-text-muted">
            No manufacturing trees found. Use the BOM Ingest or Agent Chat to create parts.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredRoots.map((root) => (
            <TreeCard
              key={root.id}
              root={root}
              expanded={expandedTrees.has(root.id ?? "")}
              onToggle={() => root.id && toggleTree(root.id)}
              searchQuery={search}
            />
          ))}
        </div>
      )}
    </div>
  );
}

const NODE_TYPE_COLORS: Record<string, string> = {
  part: "#1E40AF",
  operation: "#8B5CF6",
  currency: "#10B981",
  labor: "#F59E0B",
  tool: "#6366F1",
};

function TreeCard({
  root,
  expanded,
  onToggle,
  searchQuery,
}: {
  root: PartNode;
  expanded: boolean;
  onToggle: () => void;
  searchQuery: string;
}) {
  const { data: treeData, isLoading } = useQuery({
    queryKey: ["tree", root.id],
    queryFn: async () => (await DefaultService.readTreeStructureTreesPartIdGet(root.id!)) as NodeData,
    enabled: expanded && !!root.id,
  });

  const partCount = treeData ? countParts(treeData) : null;

  return (
    <div className="rounded-md border border-border bg-surface-light overflow-hidden">
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-3 px-5 py-4 text-left hover:bg-surface transition-colors"
      >
        {expanded ? (
          <ChevronDown className="h-5 w-5 text-primary flex-shrink-0" />
        ) : (
          <ChevronRight className="h-5 w-5 text-text-muted flex-shrink-0" />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <span className="font-mono text-sm font-semibold text-text-primary truncate">
              {root.name || "Unnamed Product"}
            </span>
            <StatusBadge status={root.status} />
            {partCount !== null && (
              <span className="text-xs text-text-muted">
                {partCount} part{partCount !== 1 ? "s" : ""}
              </span>
            )}
          </div>
          {root.description && (
            <p className="mt-0.5 text-xs text-text-muted truncate">
              {root.description}
            </p>
          )}
        </div>
        {root.unit_of_measure && (
          <span className="text-xs text-text-muted flex-shrink-0">
            {root.unit_of_measure}
          </span>
        )}
      </button>

      {expanded && (
        <div className="border-t border-border px-5 py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-6">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : treeData ? (
            <TreeNode node={treeData} depth={0} searchQuery={searchQuery} />
          ) : (
            <p className="text-sm text-text-muted">No tree data available.</p>
          )}
        </div>
      )}
    </div>
  );
}

function countParts(node: NodeData): number {
  let count = node.type === "part" ? 1 : 0;
  if (node.children) {
    for (const child of node.children) {
      count += countParts(child);
    }
  }
  return count;
}

function TreeNode({
  node,
  depth,
  searchQuery,
}: {
  node: NodeData;
  depth: number;
  searchQuery: string;
}) {
  const [collapsed, setCollapsed] = useState(depth > 2);
  const children = node.children;
  const hasChildren = children && children.length > 0;
  const typeColor = NODE_TYPE_COLORS[node.type?.toLowerCase() || ""] || "#71717A";

  return (
    <div style={{ marginLeft: depth * 20 }}>
      <div
        className="flex items-center gap-2 py-1.5 cursor-pointer group"
        onClick={() => hasChildren && setCollapsed(!collapsed)}
      >
        {hasChildren && (
          <span className="text-xs text-text-muted w-4 text-center">
            {collapsed ? "▸" : "▾"}
          </span>
        )}
        {!hasChildren && <span className="w-4" />}
        <span className="text-sm text-text-primary group-hover:text-primary transition-colors">
          {node.name || node.id || "Unknown"}
        </span>
        {node.type && (
          <span
            className="rounded-full px-2 py-0.5 text-xs font-medium"
            style={{ backgroundColor: typeColor + "30", color: typeColor }}
          >
            {node.type}
          </span>
        )}
        {node.quantity !== undefined && node.quantity !== null && (
          <span className="text-xs text-text-muted">
            x{node.quantity}{node.unit ? ` ${node.unit}` : ""}
          </span>
        )}
        {node.unit_cost !== undefined && node.unit_cost !== null && (
          <span className="text-xs text-text-muted">
            ${Number(node.unit_cost).toFixed(2)}
          </span>
        )}
      </div>
      {hasChildren && !collapsed && (
        <div>
          {children.map((child: NodeData, i: number) => (
            <TreeNode key={child.id || i} node={child} depth={depth + 1} searchQuery={searchQuery} />
          ))}
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
