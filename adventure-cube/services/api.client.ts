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

    constructor() {
        this.baseUrl = getBaseUrl();
        this.timeout = API_CONFIG.TIMEOUT;
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
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
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
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export default ApiClient;
