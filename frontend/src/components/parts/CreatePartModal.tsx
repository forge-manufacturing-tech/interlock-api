import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ManufacturingService, DefaultService } from "../../api";
import type { PurchaseRequest, AssembleRequest } from "../../api";
import {
  X,
  ShoppingCart,
  Layers,
  Plus,
  Trash2,
  Hammer,
  Wrench,
} from "lucide-react";

interface CreatePartModalProps {
  onClose: () => void;
}

interface CommonNode {
  id?: string;
  name?: string | null;
}

export default function CreatePartModal({ onClose }: CreatePartModalProps) {
  const [activeTab, setActiveTab] = useState<"purchase" | "assemble">(
    "purchase",
  );
  const queryClient = useQueryClient();

  // Purchase State
  const [pName, setPName] = useState("");
  const [pCost, setPCost] = useState<number>(0);
  const [pDesc, setPDesc] = useState("");
  const [pUnit, setPUnit] = useState("each");

  // Assemble State
  const [aName, setAName] = useState("");
  const [aDesc, setADesc] = useState("");
  const [inputs, setInputs] = useState<{ id: string; qty: number }[]>([]);
  const [labors, setLabors] = useState<{ id: string; qty: number }[]>([]);
  const [tools, setTools] = useState<{ id: string; qty: number }[]>([]);

  // Fetch available parts, labor, and tools
  const { data: availableParts } = useQuery({
    queryKey: ["trees"],
    queryFn: () => DefaultService.readTreesTreesGet(),
  });

  const { data: availableLabor } = useQuery({
    queryKey: ["labor"],
    queryFn: () => ManufacturingService.listLaborEndpointLaborGet(),
  });

  const { data: availableTools } = useQuery({
    queryKey: ["tools"],
    queryFn: () => ManufacturingService.listToolsEndpointToolsGet(),
  });

  const purchaseMutation = useMutation({
    mutationFn: (data: PurchaseRequest) =>
      ManufacturingService.purchaseMaterialEndpointPartsPurchasePost(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trees"] });
      onClose();
    },
  });

  const assembleMutation = useMutation({
    mutationFn: (data: AssembleRequest) =>
      ManufacturingService.assemblePartEndpointPartsAssemblePost(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trees"] });
      onClose();
    },
  });

  const handlePurchase = (e: React.FormEvent) => {
    e.preventDefault();
    purchaseMutation.mutate({
      name: pName,
      cost: Number(pCost),
      description: pDesc,
      unit_of_measure: pUnit,
      currency: "USD",
    });
  };

  const handleAssemble = (e: React.FormEvent) => {
    e.preventDefault();
    assembleMutation.mutate({
      name: aName,
      description: aDesc,
      input_part_ids: inputs.filter((i) => i.id).map((i) => i.id),
      quantities: inputs.filter((i) => i.id).map((i) => i.qty),
      labor_ids: labors.filter((l) => l.id).map((l) => l.id),
      labor_quantities: labors.filter((l) => l.id).map((l) => l.qty),
      tool_ids: tools.filter((t) => t.id).map((t) => t.id),
      tool_quantities: tools.filter((t) => t.id).map((t) => t.qty),
    });
  };

  const addRow = (type: "inputs" | "labors" | "tools") => {
    if (type === "inputs") setInputs([...inputs, { id: "", qty: 1 }]);
    if (type === "labors") setLabors([...labors, { id: "", qty: 1 }]);
    if (type === "tools") setTools([...tools, { id: "", qty: 1 }]);
  };

  const updateRow = (
    type: "inputs" | "labors" | "tools",
    index: number,
    field: "id" | "qty",
    value: string | number,
  ) => {
    const setter =
      type === "inputs" ? setInputs : type === "labors" ? setLabors : setTools;
    const current =
      type === "inputs" ? inputs : type === "labors" ? labors : tools;

    const next = [...current];
    const item = { ...next[index] };
    if (field === "id") item.id = value as string;
    else item.qty = Number(value);
    next[index] = item;
    setter(next);
  };

  const removeRow = (type: "inputs" | "labors" | "tools", index: number) => {
    const setter =
      type === "inputs" ? setInputs : type === "labors" ? setLabors : setTools;
    const current =
      type === "inputs" ? inputs : type === "labors" ? labors : tools;
    setter(current.filter((_, i) => i !== index));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-3xl bg-surface border border-border rounded-xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-border bg-surface-light/50">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Plus className="text-primary" size={20} />
            </div>
            <h2 className="text-xl font-bold text-text-primary font-mono tracking-tight">
              Create New Manufacturing Item
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-surface-hover rounded-full text-text-muted hover:text-text-primary transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex border-b border-border bg-surface-light/30">
          <button
            onClick={() => setActiveTab("purchase")}
            className={`flex-1 py-4 text-sm font-bold transition-all flex items-center justify-center gap-2 border-b-2 ${
              activeTab === "purchase"
                ? "text-primary border-primary bg-surface"
                : "text-text-secondary border-transparent hover:text-text-primary hover:bg-surface/50"
            }`}
          >
            <ShoppingCart size={18} />
            PURCHASED MATERIAL
          </button>
          <button
            onClick={() => setActiveTab("assemble")}
            className={`flex-1 py-4 text-sm font-bold transition-all flex items-center justify-center gap-2 border-b-2 ${
              activeTab === "assemble"
                ? "text-primary border-primary bg-surface"
                : "text-text-secondary border-transparent hover:text-text-primary hover:bg-surface/50"
            }`}
          >
            <Layers size={18} />
            ASSEMBLED PRODUCT
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-8 scrollbar-thin">
          {activeTab === "purchase" ? (
            <form
              onSubmit={handlePurchase}
              className="space-y-6 max-w-xl mx-auto"
            >
              <div className="grid grid-cols-2 gap-6">
                <div className="col-span-2">
                  <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">
                    Item Name
                  </label>
                  <input
                    required
                    value={pName}
                    onChange={(e) => setPName(e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface px-4 py-3 text-text-primary focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                    placeholder="e.g. 6061 Aluminum Plate"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">
                    Unit Cost ($)
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted">
                      $
                    </span>
                    <input
                      type="number"
                      required
                      min="0"
                      step="0.01"
                      value={pCost}
                      onChange={(e) => setPCost(parseFloat(e.target.value))}
                      className="w-full rounded-lg border border-border bg-surface pl-8 pr-4 py-3 text-text-primary focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">
                    Unit of Measure
                  </label>
                  <select
                    value={pUnit}
                    onChange={(e) => setPUnit(e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface px-4 py-3 text-text-primary focus:border-primary outline-none transition-all appearance-none"
                  >
                    <option value="each">Each</option>
                    <option value="kg">Kilogram (kg)</option>
                    <option value="m">Meter (m)</option>
                    <option value="l">Liter (l)</option>
                    <option value="sq_ft">Square Foot (sq ft)</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">
                  Description
                </label>
                <textarea
                  value={pDesc}
                  onChange={(e) => setPDesc(e.target.value)}
                  className="w-full rounded-lg border border-border bg-surface px-4 py-3 text-text-primary focus:border-primary outline-none transition-all"
                  rows={3}
                  placeholder="Specify grade, dimensions, or vendor details..."
                />
              </div>

              <div className="pt-6 flex justify-end">
                <button
                  type="submit"
                  disabled={purchaseMutation.isPending}
                  className="px-8 py-3 bg-primary text-white font-bold rounded-lg hover:bg-primary/90 disabled:opacity-50 shadow-lg shadow-primary/20 transition-all active:scale-95"
                >
                  CREATE MATERIAL
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleAssemble} className="space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="md:col-span-2">
                  <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">
                    Assembly Name
                  </label>
                  <input
                    required
                    value={aName}
                    onChange={(e) => setAName(e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface px-4 py-3 text-text-primary focus:border-primary outline-none transition-all"
                    placeholder="e.g. Main Frame Sub-Assembly"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">
                    Description / Instructions
                  </label>
                  <textarea
                    value={aDesc}
                    onChange={(e) => setADesc(e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface px-4 py-3 text-text-primary focus:border-primary outline-none transition-all"
                    rows={2}
                    placeholder="Assembly steps or quality requirements..."
                  />
                </div>
              </div>

              <div className="space-y-6">
                {/* Sections for Inputs, Labor, Tools */}
                {[
                  {
                    title: "Input Parts",
                    type: "inputs",
                    icon: Layers,
                    data: availableParts as CommonNode[] | undefined,
                    color: "text-primary",
                  },
                  {
                    title: "Labor Requirements",
                    type: "labors",
                    icon: Hammer,
                    data: availableLabor as CommonNode[] | undefined,
                    color: "text-amber-500",
                  },
                  {
                    title: "Tooling & Machines",
                    type: "tools",
                    icon: availableTools as CommonNode[] | undefined,
                    color: "text-purple-500",
                  },
                ].map((section) => {
                  const Icon =
                    section.type === "inputs"
                      ? Layers
                      : section.type === "labors"
                        ? Hammer
                        : Wrench;
                  const items =
                    section.type === "inputs"
                      ? inputs
                      : section.type === "labors"
                        ? labors
                        : tools;

                  return (
                    <div key={section.type} className="space-y-3">
                      <div className="flex items-center justify-between border-b border-border pb-2">
                        <div className="flex items-center gap-2">
                          <Icon className={section.color} size={16} />
                          <h3 className="text-xs font-bold text-text-primary uppercase tracking-widest">
                            {section.title}
                          </h3>
                        </div>
                        <button
                          type="button"
                          onClick={() =>
                            addRow(
                              section.type as "inputs" | "labors" | "tools",
                            )
                          }
                          className="text-xs font-bold flex items-center gap-1 text-primary hover:bg-primary/5 px-2 py-1 rounded transition-colors"
                        >
                          <Plus size={14} /> Add Line
                        </button>
                      </div>

                      <div className="space-y-2">
                        {items.length === 0 && (
                          <p className="text-[11px] text-text-muted italic py-2">
                            Click "Add Line" to include{" "}
                            {section.title.toLowerCase()}.
                          </p>
                        )}
                        {items.map((item, idx) => (
                          <div
                            key={idx}
                            className="flex gap-3 items-center animate-in fade-in slide-in-from-left duration-200"
                          >
                            <select
                              className="flex-1 rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text-primary focus:border-primary outline-none"
                              value={item.id}
                              onChange={(e) =>
                                updateRow(
                                  section.type as "inputs" | "labors" | "tools",
                                  idx,
                                  "id",
                                  e.target.value,
                                )
                              }
                              required
                            >
                              <option value="">Select...</option>
                              {section.data?.map((p) => (
                                <option key={p.id} value={p.id!}>
                                  {p.name} ({p.id})
                                </option>
                              ))}
                            </select>
                            <div className="flex items-center gap-2">
                              <input
                                type="number"
                                min="0.001"
                                step="any"
                                className="w-24 rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text-primary focus:border-primary outline-none"
                                value={item.qty}
                                onChange={(e) =>
                                  updateRow(
                                    section.type as
                                      | "inputs"
                                      | "labors"
                                      | "tools",
                                    idx,
                                    "qty",
                                    e.target.value,
                                  )
                                }
                                required
                              />
                              <span className="text-[10px] text-text-muted uppercase font-bold w-12">
                                Qty
                              </span>
                            </div>
                            <button
                              type="button"
                              onClick={() =>
                                removeRow(
                                  section.type as "inputs" | "labors" | "tools",
                                  idx,
                                )
                              }
                              className="p-2 text-text-muted hover:text-destructive hover:bg-destructive/5 rounded-lg transition-colors"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="pt-8 border-t border-border flex justify-end">
                <button
                  type="submit"
                  disabled={assembleMutation.isPending}
                  className="px-10 py-4 bg-primary text-white font-bold rounded-xl hover:bg-primary/90 disabled:opacity-50 shadow-xl shadow-primary/30 transition-all active:scale-95"
                >
                  CREATE ASSEMBLY
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
