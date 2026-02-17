import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { DefaultService } from "../api";
import type { PartNode } from "../api";
import { ChevronRight, ChevronDown, Search, Plus, Hammer, Box } from "lucide-react";
import PartDetailPanel from "../components/parts/PartDetailPanel";
import CreatePartModal from "../components/parts/CreatePartModal";
import CreateResourceModal from "../components/parts/CreateResourceModal";

interface NodeData extends PartNode {
  children?: NodeData[];
  type?: string;
  status?: string;
  quantity?: number;
  unit?: string;
  unit_cost?: number;
  [key: string]: unknown;
}

export default function PartsPage() {
  const [search, setSearch] = useState("");
  const [expandedTrees, setExpandedTrees] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<NodeData | null>(null);
  const [showCreatePart, setShowCreatePart] = useState(false);
  const [showCreateResource, setShowCreateResource] = useState(false);

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
    <div className="flex h-full overflow-hidden">
      {/* Main Content - Tree List */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="p-6 space-y-6 flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-mono text-2xl font-bold uppercase tracking-wider text-text-primary">
                Parts Explorer
              </h1>
              <p className="mt-1 text-text-secondary">
                Manufacturing parts organized by product tree.
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowCreateResource(true)}
                className="flex items-center gap-2 px-3 py-2 rounded-md bg-surface border border-border text-sm text-text-secondary hover:text-primary hover:border-primary transition-colors"
              >
                <Hammer size={16} />
                Resources
              </button>
              <button
                onClick={() => setShowCreatePart(true)}
                className="flex items-center gap-2 px-3 py-2 rounded-md bg-primary text-sm font-medium text-white hover:bg-primary/90 transition-colors shadow-sm"
              >
                <Plus size={16} />
                New Part
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
              <input
                type="text"
                placeholder="Search trees..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-md border border-border bg-surface pl-10 pr-4 py-2.5 text-text-primary placeholder-text-muted outline-none focus:border-primary transition-all shadow-sm"
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
            <div className="rounded-md border border-border bg-surface-light p-12 text-center flex flex-col items-center gap-4">
              <Box className="h-12 w-12 text-text-muted" />
              <p className="text-text-muted">
                No manufacturing trees found. Use the "New Part" button to create one.
              </p>
            </div>
          ) : (
            <div className="space-y-3 pb-10">
              {filteredRoots.map((root) => (
                <TreeCard
                  key={root.id}
                  root={root as NodeData}
                  expanded={expandedTrees.has(root.id ?? "")}
                  onToggle={() => root.id && toggleTree(root.id)}
                  onSelect={(node) => setSelectedNode(node as NodeData)}
                  selectedId={selectedNode?.id}
                  searchQuery={search}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Detail Panel */}
      {selectedNode && (
        <div className="w-[450px] flex-shrink-0 h-full border-l border-border transition-all animate-in slide-in-from-right duration-300">
          <PartDetailPanel
            key={selectedNode.id}
            node={selectedNode}
            onSelect={(node) => setSelectedNode(node)}
            onClose={() => setSelectedNode(null)}
          />
        </div>
      )}

      {/* Modals */}
      {showCreatePart && <CreatePartModal onClose={() => setShowCreatePart(false)} />}
      {showCreateResource && <CreateResourceModal onClose={() => setShowCreateResource(false)} />}
    </div>
  );
}

const NODE_TYPE_COLORS: Record<string, string> = {
  part: "#3B82F6", // Blue
  operation: "#8B5CF6", // Purple
  currency: "#10B981", // Green
  labor: "#F59E0B", // Amber
  tool: "#EC4899", // Pink
};

function TreeCard({
  root,
  expanded,
  onToggle,
  onSelect,
  selectedId,
  searchQuery,
}: {
  root: NodeData;
  expanded: boolean;
  onToggle: () => void;
  onSelect: (node: NodeData) => void;
  selectedId?: string;
  searchQuery: string;
}) {
  const { data: treeData, isLoading } = useQuery({
    queryKey: ["tree", root.id],
    queryFn: async () => (await DefaultService.readTreeStructureTreesPartIdGet(root.id!)) as NodeData,
    enabled: expanded && !!root.id,
  });

  const partCount = treeData ? countParts(treeData) : null;
  const isSelected = selectedId === root.id;

  return (
    <div className={`rounded-md border transition-all ${isSelected ? 'border-primary shadow-sm ring-1 ring-primary/20' : 'border-border'} bg-surface-light overflow-hidden`}>
      <button
        type="button"
        className={`flex w-full items-center gap-3 px-5 py-4 text-left hover:bg-surface transition-colors cursor-pointer ${isSelected ? 'bg-primary/5' : ''}`}
        onClick={() => {
          onSelect(root);
        }}
      >
        <div
          onClick={(e) => { e.stopPropagation(); onToggle(); }}
          className="p-1 hover:bg-surface-hover rounded text-text-muted hover:text-text-primary transition-colors"
        >
          {expanded ? (
            <ChevronDown className="h-5 w-5 flex-shrink-0" />
          ) : (
            <ChevronRight className="h-5 w-5 flex-shrink-0" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <span className={`font-mono text-sm font-semibold truncate ${isSelected ? 'text-primary' : 'text-text-primary'}`}>
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
        <div className="border-t border-border px-5 py-4 pl-12 bg-surface/50">
          {isLoading ? (
            <div className="flex items-center justify-center py-6">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : treeData ? (
            <TreeNode
              node={treeData}
              depth={0}
              searchQuery={searchQuery}
              onSelect={onSelect}
              selectedId={selectedId}
            />
          ) : (
            <p className="text-sm text-text-muted italic">No tree data available.</p>
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
  onSelect,
  selectedId,
}: {
  node: NodeData;
  depth: number;
  searchQuery: string;
  onSelect: (node: NodeData) => void;
  selectedId?: string;
}) {
  const [collapsed, setCollapsed] = useState(depth > 2);
  const children = node.children;
  const hasChildren = children && children.length > 0;
  const typeColor = NODE_TYPE_COLORS[node.type?.toLowerCase() || ""] || "#71717A";
  const isSelected = selectedId === node.id;

  return (
    <div className="relative">
      {/* Indentation guide line */}
      {depth > 0 && (
        <div className="absolute left-[7px] top-0 bottom-0 w-px bg-border/50" />
      )}

      <div className="relative" style={{ paddingLeft: '24px' }}>
        {/* Connector line */}
        {depth > 0 && <div className="absolute left-[7px] top-1/2 w-[17px] h-px bg-border/50" />}

        <div
          className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer group transition-colors ${isSelected ? 'bg-primary/10 ring-1 ring-primary/20' : 'hover:bg-surface-hover'}`}
          onClick={(e) => {
            e.stopPropagation();
            onSelect(node);
          }}
        >
          {/* Toggle Logic */}
          <div
            className={`w-4 h-4 flex items-center justify-center rounded hover:bg-black/5 transition-colors text-text-muted cursor-pointer ${hasChildren ? '' : 'invisible'}`}
            onClick={(e) => {
              e.stopPropagation();
              if (hasChildren) setCollapsed(!collapsed);
            }}
          >
            {collapsed ? "▸" : "▾"}
          </div>

          <span className={`text-[12px] transition-colors font-medium truncate ${isSelected ? 'text-primary' : 'text-text-primary'}`}>
            {node.name || node.id || "Unknown"}
          </span>

          {node.type && (
            <span
              className="rounded px-1.5 py-0.5 text-[10px] uppercase font-bold tracking-wider"
              style={{
                backgroundColor: typeColor + "15",
                color: typeColor,
              }}
            >
              {node.type}
            </span>
          )}

          {/* Spacer */}
          <div className="flex-1" />

          {node.quantity !== undefined && node.quantity !== null && (
            <span className="text-[10px] text-text-muted font-mono whitespace-nowrap">
              x{node.quantity}{node.unit ? ` ${node.unit}` : ""}
            </span>
          )}
          {node.unit_cost !== undefined && node.unit_cost !== null && (
            <span className="text-[10px] text-text-muted font-mono whitespace-nowrap">
              ${Number(node.unit_cost).toFixed(2)}
            </span>
          )}
        </div>
      </div>

      {hasChildren && !collapsed && (
        <div className="ml-0">
          {children.map((child: NodeData, i: number) => (
            <TreeNode
              key={child.id || i}
              node={child}
              depth={depth + 1}
              searchQuery={searchQuery}
              onSelect={onSelect}
              selectedId={selectedId}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status?: string }) {
  const colors: Record<string, string> = {
    APPROVED: "bg-green-500/10 text-green-500 ring-green-500/20",
    PENDING: "bg-yellow-500/10 text-yellow-500 ring-yellow-500/20",
    REJECTED: "bg-red-500/10 text-red-500 ring-red-500/20",
  };
  const cls = status ? colors[status] || "bg-surface text-text-muted ring-border" : "bg-surface text-text-muted ring-border";
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-1 text-[10px] font-bold ring-1 ring-inset ${cls}`}>
      {status || "DRAFT"}
    </span>
  );
}
