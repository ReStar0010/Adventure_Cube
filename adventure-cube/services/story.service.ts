/**
 * Story Service - Bridge between frontend Story type and backend API
 */

import { apiClient } from './api.client';
import { Story, StoryAsset } from '../types/Story';
import type { BackendStory, StoryGenerateRequest } from './api.types';

export class StoryService {
    /**
     * Generate a story using the backend API
     */
    static async generateStory(
        storyTitle: string,
        theme: StoryAsset,
        character: StoryAsset,
        background: StoryAsset,
        keyItems?: StoryAsset[],
        childName?: string,
        childAge?: number
    ): Promise<{ story: Story; backendData: BackendStory }> {
        try {
            // Prepare request
            const request: StoryGenerateRequest = {
                theme: theme.name.toLowerCase(),
                child_name: childName,
                child_age: childAge,
                language: 'en',
                character: character.name,
                background: background.name,
                key_items: keyItems?.map(item => item.name),
            };

            // Call backend API
            const backendStory = await apiClient.generateStory(request);

            // Create frontend Story instance
            const story = new Story(
                backendStory.id,
                storyTitle || backendStory.title,
                background,
                character,
                theme,
                keyItems || []
            );

            // Set the generated story text
            story.generatedStory = `${backendStory.title}\n\n${backendStory.body}`;

            return { story, backendData: backendStory };
        } catch (error) {
            console.error('Story generation failed:', error);
            throw error;
        }
    }

    /**
     * Get all saved stories from backend
     */
    static async getSavedStories(): Promise<BackendStory[]> {
        try {
            return await apiClient.getStories();
        } catch (error) {
            console.error('Failed to fetch stories:', error);
            throw error;
        }
    }

    /**
     * Delete a story
     */
    static async deleteStory(storyId: string): Promise<void> {
        try {
            await apiClient.deleteStory(storyId);
        } catch (error) {
            console.error('Failed to delete story:', error);
            throw error;
        }
    }

    /**
     * Generate audio narration for a story
     */
    static async generateAudio(
        storyId: string,
        language: string = 'en'
    ): Promise<string> {
        try {
            const audioFile = await apiClient.generateAudio({
                story_id: storyId,
                language,
            });
            return audioFile.audio_url;
        } catch (error) {
            console.error('Audio generation failed:', error);
            throw error;
        }
    }

    /**
     * Convert backend story to frontend Story object
     */
    static backendToFrontend(
        backendStory: BackendStory,
        assets: {
            background?: StoryAsset;
            character?: StoryAsset;
            theme?: StoryAsset;
        } = {}
    ): Story {
        const story = new Story(
            backendStory.id,
            backendStory.title,
            assets.background || { name: backendStory.background || '', image: null },
            assets.character || { name: backendStory.character || '', image: null },
            assets.theme || { name: backendStory.theme, image: null },
            []
        );

        story.generatedStory = `${backendStory.title}\n\n${backendStory.body}`;

        return story;
    }
}

export default StoryService;
