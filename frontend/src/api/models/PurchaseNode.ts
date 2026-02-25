/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CurrencyAmount } from './CurrencyAmount';
/**
 * A purchasing operation for raw materials.
 */
export type PurchaseNode = {
    id?: string;
    name?: (string | null);
    description?: (string | null);
    cost: CurrencyAmount;
};

