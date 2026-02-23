/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { OpType } from './OpType';
export type UpdateOperationRequest = {
    name?: (string | null);
    description?: (string | null);
    instructions?: (string | null);
    op_type?: (OpType | null);
    yield_rate?: (number | null);
    setup_time_minutes?: (number | null);
    estimated_duration_minutes?: (number | null);
};

