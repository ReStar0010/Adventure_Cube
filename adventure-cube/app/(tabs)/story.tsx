import React, { useState, useEffect, useCallback } from "react";
import { XStack, YStack, Text, H4, Button, Image } from "tamagui";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { Story } from "../../types/Story";
import { StorageManager } from "../../utils/storage";
import { useStoryGeneration } from "../../hooks/use-story-generation";
import { ActivityIndicator, ScrollView, Alert } from "react-native";
import { Play, Pause } from "lucide-react-native";
import { Audio } from "expo-av";

export default function StoryScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [currentStory, setCurrentStory] = useState<Story | null>(null);
  const [loading, setLoading] = useState(true);
  const [playingAudioIndex, setPlayingAudioIndex] = useState<number | null>(null);
  const [sound, setSound] = useState<any>(null);

  // Use the backend story generation hook
  const { 
    isGenerating, 
    isGeneratingRemaining,
    error, 
    backendData, 
    generateStory,
    currentParagraphIndex,
    paragraphs,
    goToNextParagraph,
    goToPreviousParagraph
  } = useStoryGeneration();

  const loadCurrentStory = useCallback(async () => {
    try {
      const story = await StorageManager.getCurrentStory();
      setCurrentStory(story);
    } catch (error) {
      console.error("Failed to load current story:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load story on mount
  useEffect(() => {
    loadCurrentStory();
  }, [loadCurrentStory]);

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (sound && sound.unloadAsync) {
        sound.unloadAsync();
      }
    };
  }, [sound]);

  // Save story when backend data is available
  useEffect(() => {
    const saveGeneratedStory = async () => {
      if (backendData && currentStory && !currentStory.generatedStory) {
        console.log("Saving generated story to storage...");
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
        console.log("Story saved successfully and cache cleared");
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
        currentStory.keyItems
      );

      // Note: backendData will be updated by the hook automatically
      // The useEffect watching backendData will handle saving
      console.log("Story generation completed");
    } catch (err) {
      console.error("Failed to generate story:", err);
    }
  };

  const handlePlayAudio = async (paragraphIndex: number, audioUrl?: string) => {
    if (!audioUrl) {
      Alert.alert("提示", "此段落尚未生成音訊");
      return;
    }

    try {
      // Stop current audio if playing
      if (sound) {
        await sound.stopAsync();
        await sound.unloadAsync();
        setSound(null);
        if (playingAudioIndex === paragraphIndex) {
          setPlayingAudioIndex(null);
          return;
        }
      }

      // Set audio mode for playback
      await Audio.setAudioModeAsync({
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
      });

      // Load and play new audio
      const { sound: newSound } = await Audio.Sound.createAsync(
        { uri: audioUrl },
        { shouldPlay: true }
      );
      setSound(newSound);
      setPlayingAudioIndex(paragraphIndex);

      // Clean up when finished
      newSound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded && status.didJustFinish) {
          setPlayingAudioIndex(null);
          newSound.unloadAsync();
          setSound(null);
        }
      });
    } catch (error) {
      console.error("Failed to play audio:", error);
      Alert.alert("錯誤", "無法播放音訊");
    }
  };

  const handlePreviousNext = (direction: 'prev' | 'next') => {
    if (isGenerating || isGeneratingRemaining) {
      Alert.alert("故事生成中", "故事正在生成中，請稍候...");
      return;
    }

    if (direction === 'prev') {
      goToPreviousParagraph();
    } else {
      goToNextParagraph();
    }
  };

  const handleBackToLibrary = async () => {
    // If story is generating, show warning
    if (isGenerating || isGeneratingRemaining) {
      Alert.alert(
        "返回首頁",
        "故事正在生成中，返回首頁後可以刪除這個故事。確定要返回嗎？",
        [
          { text: "取消", style: "cancel" },
          {
            text: "返回",
            style: "destructive",
            onPress: async () => {
              try {
                await StorageManager.clearCurrentStory();
                router.replace("/(tabs)/library");
              } catch (error) {
                console.error("Failed to clear current story cache:", error);
                router.replace("/(tabs)/library");
              }
            }
          }
        ]
      );
      return;
    }

    // Normal back to library
    try {
      await StorageManager.clearCurrentStory();
      console.log("Cleared current story cache");
    } catch (error) {
      console.error("Failed to clear current story cache:", error);
    }
    router.replace("/(tabs)/library");
  };

  if (loading) {
    return (
      <YStack
        flex={1}
        bg="#d9d9d9"
        style={{
          paddingTop: insets.top + 10,
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <H4 color="#404040">Loading story...</H4>
      </YStack>
    );
  }

  if (!currentStory) {
    return (
      <YStack
        flex={1}
        bg="#d9d9d9"
        style={{
          paddingTop: insets.top + 10,
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <H4 color="#404040">No story selected</H4>
        <Button onPress={handleBackToLibrary} mt={16}>
          Back to Library
        </Button>
      </YStack>
    );
  }

  return (
    <YStack flex={1} bg="#d9d9d9" style={{ paddingTop: insets.top + 10 }}>
      <ScrollView
        contentContainerStyle={{
          alignItems: "center",
          paddingBottom: 20,
          paddingHorizontal: 16,
        }}
        showsVerticalScrollIndicator={true}
      >
        <YStack px={16} width="100%" style={{ alignItems: "center" }}>
          {currentStory.background?.image && (
            <Image
              source={currentStory.background.image}
              width={250}
              height={250}
            />
          )}
          <H4
            fontWeight="bold"
            color="#404040"
            mt={16}
            style={{ textAlign: "center" }}
          >
            {backendData?.title || currentStory.storyTitle}
          </H4>

          {/* Show loading indicator when generating intro */}
          {isGenerating && (
            <YStack mt={16} style={{ alignItems: "center" }}>
              <ActivityIndicator size="large" color="#5A9FD4" />
              <Text color="#404040" mt={8}>
                Generating your story...
              </Text>
            </YStack>
          )}

          {/* Show loading indicator when generating remaining paragraphs */}
          {isGeneratingRemaining && (
            <YStack mt={8} style={{ alignItems: "center" }}>
              <Text color="#666" fontSize={12}>
                Generating remaining paragraphs... ({backendData?.paragraphs_ready || 0}/{backendData?.total_paragraphs || 5})
              </Text>
            </YStack>
          )}

          {/* Show error if generation failed */}
          {error && (
            <Text
              color="#c62828"
              mt={8}
              px={16}
              style={{ textAlign: "center" }}
            >
              Error: {error}
            </Text>
          )}

          {/* Show paragraphs page by page */}
          {!isGenerating && backendData && (
            <YStack mt={16} width="100%" style={{ alignItems: "center" }}>
              {paragraphs.length > 0 ? (
                <>
                  {/* Current paragraph */}
                  <YStack mt={8} width="100%" ai="center">
                    <Text 
                      color="#404040" 
                      px={16}
                      fontSize={16}
                      lineHeight={24}
                      style={{ textAlign: "center" }}
                    >
                      {paragraphs[currentParagraphIndex]?.text || "Loading..."}
                    </Text>
                    
                    {/* TTS Playback Button */}
                    {paragraphs[currentParagraphIndex]?.tts_url && (
                      <Button
                        mt={12}
                        bg="#5A9FD4"
                        color="white"
                        onPress={() => handlePlayAudio(
                          currentParagraphIndex,
                          paragraphs[currentParagraphIndex]?.tts_url
                        )}
                      >
                        {playingAudioIndex === currentParagraphIndex ? (
                          <XStack gap={8} ai="center">
                            <Pause size={16} color="white" />
                            <Text color="white">暫停</Text>
                          </XStack>
                        ) : (
                          <XStack gap={8} ai="center">
                            <Play size={16} color="white" />
                            <Text color="white">播放</Text>
                          </XStack>
                        )}
                      </Button>
                    )}
                  </YStack>
                  
                  {/* Paragraph navigation */}
                  <XStack mt={16} gap={12} ai="center">
                    <Button
                      onPress={() => handlePreviousNext('prev')}
                      disabled={currentParagraphIndex === 0 || isGenerating || isGeneratingRemaining}
                      opacity={currentParagraphIndex === 0 || isGenerating || isGeneratingRemaining ? 0.5 : 1}
                    >
                      上一段
                    </Button>
                    <Text color="#666" fontSize={12}>
                      {currentParagraphIndex + 1} / {paragraphs.length}
                    </Text>
                    <Button
                      onPress={() => handlePreviousNext('next')}
                      disabled={currentParagraphIndex >= paragraphs.length - 1 || isGenerating || isGeneratingRemaining}
                      opacity={currentParagraphIndex >= paragraphs.length - 1 || isGenerating || isGeneratingRemaining ? 0.5 : 1}
                    >
                      下一段
                    </Button>
                  </XStack>
                </>
              ) : (
                <Text color="#404040" mt={8} style={{ textAlign: "center" }}>
                  {backendData.body || "Press 'Generate Story' to create your adventure!"}
                </Text>
              )}
            </YStack>
          )}

          {/* Show placeholder when no story generated */}
          {!isGenerating && !backendData && (
            <Text color="#404040" mt={8} style={{ textAlign: "center" }}>
              Press 'Generate Story' to create your adventure!
            </Text>
          )}

          {/* Show model source indicator */}
          {backendData && (
            <Text color="#666" fontSize={12} mt={8}>
              {backendData.model_source === "online"
                ? "🌐 AI Generated"
                : "📝 Template"}
            </Text>
          )}

          {/* Story elements display */}
          <XStack
            gap={12}
            mt={16}
            flexWrap="wrap"
            style={{ justifyContent: "center" }}
          >
            {currentStory.character?.image && (
              <Image
                source={currentStory.character.image}
                width={40}
                height={40}
              />
            )}
            {currentStory.theme?.image && (
              <Image source={currentStory.theme.image} width={40} height={40} />
            )}
            {currentStory.keyItems?.map((item, index) =>
              item?.image ? (
                <Image key={index} source={item.image} width={35} height={35} />
              ) : null
            )}
          </XStack>
        </YStack>
      </ScrollView>

      <XStack
        width={"100%"}
        px={16}
        pb={40}
        gap={12}
        bg="#d9d9d9"
        style={{ justifyContent: "center", alignItems: "center" }}
      >
        <Button 
          onPress={handleBackToLibrary}
          disabled={isGenerating && !backendData}
        >
          返回首頁
        </Button>
        {!backendData && !isGenerating && (
          <Button
            onPress={handleGenerateStory}
            bg="#5A9FD4"
            color="white"
            disabled={isGenerating}
          >
            {isGenerating ? "生成中..." : "生成故事"}
          </Button>
        )}
      </XStack>
    </YStack>
  );
}
