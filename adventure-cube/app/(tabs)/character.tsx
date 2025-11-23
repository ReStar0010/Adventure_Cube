import React, { useState, useEffect, useCallback } from 'react';
import { TouchableOpacity, Dimensions } from 'react-native';
import { XStack, YStack, H4, Button, Image, ScrollView, Group } from "tamagui";
import { Dices, CheckCircle2, ArrowLeft, ArrowRight } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Story } from '../../types/Story';
import { StorageManager } from '../../utils/storage';
import { CHARACTERS } from '../../constants/assets';

export default function CharacterScreen() {
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

    // Load story every time the screen is focused
    useFocusEffect(
        useCallback(() => {
            console.log('Character screen focused, loading current story...');
            loadCurrentStory();
        }, [])
    );

    const loadCurrentStory = async () => {
        try {
            const story = await StorageManager.getCurrentStory();
            if (story) {
                setCurrentStory(story);
                // If story already has a character, set it as selected
                const existingIndex = CHARACTERS.findIndex(char => char.name === story.character.name);
                if (existingIndex !== -1) {
                    setSelectedIndex(existingIndex);
                }
            }
        } catch (error) {
            console.error('Failed to load current story:', error);
        }
    };

    const handleButtonPress = (index: number) => {
        setSelectedIndex(index);
    };

    const handleDicePress = () => {
        const randomIndex = Math.floor(Math.random() * CHARACTERS.length);
        setSelectedIndex(randomIndex);
    };

    const handleConfirmPress = async () => {
        if (!currentStory) return;

        try {
            const selectedCharacter = CHARACTERS[selectedIndex];
            console.log('🎭 Selected character:', selectedCharacter.name, selectedCharacter);
            currentStory.character = selectedCharacter;
            console.log('📝 Story character after assignment:', currentStory.character.name);

            await StorageManager.updateStory(currentStory);
            await StorageManager.setCurrentStory(currentStory);
            
            // Verify it was saved
            const savedStory = await StorageManager.getCurrentStory();
            console.log('✅ Verified saved character:', savedStory?.character?.name);

            // Navigate to next step (theme selection)
            router.push('/theme');
        } catch (error) {
            console.error('Failed to save character selection:', error);
        }
    };

    const handleBackPress = async () => {
        // User is going back from character selection - just navigate back
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
                        角色
                    </H4>
                </XStack>

                <YStack gap={16} mt={20}>
                    {/* Button group */}
                    <XStack items="center" gap={10}>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ width: 300 }} contentContainerStyle={{ overflow: 'hidden' }}>
                            <Group orientation="horizontal">
                                {CHARACTERS.map((character, index) => (
                                    <Group.Item key={index}>
                                        <Button
                                            onPress={() => handleButtonPress(index)}
                                            bg={selectedIndex === index ? '#5A9FD4' : undefined}
                                            color={selectedIndex === index ? 'white' : undefined}
                                        >
                                            {character.name}
                                        </Button>
                                    </Group.Item>
                                ))}
                            </Group>
                        </ScrollView>
                        <ArrowRight color='#404040' size={24} />
                    </XStack>

                    {/* Center preview image - scrollable */}
                    <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                        <XStack gap={16} px={16}>
                            {CHARACTERS.map((character, index) => (
                                <TouchableOpacity key={index} onPress={() => setSelectedIndex(index)}>
                                    <YStack items="center" gap={8}>
                                        <Image
                                            source={character.image}
                                            style={{
                                                width: imageWidth,
                                                height: imageHeight,
                                                borderWidth: selectedIndex === index ? 4 : 0,
                                                borderColor: '#5A9FD4',
                                                borderRadius: 8,
                                            }}
                                        />
                                        <H4 color='#404040' textAlign="center" fontWeight={selectedIndex === index ? "bold" : "normal"}>
                                            {character.name}
                                        </H4>
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
