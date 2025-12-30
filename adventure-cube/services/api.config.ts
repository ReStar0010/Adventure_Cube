/**
 * API Configuration for Adventure Cube Backend
 */

import { Platform } from 'react-native';

// Determine the correct backend URL based on platform
// IMPORTANT: localhost on device/simulator refers to the DEVICE, not your computer!
function getServerUrl(): string {
    if (!__DEV__) {
        // Production: use your production API URL
        return 'https://your-production-api.com';
    }
    
    // Development: choose based on platform
    if (Platform.OS === 'android') {
        // Android Emulator: use special IP that maps to host machine
        return 'http://10.0.2.2:8000';
    } else if (Platform.OS === 'ios') {
        // iOS Simulator: can use localhost (shares network with Mac)
        return 'http://localhost:8000';
    } else {
        // Web or other platforms
        return 'http://localhost:8000';
    }
    
    // For physical device testing, you MUST use your computer's IP:
    // Uncomment and replace with YOUR computer's IP address:
    // return 'http://192.168.0.153:8000';  // Replace with your actual IP
}

const SERVER_URL = getServerUrl();

// Debug: Log the URL being used (remove in production)
if (__DEV__) {
    console.log('🔗 Backend URL configured:', SERVER_URL);
    console.log('📱 Platform:', Platform.OS);
    console.log('🌐 Full API URL:', `${SERVER_URL}/api`);
}

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