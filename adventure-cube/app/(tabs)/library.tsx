import React, { useState, useEffect } from 'react';
import { TouchableOpacity } from 'react-native';
import { Button, Card, H2, H4, Image, XStack, YStack, ScrollView } from "tamagui";
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Story } from '../../types/Story';
import { StorageManager } from '../../utils/storage';

export default function LibraryScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const [stories, setStories] = useState<Story[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadStories();
    }, []);

    const loadStories = async () => {
        try {
            const storedStories = await StorageManager.getStories();
            console.log('Loaded stories from storage:', storedStories);
            setStories(storedStories);
        } catch (error) {
            console.error('Failed to load stories:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleNewStory = async () => {
        try {
            const newStory = new Story(
                Date.now().toString(),
                "New Adventure"
            );
            await StorageManager.setCurrentStory(newStory);
            router.push('/background');
        } catch (error) {
            console.error('Failed to create new story:', error);
        }
    };

    const handleStoryPress = async (story: Story) => {
        try {
            await StorageManager.setCurrentStory(story);
            router.push('/story');
        } catch (error) {
            console.error('Failed to select story:', error);
        }
    };

    const renderStoryCard = (story: Story) => (
        <TouchableOpacity key={story.id} onPress={() => handleStoryPress(story)}>
            <Card bg='white' width="100%" pressStyle={{ scale: 0.98 }}>
                <Card.Header>
                    <H4 fontWeight="bold" color="#404040">{story.storyTitle}</H4>
                </Card.Header>
                <Card.Footer>
                    <XStack flex={1} justifyContent="center" alignItems="flex-start" gap={12}>
                        {story.background?.image && story.background.name && (
                            <YStack items="center" gap={4}>
                                <Image source={story.background.image} width={50} height={50} />
                                <H4 fontSize={10} color="#666" textAlign="center" width={60}>
                                    {story.background.name}
                                </H4>
                            </YStack>
                        )}
                        {story.character?.image && story.character.name && (
                            <YStack items="center" gap={4}>
                                <Image source={story.character.image} width={50} height={50} />
                                <H4 fontSize={10} color="#666" textAlign="center" width={60}>
                                    {story.character.name}
                                </H4>
                            </YStack>
                        )}
                        {story.theme?.image && story.theme.name && (
                            <YStack items="center" gap={4}>
                                <Image source={story.theme.image} width={50} height={50} />
                                <H4 fontSize={10} color="#666" textAlign="center" width={60}>
                                    {story.theme.name}
                                </H4>
                            </YStack>
                        )}
                        {story.keyItems?.length > 0 && story.keyItems.map((item, index) => (
                            item?.image && item.name ? (
                                <YStack key={index} items="center" gap={4}>
                                    <Image source={item.image} width={40} height={40} />
                                    <H4 fontSize={9} color="#666" textAlign="center" width={50}>
                                        {item.name}
                                    </H4>
                                </YStack>
                            ) : null
                        ))}
                    </XStack>
                </Card.Footer>
            </Card>
        </TouchableOpacity>
    );

    return (
        <YStack flex={1} bg='#d9d9d9' style={{ paddingTop: insets.top + 10 }}>
            <YStack px={16} pt={20}>
                <H2 color='#404040' fontWeight={'bold'}>
                    故事庫
                </H2>
            </YStack>

            <ScrollView flex={1}>
                <YStack my={20} px={16} gap={20}>
                    {loading ? (
                        <YStack py={40} items="center">
                            <H4 color='#404040'>Loading stories...</H4>
                        </YStack>
                    ) : stories.length > 0 ? (
                        stories.map(renderStoryCard)
                    ) : (
                        <YStack py={40} items="center">
                            <H4 color='#404040'>No stories yet. Create your first story!</H4>
                        </YStack>
                    )}

                    <YStack items="center" mt={10}>
                        <Button onPress={handleNewStory} bg='#5A9FD4' color='white'>
                            New Story
                        </Button>
                    </YStack>
                </YStack>
            </ScrollView>
        </YStack>
    );
}
