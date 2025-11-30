import React, { useState, useEffect, useCallback, useRef } from "react";
import { XStack, YStack, Text, H4, Button, Image } from "tamagui";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter, useFocusEffect } from "expo-router";
import { useNavigation } from "@react-navigation/native";
import { Story } from "../../types/Story";
import { StorageManager } from "../../utils/storage";
import { useStoryGeneration } from "../../hooks/use-story-generation";
import { getMediaUrl } from "../../services/api.config";
import {
  ActivityIndicator,
  ScrollView,
  Alert,
  BackHandler,
} from "react-native";
import { Play, Pause } from "lucide-react-native";
import { Audio } from "expo-av";

export default function StoryScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [currentStory, setCurrentStory] = useState<Story | null>(null);
  const [loading, setLoading] = useState(true);
  const [playingAudioIndex, setPlayingAudioIndex] = useState<number | null>(
    null
  );
  const [sound, setSound] = useState<any>(null);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);

  // Track the last story ID to avoid unnecessary resets
  const lastStoryIdRef = useRef<string | null>(null);

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
    goToPreviousParagraph,
    reset: resetGeneration,
  } = useStoryGeneration();

  const loadCurrentStory = useCallback(async () => {
    try {
      const story = await StorageManager.getCurrentStory();
      console.log("📖 Loaded current story:", story?.storyTitle);
      console.log(
        "🎭 Story character:",
        story?.character?.name,
        story?.character
      );
      console.log("🌍 Story background:", story?.background?.name);
      console.log("🎨 Story theme:", story?.theme?.name);
      console.log(
        "🔑 Story key items:",
        story?.keyItems?.map((item) => item.name)
      );

      setCurrentStory(story);
    } catch (error) {
      console.error("Failed to load current story:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Reset generation state when story changes (different story ID and not yet generated)
  useEffect(() => {
    if (currentStory && currentStory.id !== lastStoryIdRef.current) {
      // Story ID changed - check if we need to reset
      if (!currentStory.generatedStory) {
        console.log(
          "🔄 Resetting generation state for new story:",
          currentStory.id
        );
        resetGeneration();
      }
      lastStoryIdRef.current = currentStory.id;
    }
  }, [currentStory, resetGeneration]);

  // Load story on mount
  useEffect(() => {
    loadCurrentStory();
  }, [loadCurrentStory]);

  // Reload story when screen is focused (in case it was updated in another screen)
  useFocusEffect(
    useCallback(() => {
      console.log("📱 Story screen focused, reloading story...");
      loadCurrentStory();
    }, [loadCurrentStory])
  );

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (sound && sound.unloadAsync) {
        sound.unloadAsync();
      }
    };
  }, [sound]);

  // Prevent back navigation while story is generating
  const navigation = useNavigation();
  const isGeneratingAny = isGenerating || isGeneratingRemaining;

  // Handle Android hardware back button
  useEffect(() => {
    const backHandler = BackHandler.addEventListener(
      "hardwareBackPress",
      () => {
        if (isGeneratingAny) {
          Alert.alert(
            "故事生成中",
            "故事正在生成中，請等待生成完成後再離開此頁面。",
            [{ text: "知道了", style: "default" }]
          );
          return true; // Prevent default back behavior
        }
        return false; // Allow default back behavior
      }
    );

    return () => backHandler.remove();
  }, [isGeneratingAny]);

  // Prevent gesture/navigation-based back while generating
  useEffect(() => {
    if (isGeneratingAny) {
      navigation.setOptions({
        gestureEnabled: false,
      });
    } else {
      navigation.setOptions({
        gestureEnabled: true,
      });
    }
  }, [isGeneratingAny, navigation]);

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
      console.log("🚀 Generating story with:");
      console.log("   Title:", currentStory.storyTitle);
      console.log("   Character:", currentStory.character?.name);
      console.log("   Background:", currentStory.background?.name);
      console.log("   Theme:", currentStory.theme?.name);
      console.log(
        "   Key Items:",
        currentStory.keyItems?.map((item) => item.name)
      );

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

  // Helper function to safely stop and cleanup audio
  const cleanupAudio = async (soundToClean: any) => {
    if (!soundToClean) return;
    
    try {
      const status = await soundToClean.getStatusAsync();
      if (status.isLoaded) {
        // Only try to stop if it's actually playing or paused
        if (status.isPlaying) {
          await soundToClean.stopAsync();
        }
        await soundToClean.unloadAsync();
      }
    } catch (e: any) {
      // Ignore "seeking interrupted" and similar errors during cleanup
      if (!e?.message?.includes("seeking") && !e?.message?.includes("interrupt")) {
        console.log("Audio cleanup warning:", e?.message || e);
      }
    }
  };

  const handlePlayAudio = async (paragraphIndex: number, audioUrl?: string) => {
    // Get the full URL for the audio file
    const fullAudioUrl = getMediaUrl(audioUrl);
    
    if (!fullAudioUrl) {
      Alert.alert("提示", "此段落尚未生成音訊");
      return;
    }

    // Don't allow new actions while loading
    if (isLoadingAudio) {
      return;
    }

    try {
      // If we have a sound loaded for this paragraph, toggle play/pause
      if (sound && playingAudioIndex === paragraphIndex) {
        const status = await sound.getStatusAsync();
        if (status.isLoaded) {
          if (status.isPlaying) {
            // Pause the audio
            console.log("⏸️ Pausing audio");
            await sound.pauseAsync();
            setPlayingAudioIndex(null);
          } else {
            // Resume the audio
            console.log("▶️ Resuming audio");
            await sound.playAsync();
            setPlayingAudioIndex(paragraphIndex);
          }
          return;
        }
      }

      // If playing a different paragraph, stop the current one first
      if (sound) {
        console.log("🛑 Stopping previous audio");
        await cleanupAudio(sound);
        setSound(null);
        setPlayingAudioIndex(null);
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
      setSound(newSound);
      setPlayingAudioIndex(paragraphIndex);
      setIsLoadingAudio(false);

      // Clean up when finished
      newSound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded && status.didJustFinish) {
          console.log("🏁 Audio finished playing");
          setPlayingAudioIndex(null);
          // Don't unload immediately to allow replay
        }
      });
    } catch (error: any) {
      setIsLoadingAudio(false);
      console.error("Failed to play audio:", error);
      console.error("Audio URL was:", fullAudioUrl);
      console.error("Error details:", error?.message || error);
      
      // Provide more detailed error message
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

  const handlePreviousNext = async (direction: "prev" | "next") => {
    if (isGenerating || isGeneratingRemaining) {
      Alert.alert("故事生成中", "故事正在生成中，請稍候...");
      return;
    }

    // Stop current audio if playing before navigating
    if (sound) {
      await cleanupAudio(sound);
      setSound(null);
      setPlayingAudioIndex(null);
    }
    setIsLoadingAudio(false);

    if (direction === "prev") {
      goToPreviousParagraph();
    } else {
      goToNextParagraph();
    }
  };

  const handleBackToLibrary = async () => {
    // If story is generating, prevent navigation completely
    if (isGenerating || isGeneratingRemaining) {
      Alert.alert(
        "故事生成中",
        "故事正在生成中，請等待生成完成後再離開此頁面。",
        [{ text: "知道了", style: "default" }]
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
                Generating remaining paragraphs... (
                {backendData?.paragraphs_ready || 0}/
                {backendData?.total_paragraphs || 5})
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
                        disabled={isLoadingAudio}
                        opacity={isLoadingAudio ? 0.7 : 1}
                        onPress={() =>
                          handlePlayAudio(
                            currentParagraphIndex,
                            paragraphs[currentParagraphIndex]?.tts_url
                          )
                        }
                      >
                        {isLoadingAudio ? (
                          <XStack gap={8} ai="center">
                            <ActivityIndicator size="small" color="white" />
                            <Text color="white">載入中...</Text>
                          </XStack>
                        ) : playingAudioIndex === currentParagraphIndex ? (
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
                      onPress={() => handlePreviousNext("prev")}
                      disabled={
                        currentParagraphIndex === 0 ||
                        isGenerating ||
                        isGeneratingRemaining
                      }
                      opacity={
                        currentParagraphIndex === 0 ||
                        isGenerating ||
                        isGeneratingRemaining
                          ? 0.5
                          : 1
                      }
                    >
                      上一段
                    </Button>
                    <Text color="#666" fontSize={12}>
                      {currentParagraphIndex + 1} / {paragraphs.length}
                    </Text>
                    <Button
                      onPress={() => handlePreviousNext("next")}
                      disabled={
                        currentParagraphIndex >= paragraphs.length - 1 ||
                        isGenerating ||
                        isGeneratingRemaining
                      }
                      opacity={
                        currentParagraphIndex >= paragraphs.length - 1 ||
                        isGenerating ||
                        isGeneratingRemaining
                          ? 0.5
                          : 1
                      }
                    >
                      下一段
                    </Button>
                  </XStack>
                </>
              ) : (
                <Text color="#404040" mt={8} style={{ textAlign: "center" }}>
                  {backendData.body ||
                    "Press 'Generate Story' to create your adventure!"}
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
