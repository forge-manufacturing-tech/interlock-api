/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type AssembleRequest = {
    name: string;
    input_part_ids: Array<string>;
    description?: (string | null);
    instructions?: (string | null);
    yield_rate?: number;
    setup_time_minutes?: number;
    estimated_duration_minutes?: number;
    labor_id?: (string | null);
    tool_id?: (string | null);
};

