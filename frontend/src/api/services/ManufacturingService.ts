/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
import type { AssembleRequest } from '../models/AssembleRequest';
import type { CreateLaborRequest } from '../models/CreateLaborRequest';
import type { CreateToolRequest } from '../models/CreateToolRequest';
import type { LaborNode } from '../models/LaborNode';
import type { ModifyPartRequest } from '../models/ModifyPartRequest';
import type { OperationNode } from '../models/OperationNode';
import type { PartNode } from '../models/PartNode';
import type { PurchaseRequest } from '../models/PurchaseRequest';
import type { ToolNode } from '../models/ToolNode';
import type { UpdateOperationInputsRequest } from '../models/UpdateOperationInputsRequest';
import type { UpdateOperationRequest } from '../models/UpdateOperationRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ManufacturingService {
    /**
     * Purchase Material Endpoint
     * Purchase a new raw material or component.
     * Creates a purchased part with an associated Purchase operation and cost.
     * @param requestBody
     * @returns PartNode Successful Response
     * @throws ApiError
     */
    public static purchaseMaterialEndpointPartsPurchasePost(
        requestBody: PurchaseRequest,
    ): CancelablePromise<PartNode> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/parts/purchase',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Assemble Part Endpoint
     * Assemble/manufacture a new part from existing input parts, with labor and tool usage.
     * @param requestBody
     * @returns PartNode Successful Response
     * @throws ApiError
     */
    public static assemblePartEndpointPartsAssemblePost(
        requestBody: AssembleRequest,
    ): CancelablePromise<PartNode> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/parts/assemble',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Modify Part Endpoint
     * Modify an existing part's name or description.
     * @param partId
     * @param requestBody
     * @returns PartNode Successful Response
     * @throws ApiError
     */
    public static modifyPartEndpointPartsPartIdPatch(
        partId: string,
        requestBody: ModifyPartRequest,
    ): CancelablePromise<PartNode> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/parts/{part_id}',
            path: {
                'part_id': partId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Remove Part Endpoint
     * Delete a part from the database.
     * @param partId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static removePartEndpointPartsPartIdDelete(
        partId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/parts/{part_id}',
            path: {
                'part_id': partId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Validate Part Endpoint
     * Validate the manufacturing tree starting from a root part.
     * @param partId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static validatePartEndpointPartsPartIdValidateGet(
        partId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/parts/{part_id}/validate',
            path: {
                'part_id': partId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Part Ancestors Endpoint
     * Get all upstream ancestor parts that feed into this part.
     * @param partId
     * @returns PartNode Successful Response
     * @throws ApiError
     */
    public static getPartAncestorsEndpointPartsPartIdAncestorsGet(
        partId: string,
    ): CancelablePromise<Array<PartNode>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/parts/{part_id}/ancestors',
            path: {
                'part_id': partId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Part Costs Endpoint
     * Get all leaf currency nodes (raw costs) upstream of a part.
     * @param partId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPartCostsEndpointPartsPartIdCostsGet(
        partId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/parts/{part_id}/costs',
            path: {
                'part_id': partId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Part Timeline Endpoint
     * Get the full manufacturing timeline for a part.
     * @param partId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPartTimelineEndpointPartsPartIdTimelineGet(
        partId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/parts/{part_id}/timeline',
            path: {
                'part_id': partId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Part Bom Endpoint
     * Get the flattened Bill of Materials for a part and quantity.
     * @param partId
     * @param quantity
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPartBomEndpointPartsPartIdBomGet(
        partId: string,
        quantity: number = 1,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/parts/{part_id}/bom',
            path: {
                'part_id': partId,
            },
            query: {
                'quantity': quantity,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Patch Operation Endpoint
     * Update operation details.
     * @param opId
     * @param requestBody
     * @returns OperationNode Successful Response
     * @throws ApiError
     */
    public static patchOperationEndpointOperationsOpIdPatch(
        opId: string,
        requestBody: UpdateOperationRequest,
    ): CancelablePromise<OperationNode> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/operations/{op_id}',
            path: {
                'op_id': opId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Operation Inputs Endpoint
     * Update operation inputs (parts, labor, tools, currencies).
     * @param opId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateOperationInputsEndpointOperationsOpIdInputsPut(
        opId: string,
        requestBody: UpdateOperationInputsRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/operations/{op_id}/inputs',
            path: {
                'op_id': opId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Labor Endpoint
     * List all labor types available in the system.
     * @returns LaborNode Successful Response
     * @throws ApiError
     */
    public static listLaborEndpointLaborGet(): CancelablePromise<Array<LaborNode>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/labor',
        });
    }
    /**
     * Create Labor Endpoint
     * Create a new type of labor.
     * @param requestBody
     * @returns LaborNode Successful Response
     * @throws ApiError
     */
    public static createLaborEndpointLaborPost(
        requestBody: CreateLaborRequest,
    ): CancelablePromise<LaborNode> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/labor',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Tools Endpoint
     * List all tools/machines available in the system.
     * @returns ToolNode Successful Response
     * @throws ApiError
     */
    public static listToolsEndpointToolsGet(): CancelablePromise<Array<ToolNode>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/tools',
        });
    }
    /**
     * Create Tool Endpoint
     * Create a new tool/machine entry.
     * @param requestBody
     * @returns ToolNode Successful Response
     * @throws ApiError
     */
    public static createToolEndpointToolsPost(
        requestBody: CreateToolRequest,
    ): CancelablePromise<ToolNode> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/tools',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
