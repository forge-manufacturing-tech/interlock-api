import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ManufacturingService } from "../../api";
import type { PartNode } from "../../api";
import {
  X,
  Save,
  Trash2,
  ArrowUpRight,
  ArrowDownRight,
  Wrench,
  DollarSign,
  Clock,
  Cuboid,
  Hammer,
  Package,
} from "lucide-react";
import BOMWizardModal from "./BOMWizardModal";

interface NodeData extends PartNode {
  children?: NodeData[];
  type?: string;
  quantity?: number;
  unit?: string;
  unit_cost?: number;
  [key: string]: unknown;
}

interface PartDetailPanelProps {
  node: NodeData; // Accepted full node data from tree
  onClose: () => void;
  onSelect: (node: NodeData) => void;
}

export default function PartDetailPanel({
  node,
  onClose,
  onSelect,
}: PartDetailPanelProps) {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [showBOMWizard, setShowBOMWizard] = useState(false);

  // Part basic info editing state
  const [editName, setEditName] = useState(node.name || "");
  const [editDesc, setEditDesc] = useState(node.description || "");
  const [editUnit, setEditUnit] = useState(node.unit_of_measure || "each");

  // Operation editing state
  const operation = (node.children || []).find((c) => c.type === "operation");
  const [opYield, setOpYield] = useState(Number(operation?.yield_rate ?? 1.0));
  const [opSetup, setOpSetup] = useState(
    Number(operation?.setup_time_minutes ?? 0),
  );
  const [opDuration, setOpDuration] = useState(
    Number(operation?.estimated_duration_minutes ?? 0),
  );
  const [opInstructions, setOpInstructions] = useState(
    (operation?.instructions as string) || "",
  );

  // Input quantities state
  const initialInputs = operation?.children || node.children || [];
  const [inputQtys, setInputQtys] = useState<Record<string, number>>(
    Object.fromEntries(
      initialInputs.map((c) => [c.id!, Number(c.quantity || 0)]),
    ),
  );
  const [inputUnits, setInputUnits] = useState<Record<string, string>>(
    Object.fromEntries(
      initialInputs.map((c) => [c.id!, (c.unit as string) || ""]),
    ),
  );

  const { data: ancestors } = useQuery({
    queryKey: ["part", node.id, "ancestors"],
    queryFn: () =>
      ManufacturingService.getPartAncestorsEndpointPartsPartIdAncestorsGet(
        node.id!,
      ),
    enabled: !!node.id,
  });

  const { data: costs } = useQuery({
    queryKey: ["part", node.id, "costs"],
    queryFn: () =>
      ManufacturingService.getPartCostsEndpointPartsPartIdCostsGet(node.id!),
    enabled: !!node.id,
  });

  const { data: timeline } = useQuery({
    queryKey: ["part", node.id, "timeline"],
    queryFn: () =>
      ManufacturingService.getPartTimelineEndpointPartsPartIdTimelineGet(
        node.id!,
      ),
    enabled: !!node.id,
  });

  const modifyMutation = useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      ManufacturingService.modifyPartEndpointPartsPartIdPatch(node.id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trees"] });
      queryClient.invalidateQueries({ queryKey: ["tree"] });
      setIsEditing(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () =>
      ManufacturingService.removePartEndpointPartsPartIdDelete(node.id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trees"] });
      onClose();
    },
  });

  const opMutation = useMutation({
    mutationFn: async () => {
      if (!operation?.id) return;

      // 1. Update operation basic details
      await ManufacturingService.patchOperationEndpointOperationsOpIdPatch(
        operation.id as string,
        {
          name: operation?.name,
          yield_rate: opYield,
          setup_time_minutes: opSetup,
          estimated_duration_minutes: opDuration,
          instructions: opInstructions,
        },
      );

      // 2. Update operation inputs
      const opChildren = operation.children || [];
      await ManufacturingService.updateOperationInputsEndpointOperationsOpIdInputsPut(
        operation.id as string,
        {
          input_parts: opChildren
            .filter((c) => c.type === "part" || !c.type)
            .map((c) => ({
              resource_id: c.id!,
              quantity: inputQtys[c.id!] ?? 0,
              unit: inputUnits[c.id!] ?? "each",
            })),
          input_labor: opChildren
            .filter((c) => c.type === "labor")
            .map((c) => ({
              resource_id: c.id!,
              quantity: inputQtys[c.id!] ?? 0,
              unit: inputUnits[c.id!] ?? "hours",
            })),
          input_tools: opChildren
            .filter((c) => c.type === "tool")
            .map((c) => ({
              resource_id: c.id!,
              quantity: inputQtys[c.id!] ?? 0,
              unit: inputUnits[c.id!] ?? "hours",
            })),
          input_currencies: opChildren
            .filter((c) => c.type === "currency")
            .map((c) => ({
              resource_id: c.id!,
              quantity: inputQtys[c.id!] ?? 0,
              unit: inputUnits[c.id!] ?? "units",
            })),
        },
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trees"] });
      queryClient.invalidateQueries({ queryKey: ["tree"] });
      setIsEditing(false);
    },
  });

  const handleSave = async () => {
    if (!node.id) return;

    // Save part basic info
    modifyMutation.mutate({
      name: editName,
      description: editDesc,
    });

    // Save operation and inputs if it exists
    if (operation?.id) {
      opMutation.mutate();
    }
  };

  const inputs = operation?.children || node.children || [];

  // Group inputs by type for better display
  const childParts = inputs.filter((c) => c.type === "part" || !c.type);
  const childLabor = inputs.filter((c) => c.type === "labor");
  const childTools = inputs.filter((c) => c.type === "tool");
  const childCurrencies = inputs.filter((c) => c.type === "currency");

  return (
    <div className="h-full flex flex-col bg-surface border-l border-border shadow-xl">
      <div className="flex items-center justify-between p-4 border-b border-border bg-surface-light/50">
        <div className="flex items-center gap-2">
          <Cuboid className="text-secondary" size={20} />
          <h2 className="text-lg font-bold font-mono text-text-primary truncate">
            Part Details
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowBOMWizard(true)}
            className="flex items-center gap-1.5 px-2 py-1 rounded bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 text-xs font-bold transition-colors border border-emerald-500/20"
            title="Export Bill of Materials"
          >
            <Package size={14} />
            BOM
          </button>
          <button
            onClick={onClose}
            className="p-1 hover:bg-surface-hover rounded text-text-muted hover:text-text-primary transition-colors"
          >
            <X size={20} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        {/* Basic Information */}
        <div className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1 flex-1">
              {isEditing ? (
                <input
                  className="w-full text-xl font-bold bg-surface border border-border rounded px-2 py-1 focus:border-primary outline-none"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  placeholder="Part Name"
                />
              ) : (
                <h1 className="text-xl font-bold text-text-primary break-words">
                  {node.name || "Unnamed Part"}
                </h1>
              )}
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center rounded-md bg-blue-400/10 px-2 py-1 text-[10px] font-mono font-medium text-blue-400 ring-1 ring-inset ring-blue-400/20">
                  {node.id}
                </span>
                {isEditing ? (
                  <input
                    className="text-[10px] bg-surface border border-border rounded px-1 text-text-muted uppercase font-bold tracking-wider w-20"
                    value={editUnit}
                    onChange={(e) => setEditUnit(e.target.value)}
                    placeholder="Unit (e.g. EACH)"
                  />
                ) : (
                  node.unit_of_measure && (
                    <span className="text-[10px] text-text-muted uppercase font-bold tracking-wider">
                      {node.unit_of_measure}
                    </span>
                  )
                )}
              </div>
            </div>

            <div className="flex gap-1">
              <button
                onClick={() => setIsEditing(!isEditing)}
                className={`p-2 rounded transition-colors ${isEditing ? "bg-primary text-white" : "bg-surface-hover text-text-secondary hover:text-primary"}`}
                title={isEditing ? "Cancel" : "Edit Name/Desc"}
              >
                <Wrench size={16} />
              </button>
              <button
                onClick={() => {
                  if (
                    window.confirm(
                      "Are you sure you want to delete this part? This cannot be undone.",
                    )
                  ) {
                    deleteMutation.mutate();
                  }
                }}
                className="p-2 rounded bg-surface-hover text-text-secondary hover:text-destructive hover:bg-destructive/10 transition-colors"
                title="Delete Part"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>

          {isEditing ? (
            <div className="space-y-3">
              <textarea
                className="w-full rounded border border-border bg-surface px-3 py-2 text-sm text-text-primary focus:border-primary outline-none"
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                placeholder="Description"
                rows={4}
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setIsEditing(false)}
                  className="px-3 py-1.5 text-sm font-medium text-text-secondary hover:text-primary transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={modifyMutation.isPending}
                  className="flex items-center gap-2 rounded-md bg-primary px-3 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50"
                >
                  <Save size={14} />
                  Save Changes
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-text-secondary leading-relaxed">
              {(node.description as string) || "No description provided."}
            </p>
          )}
        </div>

        <div className="border-t border-border" />

        {/* Navigation / Connections */}
        <div className="grid grid-cols-2 gap-6">
          {/* Upstream Ancestors */}
          <div className="space-y-3">
            <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-text-muted">
              <ArrowUpRight size={14} />
              Upstream
            </h4>
            {!ancestors || ancestors.length === 0 ? (
              <p className="text-xs text-text-muted italic">No ancestors.</p>
            ) : (
              <div className="space-y-1">
                {ancestors.map((a) => (
                  <button
                    key={a.id}
                    onClick={() => onSelect(a as NodeData)}
                    className="w-full text-left p-2 rounded bg-surface-light border border-border hover:border-primary hover:bg-primary/5 transition-colors group"
                  >
                    <span className="text-[10px] font-mono text-text-muted block truncate group-hover:text-primary/70">
                      {a.id}
                    </span>
                    <span className="text-xs font-medium text-text-primary block truncate group-hover:text-primary">
                      {a.name}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Downstream Inputs */}
          <div className="space-y-3">
            <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-text-muted">
              <ArrowDownRight size={14} />
              Inputs
            </h4>
            {childParts.length === 0 ? (
              <p className="text-xs text-text-muted italic">No input parts.</p>
            ) : (
              <div className="space-y-1">
                {childParts.map((c) => (
                  <div
                    key={c.id}
                    className="w-full text-left p-2 rounded bg-surface-light border border-border"
                  >
                    <button
                      onClick={() => onSelect(c)}
                      className="w-full text-left group"
                    >
                      <span className="text-[10px] font-mono text-text-muted block truncate group-hover:text-primary/70">
                        {c.id}
                      </span>
                      <span className="text-xs font-medium text-text-primary block truncate group-hover:text-primary">
                        {c.name}
                      </span>
                    </button>
                    <div className="mt-2 flex items-center gap-2">
                      {isEditing ? (
                        <>
                          <input
                            type="number"
                            className="w-16 text-[10px] bg-surface border border-border rounded px-1 outline-none focus:border-primary"
                            value={inputQtys[c.id!] ?? 0}
                            onChange={(e) =>
                              setInputQtys({
                                ...inputQtys,
                                [c.id!]: parseFloat(e.target.value),
                              })
                            }
                          />
                          <input
                            type="text"
                            className="w-12 text-[10px] bg-surface border border-border rounded px-1 outline-none focus:border-primary"
                            value={inputUnits[c.id!] ?? "each"}
                            onChange={(e) =>
                              setInputUnits({
                                ...inputUnits,
                                [c.id!]: e.target.value,
                              })
                            }
                          />
                        </>
                      ) : (
                        <span className="text-[10px] text-text-muted">
                          {c.quantity} {c.unit || "each"}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Resources Section */}
        {(childLabor.length > 0 ||
          childTools.length > 0 ||
          childCurrencies.length > 0) && (
          <div className="space-y-4 pt-4 border-t border-border">
            <h4 className="text-xs font-bold uppercase tracking-wider text-text-muted">
              Resources & Costs
            </h4>

            <div className="space-y-4">
              {childLabor.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-text-secondary">
                    <Hammer size={12} className="text-amber-500" /> Labor
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {childLabor.map((l) => (
                      <div
                        key={l.id}
                        className="p-2 rounded bg-amber-500/5 border border-amber-500/10"
                      >
                        <p className="text-xs font-medium text-text-primary truncate">
                          {l.name}
                        </p>
                        {isEditing ? (
                          <div className="mt-1 flex gap-1">
                            <input
                              type="number"
                              className="w-full text-[10px] bg-surface border border-border rounded px-1"
                              value={inputQtys[l.id!] ?? 0}
                              onChange={(e) =>
                                setInputQtys({
                                  ...inputQtys,
                                  [l.id!]: parseFloat(e.target.value),
                                })
                              }
                            />
                            <input
                              type="text"
                              className="w-full text-[10px] bg-surface border border-border rounded px-1"
                              value={inputUnits[l.id!] ?? "hours"}
                              onChange={(e) =>
                                setInputUnits({
                                  ...inputUnits,
                                  [l.id!]: e.target.value,
                                })
                              }
                            />
                          </div>
                        ) : (
                          <p className="text-[10px] text-text-muted">
                            {l.quantity} {l.unit || "hours"}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {childTools.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-text-secondary">
                    <Wrench size={12} className="text-purple-500" /> Tools
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {childTools.map((t) => (
                      <div
                        key={t.id}
                        className="p-2 rounded bg-purple-500/5 border border-purple-500/10"
                      >
                        <p className="text-xs font-medium text-text-primary truncate">
                          {t.name}
                        </p>
                        {isEditing ? (
                          <div className="mt-1 flex gap-1">
                            <input
                              type="number"
                              className="w-full text-[10px] bg-surface border border-border rounded px-1"
                              value={inputQtys[t.id!] ?? 0}
                              onChange={(e) =>
                                setInputQtys({
                                  ...inputQtys,
                                  [t.id!]: parseFloat(e.target.value),
                                })
                              }
                            />
                            <input
                              type="text"
                              className="w-full text-[10px] bg-surface border border-border rounded px-1"
                              value={inputUnits[t.id!] ?? "hours"}
                              onChange={(e) =>
                                setInputUnits({
                                  ...inputUnits,
                                  [t.id!]: e.target.value,
                                })
                              }
                            />
                          </div>
                        ) : (
                          <p className="text-[10px] text-text-muted">
                            {t.quantity} {t.unit || "hours"}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {childCurrencies.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-text-secondary">
                    <DollarSign size={12} className="text-emerald-500" />{" "}
                    Purchase Cost
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {childCurrencies.map((c) => (
                      <div
                        key={c.id}
                        className="p-2 rounded bg-emerald-500/5 border border-emerald-500/10"
                      >
                        <p className="text-xs font-medium text-text-primary truncate">
                          {c.name}
                        </p>
                        {isEditing ? (
                          <div className="mt-1 flex gap-1">
                            <input
                              type="number"
                              className="w-full text-[10px] bg-surface border border-border rounded px-1"
                              value={inputQtys[c.id!] ?? 0}
                              onChange={(e) =>
                                setInputQtys({
                                  ...inputQtys,
                                  [c.id!]: parseFloat(e.target.value),
                                })
                              }
                            />
                            <span className="text-[10px] text-text-muted">
                              {(c.iso_code as string) || "USD"}
                            </span>
                          </div>
                        ) : (
                          <p className="text-[10px] text-text-muted">
                            ${c.quantity as number}{" "}
                            {(c.iso_code as string) || "USD"}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Financials & Logistics */}
        <div className="space-y-4 pt-4 border-t border-border">
          <h4 className="text-xs font-bold uppercase tracking-wider text-text-muted">
            Operation Details & Analysis
          </h4>

          {operation && (
            <div className="grid grid-cols-2 gap-4 bg-surface-light p-3 rounded-md border border-border">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-text-muted uppercase">
                  Yield Rate
                </label>
                {isEditing ? (
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    className="w-full text-xs bg-surface border border-border rounded px-1"
                    value={opYield}
                    onChange={(e) => setOpYield(parseFloat(e.target.value))}
                  />
                ) : (
                  <p className="text-xs font-mono text-text-primary">
                    {(opYield * 100).toFixed(1)}%
                  </p>
                )}
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-text-muted uppercase">
                  Setup Time
                </label>
                {isEditing ? (
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      className="w-full text-xs bg-surface border border-border rounded px-1"
                      value={opSetup}
                      onChange={(e) => setOpSetup(parseFloat(e.target.value))}
                    />
                    <span className="text-[10px] text-text-muted">min</span>
                  </div>
                ) : (
                  <p className="text-xs font-mono text-text-primary">
                    {opSetup} min
                  </p>
                )}
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-text-muted uppercase">
                  Run Time / Unit
                </label>
                {isEditing ? (
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      className="w-full text-xs bg-surface border border-border rounded px-1"
                      value={opDuration}
                      onChange={(e) =>
                        setOpDuration(parseFloat(e.target.value))
                      }
                    />
                    <span className="text-[10px] text-text-muted">min</span>
                  </div>
                ) : (
                  <p className="text-xs font-mono text-text-primary">
                    {opDuration} min
                  </p>
                )}
              </div>
              {isEditing && (
                <div className="col-span-2 space-y-1">
                  <label className="text-[10px] font-bold text-text-muted uppercase">
                    Operation Instructions
                  </label>
                  <textarea
                    className="w-full text-xs bg-surface border border-border rounded px-1"
                    value={opInstructions}
                    onChange={(e) => setOpInstructions(e.target.value)}
                    rows={2}
                  />
                </div>
              )}
            </div>
          )}

          <div className="space-y-4">
            {costs && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                  <DollarSign size={16} className="text-emerald-500" />
                  Cost Breakdown
                </div>
                <div className="bg-surface-light p-3 rounded-md border border-border overflow-hidden">
                  <pre className="text-[10px] text-text-secondary font-mono overflow-auto max-h-40 scrollbar-thin">
                    {JSON.stringify(costs, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {timeline && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                  <Clock size={16} className="text-blue-500" />
                  Timeline
                </div>
                <div className="bg-surface-light p-3 rounded-md border border-border">
                  <pre className="text-[10px] text-text-secondary font-mono overflow-auto max-h-40 scrollbar-thin">
                    {JSON.stringify(timeline, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      {showBOMWizard && node.id && (
        <BOMWizardModal
          partId={node.id}
          partName={node.name || "Unnamed Part"}
          onClose={() => setShowBOMWizard(false)}
        />
      )}
    </div>
  );
}
