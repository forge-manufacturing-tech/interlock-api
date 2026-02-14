/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApiKeyCreate } from '../models/ApiKeyCreate';
import type { ApiKeyRead } from '../models/ApiKeyRead';
import type { TokenResponse } from '../models/TokenResponse';
import type { UserCreate } from '../models/UserCreate';
import type { UserLogin } from '../models/UserLogin';
import type { UserRead } from '../models/UserRead';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AuthenticationService {
    /**
     * Signup
     * @param requestBody
     * @returns TokenResponse Successful Response
     * @throws ApiError
     */
    public static signupAuthSignupPost(
        requestBody: UserCreate,
    ): CancelablePromise<TokenResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/signup',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Login
     * @param requestBody
     * @returns TokenResponse Successful Response
     * @throws ApiError
     */
    public static loginAuthLoginPost(
        requestBody: UserLogin,
    ): CancelablePromise<TokenResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/login',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Me
     * @returns UserRead Successful Response
     * @throws ApiError
     */
    public static getMeAuthMeGet(): CancelablePromise<UserRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/auth/me',
        });
    }
    /**
     * List Api Keys
     * @returns ApiKeyRead Successful Response
     * @throws ApiError
     */
    public static listApiKeysAuthApiKeysGet(): CancelablePromise<Array<ApiKeyRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/auth/api-keys',
        });
    }
    /**
     * Create Api Key
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createApiKeyAuthApiKeysPost(
        requestBody: ApiKeyCreate,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/api-keys',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Revoke Api Key
     * @param keyId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static revokeApiKeyAuthApiKeysKeyIdDelete(
        keyId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/auth/api-keys/{key_id}',
            path: {
                'key_id': keyId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
