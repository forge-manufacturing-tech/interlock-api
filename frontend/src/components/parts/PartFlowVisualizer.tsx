import { useCallback, useMemo, useEffect } from 'react';
import {
    ReactFlow,
    Handle,
    Position,
    Background,
    Controls,
    type Edge,
    type Node,
    Panel,
    useNodesState,
    useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Box, Hammer, Coins, User, Square, Plus, type LucideIcon } from 'lucide-react';
import type { NodeData } from '../../types/parts';


const NODE_TYPE_ICONS: Record<string, LucideIcon> = {
    part: Box,
    operation: Hammer,
    currency: Coins,
    labor: User,
    tool: Square,
};

const NODE_TYPE_COLORS: Record<string, string> = {
    part: "#EC5B13", // Brand Orange
    operation: "#8B5CF6", // Purple
    currency: "#10B981", // Green
    labor: "#F59E0B", // Amber
    tool: "#EC4899", // Pink
};

// Custom Node Component
const CustomPartNode = ({ data }: { data: NodeData & { selected?: boolean, onAddChild?: (node: NodeData) => void } }) => {
    const nodeType = data.type?.toLowerCase() || 'part';
    const Icon = NODE_TYPE_ICONS[nodeType] || Box;
    const color = NODE_TYPE_COLORS[nodeType] || "#71717A";

    return (
        <div className="group relative">
            {/* Selection Ring */}
            {data.selected && (
                <div className="absolute -inset-1 rounded-xl bg-primary/20 animate-pulse" />
            )}

            <div
                className={`relative w-64 rounded-xl border-2 bg-surface p-4 transition-all duration-300 ${data.selected
                    ? 'border-primary shadow-[0_0_20px_rgba(236,91,19,0.2)]'
                    : 'border-border hover:border-text-muted'
                    }`}
            >
                <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-border !border-2 !border-surface" />

                <div
                    onClick={(e) => {
                        if (data.onAddChild) {
                            e.stopPropagation();
                            data.onAddChild(data);
                        }
                    }}
                    className="absolute -right-3 -top-3 p-1.5 rounded-full bg-primary text-white shadow-lg hover:scale-110 transition-transform cursor-pointer z-10 opacity-0 group-hover:opacity-100"
                    title="Add Child Component"
                >
                    <Plus size={16} strokeWidth={3} />
                </div>

                <div className="flex items-start gap-3">
                    <div
                        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
                        style={{ backgroundColor: `${color}20`, color: color }}
                    >
                        <Icon size={20} />
                    </div>

                    <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                            <span className="truncate font-mono text-sm font-bold text-text-primary">
                                {data.name || "Unknown Part"}
                            </span>
                        </div>

                        <div className="mt-1 flex flex-wrap gap-1.5">
                            <span
                                className="rounded px-1.5 py-0.5 text-[10px] uppercase font-bold tracking-wider"
                                style={{ backgroundColor: `${color}15`, color: color }}
                            >
                                {data.type || "Component"}
                            </span>

                            {data.quantity !== undefined && (
                                <span className="rounded bg-surface-light px-1.5 py-0.5 text-[10px] font-mono text-text-secondary">
                                    x{data.quantity} {data.unit || ""}
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                {data.unit_cost !== undefined && (
                    <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
                        <span className="text-[10px] uppercase tracking-widest text-text-muted font-semibold">Unit Cost</span>
                        <span className="font-mono text-sm font-bold text-primary">
                            ${Number(data.unit_cost).toFixed(2)}
                        </span>
                    </div>
                )}

                <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-border !border-2 !border-surface" />
            </div>
        </div>
    );
};

const nodeTypes = {
    partNode: CustomPartNode,
};

interface PartFlowVisualizerProps {
    treeData: NodeData;
    onSelectNode: (node: NodeData) => void;
    onAddChild?: (node: NodeData) => void;
    selectedId?: string;
}

export default function PartFlowVisualizer({ treeData, onSelectNode, onAddChild, selectedId }: PartFlowVisualizerProps) {
    const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
        const nodes: Node[] = [];
        const edges: Edge[] = [];

        const traverse = (node: NodeData, depth: number, x: number, parentId?: string, path: string = 'root') => {
            const id = node.id || `node-${path}`;

            // Calculate horizontal position to spread children
            // This is a very simple layout algorithm
            nodes.push({
                id,
                type: 'partNode',
                position: { x: x * 300, y: depth * 220 },
                data: {
                    ...node,
                    selected: selectedId === node.id,
                    onAddChild
                },
            });

            if (parentId) {
                edges.push({
                    id: `e-${parentId}-${id}`,
                    source: parentId,
                    target: id,
                    animated: node.type === 'operation',
                    style: { stroke: '#27272A', strokeWidth: 2 },
                });
            }

            if (node.children) {
                node.children.forEach((child, index) => {
                    // Spread children around parent's X position
                    const childX = x + (index - (node.children!.length - 1) / 2);
                    traverse(child, depth + 1, childX, id, `${path}-${index}`);
                });
            }
        };

        traverse(treeData, 0, 0);
        return { nodes, edges };
    }, [treeData, selectedId]);

    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    useEffect(() => {
        setNodes(initialNodes);
        setEdges(initialEdges);
    }, [initialNodes, initialEdges, setNodes, setEdges]);

    const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
        onSelectNode(node.data as NodeData);
    }, [onSelectNode]);

    return (
        <div className="h-full w-full bg-surface">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={onNodeClick}
                nodeTypes={nodeTypes}
                fitView
                className="bg-surface"
                minZoom={0.2}
                maxZoom={1.5}
            >
                <Background color="#27272A" gap={20} />
                <Controls showInteractive={false} className="border border-border shadow-2xl" />
                <Panel position="top-right" className="rounded-lg border border-border bg-surface-light/80 p-3 backdrop-blur-md shadow-xl">
                    <div className="flex flex-col gap-2">
                        <h3 className="text-xs font-bold uppercase tracking-widest text-text-secondary">Process View</h3>
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-1.5">
                                <div className="h-2 w-2 rounded-full" style={{ backgroundColor: NODE_TYPE_COLORS.part }} />
                                <span className="text-[10px] text-text-muted">Part</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                                <div className="h-2 w-2 rounded-full" style={{ backgroundColor: NODE_TYPE_COLORS.operation }} />
                                <span className="text-[10px] text-text-muted">Op</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                                <div className="h-2 w-2 rounded-full" style={{ backgroundColor: NODE_TYPE_COLORS.currency }} />
                                <span className="text-[10px] text-text-muted">Cost</span>
                            </div>
                        </div>
                    </div>
                </Panel>
            </ReactFlow>
        </div>
    );
}
