/**
 * Custom hook for story generation
 */

import { useState } from 'react';
import { StoryService } from '../services';
import type { Story, StoryAsset } from '../types/Story';
import type { BackendStory } from '../services/api.types';

interface UseStoryGenerationResult {
    isGenerating: boolean;
    error: string | null;
    generatedStory: Story | null;
    backendData: BackendStory | null;
    generateStory: (
        title: string,
        theme: StoryAsset,
        character: StoryAsset,
        background: StoryAsset,
        keyItems?: StoryAsset[],
        childName?: string,
        childAge?: number
    ) => Promise<void>;
    reset: () => void;
}

export function useStoryGeneration(): UseStoryGenerationResult {
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [generatedStory, setGeneratedStory] = useState<Story | null>(null);
    const [backendData, setBackendData] = useState<BackendStory | null>(null);

    const generateStory = async (
        title: string,
        theme: StoryAsset,
        character: StoryAsset,
        background: StoryAsset,
        keyItems?: StoryAsset[],
        childName?: string,
        childAge?: number
    ) => {
        setIsGenerating(true);
        setError(null);

        try {
            const result = await StoryService.generateStory(
                title,
                theme,
                character,
                background,
                keyItems,
                childName,
                childAge
            );

            setGeneratedStory(result.story);
            setBackendData(result.backendData);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to generate story';
            setError(errorMessage);
            console.error('Story generation error:', err);
        } finally {
            setIsGenerating(false);
        }
    };

    const reset = () => {
        setIsGenerating(false);
        setError(null);
        setGeneratedStory(null);
        setBackendData(null);
    };

    return {
        isGenerating,
        error,
        generatedStory,
        backendData,
        generateStory,
        reset,
    };
}
