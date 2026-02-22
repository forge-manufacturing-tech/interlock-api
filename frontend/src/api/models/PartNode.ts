/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
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
    owner_id?: (string | null);
    is_public?: boolean;
    project_label?: (string | null);
    unit_of_measure?: string;
    created_by_id?: (string | null);
    created_by_type?: (string | null);
};

