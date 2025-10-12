import React, { useState, useEffect, useCallback } from 'react';
import { XStack, YStack, Text, H4, Button, Image } from "tamagui";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from 'expo-router';
import { Story } from '../../types/Story';
import { StorageManager } from '../../utils/storage';
import { useStoryGeneration } from '../../hooks/use-story-generation';
import { ActivityIndicator, ScrollView } from 'react-native';

export default function StoryScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const [currentStory, setCurrentStory] = useState<Story | null>(null);
    const [loading, setLoading] = useState(true);

    // Use the backend story generation hook
    const { isGenerating, error, backendData, generateStory } = useStoryGeneration();

    const loadCurrentStory = useCallback(async () => {
        try {
            const story = await StorageManager.getCurrentStory();
            setCurrentStory(story);
        } catch (error) {
            console.error('Failed to load current story:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    // Load story on mount
    useEffect(() => {
        loadCurrentStory();
    }, [loadCurrentStory]);

    // Save story when backend data is available
    useEffect(() => {
        const saveGeneratedStory = async () => {
            if (backendData && currentStory && !currentStory.generatedStory) {
                console.log('Saving generated story to storage...');
                // Create updated story object (don't mutate)
                const updatedStory = new Story(
                    currentStory.id,
                    currentStory.storyTitle,
                    currentStory.background,
                    currentStory.character,
                    currentStory.theme,
                    currentStory.keyItems
                );
                updatedStory.generatedStory = backendData.body;

                await StorageManager.updateStory(updatedStory);
                setCurrentStory(updatedStory); // Update state with new story

                // Clear current story cache after successful save
                // Story is now permanently saved in library
                await StorageManager.clearCurrentStory();
                console.log('Story saved successfully and cache cleared');
            }
        };

        saveGeneratedStory();
    }, [backendData, currentStory]);

    const handleGenerateStory = async () => {
        if (!currentStory) {
            return;
        }

        try {
            // Call the backend to generate the story
            await generateStory(
                currentStory.storyTitle,
                currentStory.theme,
                currentStory.character,
                currentStory.background,
                undefined, // childName - optional
                undefined  // childAge - optional
            );

            // Note: backendData will be updated by the hook automatically
            // The useEffect watching backendData will handle saving
            console.log('Story generation completed');
        } catch (err) {
            console.error('Failed to generate story:', err);
        }
    };

    const handleBackToLibrary = async () => {
        // Clear current story cache when returning to library
        try {
            await StorageManager.clearCurrentStory();
            console.log('Cleared current story cache');
        } catch (error) {
            console.error('Failed to clear current story cache:', error);
        }
        router.push('/library');
    };

    if (loading) {
        return (
            <YStack flex={1} bg='#d9d9d9' style={{ paddingTop: insets.top + 10, alignItems: 'center', justifyContent: 'center' }}>
                <H4 color='#404040'>Loading story...</H4>
            </YStack>
        );
    }

    if (!currentStory) {
        return (
            <YStack flex={1} bg='#d9d9d9' style={{ paddingTop: insets.top + 10, alignItems: 'center', justifyContent: 'center' }}>
                <H4 color='#404040'>No story selected</H4>
                <Button onPress={handleBackToLibrary} mt={16}>Back to Library</Button>
            </YStack>
        );
    }

    return (
        <YStack flex={1} bg='#d9d9d9' style={{ paddingTop: insets.top + 10 }}>
            <ScrollView
                contentContainerStyle={{
                    alignItems: 'center',
                    paddingBottom: 20,
                    paddingHorizontal: 16
                }}
                showsVerticalScrollIndicator={true}
            >
                <YStack px={16} width="100%" style={{ alignItems: 'center' }}>
                    {currentStory.background?.image && (
                        <Image source={currentStory.background.image} width={250} height={250} />
                    )}
                    <H4 fontWeight="bold" color="#404040" mt={16} style={{ textAlign: 'center' }}>
                        {backendData?.title || currentStory.storyTitle}
                    </H4>

                    {/* Show loading indicator when generating */}
                    {isGenerating && (
                        <YStack mt={16} style={{ alignItems: 'center' }}>
                            <ActivityIndicator size="large" color="#5A9FD4" />
                            <Text color="#404040" mt={8}>Generating your story...</Text>
                        </YStack>
                    )}

                    {/* Show error if generation failed */}
                    {error && (
                        <Text color="#c62828" mt={8} px={16} style={{ textAlign: 'center' }}>
                            Error: {error}
                        </Text>
                    )}

                    {/* Show the generated story */}
                    {!isGenerating && (
                        <Text color="#404040" mt={8} style={{ textAlign: 'center' }}>
                            {backendData?.body || "Press 'Generate Story' to create your adventure!"}
                        </Text>
                    )}

                    {/* Show model source indicator */}
                    {backendData && (
                        <Text color="#666" fontSize={12} mt={8}>
                            {backendData.model_source === 'online' ? '🌐 AI Generated' : '📝 Template'}
                        </Text>
                    )}

                    {/* Story elements display */}
                    <XStack gap={12} mt={16} flexWrap="wrap" style={{ justifyContent: 'center' }}>
                        {currentStory.character?.image && (
                            <Image source={currentStory.character.image} width={40} height={40} />
                        )}
                        {currentStory.theme?.image && (
                            <Image source={currentStory.theme.image} width={40} height={40} />
                        )}
                        {currentStory.keyItems?.map((item, index) => (
                            item?.image ? <Image key={index} source={item.image} width={35} height={35} /> : null
                        ))}
                    </XStack>
                </YStack>
            </ScrollView>

            <XStack width={'100%'} px={16} pb={40} gap={12} bg='#d9d9d9' style={{ justifyContent: 'center', alignItems: 'center' }}>
                <Button onPress={handleBackToLibrary} disabled={isGenerating}>Back</Button>
                <Button
                    onPress={handleGenerateStory}
                    bg='#5A9FD4'
                    color='white'
                    disabled={isGenerating}
                >
                    {isGenerating ? 'Generating...' : 'Generate Story'}
                </Button>
            </XStack>
        </YStack>
    );
}