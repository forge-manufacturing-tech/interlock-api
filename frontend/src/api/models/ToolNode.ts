/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Represents a tool or machine instance.
 * Must reference a PartNode that defines the physical equipment.
 *
 * ``cost_rate`` and ``rate_unit`` describe operating cost (e.g. $50/hour).
 * ``setup_time_minutes`` is the fixed time to set up the machine before
 * each use — this is a separate cost bucket from run time.
 */
export type ToolNode = {
    id?: string;
    name?: (string | null);
    description?: (string | null);
    owner_id?: (string | null);
    is_public?: boolean;
    project_label?: (string | null);
    linked_part_id: string;
    cost_rate?: number;
    rate_unit?: string;
    setup_time_minutes?: number;
};

