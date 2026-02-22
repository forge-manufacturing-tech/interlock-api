/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { OpType } from './OpType';
/**
 * A manufacturing procedure.
 *
 * STANDARD: consumes Parts + Labor + Tools → produces one Part.
 * PURCHASE: consumes Currency → produces one Part.
 *
 * Fields for work instructions & quoting:
 * - ``instructions``:  Step-by-step work instruction text.
 * - ``setup_time_minutes``:  Fixed setup time (independent of quantity).
 * - ``estimated_duration_minutes``:  Run time per unit produced.
 * - ``yield_rate``:  Fraction of good output (0.95 = 5% scrap).
 * To produce N good units you need N / yield_rate of input.
 * - ``cost_estimate``:  Optional override / estimate for the total op cost.
 * - ``properties``:  Freeform key-value bag for any extra parameters
 * (temperatures, tolerances, pressures, etc.).
 */
export type OperationNode = {
    id?: string;
    name?: (string | null);
    description?: (string | null);
    owner_id?: (string | null);
    is_public?: boolean;
    project_label?: (string | null);
    op_type?: OpType;
    instructions?: (string | null);
    setup_time_minutes?: number;
    estimated_duration_minutes?: number;
    yield_rate?: number;
    cost_estimate?: number;
    properties?: Record<string, any>;
};

