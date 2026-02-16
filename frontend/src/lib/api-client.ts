import { redirect } from 'next/navigation';

type FetchOptions = RequestInit & {
    headers?: Record<string, string>;
};

export class ApiError extends Error {
    status: number;
    data: any;

    constructor(message: string, status: number, data?: any) {
        super(message);
        this.status = status;
        this.data = data;
        this.name = 'ApiError';
    }
}

// Event to trigger logout across the app
export const AUTH_EVENT_LOGOUT = 'auth:logout';

export const apiClient = {
    async fetch(url: string, options: FetchOptions = {}) {
        // Ensure headers exist
        const headers = options.headers || {};

        // Get token from localStorage if executing on client
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('vsa_token');
            if (token && !headers['Authorization']) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }

        const defaultHeaders: Record<string, string> = {};

        // Only set Content-Type to application/json if body is not FormData
        if (!(options.body instanceof FormData)) {
            defaultHeaders['Content-Type'] = 'application/json';
        }

        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...headers,
            },
        };

        try {
            const response = await fetch(url, config);

            // Handle 401 Unauthorized globally
            if (response.status === 401) {
                if (typeof window !== 'undefined') {
                    // Dispatch logout event
                    window.dispatchEvent(new Event(AUTH_EVENT_LOGOUT));
                }
                throw new ApiError('Unauthorized', 401);
            }

            return response;
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            // Re-throw other errors
            throw new Error(error instanceof Error ? error.message : 'Network error');
        }
    },

    async get(url: string, options: FetchOptions = {}) {
        return this.fetch(url, { ...options, method: 'GET' });
    },

    async post(url: string, body: any, options: FetchOptions = {}) {
        return this.fetch(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(body),
        });
    },

    async put(url: string, body: any, options: FetchOptions = {}) {
        return this.fetch(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(body),
        });
    },

    async delete(url: string, options: FetchOptions = {}) {
        return this.fetch(url, { ...options, method: 'DELETE' });
    }
};
