import AsyncStorage from '@react-native-async-storage/async-storage';
import { Story } from '../types/Story';

const STORIES_KEY = 'adventure_cube_stories';
const CURRENT_STORY_KEY = 'adventure_cube_current_story';

export class StorageManager {
  static async getStories(): Promise<Story[]> {
    try {
      const storiesJson = await AsyncStorage.getItem(STORIES_KEY);
      if (!storiesJson) return [];

      const storiesData = JSON.parse(storiesJson);
      return storiesData.map((data: any) => Story.fromJSON(data));
    } catch (error) {
      console.error('Failed to get stories from storage:', error);
      return [];
    }
  }

  static async saveStories(stories: Story[]): Promise<void> {
    try {
      const storiesJson = JSON.stringify(stories.map(story => story.toJSON()));
      await AsyncStorage.setItem(STORIES_KEY, storiesJson);
    } catch (error) {
      console.error('Failed to save stories to storage:', error);
      throw error;
    }
  }

  static async addStory(story: Story): Promise<void> {
    try {
      const stories = await this.getStories();
      stories.push(story);
      await this.saveStories(stories);
    } catch (error) {
      console.error('Failed to add story to storage:', error);
      throw error;
    }
  }

  static async updateStory(updatedStory: Story): Promise<void> {
    try {
      const stories = await this.getStories();
      const index = stories.findIndex(story => story.id === updatedStory.id);

      if (index !== -1) {
        stories[index] = updatedStory;
        await this.saveStories(stories);
      } else {
        throw new Error(`Story with id ${updatedStory.id} not found`);
      }
    } catch (error) {
      console.error('Failed to update story in storage:', error);
      throw error;
    }
  }

  static async deleteStory(storyId: string): Promise<void> {
    try {
      const stories = await this.getStories();
      const filteredStories = stories.filter(story => story.id !== storyId);
      await this.saveStories(filteredStories);
    } catch (error) {
      console.error('Failed to delete story from storage:', error);
      throw error;
    }
  }

  static async getCurrentStory(): Promise<Story | null> {
    try {
      const currentStoryJson = await AsyncStorage.getItem(CURRENT_STORY_KEY);
      if (!currentStoryJson) return null;

      const storyData = JSON.parse(currentStoryJson);
      return Story.fromJSON(storyData);
    } catch (error) {
      console.error('Failed to get current story from storage:', error);
      return null;
    }
  }

  static async setCurrentStory(story: Story): Promise<void> {
    try {
      const storyJson = JSON.stringify(story.toJSON());
      await AsyncStorage.setItem(CURRENT_STORY_KEY, storyJson);
    } catch (error) {
      console.error('Failed to set current story in storage:', error);
      throw error;
    }
  }

  static async clearCurrentStory(): Promise<void> {
    try {
      await AsyncStorage.removeItem(CURRENT_STORY_KEY);
    } catch (error) {
      console.error('Failed to clear current story from storage:', error);
      throw error;
    }
  }
}