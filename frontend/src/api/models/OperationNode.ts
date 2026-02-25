/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LaborNode } from './LaborNode';
import type { ToolNode } from './ToolNode';
/**
 * A manufacturing procedure.
 */
export type OperationNode = {
    id?: string;
    name?: (string | null);
    description?: (string | null);
    instructions?: (string | null);
    setup_time_minutes?: number;
    estimated_duration_minutes?: number;
    yield_rate?: number;
    labor_node?: (LaborNode | null);
    tool_node?: (ToolNode | null);
    part_nodes?: (any[] | null);
};

