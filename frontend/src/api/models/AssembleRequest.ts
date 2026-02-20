/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
export type AssembleRequest = {
    name: string;
    input_part_ids: Array<string>;
    quantities?: (Array<number> | null);
    description?: (string | null);
    instructions?: (string | null);
    yield_rate?: number;
    setup_time_minutes?: number;
    estimated_duration_minutes?: number;
    labor_ids?: (Array<string> | null);
    labor_quantities?: (Array<number> | null);
    labor_units?: (Array<string> | null);
    tool_ids?: (Array<string> | null);
    tool_quantities?: (Array<number> | null);
    tool_units?: (Array<string> | null);
};

