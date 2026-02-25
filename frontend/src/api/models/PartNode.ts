/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { OperationNode } from './OperationNode';
import type { PurchaseNode } from './PurchaseNode';
/**
 * A physical thing: raw material, sub-assembly, or finished product.
 * Each part is created by EXACTLY one operation (PurchaseNode or OperationNode).
 */
export type PartNode = {
    id?: string;
    name?: (string | null);
    description?: (string | null);
    unit_of_measure?: string;
    child_node?: (OperationNode | PurchaseNode | null);
};

