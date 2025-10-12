/**
 * Assets Service - Fetch dynamic assets from backend
 */

import { apiClient } from './api.client';
import type { ImagesResponse, Theme } from './api.types';

export class AssetsService {
    /**
     * Fetch all available images from backend
     */
    static async fetchImages(): Promise<ImagesResponse> {
        try {
            return await apiClient.getImages();
        } catch (error) {
            console.error('Failed to fetch images:', error);
            throw error;
        }
    }

    /**
     * Fetch images by category
     */
    static async fetchImagesByCategory(
        category: 'characters' | 'backgrounds' | 'themes' | 'key_items'
    ): Promise<ImagesResponse> {
        try {
            return await apiClient.getImages(category);
        } catch (error) {
            console.error(`Failed to fetch ${category} images:`, error);
            throw error;
        }
    }

    /**
     * Fetch available themes
     */
    static async fetchThemes(): Promise<Theme[]> {
        try {
            const response = await apiClient.getThemes();
            return response.themes;
        } catch (error) {
            console.error('Failed to fetch themes:', error);
            throw error;
        }
    }

    /**
     * Get full image URL from path
     * Assumes backend serves media files at /media/
     */
    static getImageUrl(path: string, baseUrl?: string): string {
        const base = baseUrl || apiClient['baseUrl'].replace('/api', '');
        return `${base}${path}`;
    }
}

export default AssetsService;
