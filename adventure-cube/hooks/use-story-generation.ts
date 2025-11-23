/**
 * Custom hook for two-stage story generation
 */

import { useState, useEffect, useRef } from 'react';
import { StoryService } from '../services';
import type { Story, StoryAsset } from '../types/Story';
import type { BackendStory, StoryParagraph } from '../services/api.types';

interface UseStoryGenerationResult {
    isGenerating: boolean;
    isGeneratingRemaining: boolean;
    error: string | null;
    generatedStory: Story | null;
    backendData: BackendStory | null;
    currentParagraphIndex: number;
    paragraphs: StoryParagraph[];
    generateStory: (
        title: string,
        theme: StoryAsset,
        character: StoryAsset,
        background: StoryAsset,
        keyItems?: StoryAsset[],
        childName?: string,
        childAge?: number
    ) => Promise<void>;
    goToNextParagraph: () => void;
    goToPreviousParagraph: () => void;
    reset: () => void;
}

const POLL_INTERVAL = 2000; // Poll every 2 seconds for new paragraphs

export function useStoryGeneration(): UseStoryGenerationResult {
    const [isGenerating, setIsGenerating] = useState(false);
    const [isGeneratingRemaining, setIsGeneratingRemaining] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [generatedStory, setGeneratedStory] = useState<Story | null>(null);
    const [backendData, setBackendData] = useState<BackendStory | null>(null);
    const [currentParagraphIndex, setCurrentParagraphIndex] = useState(0);
    const [paragraphs, setParagraphs] = useState<StoryParagraph[]>([]);
    const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

    // Poll for story status updates
    useEffect(() => {
        if (!backendData?.id || backendData.generation_status === 'completed') {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
            return;
        }

        // Start polling if intro is ready but remaining paragraphs are being generated
        if (backendData.generation_status === 'intro_ready' || backendData.generation_status === 'generating_remaining') {
            setIsGeneratingRemaining(true);
            
            pollingIntervalRef.current = setInterval(async () => {
                try {
                    const updatedStory = await StoryService.getStoryStatus(backendData.id);
                    setBackendData(updatedStory);
                    
                    if (updatedStory.paragraphs) {
                        setParagraphs(updatedStory.paragraphs.sort((a, b) => a.paragraph_index - b.paragraph_index));
                    }

                    if (updatedStory.generation_status === 'completed') {
                        setIsGeneratingRemaining(false);
                        if (pollingIntervalRef.current) {
                            clearInterval(pollingIntervalRef.current);
                            pollingIntervalRef.current = null;
                        }
                    }
                } catch (err) {
                    console.error('Failed to poll story status:', err);
                }
            }, POLL_INTERVAL);
        }

        return () => {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
        };
    }, [backendData?.id, backendData?.generation_status]);

    // Update paragraphs when backendData changes
    useEffect(() => {
        if (backendData?.paragraphs) {
            setParagraphs(backendData.paragraphs.sort((a, b) => a.paragraph_index - b.paragraph_index));
        }
    }, [backendData]);

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
        setCurrentParagraphIndex(0);

        try {
            // Stage 1: Generate intro paragraph
            const result = await StoryService.generateIntro(
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
            
            if (result.backendData.paragraphs) {
                setParagraphs(result.backendData.paragraphs.sort((a, b) => a.paragraph_index - b.paragraph_index));
            }

            // Stage 2: Start generating remaining paragraphs in background
            if (result.backendData.id) {
                setIsGeneratingRemaining(true);
                StoryService.generateRemaining(result.backendData.id)
                    .then((updatedStory) => {
                        setBackendData(updatedStory);
                        if (updatedStory.paragraphs) {
                            setParagraphs(updatedStory.paragraphs.sort((a, b) => a.paragraph_index - b.paragraph_index));
                        }
                        setIsGeneratingRemaining(false);
                    })
                    .catch((err) => {
                        console.error('Background generation failed:', err);
                        setIsGeneratingRemaining(false);
                    });
            }
        } catch (err) {
            let errorMessage = 'Failed to generate story';
            if (err instanceof Error) {
                errorMessage = err.message;
            } else if (typeof err === 'string') {
                errorMessage = err;
            } else if ((err as any)?.message) {
                errorMessage = (err as any).message;
            }
            
            // Log full error for debugging
            console.error('Story generation error:', err);
            try {
                // Try to stringify error, but handle circular references
                const errorDetails = err instanceof Error 
                    ? { message: err.message, name: err.name, stack: err.stack }
                    : err;
                console.error('Error details:', JSON.stringify(errorDetails, null, 2));
            } catch (stringifyError) {
                console.error('Error details (could not stringify):', err);
            }
            
            setError(errorMessage);
        } finally {
            setIsGenerating(false);
        }
    };

    const goToNextParagraph = () => {
        if (currentParagraphIndex < paragraphs.length - 1) {
            setCurrentParagraphIndex(currentParagraphIndex + 1);
        }
    };

    const goToPreviousParagraph = () => {
        if (currentParagraphIndex > 0) {
            setCurrentParagraphIndex(currentParagraphIndex - 1);
        }
    };

    const reset = () => {
        setIsGenerating(false);
        setIsGeneratingRemaining(false);
        setError(null);
        setGeneratedStory(null);
        setBackendData(null);
        setCurrentParagraphIndex(0);
        setParagraphs([]);
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
        }
    };

    return {
        isGenerating,
        isGeneratingRemaining,
        error,
        generatedStory,
        backendData,
        currentParagraphIndex,
        paragraphs,
        generateStory,
        goToNextParagraph,
        goToPreviousParagraph,
        reset,
    };
}
