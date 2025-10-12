/**
 * API Configuration for Adventure Cube Backend
 */

// Change this to your backend URL
// For local development:
// - Android Emulator: use 10.0.2.2:8000
// - iOS Simulator: use localhost:8000
// - Physical Device: use your computer's IP address (e.g., 192.168.1.100:8000)
export const API_CONFIG = {
    // Development URLs
    BASE_URL: __DEV__
        ? 'http://10.0.2.2:8000/api'  // Android Emulator default
        : 'https://your-production-api.com/api',

    // Alternative URLs for different platforms
    IOS_BASE_URL: 'http://localhost:8000/api',
    ANDROID_BASE_URL: 'http://10.0.2.2:8000/api',

    // Timeout settings
    TIMEOUT: 30000, // 30 seconds

    // Endpoints
    ENDPOINTS: {
        // Story endpoints
        STORIES: '/stories/',
        GENERATE_STORY: '/stories/generate/',

        // TTS endpoint
        GENERATE_AUDIO: '/tts/generate/',

        // Assets endpoints
        IMAGES: '/images/',
        THEMES: '/themes/',
    }
};

/**
 * Get the appropriate base URL based on platform
 */
export const getBaseUrl = (): string => {
    if (__DEV__) {
        // You can detect platform here if needed
        // For now, return the default BASE_URL
        return API_CONFIG.BASE_URL;
    }
    return API_CONFIG.BASE_URL;
};
