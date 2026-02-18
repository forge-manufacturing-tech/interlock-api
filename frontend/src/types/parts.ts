import type { PartNode } from "../api";

export interface NodeData extends PartNode {
    children?: NodeData[];
    type?: string;
    status?: string;
    quantity?: number;
    unit?: string;
    unit_cost?: number;
    [key: string]: unknown;
}
