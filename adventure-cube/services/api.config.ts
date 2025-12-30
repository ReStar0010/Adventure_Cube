/**
 * API Configuration for Adventure Cube Backend
 */

// Change this to your backend URL
// For local development:
// - Android Emulator: use 10.0.2.2:8000
// - iOS Simulator: use localhost:8000
// - Physical Device: use your computer's IP address (e.g., 192.168.1.100:8000)
const SERVER_URL = __DEV__
    ? 'http://localhost:8000'  // Development server - YOUR IP ADDRESS
    : 'https://your-production-api.com';  // Production URL

export const API_CONFIG = {
    // Server base URL (without /api)
    SERVER_URL: SERVER_URL,
    
    // API base URL
    BASE_URL: `${SERVER_URL}/api`,

    // Timeout settings
    TIMEOUT: 30000, // 30 seconds

    // Endpoints
    ENDPOINTS: {
        // Story endpoints
        STORIES: '/stories/',
        GENERATE_STORY: '/stories/generate/',
        GENERATE_INTRO: '/stories/generate_intro/',
        GENERATE_REMAINING: '/stories/{id}/generate_remaining/',
        GET_STORY_STATUS: '/stories/{id}/get_status/',
        GET_PARAGRAPH: '/stories/{id}/paragraphs/{index}/',

        // TTS endpoint
        GENERATE_AUDIO: '/tts/generate/',

        // Assets endpoints
        IMAGES: '/images/',
        THEMES: '/themes/',

        // Auth endpoints
        AUTH_REGISTER: '/auth/register/',
        AUTH_LOGIN: '/auth/login/',
        AUTH_LOGOUT: '/auth/logout/',
    }
};

/**
 * Get the appropriate base URL based on platform
 */
export const getBaseUrl = (): string => {
    return API_CONFIG.BASE_URL;
};

/**
 * Get the full URL for a media file (e.g., TTS audio)
 * Handles both relative and absolute URLs
 */
export const getMediaUrl = (relativeUrl: string | undefined): string | undefined => {
    if (!relativeUrl) return undefined;
    
    // If already an absolute URL, return as-is
    if (relativeUrl.startsWith('http://') || relativeUrl.startsWith('https://')) {
        return relativeUrl;
    }
    
    // Prepend server URL to relative path
    return `${API_CONFIG.SERVER_URL}${relativeUrl.startsWith('/') ? '' : '/'}${relativeUrl}`;
};