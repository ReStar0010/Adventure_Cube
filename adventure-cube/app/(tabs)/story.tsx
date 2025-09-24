import React, { useState, useEffect } from 'react';
import { XStack, YStack, Text, H4, Button, Image } from "tamagui";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from 'expo-router';
import { Story } from '../../types/Story';
import { StorageManager } from '../../utils/storage';

export default function StoryScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const [currentStory, setCurrentStory] = useState<Story | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadCurrentStory();
    }, []);

    const loadCurrentStory = async () => {
        try {
            const story = await StorageManager.getCurrentStory();
            setCurrentStory(story);
        } catch (error) {
            console.error('Failed to load current story:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateStory = () => {
        if (currentStory) {
            currentStory.generateStory();
            setCurrentStory({ ...currentStory });
        }
    };

    const handleBackToLibrary = () => {
        router.push('/library');
    };

    if (loading) {
        return (
            <YStack flex={1} bg='#d9d9d9' style={{ paddingTop: insets.top + 10 }} items="center" justifyContent="center">
                <H4 color='#404040'>Loading story...</H4>
            </YStack>
        );
    }

    if (!currentStory) {
        return (
            <YStack flex={1} bg='#d9d9d9' style={{ paddingTop: insets.top + 10 }} items="center" justifyContent="center">
                <H4 color='#404040'>No story selected</H4>
                <Button onPress={handleBackToLibrary} mt={16}>Back to Library</Button>
            </YStack>
        );
    }

    return (
        <YStack flex={1} bg='#d9d9d9' style={{ paddingTop: insets.top + 10 }} alignItems='center' justifyContent='flex-start'>
            <YStack alignItems='center' justify={'center'} mb={100} px={16}>
                {currentStory.background.image && (
                    <Image source={currentStory.background.image} width={250} height={250} />
                )}
                <H4 fontWeight="bold" color="#404040" textAlign="center" mt={16}>
                    {currentStory.storyTitle}
                </H4>
                <Text color="#404040" textAlign="center" mt={8}>
                    {currentStory.generatedStory || "Press 'Generate Story' to create your adventure!"}
                </Text>

                {/* Story elements display */}
                <XStack gap={12} mt={16} flexWrap="wrap" justifyContent="center">
                    {currentStory.character.image && (
                        <Image source={currentStory.character.image} width={40} height={40} />
                    )}
                    {currentStory.theme.image && (
                        <Image source={currentStory.theme.image} width={40} height={40} />
                    )}
                    {currentStory.keyItems.map((item, index) => (
                        item.image ? <Image key={index} source={item.image} width={35} height={35} /> : null
                    ))}
                </XStack>
            </YStack>

            <XStack width={'100%'} justifyContent='center' alignItems='center' marginTop="auto" px={16} pb={40} gap={12}>
                <Button onPress={handleBackToLibrary}>Back</Button>
                <Button onPress={handleGenerateStory} bg='#5A9FD4' color='white'>Generate Story</Button>
                <Button>Share</Button>
            </XStack>
        </YStack>
    );
}