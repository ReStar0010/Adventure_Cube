import React, { useState, useEffect } from 'react';
import { TouchableOpacity, Dimensions } from 'react-native';
import { XStack, YStack, H4, Button, Image, ScrollView, Group } from "tamagui";
import { Dices, CheckCircle2, ArrowLeft, ArrowRight } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Story } from '../../types/Story';
import { StorageManager } from '../../utils/storage';
import { BACKGROUNDS } from '../../constants/assets';

export default function BackgroundScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const [currentStory, setCurrentStory] = useState<Story | null>(null);
    const [selectedIndex, setSelectedIndex] = useState(0);

    const { width: screenWidth } = Dimensions.get('window');
    const { height: screenHeight } = Dimensions.get('window');
    const imageWidth = screenWidth * 0.6; // Reduced to 60% to account for padding and gaps
    const imageHeight = screenHeight * 0.4;

    useEffect(() => {
        loadCurrentStory();
    }, []);

    const loadCurrentStory = async () => {
        try {
            const story = await StorageManager.getCurrentStory();
            console.log('Loaded current story:', story);

            if (story) {
                setCurrentStory(story);
                // If story already has a background, set it as selected
                const existingIndex = BACKGROUNDS.findIndex(bg => bg.name === story.background.name);
                if (existingIndex !== -1) {
                    setSelectedIndex(existingIndex);
                    console.log('Found existing background, setting selected index to:', existingIndex);
                }
            } else {
                console.log('No current story found in storage');
            }
        } catch (error) {
            console.error('Failed to load current story:', error);
        }
    };

    const handleButtonPress = (index: number) => {
        setSelectedIndex(index);
    };

    const handleDicePress = () => {
        const randomIndex = Math.floor(Math.random() * BACKGROUNDS.length);
        setSelectedIndex(randomIndex);
    };

    const handleConfirmPress = async () => {
        if (!currentStory){
            console.error('No current story found');
            return;
        }

        try {
            const selectedBackground = BACKGROUNDS[selectedIndex];
            console.log('Selected background:', selectedBackground);

            // Update the story object
            currentStory.background = selectedBackground;
            console.log('Updated story:', currentStory);

            // First try to update existing story, if not found, add it
            try {
                await StorageManager.updateStory(currentStory);
                console.log('Story updated successfully');
            } catch (updateError) {
                console.log('Story not found in storage, adding as new story');
                await StorageManager.addStory(currentStory);
            }

            // Set as current story
            await StorageManager.setCurrentStory(currentStory);
            console.log('Current story set successfully');

            // Navigate to next step (character selection)
            router.push('/character');
        } catch (error) {
            console.error('Failed to save background selection:', error);
            console.error('Error details:', error);
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
                        背景
                    </H4>
                </XStack>

                <YStack gap={16} mt={20}>
                    {/* Button group */}
                    <XStack items="center" gap={10}>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ width: 300 }} contentContainerStyle={{ overflow: 'hidden' }}>
                            <Group orientation="horizontal">
                                {BACKGROUNDS.map((background, index) => (
                                    <Group.Item key={index}>
                                        <Button
                                            onPress={() => handleButtonPress(index)}
                                            bg={selectedIndex === index ? '#5A9FD4' : undefined}
                                            color={selectedIndex === index ? 'white' : undefined}
                                        >
                                            {background.name}
                                        </Button>
                                    </Group.Item>
                                ))}
                            </Group>
                        </ScrollView>
                        <ArrowRight color='#404040' size={24} />
                    </XStack>

                    {/* Scrollable image container */}
                    <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                        <XStack gap={16} px={16}>
                            {BACKGROUNDS.map((background, index) => (
                                <TouchableOpacity key={index} onPress={() => setSelectedIndex(index)}>
                                    <YStack items="center" gap={8}>
                                        <Image
                                            source={background.image}
                                            style={{
                                                width: imageWidth,
                                                height: imageHeight,
                                                // aspectRatio: 1,  // Maintain original aspect ratio
                                                borderWidth: selectedIndex === index ? 4 : 0,
                                                borderColor: '#5A9FD4',
                                                borderRadius: 8,
                                            }}
                                        />
                                        <H4 color='#404040' textAlign="center">{background.name}</H4>
                                    </YStack>
                                </TouchableOpacity>
                            ))}
                        </XStack>
                    </ScrollView>

                    {/* Icon stack */}
                    <XStack gap={16} justifyContent="center">
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
