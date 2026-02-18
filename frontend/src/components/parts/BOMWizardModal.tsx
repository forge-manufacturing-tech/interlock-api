import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ManufacturingService } from "../../api";
import { X, Download, Calculator, Loader2, Package } from "lucide-react";

interface BOMWizardModalProps {
    partId: string;
    partName: string;
    onClose: () => void;
}

interface BOMItem {
    part_id: string;
    name: string;
    quantity: number;
    unit: string;
    unit_cost: number;
    total_cost: number;
}

export default function BOMWizardModal({ partId, partName, onClose }: BOMWizardModalProps) {
    const [quantity, setQuantity] = useState(1);
    const [step, setStep] = useState<1 | 2>(1);

    const { data: bomData, isLoading, error } = useQuery({
        queryKey: ["part", partId, "bom", quantity],
        queryFn: () => ManufacturingService.getPartBomEndpointPartsPartIdBomGet(partId, quantity),
        enabled: step === 2,
    });

    const handleExportCSV = () => {
        if (!bomData) return;

        const headers = ["Part Name", "Part ID", "Quantity", "Unit", "Unit Cost", "Total Cost"];
        const rows = (bomData as BOMItem[]).map(item => [
            item.name,
            item.part_id,
            item.quantity.toFixed(4),
            item.unit,
            item.unit_cost.toFixed(2),
            item.total_cost.toFixed(2)
        ]);

        const csvContent = [
            headers.join(","),
            ...rows.map(row => row.join(","))
        ].join("\n");

        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", `${partName.replace(/\s+/g, "_")}_BOM_${quantity}units.csv`);
        link.style.visibility = "hidden";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-4xl bg-surface border border-border rounded-xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
                <div className="flex items-center justify-between p-4 border-b border-border bg-surface-light/50">
                    <div className="flex items-center gap-2">
                        <div className="p-2 bg-primary/10 rounded-lg">
                            <Package className="text-primary" size={20} />
                        </div>
                        <h2 className="text-xl font-bold text-text-primary font-mono tracking-tight">
                            BOM Export Wizard
                        </h2>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-surface-hover rounded-full text-text-muted hover:text-text-primary transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-8">
                    {step === 1 ? (
                        <div className="max-w-md mx-auto space-y-8 py-10">
                            <div className="text-center space-y-2">
                                <h3 className="text-lg font-bold text-text-primary">Configure Production Quantity</h3>
                                <p className="text-sm text-text-secondary">Specify how many units of <span className="text-primary font-semibold">{partName}</span> you plan to produce.</p>
                            </div>

                            <div className="space-y-4">
                                <label className="block text-xs font-bold text-text-muted uppercase tracking-wider">
                                    Target Quantity
                                </label>
                                <div className="relative">
                                    <input
                                        type="number"
                                        min="0.001"
                                        step="any"
                                        value={quantity}
                                        onChange={(e) => setQuantity(parseFloat(e.target.value))}
                                        className="w-full rounded-lg border border-border bg-surface px-4 py-4 text-2xl font-bold text-text-primary focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                                    />
                                    <div className="absolute right-4 top-1/2 -translate-y-1/2 text-text-muted font-mono">
                                        UNITS
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={() => setStep(2)}
                                className="w-full py-4 bg-primary text-white font-bold rounded-lg hover:bg-primary/90 shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-2"
                            >
                                <Calculator size={20} />
                                CALCULATE REQUIREMENTS
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-bold text-text-primary">Bill of Materials</h3>
                                    <p className="text-sm text-text-secondary">Required items for {quantity} units of {partName}</p>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setStep(1)}
                                        className="px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary border border-border rounded-lg hover:bg-surface-light transition-colors"
                                    >
                                        Change Quantity
                                    </button>
                                    <button
                                        onClick={handleExportCSV}
                                        disabled={!bomData}
                                        className="px-4 py-2 bg-emerald-600 text-white text-sm font-bold rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-all flex items-center gap-2 shadow-lg shadow-emerald-500/20"
                                    >
                                        <Download size={16} />
                                        EXPORT CSV
                                    </button>
                                </div>
                            </div>

                            <div className="border border-border rounded-xl overflow-hidden bg-surface-light/30">
                                {isLoading ? (
                                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                                        <Loader2 className="animate-spin text-primary" size={32} />
                                        <p className="text-sm text-text-muted font-mono animate-pulse">TRAVERSING MANUFACTURING GRAPH...</p>
                                    </div>
                                ) : error ? (
                                    <div className="p-8 text-center text-destructive">
                                        Failed to calculate BOM. Please check tree validity.
                                    </div>
                                ) : (
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-left text-sm">
                                            <thead className="bg-surface-light border-b border-border">
                                                <tr>
                                                    <th className="px-6 py-4 font-bold text-text-muted uppercase tracking-wider text-[10px]">Purchased Item</th>
                                                    <th className="px-6 py-4 font-bold text-text-muted uppercase tracking-wider text-[10px]">Total Qty</th>
                                                    <th className="px-6 py-4 font-bold text-text-muted uppercase tracking-wider text-[10px]">Unit Cost</th>
                                                    <th className="px-6 py-4 font-bold text-text-muted uppercase tracking-wider text-[10px] text-right">Ext. Cost</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-border">
                                                {(bomData as BOMItem[]).map((item) => (
                                                    <tr key={item.part_id} className="hover:bg-surface-hover/50 transition-colors">
                                                        <td className="px-6 py-4">
                                                            <div className="font-bold text-text-primary">{item.name}</div>
                                                            <div className="text-[10px] font-mono text-text-muted">{item.part_id}</div>
                                                        </td>
                                                        <td className="px-6 py-4 font-mono">
                                                            {item.quantity.toLocaleString(undefined, { maximumFractionDigits: 4 })}
                                                            <span className="ml-1 text-[10px] text-text-muted uppercase">{item.unit}</span>
                                                        </td>
                                                        <td className="px-6 py-4 font-mono text-text-secondary">
                                                            ${item.unit_cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                                        </td>
                                                        <td className="px-6 py-4 text-right font-mono font-bold text-text-primary">
                                                            ${item.total_cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                                        </td>
                                                    </tr>
                                                ))}
                                                {(!bomData || (bomData as BOMItem[]).length === 0) && (
                                                    <tr>
                                                        <td colSpan={4} className="px-6 py-12 text-center text-text-muted italic">
                                                            No purchased items found in the assembly tree.
                                                        </td>
                                                    </tr>
                                                )}
                                            </tbody>
                                            {bomData && (bomData as BOMItem[]).length > 0 && (
                                                <tfoot className="bg-surface-light/50 font-bold border-t border-border">
                                                    <tr>
                                                        <td colSpan={3} className="px-6 py-4 text-right text-text-muted uppercase tracking-wider text-[10px]">Total Material Cost</td>
                                                        <td className="px-6 py-4 text-right text-emerald-500 text-lg">
                                                            ${(bomData as BOMItem[]).reduce((sum, item) => sum + item.total_cost, 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                                        </td>
                                                    </tr>
                                                </tfoot>
                                            )}
                                        </table>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
