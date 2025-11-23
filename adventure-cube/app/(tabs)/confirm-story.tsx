import React, { useState, useCallback } from 'react';
import { XStack, YStack, Text, H4, Button, Image, ScrollView } from "tamagui";
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Story } from '../../types/Story';
import { StorageManager } from '../../utils/storage';
import { ArrowLeft } from 'lucide-react-native';
import { TouchableOpacity, Alert } from 'react-native';

export default function ConfirmStoryScreen() {
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

    useFocusEffect(
        useCallback(() => {
            loadCurrentStory();
        }, [loadCurrentStory])
    );

    const handleBackPress = () => {
        router.back();
    };

    const handleConfirmGenerate = async () => {
        if (!currentStory) return;

        // Show final confirmation
        Alert.alert(
            "確認生成故事",
            "開始生成後將無法取消，確定要繼續嗎？",
            [
                { text: "取消", style: "cancel" },
                {
                    text: "確認生成",
                    style: "default",
                    onPress: async () => {
                        // Navigate to story generation screen
                        router.push('/story');
                    }
                }
            ]
        );
    };

    if (loading) {
        return (
            <YStack flex={1} bg='#d9d9d9' style={{ paddingTop: insets.top + 10, alignItems: 'center', justifyContent: 'center' }}>
                <H4 color='#404040'>載入中...</H4>
            </YStack>
        );
    }

    if (!currentStory) {
        return (
            <YStack flex={1} bg='#d9d9d9' style={{ paddingTop: insets.top + 10, alignItems: 'center', justifyContent: 'center' }}>
                <H4 color='#404040'>找不到故事</H4>
                <Button onPress={handleBackPress} mt={16}>返回</Button>
            </YStack>
        );
    }

    return (
        <YStack flex={1} bg='#d9d9d9' style={{ paddingTop: insets.top + 10 }}>
            <YStack px={16} pt={20}>
                <XStack ai="center" gap={8} items={'center'}>
                    <TouchableOpacity onPress={handleBackPress}>
                        <ArrowLeft color='#404040' size={24} />
                    </TouchableOpacity>
                    <H4 color='#404040' fontWeight={'bold'}>
                        確認故事設定
                    </H4>
                </XStack>
            </YStack>

            <ScrollView
                contentContainerStyle={{
                    paddingHorizontal: 16,
                    paddingBottom: 20,
                }}
            >
                <YStack gap={20} mt={20}>
                    {/* Story Title */}
                    <YStack bg="white" p={16} borderRadius={8}>
                        <Text color="#666" fontSize={12} mb={4}>故事標題</Text>
                        <H4 color="#404040" fontWeight="bold">{currentStory.storyTitle}</H4>
                    </YStack>

                    {/* Background */}
                    {currentStory.background && (
                        <YStack bg="white" p={16} borderRadius={8}>
                            <Text color="#666" fontSize={12} mb={8}>背景</Text>
                            <XStack gap={12} alignItems="center">
                                {currentStory.background.image && (
                                    <Image source={currentStory.background.image} width={60} height={60} />
                                )}
                                <H4 color="#404040">{currentStory.background.name}</H4>
                            </XStack>
                        </YStack>
                    )}

                    {/* Character */}
                    {currentStory.character && (
                        <YStack bg="white" p={16} borderRadius={8}>
                            <Text color="#666" fontSize={12} mb={8}>角色</Text>
                            <XStack gap={12} alignItems="center">
                                {currentStory.character.image && (
                                    <Image source={currentStory.character.image} width={60} height={60} />
                                )}
                                <H4 color="#404040">{currentStory.character.name}</H4>
                            </XStack>
                        </YStack>
                    )}

                    {/* Theme */}
                    {currentStory.theme && (
                        <YStack bg="white" p={16} borderRadius={8}>
                            <Text color="#666" fontSize={12} mb={8}>主題</Text>
                            <XStack gap={12} alignItems="center">
                                {currentStory.theme.image && (
                                    <Image source={currentStory.theme.image} width={60} height={60} />
                                )}
                                <H4 color="#404040">{currentStory.theme.name}</H4>
                            </XStack>
                        </YStack>
                    )}

                    {/* Key Items */}
                    {currentStory.keyItems && currentStory.keyItems.length > 0 && (
                        <YStack bg="white" p={16} borderRadius={8}>
                            <Text color="#666" fontSize={12} mb={8}>關鍵道具</Text>
                            <XStack gap={12} flexWrap="wrap">
                                {currentStory.keyItems.map((item, index) => (
                                    <XStack key={index} gap={8} alignItems="center" mb={8}>
                                        {item.image && (
                                            <Image source={item.image} width={50} height={50} />
                                        )}
                                        <H4 color="#404040">{item.name}</H4>
                                    </XStack>
                                ))}
                            </XStack>
                        </YStack>
                    )}

                    {/* Warning Message */}
                    <YStack bg="#fff3cd" p={16} borderRadius={8} borderWidth={1} borderColor="#ffc107">
                        <Text color="#856404" fontSize={14} fontWeight="bold" mb={4}>
                            ⚠️ 注意
                        </Text>
                        <Text color="#856404" fontSize={12}>
                            開始生成故事後將無法取消，只能返回首頁並刪除故事。請確認所有設定無誤後再開始生成。
                        </Text>
                    </YStack>
                </YStack>
            </ScrollView>

            <XStack
                width="100%"
                px={16}
                pb={40}
                gap={12}
                bg="#d9d9d9"
                style={{ justifyContent: "center", alignItems: "center" }}
            >
                <Button onPress={handleBackPress} flex={1}>
                    返回修改
                </Button>
                <Button
                    onPress={handleConfirmGenerate}
                    bg="#5A9FD4"
                    color="white"
                    flex={1}
                >
                    確認生成
                </Button>
            </XStack>
        </YStack>
    );
}

