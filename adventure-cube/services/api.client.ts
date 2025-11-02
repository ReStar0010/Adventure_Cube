/**
 * API Client for Adventure Cube Backend
 * Handles all HTTP requests to the Django backend
 */

import { API_CONFIG, getBaseUrl } from './api.config';
import type {
    BackendStory,
    StoryGenerateRequest,
    AudioFile,
    TTSGenerateRequest,
    ImagesResponse,
    ThemesResponse,
    ApiError,
} from './api.types';

class ApiClient {
    private baseUrl: string;
    private timeout: number;
    private authToken: string | null = null;

    constructor() {
        this.baseUrl = getBaseUrl();
        this.timeout = API_CONFIG.TIMEOUT;
    }

    /**
     * Set authentication token
     */
    setToken(token: string) {
        this.authToken = token;
    }

    /**
     * Clear authentication token
     */
    clearToken() {
        this.authToken = null;
    }

    /**
     * Get current token
     */
    getToken(): string | null {
        return this.authToken;
    }

    /**
     * Generic fetch wrapper with error handling
     */
    private async fetch<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json',
                ...options.headers as Record<string, string>,
            };

            // Add authorization header if token exists
            if (this.authToken) {
                headers['Authorization'] = `Token ${this.authToken}`;
            }

            const response = await fetch(url, {
                ...options,
                headers,
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData: ApiError = await response.json().catch(() => ({
                    error: `HTTP ${response.status}: ${response.statusText}`,
                }));
                throw new Error(errorData.error || `Request failed with status ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);

            if (error instanceof Error) {
                if (error.name === 'AbortError') {
                    throw new Error('Request timeout - please check your connection');
                }
                throw error;
            }

            throw new Error('An unexpected error occurred');
        }
    }

    /**
     * Story API Methods
     */

    async generateStory(request: StoryGenerateRequest): Promise<BackendStory> {
        return this.fetch<BackendStory>(API_CONFIG.ENDPOINTS.GENERATE_STORY, {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async getStories(): Promise<BackendStory[]> {
        return this.fetch<BackendStory[]>(API_CONFIG.ENDPOINTS.STORIES);
    }

    async getStory(id: string): Promise<BackendStory> {
        return this.fetch<BackendStory>(`${API_CONFIG.ENDPOINTS.STORIES}${id}/`);
    }

    async deleteStory(id: string): Promise<void> {
        await this.fetch<void>(`${API_CONFIG.ENDPOINTS.STORIES}${id}/`, {
            method: 'DELETE',
        });
    }

    /**
     * TTS API Methods
     */

    async generateAudio(request: TTSGenerateRequest): Promise<AudioFile> {
        return this.fetch<AudioFile>(API_CONFIG.ENDPOINTS.GENERATE_AUDIO, {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    /**
     * Assets API Methods
     */

    async getImages(category?: string): Promise<ImagesResponse> {
        const endpoint = category
            ? `${API_CONFIG.ENDPOINTS.IMAGES}?category=${category}`
            : API_CONFIG.ENDPOINTS.IMAGES;
        return this.fetch<ImagesResponse>(endpoint);
    }

    async getThemes(): Promise<ThemesResponse> {
        return this.fetch<ThemesResponse>(API_CONFIG.ENDPOINTS.THEMES);
    }

    /**
     * Health check
     */
    async healthCheck(): Promise<boolean> {
        try {
            await this.getThemes();
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Update base URL (useful for switching between environments)
     */
    setBaseUrl(url: string) {
        this.baseUrl = url;
    }

    /**
     * Auth API Methods
     */

    async register(username: string, password: string, email?: string): Promise<{ user: any; token: string }> {
        return this.fetch(API_CONFIG.ENDPOINTS.AUTH_REGISTER, {
            method: 'POST',
            body: JSON.stringify({
                username,
                password,
                password2: password,
                email,
            }),
        });
    }

    async login(username: string, password: string): Promise<{ user: any; token: string }> {
        return this.fetch(API_CONFIG.ENDPOINTS.AUTH_LOGIN, {
            method: 'POST',
            body: JSON.stringify({
                username,
                password,
            }),
        });
    }

    async logout(): Promise<{ message: string }> {
        return this.fetch(API_CONFIG.ENDPOINTS.AUTH_LOGOUT, {
            method: 'POST',
        });
    }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export default ApiClient;
