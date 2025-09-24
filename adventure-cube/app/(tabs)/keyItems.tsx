import React, { useState, useEffect } from 'react';
import { TouchableOpacity } from 'react-native';
import { XStack, YStack, H4, Card, Image, ScrollView } from "tamagui";
import { Dices, CheckCircle2, ArrowLeft, Check } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Story, StoryAsset } from '../../types/Story';
import { StorageManager } from '../../utils/storage';
import { KEY_ITEMS } from '../../constants/assets';

export default function KeyItemsScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const [currentStory, setCurrentStory] = useState<Story | null>(null);
    const [selectedItems, setSelectedItems] = useState<boolean[]>(new Array(KEY_ITEMS.length).fill(false));

    useEffect(() => {
        loadCurrentStory();
    }, []);

    const loadCurrentStory = async () => {
        try {
            const story = await StorageManager.getCurrentStory();
            if (story) {
                setCurrentStory(story);
                // If story already has key items, set them as selected
                const newSelectedItems = new Array(KEY_ITEMS.length).fill(false);
                story.keyItems.forEach(item => {
                    const index = KEY_ITEMS.findIndex(keyItem => keyItem.name === item.name);
                    if (index !== -1) {
                        newSelectedItems[index] = true;
                    }
                });
                setSelectedItems(newSelectedItems);
            }
        } catch (error) {
            console.error('Failed to load current story:', error);
        }
    };

    const handleItemToggle = (index: number) => {
        const newSelectedItems = [...selectedItems];
        newSelectedItems[index] = !newSelectedItems[index];
        setSelectedItems(newSelectedItems);
    };

    const handleDicePress = () => {
        // Randomly select 1-3 items
        const numItems = Math.floor(Math.random() * 3) + 1;
        const newSelectedItems = new Array(KEY_ITEMS.length).fill(false);

        const shuffledIndices = Array.from({ length: KEY_ITEMS.length }, (_, i) => i)
            .sort(() => Math.random() - 0.5);

        for (let i = 0; i < numItems; i++) {
            newSelectedItems[shuffledIndices[i]] = true;
        }

        setSelectedItems(newSelectedItems);
    };

    const handleConfirmPress = async () => {
        if (!currentStory) return;

        try {
            const selectedKeyItems: StoryAsset[] = [];
            selectedItems.forEach((isSelected, index) => {
                if (isSelected) {
                    selectedKeyItems.push(KEY_ITEMS[index]);
                }
            });

            currentStory.keyItems = selectedKeyItems;

            await StorageManager.updateStory(currentStory);
            await StorageManager.setCurrentStory(currentStory);

            // Save the story to the main list if it's new
            const stories = await StorageManager.getStories();
            const existingStoryIndex = stories.findIndex(s => s.id === currentStory.id);
            if (existingStoryIndex === -1) {
                await StorageManager.addStory(currentStory);
            }

            // Navigate back to library
            router.push('/library');
        } catch (error) {
            console.error('Failed to save key items selection:', error);
        }
    };

    const handleBackPress = () => {
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
                        �uSw
                    </H4>
                </XStack>

                <YStack gap={16} mt={20}>
                    {/* Grid of key items with checkboxes */}
                    <ScrollView>
                        <YStack gap={12}>
                            {KEY_ITEMS.map((item, index) => (
                                <TouchableOpacity key={index} onPress={() => handleItemToggle(index)}>
                                    <Card
                                        bg='white'
                                        width="100%"
                                        p={16}
                                        style={{
                                            borderWidth: selectedItems[index] ? 2 : 0,
                                            borderColor: '#5A9FD4'
                                        }}
                                    >
                                        <XStack items="center" gap={16}>
                                            <Image source={item.image} width={60} height={60} />
                                            <YStack flex={1}>
                                                <H4 color='#404040'>{item.name}</H4>
                                            </YStack>
                                            <YStack w={24} h={24} bg={selectedItems[index] ? '#5A9FD4' : 'white'}
                                                borderWidth={2} borderColor='#5A9FD4' borderRadius={4}
                                                items="center" justifyContent="center">
                                                {selectedItems[index] && <Check color='white' size={16} />}
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