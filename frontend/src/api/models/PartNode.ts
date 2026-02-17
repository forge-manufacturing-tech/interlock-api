/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
import type { NodeStatus } from './NodeStatus';
/**
 * A physical thing: raw material, sub-assembly, or finished product.
 * Each part is created by exactly one operation (purchase or assembly).
 *
 * ``unit_of_measure`` defines what "1 unit" of this part means — e.g.
 * "each", "kg", "meter", "liter".  This is critical for correct
 * quantity calculations in BOMs and quotes.
 */
export type PartNode = {
    id?: string;
    name?: (string | null);
    description?: (string | null);
    status?: NodeStatus;
    unit_of_measure?: string;
};

