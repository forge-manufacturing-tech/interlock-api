import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { DefaultService } from "../api";

const NODE_TYPE_COLORS: Record<string, string> = {
  part: "#1E40AF",
  operation: "#8B5CF6",
  currency: "#10B981",
  labor: "#F59E0B",
  tool: "#6366F1",
};

export default function TreesPage() {
  const [selectedRoot, setSelectedRoot] = useState<string | null>(null);

  const { data: roots, isLoading } = useQuery({
    queryKey: ["trees"],
    queryFn: () => DefaultService.readTreesTreesGet(),
  });

  const { data: treeData, isLoading: treeLoading } = useQuery({
    queryKey: ["tree", selectedRoot],
    queryFn: () => DefaultService.readTreeStructureTreesPartIdGet(selectedRoot!),
    enabled: !!selectedRoot,
  });

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-text-primary">
          Manufacturing Trees
        </h1>
        <p className="mt-1 text-text-secondary">
          Visualize manufacturing tree structures.
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : !roots || roots.length === 0 ? (
        <div className="rounded-md border border-border bg-surface-light p-12 text-center">
          <p className="text-text-muted">
            No manufacturing trees found. Ingest a BOM to create trees.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {roots.map((root) => (
              <button
                key={root.id}
                onClick={() => setSelectedRoot(root.id ?? null)}
                className={`rounded-md border p-4 text-left transition-colors ${
                  selectedRoot === root.id
                    ? "border-primary bg-primary/10"
                    : "border-border bg-surface-light hover:border-text-muted"
                }`}
              >
                <p className="font-mono text-sm font-medium text-text-primary">
                  {root.name || "Unnamed"}
                </p>
                <p className="mt-1 text-xs text-text-muted truncate">
                  {root.description || "No description"}
                </p>
                {root.status && (
                  <span className="mt-2 inline-block rounded-full bg-surface px-2 py-0.5 text-xs text-text-secondary">
                    {root.status}
                  </span>
                )}
              </button>
            ))}
          </div>

          {selectedRoot && (
            <div className="rounded-md border border-border bg-surface-light p-6">
              {treeLoading ? (
                <div className="flex items-center justify-center py-10">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                </div>
              ) : treeData ? (
                <TreeNode node={treeData} depth={0} />
              ) : (
                <p className="text-text-muted">No tree data available.</p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function TreeNode({ node, depth }: { node: Record<string, any>; depth: number }) {
  const [collapsed, setCollapsed] = useState(depth > 1);
  const children = node.children as Record<string, any>[] | undefined;
  const hasChildren = children && children.length > 0;
  const typeColor = NODE_TYPE_COLORS[node.type?.toLowerCase?.()] || "#71717A";

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
        {node.cost !== undefined && node.cost !== null && (
          <span className="text-xs text-text-muted">
            ${Number(node.cost).toFixed(2)}
          </span>
        )}
      </div>
      {hasChildren && !collapsed && (
        <div>
          {children.map((child: Record<string, any>, i: number) => (
            <TreeNode key={child.id || i} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}
