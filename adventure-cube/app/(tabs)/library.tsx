import React, { useState, useEffect, useCallback } from "react";
import { TouchableOpacity, Alert, ActivityIndicator } from "react-native";
import {
  Button,
  Card,
  H2,
  H4,
  Image,
  XStack,
  YStack,
  ScrollView,
  Input,
  Dialog,
  Adapt,
  Sheet,
  Text,
} from "tamagui";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter, useFocusEffect } from "expo-router";
import { MoreVertical, Edit2, Trash2, LogOut } from "lucide-react-native";
import { Story } from "../../types/Story";
import { StorageManager } from "../../utils/storage";
import { StoryService, AuthService } from "../../services";
import type { AuthUser } from "../../services";
import { BACKGROUNDS, CHARACTERS, THEMES } from "../../constants/assets";
import type { BackendStory } from "../../services/api.types";

export default function LibraryScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingStory, setEditingStory] = useState<Story | null>(null);
  const [newStoryName, setNewStoryName] = useState("");
  const [createStoryDialogOpen, setCreateStoryDialogOpen] = useState(false);
  const [newStoryTitle, setNewStoryTitle] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    checkAuthentication();
  }, []);

  // Reload stories and check auth every time the screen is focused
  useFocusEffect(
    useCallback(() => {
      checkAuthentication();
    }, [])
  );

  const checkAuthentication = async () => {
    setCheckingAuth(true);
    try {
      // Initialize auth service (restore token from storage)
      await AuthService.initialize();

      const authenticated = await AuthService.isAuthenticated();
      const user = await AuthService.getUser();

      setIsAuthenticated(authenticated);
      setCurrentUser(user);

      if (authenticated) {
        await loadStories();
      } else {
        setLoading(false);
      }
    } catch (error) {
      console.error("Auth check failed:", error);
      setIsAuthenticated(false);
      setCurrentUser(null);
      setLoading(false);
    } finally {
      setCheckingAuth(false);
    }
  };

  const loadStories = async () => {
    try {
      setError(null);
      // Fetch stories from backend API
      const backendStories = await StoryService.getSavedStories();
      console.log("Loaded stories from backend:", backendStories);

      // Convert backend stories to frontend Story objects
      const frontendStories = backendStories.map(
        (backendStory: BackendStory) => {
          // Find matching assets by name
          const background = BACKGROUNDS.find(
            (b) =>
              b.name.toLowerCase() === backendStory.background?.toLowerCase()
          );
          const character = CHARACTERS.find(
            (c) =>
              c.name.toLowerCase() === backendStory.character?.toLowerCase()
          );
          const theme = THEMES.find(
            (t) => t.name.toLowerCase() === backendStory.theme.toLowerCase()
          );

          // Convert to frontend Story object
          return StoryService.backendToFrontend(backendStory, {
            background,
            character,
            theme,
          });
        }
      );

      setStories(frontendStories);
    } catch (err) {
      console.error("Failed to load stories from backend:", err);
      setError(err instanceof Error ? err.message : "Failed to load stories");

      // Fallback to local storage if backend fails
      try {
        const storedStories = await StorageManager.getStories();
        console.log(
          "Loaded stories from local storage (fallback):",
          storedStories
        );
        setStories(storedStories);
        setError("Using offline stories - backend unavailable");
      } catch (fallbackError) {
        console.error("Failed to load stories from storage:", fallbackError);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleNewStory = () => {
    setNewStoryTitle("");
    setCreateStoryDialogOpen(true);
  };

  const handleCreateStory = async () => {
    if (!newStoryTitle.trim()) {
      Alert.alert("Error", "Please enter a story name");
      return;
    }

    try {
      // Clear any existing current story cache before creating new one
      await StorageManager.clearCurrentStory();
      console.log("Cleared old current story cache before creating new story");

      const newStory = new Story(Date.now().toString(), newStoryTitle.trim());

      // Save the new story to the library immediately
      await StorageManager.addStory(newStory);

      // Set as current story for editing
      await StorageManager.setCurrentStory(newStory);

      setCreateStoryDialogOpen(false);
      setNewStoryTitle("");
      router.push("/background");
    } catch (error) {
      console.error("Failed to create new story:", error);
      Alert.alert("Error", "Failed to create new story");
    }
  };

  const handleStoryPress = async (story: Story) => {
    try {
      // Set story as current for viewing
      // Note: This is temporary and will be cleared when user returns to library
      await StorageManager.setCurrentStory(story);
      router.push("/view-story");
    } catch (error) {
      console.error("Failed to select story:", error);
    }
  };

  const handleEditStory = (story: Story) => {
    setEditingStory(story);
    setNewStoryName(story.storyTitle);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!editingStory || !newStoryName.trim()) {
      Alert.alert("Error", "Please enter a valid story name");
      return;
    }

    try {
      // Create a proper Story instance with updated title
      const updatedStory = new Story(
        editingStory.id,
        newStoryName.trim(),
        editingStory.background,
        editingStory.character,
        editingStory.theme,
        editingStory.keyItems
      );
      updatedStory.generatedStory = editingStory.generatedStory;

      await StorageManager.updateStory(updatedStory);

      // Update local state
      setStories(
        stories.map((s) => (s.id === updatedStory.id ? updatedStory : s))
      );

      setEditDialogOpen(false);
      setEditingStory(null);
      setNewStoryName("");
    } catch (error) {
      console.error("Failed to update story:", error);
      Alert.alert("Error", "Failed to update story name");
    }
  };

  const handleDeleteStory = (story: Story) => {
    Alert.alert(
      "Delete Story",
      `Are you sure you want to delete "${story.storyTitle}"?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              // Delete from backend if story has backend ID
              if (story.id && story.id.length > 10) {
                try {
                  await StoryService.deleteStory(story.id);
                } catch (backendError) {
                  console.warn("Backend delete failed, continuing with local delete:", backendError);
                }
              }
              // Delete from local storage
              await StorageManager.deleteStory(story.id);
              setEditDialogOpen(false);
              // Reload stories from backend
              await loadStories();
            } catch (error) {
              console.error("Failed to delete story:", error);
              Alert.alert("Error", "Failed to delete story");
            }
          },
        },
      ]
    );
  };

  const handleLogout = async () => { 
    try {
      await AuthService.logout();
      setIsAuthenticated(false);
      setCurrentUser(null);
      setStories([]);
      // Navigate to welcome page
      router.replace("/welcome");
    } catch (error) {
      console.error('Logout error:', error);
      Alert.alert('Error', 'Failed to logout');
    }
  };

  const renderStoryCard = (story: Story) => (
    <Card key={story.id} bg="white" width="100%">
      <Card.Header>
        <XStack justifyContent="space-between" alignItems="center">
          <TouchableOpacity flex={1} onPress={() => handleStoryPress(story)}>
            <H4 fontWeight="bold" color="#404040">
              {story.storyTitle}
            </H4>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => handleEditStory(story)} padding={8}>
            <MoreVertical color="#666" size={20} />
          </TouchableOpacity>
        </XStack>
      </Card.Header>
      <TouchableOpacity onPress={() => handleStoryPress(story)}>
        <Card.Footer>
          <XStack
            flex={1}
            justifyContent="center"
            alignItems="flex-start"
            gap={12}
          >
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
            {story.keyItems?.length > 0 &&
              story.keyItems.map((item, index) =>
                item?.image && item.name ? (
                  <YStack key={index} items="center" gap={4}>
                    <Image source={item.image} width={40} height={40} />
                    <H4 fontSize={9} color="#666" textAlign="center" width={50}>
                      {item.name}
                    </H4>
                  </YStack>
                ) : null
              )}
          </XStack>
        </Card.Footer>
      </TouchableOpacity>
    </Card>
  );

  // Show loading spinner while checking auth or loading stories
  if (checkingAuth || (loading && stories.length === 0)) {
    return (
      <YStack flex={1} bg="#d9d9d9" justifyContent="center" alignItems="center">
        <ActivityIndicator size="large" color="#5A9FD4" />
        <H4 color="#404040" mt={12}>
          載入中...
        </H4>
      </YStack>
    );
  }

  return (
    <YStack flex={1} bg="#d9d9d9" style={{ paddingTop: insets.top + 10 }}>
      <YStack px={16} pt={20}>
        <XStack justifyContent="space-between" alignItems="center">
          <YStack>
            <H2 color="#404040" fontWeight={"bold"}>
              故事庫
            </H2>
            {currentUser && (
              <H4 color="#666" fontSize={14} mt={4}>
                歡迎，{currentUser.username}
              </H4>
            )}
          </YStack>
          <Button onPress={handleLogout}>
            <LogOut size={16} color="#666" />
            登出
          </Button>
        </XStack>
      </YStack>

      <ScrollView flex={1}>
        <YStack my={20} px={16} gap={20}>
          {loading ? (
            <YStack py={40} items="center" gap={12}>
              <ActivityIndicator size="large" color="#5A9FD4" />
              <H4 color="#404040">Loading stories...</H4>
            </YStack>
          ) : error ? (
            <YStack py={20} items="center" gap={12}>
              <Text color="#c62828" textAlign="center" px={16}>
                {error}
              </Text>
              {stories.length === 0 && (
                <Button onPress={loadStories} bg="#5A9FD4" color="white">
                  Retry
                </Button>
              )}
            </YStack>
          ) : null}

          {!loading && stories.length > 0 ? (
            stories.map(renderStoryCard)
          ) : !loading && !error ? (
            <YStack py={40} items="center">
              <H4 color="#404040">No stories yet. Create your first story!</H4>
            </YStack>
          ) : null}

          <YStack items="center" mt={10}>
            <Button onPress={handleNewStory} bg="#5A9FD4" color="white">
              New Story
            </Button>
          </YStack>
        </YStack>
      </ScrollView>

      {/* Edit Story Dialog */}
      <Dialog modal open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <Adapt when="sm" platform="touch">
          <Sheet animation="medium" zIndex={200000} modal dismissOnSnapToBottom>
            <Sheet.Frame padding="$4" gap="$4">
              <Adapt.Contents />
            </Sheet.Frame>
            <Sheet.Overlay
              animation="lazy"
              enterStyle={{ opacity: 0 }}
              exitStyle={{ opacity: 0 }}
            />
          </Sheet>
        </Adapt>

        <Dialog.Portal>
          <Dialog.Overlay
            key="overlay"
            animation="slow"
            opacity={0.5}
            enterStyle={{ opacity: 0 }}
            exitStyle={{ opacity: 0 }}
          />

          <Dialog.Content
            bordered
            elevate
            key="content"
            animateOnly={["transform", "opacity"]}
            animation={[
              "quicker",
              {
                opacity: {
                  overshootClamping: true,
                },
              },
            ]}
            enterStyle={{ x: 0, y: -20, opacity: 0, scale: 0.9 }}
            exitStyle={{ x: 0, y: 10, opacity: 0, scale: 0.95 }}
            gap="$4"
          >
            <Dialog.Title>Edit Story Name</Dialog.Title>
            <Dialog.Description>
              Enter a new name for your story
            </Dialog.Description>

            <Input
              size="$4"
              value={newStoryName}
              onChangeText={setNewStoryName}
              placeholder="Story name"
              autoFocus
            />

            <XStack alignSelf="flex-end" gap="$4">
              <Dialog.Close displayWhenAdapted asChild>
                <Button theme="alt1" aria-label="Close">
                  Cancel
                </Button>
              </Dialog.Close>
              <Button onPress={handleSaveEdit} theme="active" aria-label="Save">
                Save
              </Button>
              <Button
                onPress={() => editingStory && handleDeleteStory(editingStory)}
                theme="red"
                aria-label="Delete"
              >
                <Trash2 size={16} />
              </Button>
            </XStack>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog>

      {/* Create Story Dialog */}
      <Dialog
        modal
        open={createStoryDialogOpen}
        onOpenChange={setCreateStoryDialogOpen}
      >
        <Adapt when="sm" platform="touch">
          <Sheet animation="medium" zIndex={200000} modal dismissOnSnapToBottom>
            <Sheet.Frame padding="$4" gap="$4">
              <Adapt.Contents />
            </Sheet.Frame>
            <Sheet.Overlay
              animation="lazy"
              enterStyle={{ opacity: 0 }}
              exitStyle={{ opacity: 0 }}
            />
          </Sheet>
        </Adapt>

        <Dialog.Portal>
          <Dialog.Overlay
            key="overlay"
            animation="slow"
            opacity={0.5}
            enterStyle={{ opacity: 0 }}
            exitStyle={{ opacity: 0 }}
          />

          <Dialog.Content
            bordered
            elevate
            key="content"
            animateOnly={["transform", "opacity"]}
            animation={[
              "quicker",
              {
                opacity: {
                  overshootClamping: true,
                },
              },
            ]}
            enterStyle={{ x: 0, y: -20, opacity: 0, scale: 0.9 }}
            exitStyle={{ x: 0, y: 10, opacity: 0, scale: 0.95 }}
            gap="$4"
          >
            <Dialog.Title>Create New Story</Dialog.Title>
            <Dialog.Description>
              Enter a name for your new story
            </Dialog.Description>

            <Input
              size="$4"
              value={newStoryTitle}
              onChangeText={setNewStoryTitle}
              placeholder="Story name"
              autoFocus
            />

            <XStack alignSelf="flex-end" gap="$4">
              <Dialog.Close displayWhenAdapted asChild>
                <Button theme="alt1" aria-label="Close">
                  Cancel
                </Button>
              </Dialog.Close>
              <Button
                onPress={handleCreateStory}
                theme="active"
                aria-label="Create"
              >
                Create
              </Button>
            </XStack>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog>
    </YStack>
  );
}
