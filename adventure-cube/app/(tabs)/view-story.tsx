import React, { useState, useCallback, useRef, useEffect } from 'react';
import { XStack, YStack, Text, H4, Button, Image } from "tamagui";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter, useFocusEffect } from 'expo-router';
import { Story } from '../../types/Story';
import { StorageManager } from '../../utils/storage';
import { ScrollView, Alert, ActivityIndicator } from 'react-native';
import { Play, Pause } from 'lucide-react-native';
import { Audio } from 'expo-av';
import { StoryService } from '../../services';
import { getMediaUrl } from '../../services/api.config';

export default function ViewStoryScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const [currentStory, setCurrentStory] = useState<Story | null>(null);
    const [loading, setLoading] = useState(true);
    
    // Audio playback state
    const [isPlaying, setIsPlaying] = useState(false);
    const [sound, setSound] = useState<any>(null);
    const [isLoadingAudio, setIsLoadingAudio] = useState(false);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const soundRef = useRef<any>(null);

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

    // Cleanup audio on unmount
    useEffect(() => {
        return () => {
            if (soundRef.current) {
                soundRef.current.unloadAsync().catch((e: any) => {
                    console.log("Audio cleanup warning:", e?.message || e);
                });
            }
        };
    }, []);

    const handleBackToLibrary = async () => {
        // Stop audio before navigating
        if (soundRef.current) {
            try {
                await soundRef.current.unloadAsync();
            } catch (e) {
                console.log("Audio cleanup on back:", e);
            }
            soundRef.current = null;
            setSound(null);
            setIsPlaying(false);
        }
        
        // Clear current story cache when returning to library
        try {
            await StorageManager.clearCurrentStory();
            console.log('Cleared current story cache');
        } catch (error) {
            console.error('Failed to clear current story cache:', error);
        }
        router.push('/library');
    };

    // Cleanup audio helper
    const cleanupAudio = async (soundToClean: any) => {
        try {
            if (soundToClean) {
                const status = await soundToClean.getStatusAsync();
                if (status.isLoaded) {
                    await soundToClean.unloadAsync();
                }
            }
        } catch (e: any) {
            console.log("Audio cleanup warning:", e?.message || e);
        }
    };

    const handlePlayAudio = async () => {
        if (!currentStory) return;

        // Don't allow new actions while loading
        if (isLoadingAudio) {
            return;
        }

        try {
            // If we have a sound loaded, toggle play/pause
            if (sound && audioUrl) {
                const status = await sound.getStatusAsync();
                if (status.isLoaded) {
                    if (status.isPlaying) {
                        // Pause the audio
                        console.log("⏸️ Pausing audio");
                        await sound.pauseAsync();
                        setIsPlaying(false);
                    } else {
                        // Resume the audio
                        console.log("▶️ Resuming audio");
                        await sound.playAsync();
                        setIsPlaying(true);
                    }
                    return;
                }
            }

            // If no audio URL yet, generate or get audio
            let currentAudioUrl = audioUrl;
            
            if (!currentAudioUrl) {
                console.log("🔊 Generating/getting audio for story:", currentStory.id);
                setIsLoadingAudio(true);
                
                try {
                    // Generate or get audio from backend
                    currentAudioUrl = await StoryService.generateAudio(currentStory.id, 'zh-TW');
                    setAudioUrl(currentAudioUrl);
                } catch (error: any) {
                    setIsLoadingAudio(false);
                    console.error("Failed to generate/get audio:", error);
                    Alert.alert("錯誤", "無法生成或取得音檔。請確認故事已完整生成。");
                    return;
                }
            }

            // Get the full URL for the audio file
            const fullAudioUrl = getMediaUrl(currentAudioUrl);
            
            if (!fullAudioUrl) {
                setIsLoadingAudio(false);
                Alert.alert("錯誤", "無法取得音檔 URL");
                return;
            }

            console.log("🔊 Loading audio from:", fullAudioUrl);
            setIsLoadingAudio(true);

            // Set audio mode for playback
            await Audio.setAudioModeAsync({
                playsInSilentModeIOS: true,
                staysActiveInBackground: false,
            });

            // Load and play new audio
            const { sound: newSound } = await Audio.Sound.createAsync(
                { uri: fullAudioUrl },
                { shouldPlay: true }
            );

            console.log("🔊 Audio loaded, playing...");
            soundRef.current = newSound;
            setSound(newSound);
            setIsPlaying(true);
            setIsLoadingAudio(false);

            // Clean up when finished
            newSound.setOnPlaybackStatusUpdate((status: any) => {
                if (status.isLoaded && status.didJustFinish) {
                    console.log("🏁 Audio finished playing");
                    setIsPlaying(false);
                }
            });
        } catch (error: any) {
            setIsLoadingAudio(false);
            console.error("Failed to play audio:", error);
            
            let errorMessage = "無法播放音訊";
            if (error?.message?.includes("-1100")) {
                errorMessage = "找不到音檔。請確認伺服器已啟動且可存取媒體檔案。";
            } else if (error?.message?.includes("-1009")) {
                errorMessage = "網路連線失敗。請檢查網路連線。";
            } else if (error?.message) {
                errorMessage = `播放錯誤：${error.message}`;
            }

            Alert.alert("錯誤", errorMessage);
        }
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
                    
                    {/* TODO: Add paragraph-by-paragraph display for saved stories */}

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
                {currentStory.generatedStory && (
                    <Button
                        bg='#5A9FD4'
                        color='white'
                        onPress={handlePlayAudio}
                        disabled={isLoadingAudio}
                        opacity={isLoadingAudio ? 0.7 : 1}
                    >
                        {isLoadingAudio ? (
                            <ActivityIndicator size="small" color="white" />
                        ) : isPlaying ? (
                            <XStack gap={8} style={{ alignItems: 'center' }}>
                                <Pause size={16} color="white" />
                                <Text color="white">暫停</Text>
                            </XStack>
                        ) : (
                            <XStack gap={8} style={{ alignItems: 'center' }}>
                                <Play size={16} color="white" />
                                <Text color="white">播放</Text>
                            </XStack>
                        )}
                    </Button>
                )}
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
