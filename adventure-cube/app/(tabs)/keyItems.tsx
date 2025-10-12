import React, { useState, useEffect, useCallback } from 'react';
import { TouchableOpacity, Dimensions } from 'react-native';
import { XStack, YStack, H4, Card, Image, ScrollView } from "tamagui";
import { Dices, CheckCircle2, ArrowLeft, Check } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Story, StoryAsset } from '../../types/Story';
import { StorageManager } from '../../utils/storage';
import { KEY_ITEMS } from '../../constants/assets';

export default function KeyItemsScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const [currentStory, setCurrentStory] = useState<Story | null>(null);
    const [selectedItemIndex, setSelectedItemIndex] = useState<number | null>(null);

    const { height: screenHeight } = Dimensions.get('window');

    useEffect(() => {
        loadCurrentStory();
    }, []);

    // Load story every time the screen is focused
    useFocusEffect(
        useCallback(() => {
            console.log('KeyItems screen focused, loading current story...');
            loadCurrentStory();
        }, [])
    );

    const loadCurrentStory = async () => {
        try {
            const story = await StorageManager.getCurrentStory();
            if (story) {
                setCurrentStory(story);
                // If story already has key items, set the first one as selected
                if (story.keyItems.length > 0) {
                    const index = KEY_ITEMS.findIndex(keyItem => keyItem.name === story.keyItems[0].name);
                    if (index !== -1) {
                        setSelectedItemIndex(index);
                    } else {
                        // If saved item not found, pick random one
                        setSelectedItemIndex(Math.floor(Math.random() * KEY_ITEMS.length));
                    }
                } else {
                    // If no key items selected yet, pick random one
                    setSelectedItemIndex(Math.floor(Math.random() * KEY_ITEMS.length));
                }
            }
        } catch (error) {
            console.error('Failed to load current story:', error);
        }
    };

    const handleItemToggle = (index: number) => {
        // Single selection - always select the clicked item
        setSelectedItemIndex(index);
    };

    const handleDicePress = () => {
        // Randomly select one item
        const randomIndex = Math.floor(Math.random() * KEY_ITEMS.length);
        setSelectedItemIndex(randomIndex);
    };

    const handleConfirmPress = async () => {
        if (!currentStory) return;

        try {
            const selectedKeyItems: StoryAsset[] = [];
            if (selectedItemIndex !== null) {
                selectedKeyItems.push(KEY_ITEMS[selectedItemIndex]);
            }

            currentStory.keyItems = selectedKeyItems;

            // Update the story in the library (story should already exist from creation)
            await StorageManager.updateStory(currentStory);

            // Update current story
            await StorageManager.setCurrentStory(currentStory);

            // Navigate back to library
            router.push('/story');
        } catch (error) {
            console.error('Failed to save key items selection:', error);
        }
    };

    const handleBackPress = async () => {
        // User is going back from key items selection - just navigate back
        // Don't clear cache as they might want to continue editing
        router.back();
    };

    return (
        <YStack flex={1} bg='#d9d9d9' style={{ paddingTop: insets.top + 10 }}>
            <YStack px={16} pt={20}>
                <XStack ai="center" gap={8} items={'center'}>
                    <TouchableOpacity onPress={handleBackPress}>
                        <ArrowLeft color='#404040' size={24} />
                    </TouchableOpacity>
                    <H4 color='#404040' fontWeight={'bold'}>
                        關鍵道具
                    </H4>
                </XStack>
                <YStack gap={16} mt={20}>
                    {/* Grid of key items with checkboxes */}
                    <ScrollView style={{ height: screenHeight * 0.5 }}>
                        <YStack gap={12}>
                            {KEY_ITEMS.map((item, index) => (
                                <TouchableOpacity key={index} onPress={() => handleItemToggle(index)}>
                                    <Card
                                        bg='white'
                                        width="100%"
                                        p={16}
                                        style={{
                                            borderWidth: selectedItemIndex === index ? 2 : 0,
                                            borderColor: '#5A9FD4'
                                        }}
                                    >
                                        <XStack items="center" gap={16}>
                                            <Image source={item.image} width={50} height={60} />
                                            <YStack flex={1}>
                                                <H4 color='#404040'>{item.name}</H4>
                                            </YStack>
                                            <YStack w={24} h={24} bg={selectedItemIndex === index ? '#5A9FD4' : 'white'}
                                                borderWidth={2} borderColor='#5A9FD4' borderRadius={12}
                                                items="center" justifyContent="center">
                                                {selectedItemIndex === index && <Check color='white' size={16} />}
                                            </YStack>
                                        </XStack>
                                    </Card>
                                </TouchableOpacity>
                            ))}
                        </YStack>
                    </ScrollView>
                    {/* Icon stack */}
                    <XStack gap={16} justifyContent="center" py={20}>
                        <TouchableOpacity onPress={handleDicePress}>
                            <Dices color='#404040' size={100} />
                        </TouchableOpacity>
                        <TouchableOpacity onPress={handleConfirmPress}>
                            <CheckCircle2 color='#5A9FD4' size={100} />
                        </TouchableOpacity>
                    </XStack>
                </YStack>
            </YStack>
        </YStack>
    );
}