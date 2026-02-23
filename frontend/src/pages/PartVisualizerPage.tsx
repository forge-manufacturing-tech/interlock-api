import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { DefaultService, ManufacturingService, OpType } from "../api";
import { ArrowLeft, Box } from "lucide-react";
import PartFlowVisualizer from "../components/parts/PartFlowVisualizer";
import PartDetailPanel from "../components/parts/PartDetailPanel";
import CreatePartModal from "../components/parts/CreatePartModal";
import type { NodeData } from "../types/parts";

export default function PartVisualizerPage() {
  const queryClient = useQueryClient();
  const { partId } = useParams<{ partId: string }>();
  const navigate = useNavigate();
  const [selectedNode, setSelectedNode] = useState<NodeData | null>(null);
  const [showCreatePart, setShowCreatePart] = useState(false);
  const [initialInputs, setInitialInputs] = useState<{ id: string; qty: number }[]>([]);
  const [parentForNewInput, setParentForNewInput] = useState<NodeData | null>(null);

  const { data: treeData, isLoading, error } = useQuery({
    queryKey: ["tree", partId],
    queryFn: () => DefaultService.readTreeStructureTreesPartIdGet(partId!),
    enabled: !!partId,
  });

  const linkInputMutation = useMutation({
    mutationFn: async ({ parentNode, childPart }: { parentNode: NodeData; childPart: NodeData }) => {
        let operationId: string | undefined;
        let currentOpType: OpType | undefined;
        let currentInputs: NodeData[] = [];

        if (parentNode.type === 'operation') {
            operationId = parentNode.id;
            currentOpType = parentNode.op_type as OpType;
            currentInputs = parentNode.children || [];
        } else if (parentNode.type === 'part') {
            const opNode = (parentNode.children || []).find(c => c.type === 'operation');
            operationId = opNode?.id;
            currentOpType = opNode?.op_type as OpType;
            currentInputs = opNode?.children || [];
        }

        if (!operationId) throw new Error("Target operation not found");

        const inputParts = currentInputs.filter(c => c.type === 'part' || !c.type).map(c => ({
            resource_id: c.id!,
            quantity: Number(c.quantity || 1),
            unit: (c.unit as string) || 'each'
        }));

        inputParts.push({
            resource_id: childPart.id,
            quantity: 1,
            unit: childPart.unit_of_measure || 'each'
        });

        if (currentOpType === OpType.PURCHASE) {
            await ManufacturingService.patchOperationEndpointOperationsOpIdPatch(operationId, {
                op_type: OpType.STANDARD
            });
        }

        await ManufacturingService.updateOperationInputsEndpointOperationsOpIdInputsPut(operationId, {
            input_parts: inputParts
        });
    },
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["tree"] });
        queryClient.invalidateQueries({ queryKey: ["trees"] });
    }
  });

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-surface">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (error || !treeData) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center gap-4 bg-surface text-text-primary">
        <Box size={48} className="text-text-muted" />
        <h2 className="text-xl font-bold">Failed to load part tree</h2>
        <button
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90"
        >
          <ArrowLeft size={16} />
          Back to Parts Explorer
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full overflow-hidden bg-surface relative">
      {/* Visualizer Area */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* Header Overlay */}
        <div className="absolute top-6 left-6 z-10 flex items-center gap-4 pointer-events-none">
          <button
            onClick={() => navigate("/dashboard")}
            className="pointer-events-auto p-2 rounded-full bg-surface-light border border-border text-text-muted hover:text-text-primary hover:border-primary transition-all shadow-lg"
          >
            <ArrowLeft size={20} />
          </button>
          <div className="bg-surface-light/80 backdrop-blur-md border border-border rounded-lg p-3 shadow-lg">
            <h1 className="font-mono text-lg font-bold uppercase tracking-wider text-text-primary">
              {treeData.name || "Part Tree"}
            </h1>
            <p className="text-xs text-text-secondary">
              ID: {treeData.id}
            </p>
          </div>
        </div>

        <PartFlowVisualizer
          treeData={treeData as NodeData}
          onSelectNode={(node) => setSelectedNode(node)}
          onAddInput={(node) => {
              setSelectedNode(node);
              setParentForNewInput(node);
              setInitialInputs([]);
              setShowCreatePart(true);
          }}
          selectedId={selectedNode?.id}
        />
      </div>

      {/* Detail Panel */}
      {selectedNode && (
        <div className="w-[450px] flex-shrink-0 h-full border-l border-border transition-all animate-in slide-in-from-right duration-300 z-20">
          <PartDetailPanel
            key={selectedNode.id}
            node={selectedNode}
            onSelect={(node) => {
                setSelectedNode(node);
            }}
            onClose={() => setSelectedNode(null)}
          />
        </div>
      )}

      {/* Modals */}
      {showCreatePart && (
        <CreatePartModal
          onClose={() => {
            setShowCreatePart(false);
            setInitialInputs([]);
            setParentForNewInput(null);
          }}
          initialInputs={initialInputs}
          onSuccess={(newPart) => {
              if (parentForNewInput) {
                  linkInputMutation.mutate({ parentNode: parentForNewInput, childPart: newPart });
              }
          }}
        />
      )}
    </div>
  );
}
