/**
 * Custom hook for audio generation (TTS)
 */

import { useState } from 'react';
import { StoryService } from '../services';

interface UseAudioGenerationResult {
    isGenerating: boolean;
    error: string | null;
    audioUrl: string | null;
    generateAudio: (storyId: string, language?: string) => Promise<void>;
    reset: () => void;
}

export function useAudioGeneration(): UseAudioGenerationResult {
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);

    const generateAudio = async (storyId: string, language: string = 'en') => {
        setIsGenerating(true);
        setError(null);

        try {
            const url = await StoryService.generateAudio(storyId, language);
            setAudioUrl(url);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to generate audio';
            setError(errorMessage);
            console.error('Audio generation error:', err);
        } finally {
            setIsGenerating(false);
        }
    };

    const reset = () => {
        setIsGenerating(false);
        setError(null);
        setAudioUrl(null);
    };

    return {
        isGenerating,
        error,
        audioUrl,
        generateAudio,
        reset,
    };
}
