/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_upload_node_file_nodes__node_id__files_post } from '../models/Body_upload_node_file_nodes__node_id__files_post';
import type { FileAttachment } from '../models/FileAttachment';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class StorageService {
    /**
     * Upload Node File
     * Upload a file associated with a node.
     * @param nodeId
     * @param formData
     * @returns FileAttachment Successful Response
     * @throws ApiError
     */
    public static uploadNodeFileNodesNodeIdFilesPost(
        nodeId: string,
        formData: Body_upload_node_file_nodes__node_id__files_post,
    ): CancelablePromise<FileAttachment> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/nodes/{node_id}/files',
            path: {
                'node_id': nodeId,
            },
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Node Files
     * List all files associated with a node.
     * @param nodeId
     * @returns FileAttachment Successful Response
     * @throws ApiError
     */
    public static listNodeFilesNodesNodeIdFilesGet(
        nodeId: string,
    ): CancelablePromise<Array<FileAttachment>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/nodes/{node_id}/files',
            path: {
                'node_id': nodeId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get File Download Url
     * Get a signed URL to download a file.
     * @param fileId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getFileDownloadUrlFilesFileIdDownloadGet(
        fileId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/files/{file_id}/download',
            path: {
                'file_id': fileId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete File Endpoint
     * Delete a file from storage and database.
     * @param fileId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteFileEndpointFilesFileIdDelete(
        fileId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/files/{file_id}',
            path: {
                'file_id': fileId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
