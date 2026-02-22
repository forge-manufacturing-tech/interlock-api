/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Reference to a file stored in blob storage.
 * Associated with either a Part or an Operation.
 */
export type FileAttachment = {
    id?: string;
    name: string;
    storage_path: string;
    content_type?: (string | null);
    size?: (number | null);
    created_at?: string;
    owner_id?: (string | null);
    node_id: string;
};

