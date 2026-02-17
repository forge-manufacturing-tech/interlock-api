/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApiKeyCreate } from '../models/ApiKeyCreate';
import type { ApiKeyRead } from '../models/ApiKeyRead';
import type { SystemSettings } from '../models/SystemSettings';
import type { SystemSettingUpdate } from '../models/SystemSettingUpdate';
import type { TokenResponse } from '../models/TokenResponse';
import type { UserCreate } from '../models/UserCreate';
import type { UserLogin } from '../models/UserLogin';
import type { UserRead } from '../models/UserRead';
import type { UserUpdate } from '../models/UserUpdate';
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
    /**
     * List Users
     * @returns UserRead Successful Response
     * @throws ApiError
     */
    public static listUsersAuthAdminUsersGet(): CancelablePromise<Array<UserRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/auth/admin/users',
        });
    }
    /**
     * Update User
     * @param userId
     * @param requestBody
     * @returns UserRead Successful Response
     * @throws ApiError
     */
    public static updateUserAuthAdminUsersUserIdPatch(
        userId: string,
        requestBody: UserUpdate,
    ): CancelablePromise<UserRead> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/auth/admin/users/{user_id}',
            path: {
                'user_id': userId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get System Settings
     * @returns SystemSettings Successful Response
     * @throws ApiError
     */
    public static getSystemSettingsAuthSettingsGet(): CancelablePromise<SystemSettings> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/auth/settings',
        });
    }
    /**
     * Update System Setting
     * @param requestBody
     * @returns SystemSettings Successful Response
     * @throws ApiError
     */
    public static updateSystemSettingAuthAdminSettingsPatch(
        requestBody: SystemSettingUpdate,
    ): CancelablePromise<SystemSettings> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/auth/admin/settings',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
