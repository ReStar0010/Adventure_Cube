/**
 * Authentication Service
 * Handles user authentication with AsyncStorage persistence
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiClient } from './api.client';

const AUTH_TOKEN_KEY = 'auth_token';
const AUTH_USER_KEY = 'auth_user';

export interface AuthUser {
    id: number;
    username: string;
    email: string;
}

export class AuthService {
    /**
     * Register a new user
     */
    static async register(username: string, password: string, email?: string): Promise<{ user: AuthUser; token: string }> {
        try {
            const response = await apiClient.register(username, password, email);
            
            // Save token to storage and set in API client
            await AsyncStorage.setItem(AUTH_TOKEN_KEY, response.token);
            await AsyncStorage.setItem(AUTH_USER_KEY, JSON.stringify(response.user));
            apiClient.setToken(response.token);
            
            return response;
        } catch (error) {
            console.error('Registration failed:', error);
            throw error;
        }
    }

    /**
     * Login a user
     */
    static async login(username: string, password: string): Promise<{ user: AuthUser; token: string }> {
        try {
            const response = await apiClient.login(username, password);
            
            // Save token to storage and set in API client
            await AsyncStorage.setItem(AUTH_TOKEN_KEY, response.token);
            await AsyncStorage.setItem(AUTH_USER_KEY, JSON.stringify(response.user));
            apiClient.setToken(response.token);
            
            return response;
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    }

    /**
     * Logout the current user
     */
    static async logout(): Promise<void> {
        try {
            // Try to call backend logout (delete token)
            try {
                await apiClient.logout();
            } catch (error) {
                console.warn('Backend logout failed, clearing local data anyway:', error);
            }
            
            // Clear token from storage and API client
            await AsyncStorage.removeItem(AUTH_TOKEN_KEY);
            await AsyncStorage.removeItem(AUTH_USER_KEY);
            apiClient.clearToken();
        } catch (error) {
            console.error('Logout failed:', error);
            throw error;
        }
    }

    /**
     * Get stored authentication token
     */
    static async getToken(): Promise<string | null> {
        try {
            return await AsyncStorage.getItem(AUTH_TOKEN_KEY);
        } catch (error) {
            console.error('Failed to get token:', error);
            return null;
        }
    }

    /**
     * Get stored user data
     */
    static async getUser(): Promise<AuthUser | null> {
        try {
            const userJson = await AsyncStorage.getItem(AUTH_USER_KEY);
            if (!userJson) return null;
            return JSON.parse(userJson);
        } catch (error) {
            console.error('Failed to get user:', error);
            return null;
        }
    }

    /**
     * Check if user is authenticated
     */
    static async isAuthenticated(): Promise<boolean> {
        const token = await this.getToken();
        return token !== null;
    }

    /**
     * Initialize authentication (restore token from storage)
     * Call this on app startup
     */
    static async initialize(): Promise<void> {
        try {
            const token = await this.getToken();
            if (token) {
                apiClient.setToken(token);
                console.log('Auth initialized with stored token');
            } else {
                console.log('No stored token found');
            }
        } catch (error) {
            console.error('Failed to initialize auth:', error);
        }
    }
}

export default AuthService;

