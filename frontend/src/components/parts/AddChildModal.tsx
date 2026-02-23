import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ManufacturingService,
  DefaultService,
  type PartNode,
  type QuantityInput,
} from "../../api";
import type { NodeData } from "../../types/parts";
import {
  X,
  Search,
  Plus,
  Hammer,
  Link as LinkIcon,
  Check,
  Loader2,
  Coins,
} from "lucide-react";

interface AddChildModalProps {
  isOpen: boolean;
  onClose: () => void;
  parentNode: NodeData;
  onSuccess?: () => void;
}

export default function AddChildModal({
  isOpen,
  onClose,
  parentNode,
  onSuccess,
}: AddChildModalProps) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"link" | "new">("link");
  const [newPartType, setNewPartType] = useState<"purchase" | "assemble">(
    "purchase",
  );

  // State for Linking
  const [selectedPartId, setSelectedPartId] = useState<string>("");
  const [linkQty, setLinkQty] = useState<number>(1);
  const [linkUnit, setLinkUnit] = useState<string>("each");
  const [searchQuery, setSearchQuery] = useState("");

  // State for Creating
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newCost, setNewCost] = useState<number>(0);
  const [newUnit, setNewUnit] = useState("each");

  // Fetch available parts
  const { data: allParts, isLoading: isLoadingParts } = useQuery({
    queryKey: ["parts"],
    queryFn: () => DefaultService.readPartsPartsGet(1000), // Fetch enough parts
    enabled: isOpen && activeTab === "link",
  });

  const filteredParts = useMemo(() => {
    if (!allParts) return [];
    return allParts.filter((p) => {
      // Exclude self
      if (p.id === parentNode.id) return false;
      // Exclude already added parts? (Optional, maybe allowed to add multiple times)
      // Filter by search
      if (
        searchQuery &&
        (!p.name || !p.name.toLowerCase().includes(searchQuery.toLowerCase()))
      )
        return false;
      return true;
    });
  }, [allParts, parentNode.id, searchQuery]);

  // Prepare current inputs + new one
  const getCurrentInputs = () => {
    const inputs = {
      parts: [] as QuantityInput[],
      labor: [] as QuantityInput[],
      tools: [] as QuantityInput[],
      currencies: [] as QuantityInput[],
    };

    parentNode.children?.forEach((child) => {
      const input: QuantityInput = {
        resource_id: child.id!,
        quantity: child.quantity || 0,
        unit: child.unit || "each",
      };

      if (child.type === "part" || !child.type) inputs.parts.push(input);
      else if (child.type === "labor") inputs.labor.push(input);
      else if (child.type === "tool") inputs.tools.push(input);
      else if (child.type === "currency") inputs.currencies.push(input);
    });

    return inputs;
  };

  const updateInputsMutation = useMutation({
    mutationFn: async (newPartInput: QuantityInput) => {
      const current = getCurrentInputs();

      // Check if we are adding to an existing part input?
      // For simplicity, we just push a new entry.
      // If the part is already there, it might show up twice or backend might merge.
      // Ideally we should check if resource_id exists and sum quantity, but separate entries are fine for BOM.
      current.parts.push(newPartInput);

      return ManufacturingService.updateOperationInputsEndpointOperationsOpIdInputsPut(
        parentNode.id!,
        {
          input_parts: current.parts,
          input_labor: current.labor,
          input_tools: current.tools,
          input_currencies: current.currencies,
        },
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tree"] });
      queryClient.invalidateQueries({ queryKey: ["parts"] });
      if (onSuccess) onSuccess();
      onClose();
      // Reset states
      setSelectedPartId("");
      setNewName("");
      setNewDesc("");
      setNewCost(0);
    },
  });

  const createPartMutation = useMutation({
    mutationFn: async () => {
      let newPart: PartNode;
      if (newPartType === "purchase") {
        newPart =
          await ManufacturingService.purchaseMaterialEndpointPartsPurchasePost({
            name: newName,
            description: newDesc,
            cost: newCost,
            unit_of_measure: newUnit,
            currency: "USD",
          });
      } else {
        newPart =
          await ManufacturingService.assemblePartEndpointPartsAssemblePost({
            name: newName,
            description: newDesc,
            input_part_ids: [],
            quantities: [],
          });
      }
      return newPart;
    },
    onSuccess: (newPart) => {
      updateInputsMutation.mutate({
        resource_id: newPart.id!,
        quantity: 1,
        unit: newPart.unit_of_measure || "each",
      });
    },
  });

  const handleLink = () => {
    if (!selectedPartId) return;
    updateInputsMutation.mutate({
      resource_id: selectedPartId,
      quantity: linkQty,
      unit: linkUnit,
    });
  };

  const handleCreate = () => {
    if (!newName) return;
    createPartMutation.mutate();
  };

  const handleSelectPart = (part: PartNode) => {
    setSelectedPartId(part.id!);
    setLinkUnit(part.unit_of_measure || "each");
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg overflow-hidden rounded-xl bg-surface border border-border shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4 bg-surface-light">
          <div>
            <h2 className="text-lg font-bold text-text-primary">
              Add Component
            </h2>
            <p className="text-xs text-text-muted">
              Adding input to operation of{" "}
              <span className="font-mono text-primary">{parentNode.name}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-surface-hover text-text-secondary hover:text-text-primary transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab("link")}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === "link"
                ? "bg-surface text-primary border-b-2 border-primary"
                : "bg-surface-light text-text-muted hover:text-text-primary"
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <LinkIcon size={16} />
              Link Existing
            </div>
          </button>
          <button
            onClick={() => setActiveTab("new")}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === "new"
                ? "bg-surface text-primary border-b-2 border-primary"
                : "bg-surface-light text-text-muted hover:text-text-primary"
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <Plus size={16} />
              Create New
            </div>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === "link" ? (
            <div className="space-y-6">
              {/* Search */}
              <div className="relative">
                <Search
                  className="absolute left-3 top-2.5 text-text-muted"
                  size={16}
                />
                <input
                  type="text"
                  placeholder="Search parts..."
                  className="w-full rounded-md border border-border bg-surface-light pl-9 pr-4 py-2 text-sm text-text-primary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              {/* List */}
              <div className="h-48 overflow-y-auto rounded-md border border-border bg-surface-light scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
                {isLoadingParts ? (
                  <div className="flex h-full items-center justify-center gap-2 text-sm text-text-muted">
                    <Loader2 className="animate-spin" size={16} />
                    Loading parts...
                  </div>
                ) : filteredParts.length === 0 ? (
                  <div className="flex h-full items-center justify-center text-sm text-text-muted">
                    No parts found.
                  </div>
                ) : (
                  <div className="divide-y divide-border">
                    {filteredParts.map((part) => (
                      <button
                        key={part.id}
                        onClick={() => handleSelectPart(part)}
                        className={`flex w-full items-center justify-between px-4 py-2 text-left transition-colors hover:bg-surface-hover ${
                          selectedPartId === part.id ? "bg-primary/10" : ""
                        }`}
                      >
                        <div>
                          <p className="text-sm font-medium text-text-primary">
                            {part.name}
                          </p>
                          <p className="text-[10px] text-text-muted truncate max-w-[200px]">
                            {part.description || "No description"}
                          </p>
                        </div>
                        {selectedPartId === part.id && (
                          <Check size={16} className="text-primary" />
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Quantity */}
              {selectedPartId && (
                <div className="grid grid-cols-2 gap-4 animate-in slide-in-from-top-2">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-text-secondary">
                      Quantity
                    </label>
                    <input
                      type="number"
                      min="0.000001"
                      step="any"
                      className="w-full rounded-md border border-border bg-surface-light px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                      value={linkQty}
                      onChange={(e) => setLinkQty(parseFloat(e.target.value))}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-text-secondary">
                      Unit
                    </label>
                    <input
                      type="text"
                      className="w-full rounded-md border border-border bg-surface-light px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                      value={linkUnit}
                      onChange={(e) => setLinkUnit(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              {/* Type Selection */}
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => setNewPartType("purchase")}
                  className={`flex flex-col items-center gap-2 rounded-lg border p-4 transition-all ${
                    newPartType === "purchase"
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-surface-light text-text-muted hover:border-text-secondary"
                  }`}
                >
                  <Coins size={24} />
                  <span className="text-xs font-bold uppercase tracking-wider">
                    Purchase
                  </span>
                </button>
                <button
                  onClick={() => setNewPartType("assemble")}
                  className={`flex flex-col items-center gap-2 rounded-lg border p-4 transition-all ${
                    newPartType === "assemble"
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-surface-light text-text-muted hover:border-text-secondary"
                  }`}
                >
                  <Hammer size={24} />
                  <span className="text-xs font-bold uppercase tracking-wider">
                    Assemble
                  </span>
                </button>
              </div>

              {/* Form */}
              <div className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-text-secondary">
                    Name
                  </label>
                  <input
                    type="text"
                    className="w-full rounded-md border border-border bg-surface-light px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                    placeholder="e.g. Steel Plate, Widget Assembly"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-text-secondary">
                    Description
                  </label>
                  <textarea
                    className="w-full rounded-md border border-border bg-surface-light px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none resize-none h-20"
                    placeholder="Details about this part..."
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {newPartType === "purchase" && (
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-text-secondary">
                        Unit Cost ($)
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        className="w-full rounded-md border border-border bg-surface-light px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                        value={newCost}
                        onChange={(e) => setNewCost(parseFloat(e.target.value))}
                      />
                    </div>
                  )}
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-text-secondary">
                      Unit of Measure
                    </label>
                    <input
                      type="text"
                      className="w-full rounded-md border border-border bg-surface-light px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                      value={newUnit}
                      onChange={(e) => setNewUnit(e.target.value)}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border px-6 py-4 bg-surface-light flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
          >
            Cancel
          </button>

          {activeTab === "link" ? (
            <button
              onClick={handleLink}
              disabled={!selectedPartId || updateInputsMutation.isPending}
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {updateInputsMutation.isPending && (
                <Loader2 className="animate-spin" size={16} />
              )}
              Add Link
            </button>
          ) : (
            <button
              onClick={handleCreate}
              disabled={
                !newName ||
                createPartMutation.isPending ||
                updateInputsMutation.isPending
              }
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {(createPartMutation.isPending ||
                updateInputsMutation.isPending) && (
                <Loader2 className="animate-spin" size={16} />
              )}
              Create & Add
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
