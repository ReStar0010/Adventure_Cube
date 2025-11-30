/**
 * Story Service - Bridge between frontend Story type and backend API
 */

import { apiClient } from './api.client';
import { Story, StoryAsset } from '../types/Story';
import type { BackendStory, StoryGenerateRequest } from './api.types';

export class StoryService {
    /**
     * Generate intro paragraph (first stage) using the backend API
     */
    static async generateIntro(
        storyTitle: string,
        theme: StoryAsset,
        character: StoryAsset,
        background: StoryAsset,
        keyItems?: StoryAsset[],
        childName?: string,
        childAge?: number,
        contextTemplate: string = '5min_basic'
    ): Promise<{ story: Story; backendData: BackendStory }> {
        try {
            // Prepare request
            const request: StoryGenerateRequest = {
                title: storyTitle,
                theme: theme.name.toLowerCase(),
                child_name: childName,
                child_age: childAge,
                language: 'zh-TW', // Always use Traditional Chinese for 5min template
                character: character.name,
                background: background.name,
                key_items: keyItems?.map(item => item.name),
                context_template: contextTemplate,
            };

            // Call backend API to generate intro
            const backendStory = await apiClient.generateIntro(request);

            // Create frontend Story instance
            const story = new Story(
                backendStory.id,
                storyTitle || backendStory.title,
                background,
                character,
                theme,
                keyItems || []
            );

            // Set the generated story text from first paragraph
            const firstParagraph = backendStory.paragraphs?.[0];
            if (firstParagraph) {
                story.generatedStory = `${backendStory.title}\n\n${firstParagraph.text}`;
            } else {
                story.generatedStory = `${backendStory.title}\n\n${backendStory.body}`;
            }

            return { story, backendData: backendStory };
        } catch (error: any) {
            console.error('Intro generation failed:', error);
            // Extract more detailed error message
            let errorMessage = 'Failed to generate story intro';
            if (error instanceof Error) {
                errorMessage = error.message;
            } else if (error?.response?.data?.error) {
                errorMessage = error.response.data.error;
            } else if (error?.response?.data?.details) {
                errorMessage = typeof error.response.data.details === 'string' 
                    ? error.response.data.details 
                    : JSON.stringify(error.response.data.details);
            } else if (typeof error === 'string') {
                errorMessage = error;
            }
            throw new Error(errorMessage);
        }
    }

    /**
     * Generate remaining paragraphs (second stage) in the background
     */
    static async generateRemaining(storyId: string): Promise<BackendStory> {
        try {
            return await apiClient.generateRemaining(storyId);
        } catch (error) {
            console.error('Remaining paragraphs generation failed:', error);
            throw error;
        }
    }

    /**
     * Get story status and available paragraphs
     */
    static async getStoryStatus(storyId: string): Promise<BackendStory> {
        try {
            return await apiClient.getStoryStatus(storyId);
        } catch (error) {
            console.error('Failed to get story status:', error);
            throw error;
        }
    }

    /**
     * Get a specific paragraph by index
     */
    static async getParagraph(storyId: string, paragraphIndex: number) {
        try {
            return await apiClient.getParagraph(storyId, paragraphIndex);
        } catch (error) {
            console.error('Failed to get paragraph:', error);
            throw error;
        }
    }

    /**
     * Generate a story using the backend API (legacy method - kept for backward compatibility)
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
        // Use new two-stage generation by default
        return this.generateIntro(storyTitle, theme, character, background, keyItems, childName, childAge);
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
