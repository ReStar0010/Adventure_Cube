/**
 * API Client for Adventure Cube Backend
 * Handles all HTTP requests to the Django backend
 */

import { API_CONFIG, getBaseUrl } from './api.config';
import type {
    BackendStory,
    StoryParagraph,
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
                // Read response as text first (can only read once)
                const responseText = await response.text();
                let errorData: ApiError;
                
                // Try to parse as JSON
                try {
                    errorData = JSON.parse(responseText);
                } catch {
                    // If not JSON, use text as error message
                    errorData = {
                        error: responseText || `HTTP ${response.status}: ${response.statusText}`,
                        details: responseText
                    };
                }
                
                // Create a more detailed error message
                const errorMessage = errorData.error || errorData.details || `Request failed with status ${response.status}`;
                const error = new Error(errorMessage);
                // Attach response data for better error handling
                (error as any).response = { data: errorData, status: response.status };
                throw error;
            }

            // Handle empty responses (e.g., 204 No Content for DELETE)
            if (response.status === 204) {
                return undefined as T;
            }

            // Get response text first to check if it's empty
            const text = await response.text();
            
            // If empty, return undefined (for DELETE requests)
            if (!text || text.trim() === '') {
                return undefined as T;
            }

            // Try to parse as JSON
            try {
                return JSON.parse(text) as T;
            } catch (parseError) {
                // If parsing fails and it's a DELETE request, that's okay
                if (options.method === 'DELETE') {
                    return undefined as T;
                }
                throw new Error(`Failed to parse response as JSON: ${parseError}`);
            }
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
     * Two-stage story generation methods
     */

    async generateIntro(request: StoryGenerateRequest): Promise<BackendStory> {
        return this.fetch<BackendStory>(API_CONFIG.ENDPOINTS.GENERATE_INTRO, {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async generateRemaining(storyId: string): Promise<BackendStory> {
        const endpoint = API_CONFIG.ENDPOINTS.GENERATE_REMAINING.replace('{id}', storyId);
        return this.fetch<BackendStory>(endpoint, {
            method: 'POST',
        });
    }

    async getStoryStatus(storyId: string): Promise<BackendStory> {
        const endpoint = API_CONFIG.ENDPOINTS.GET_STORY_STATUS.replace('{id}', storyId);
        return this.fetch<BackendStory>(endpoint);
    }

    async getParagraph(storyId: string, paragraphIndex: number): Promise<StoryParagraph> {
        const endpoint = API_CONFIG.ENDPOINTS.GET_PARAGRAPH
            .replace('{id}', storyId)
            .replace('{index}', paragraphIndex.toString());
        return this.fetch<StoryParagraph>(endpoint);
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
