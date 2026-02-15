/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_chat_agent_agent_chat_post } from '../models/Body_chat_agent_agent_chat_post';
import type { Body_ingest_bom_ingest_bom_post } from '../models/Body_ingest_bom_ingest_bom_post';
import type { PartNode } from '../models/PartNode';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DefaultService {
    /**
     * Read Root
     * @returns any Successful Response
     * @throws ApiError
     */
    public static readRootGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/',
        });
    }
    /**
     * Ingest Bom
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static ingestBomIngestBomPost(
        formData: Body_ingest_bom_ingest_bom_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/ingest/bom',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Chat Agent
     * Chat with the tech transfer agent.
     * Supports optional file attachments (PDF, images).
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static chatAgentAgentChatPost(
        formData?: Body_chat_agent_agent_chat_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/agent/chat',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Export Tree As Bom
     * Export a manufacturing tree as a CSV Bill of Materials.
     * @param partId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static exportTreeAsBomTreesPartIdExportBomGet(
        partId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/trees/{part_id}/export/bom',
            path: {
                'part_id': partId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Export Tree As Work Instructions
     * Export a manufacturing tree as markdown work instructions.
     * @param partId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static exportTreeAsWorkInstructionsTreesPartIdExportWorkInstructionsGet(
        partId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/trees/{part_id}/export/work-instructions',
            path: {
                'part_id': partId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Read Parts
     * List parts in the manufacturing graph.
     * @param limit
     * @param offset
     * @returns PartNode Successful Response
     * @throws ApiError
     */
    public static readPartsPartsGet(
        limit: number = 100,
        offset?: number,
    ): CancelablePromise<Array<PartNode>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/parts',
            query: {
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Read Part
     * Get a specific part by ID.
     * @param partId
     * @returns PartNode Successful Response
     * @throws ApiError
     */
    public static readPartPartsPartIdGet(
        partId: string,
    ): CancelablePromise<PartNode> {
        return __request(OpenAPI, {
            method: 'GET',
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
     * Read Trees
     * Get all root parts (ends of trees).
     * @returns PartNode Successful Response
     * @throws ApiError
     */
    public static readTreesTreesGet(): CancelablePromise<Array<PartNode>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/trees',
        });
    }
    /**
     * Read Tree Structure
     * Get a recursive tree structure starting from part_id.
     * @param partId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static readTreeStructureTreesPartIdGet(
        partId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/trees/{part_id}',
            path: {
                'part_id': partId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Serve Spa
     * @param fullPath
     * @returns any Successful Response
     * @throws ApiError
     */
    public static serveSpaFullPathGet(
        fullPath: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/{full_path}',
            path: {
                'full_path': fullPath,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
