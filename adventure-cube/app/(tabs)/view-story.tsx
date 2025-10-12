import React, { useState, useCallback } from 'react';
import { XStack, YStack, Text, H4, Button, Image } from "tamagui";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter, useFocusEffect } from 'expo-router';
import { Story } from '../../types/Story';
import { StorageManager } from '../../utils/storage';
import { ScrollView } from 'react-native';

export default function ViewStoryScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const [currentStory, setCurrentStory] = useState<Story | null>(null);
    const [loading, setLoading] = useState(true);

    const loadCurrentStory = useCallback(async () => {
        try {
            setLoading(true);
            const story = await StorageManager.getCurrentStory();
            setCurrentStory(story);
        } catch (error) {
            console.error('Failed to load current story:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    // Load story when screen is focused
    useFocusEffect(
        useCallback(() => {
            loadCurrentStory();
        }, [loadCurrentStory])
    );

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

    const handleShare = () => {
        // TODO: Implement share functionality
        console.log('Share story:', currentStory?.storyTitle);
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
                        {currentStory.storyTitle}
                    </H4>

                    {/* Display the story content */}
                    <Text color="#404040" mt={8} style={{ textAlign: 'center' }}>
                        {currentStory.generatedStory || "Story content not available"}
                    </Text>

                    {/* Show saved story indicator */}
                    {currentStory.generatedStory && (
                        <Text color="#666" fontSize={12} mt={8}>
                            📚 Saved Story
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
                <Button onPress={handleBackToLibrary}>Back</Button>
                <Button
                    bg='#5A9FD4'
                    color='white'
                    onPress={handleShare}
                    disabled={!currentStory.generatedStory}
                >
                    Share
                </Button>
            </XStack>
        </YStack>
    );
}
