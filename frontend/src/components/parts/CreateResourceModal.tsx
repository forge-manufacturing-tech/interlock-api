import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ManufacturingService, DefaultService } from "../../api";
import type { CreateLaborRequest, CreateToolRequest } from "../../api";
import { X, Hammer, Wrench, DollarSign } from "lucide-react";

interface CreateResourceModalProps {
    onClose: () => void;
}

export default function CreateResourceModal({ onClose }: CreateResourceModalProps) {
    const [activeTab, setActiveTab] = useState<"labor" | "tool">("labor");

    // Labor State
    const [laborName, setLaborName] = useState("");
    const [laborRate, setLaborRate] = useState<number>(0);
    const [laborDesc, setLaborDesc] = useState("");

    // Tool State
    const [toolName, setToolName] = useState("");
    const [toolRate, setToolRate] = useState<number>(0);
    const [toolLinkedPart, setToolLinkedPart] = useState("");
    const [toolDesc, setToolDesc] = useState("");

    const { data: availableParts } = useQuery({
        queryKey: ["parts-all"],
        queryFn: () => DefaultService.readTreesTreesGet(),
    });

    const createLaborMutation = useMutation({
        mutationFn: (data: CreateLaborRequest) => ManufacturingService.createLaborEndpointLaborPost(data),
        onSuccess: () => {
            onClose();
        },
    });

    const createToolMutation = useMutation({
        mutationFn: (data: CreateToolRequest) => ManufacturingService.createToolEndpointToolsPost(data),
        onSuccess: () => {
            onClose();
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (activeTab === "labor") {
            createLaborMutation.mutate({
                name: laborName,
                hourly_rate: Number(laborRate),
                description: laborDesc
            });
        } else {
            createToolMutation.mutate({
                name: toolName,
                cost_rate: Number(toolRate),
                linked_part_id: toolLinkedPart,
                description: toolDesc
            });
        }
    };

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-md bg-surface border border-border rounded-xl shadow-2xl overflow-hidden flex flex-col">
                <div className="flex items-center justify-between p-4 border-b border-border bg-surface-light/50">
                    <div className="flex items-center gap-2">
                        <Hammer className="text-primary" size={20} />
                        <h2 className="text-lg font-bold text-text-primary">Create Resource</h2>
                    </div>
                    <button onClick={onClose} className="p-1 hover:bg-surface-hover rounded-full text-text-muted hover:text-text-primary transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="flex border-b border-border bg-surface-light/30">
                    <button
                        onClick={() => setActiveTab("labor")}
                        className={`flex-1 py-3 text-sm font-bold transition-all flex items-center justify-center gap-2 border-b-2 ${activeTab === "labor"
                                ? "text-primary border-primary bg-surface"
                                : "text-text-secondary border-transparent hover:text-text-primary"
                            }`}
                    >
                        <Hammer size={16} />
                        LABOR
                    </button>
                    <button
                        onClick={() => setActiveTab("tool")}
                        className={`flex-1 py-3 text-sm font-bold transition-all flex items-center justify-center gap-2 border-b-2 ${activeTab === "tool"
                                ? "text-primary border-primary bg-surface"
                                : "text-text-secondary border-transparent hover:text-text-primary"
                            }`}
                    >
                        <Wrench size={16} />
                        TOOL
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    {activeTab === "labor" ? (
                        <>
                            <div>
                                <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">Labor Type Name</label>
                                <input
                                    type="text"
                                    required
                                    value={laborName}
                                    onChange={(e) => setLaborName(e.target.value)}
                                    className="w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text-primary focus:border-primary outline-none transition-all"
                                    placeholder="e.g. Senior Assembler"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">Hourly Rate ($/hr)</label>
                                <div className="relative">
                                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={14} />
                                    <input
                                        type="number"
                                        required
                                        min="0"
                                        step="0.01"
                                        value={laborRate}
                                        onChange={(e) => setLaborRate(parseFloat(e.target.value))}
                                        className="w-full rounded-lg border border-border bg-surface pl-9 pr-4 py-2.5 text-sm text-text-primary focus:border-primary outline-none transition-all"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">Description</label>
                                <textarea
                                    value={laborDesc}
                                    onChange={(e) => setLaborDesc(e.target.value)}
                                    className="w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text-primary focus:border-primary outline-none transition-all"
                                    rows={2}
                                />
                            </div>
                        </>
                    ) : (
                        <>
                            <div>
                                <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">Tool/Machine Name</label>
                                <input
                                    type="text"
                                    required
                                    value={toolName}
                                    onChange={(e) => setToolName(e.target.value)}
                                    className="w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text-primary focus:border-primary outline-none transition-all"
                                    placeholder="e.g. 5-Axis CNC Mill"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">Cost Rate ($/unit)</label>
                                <div className="relative">
                                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={14} />
                                    <input
                                        type="number"
                                        required
                                        min="0"
                                        step="0.01"
                                        value={toolRate}
                                        onChange={(e) => setToolRate(parseFloat(e.target.value))}
                                        className="w-full rounded-lg border border-border bg-surface pl-9 pr-4 py-2.5 text-sm text-text-primary focus:border-primary outline-none transition-all"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">Linked Asset (Part)</label>
                                <select
                                    required
                                    value={toolLinkedPart}
                                    onChange={(e) => setToolLinkedPart(e.target.value)}
                                    className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-text-primary focus:border-primary outline-none transition-all"
                                >
                                    <option value="">Select Asset...</option>
                                    {availableParts?.map(p => (
                                        <option key={p.id} value={p.id!}>{p.name} ({p.id})</option>
                                    ))}
                                </select>
                                <p className="mt-1 text-[10px] text-text-muted">Tools must be linked to a physical part for asset tracking.</p>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-text-muted uppercase tracking-wider mb-2">Description</label>
                                <textarea
                                    value={toolDesc}
                                    onChange={(e) => setToolDesc(e.target.value)}
                                    className="w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text-primary focus:border-primary outline-none transition-all"
                                    rows={2}
                                />
                            </div>
                        </>
                    )}

                    <div className="pt-4 flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-sm font-bold text-text-secondary hover:text-text-primary transition-colors"
                        >
                            CANCEL
                        </button>
                        <button
                            type="submit"
                            disabled={createLaborMutation.isPending || createToolMutation.isPending}
                            className="px-6 py-2 text-sm font-bold text-white bg-primary hover:bg-primary/90 rounded-lg shadow-lg shadow-primary/20 transition-all active:scale-95 disabled:opacity-50"
                        >
                            CREATE {activeTab === "labor" ? "LABOR" : "TOOL"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
