# Backend Integration Guide

## Overview

This guide shows how to integrate the Django backend APIs with your React Native frontend.

## What's Been Created

### 1. API Services (`/services/`)
- **`api.config.ts`** - API configuration and base URLs
- **`api.types.ts`** - TypeScript types matching Django models
- **`api.client.ts`** - HTTP client with error handling
- **`story.service.ts`** - Story generation and management
- **`assets.service.ts`** - Image and theme fetching
- **`index.ts`** - Barrel export for easy imports

### 2. React Hooks (`/hooks/`)
- **`use-story-generation.ts`** - Hook for story generation
- **`use-audio-generation.ts`** - Hook for TTS audio

### 3. Example Component (`/components/examples/`)
- **`StoryGenerationExample.tsx`** - Complete working example

---

## Setup Instructions

### Step 1: Configure Backend URL

Edit `adventure-cube/services/api.config.ts`:

```typescript
export const API_CONFIG = {
  BASE_URL: __DEV__ 
    ? 'http://10.0.2.2:8000/api'  // Android Emulator
    : 'https://your-production-api.com/api',
  
  // For iOS Simulator, use:
  // BASE_URL: 'http://localhost:8000/api'
  
  // For physical device, use your computer's local IP:
  // BASE_URL: 'http://192.168.1.100:8000/api'
};
```

**Finding Your Local IP:**
```powershell
# Windows
ipconfig
# Look for "IPv4 Address" under your active network adapter
```

### Step 2: Start Backend Server

```powershell
cd server
.\venv\Scripts\Activate.ps1
python manage.py runserver 0.0.0.0:8000
```

The `0.0.0.0` makes it accessible from physical devices on your network.

### Step 3: Test Connection

Add to any component:

```typescript
import { apiClient } from '../services';

// Test in useEffect
useEffect(() => {
  apiClient.healthCheck().then(isHealthy => {
    console.log('Backend connection:', isHealthy ? 'OK' : 'Failed');
  });
}, []);
```

---

## Usage Examples

### Example 1: Generate a Story

```typescript
import { useStoryGeneration } from '../hooks/use-story-generation';

function MyComponent() {
  const { isGenerating, error, generatedStory, generateStory } = useStoryGeneration();

  const handleGenerate = async () => {
    await generateStory(
      'My Story Title',
      { name: 'Friendship', image: null },  // theme
      { name: 'Cat', image: null },         // character
      { name: 'Forest', image: null },      // background
      'Emma',                                // child name
      6                                      // child age
    );
  };

  return (
    <View>
      <Button onPress={handleGenerate} disabled={isGenerating}>
        Generate Story
      </Button>
      {error && <Text>Error: {error}</Text>}
      {generatedStory && <Text>{generatedStory.generatedStory}</Text>}
    </View>
  );
}
```

### Example 2: Generate Audio Narration

```typescript
import { useAudioGeneration } from '../hooks/use-audio-generation';

function AudioButton({ storyId }: { storyId: string }) {
  const { isGenerating, audioUrl, generateAudio } = useAudioGeneration();

  return (
    <View>
      <Button onPress={() => generateAudio(storyId)} disabled={isGenerating}>
        Generate Audio
      </Button>
      {audioUrl && <Text>Audio ready: {audioUrl}</Text>}
      {/* You can play the audio using expo-av or react-native-sound */}
    </View>
  );
}
```

### Example 3: Fetch Available Themes

```typescript
import { useEffect, useState } from 'react';
import { AssetsService } from '../services';
import type { Theme } from '../services/api.types';

function ThemeSelector() {
  const [themes, setThemes] = useState<Theme[]>([]);

  useEffect(() => {
    AssetsService.fetchThemes().then(setThemes);
  }, []);

  return (
    <View>
      {themes.map(theme => (
        <Button key={theme.id} title={theme.name} />
      ))}
    </View>
  );
}
```

### Example 4: Direct API Calls

If you don't want to use hooks:

```typescript
import { StoryService } from '../services';

// Generate story
const result = await StoryService.generateStory(
  'Title',
  theme,
  character,
  background,
  'ChildName',
  6
);

// Get saved stories
const stories = await StoryService.getSavedStories();

// Delete story
await StoryService.deleteStory(storyId);
```

---

## Integration with Existing Code

### Update Your Story.ts Class

The `generateStory()` method in your `Story` class can now call the backend:

```typescript
// In types/Story.ts
import { StoryService } from '../services';

export class Story {
  // ... existing code ...

  async generateStory(childName?: string, childAge?: number): Promise<string> {
    try {
      const result = await StoryService.generateStory(
        this.storyTitle,
        this.theme,
        this.character,
        this.background,
        childName,
        childAge
      );
      
      this.generatedStory = result.story.generatedStory;
      return this.generatedStory!;
    } catch (error) {
      console.error('Failed to generate story:', error);
      throw error;
    }
  }
}
```

### Update Your Story Tab Component

In `app/(tabs)/story.tsx`:

```typescript
import { useState } from 'react';
import { useStoryGeneration } from '../../hooks/use-story-generation';

export default function StoryTab() {
  const { isGenerating, error, generatedStory, generateStory } = useStoryGeneration();
  
  // Your existing state for selected assets
  const [selectedTheme, setSelectedTheme] = useState<StoryAsset | null>(null);
  const [selectedCharacter, setSelectedCharacter] = useState<StoryAsset | null>(null);
  const [selectedBackground, setSelectedBackground] = useState<StoryAsset | null>(null);

  const handleGenerateStory = async () => {
    if (!selectedTheme || !selectedCharacter || !selectedBackground) {
      alert('Please select all assets first');
      return;
    }

    await generateStory(
      'My Adventure',
      selectedTheme,
      selectedCharacter,
      selectedBackground
    );
  };

  return (
    <View>
      {/* Your existing UI for selecting assets */}
      
      <Button onPress={handleGenerateStory} disabled={isGenerating}>
        {isGenerating ? 'Generating...' : 'Generate Story'}
      </Button>

      {error && <Text style={{ color: 'red' }}>Error: {error}</Text>}
      
      {generatedStory && (
        <ScrollView>
          <Text>{generatedStory.generatedStory}</Text>
        </ScrollView>
      )}
    </View>
  );
}
```

---

## API Reference

### Available Endpoints

| Endpoint                 | Method | Purpose                  |
| ------------------------ | ------ | ------------------------ |
| `/api/stories/generate/` | POST   | Generate a new story     |
| `/api/stories/`          | GET    | List all saved stories   |
| `/api/stories/{id}/`     | GET    | Get specific story       |
| `/api/stories/{id}/`     | DELETE | Delete a story           |
| `/api/tts/generate/`     | POST   | Generate audio narration |
| `/api/images/`           | GET    | List available images    |
| `/api/themes/`           | GET    | List available themes    |

### Request/Response Examples

**Generate Story:**
```typescript
// Request
{
  "theme": "friendship",
  "child_name": "Emma",
  "child_age": 6,
  "character": "Cat",
  "background": "Forest"
}

// Response
{
  "id": "uuid",
  "title": "Emma and the New Friend",
  "body": "Once upon a time...",
  "theme": "friendship",
  "model_source": "offline",
  "created_at": "2025-10-12T..."
}
```

**Generate Audio:**
```typescript
// Request
{
  "story_id": "uuid",
  "language": "en"
}

// Response
{
  "id": "uuid",
  "audio_url": "http://localhost:8000/media/audio/story_uuid.mp3",
  "duration_seconds": 45.2
}
```

---

## Troubleshooting

### Issue: "Network request failed"

**Solutions:**
1. Make sure backend is running: `python manage.py runserver 0.0.0.0:8000`
2. Check firewall settings
3. For Android Emulator, use `10.0.2.2:8000`
4. For iOS Simulator, use `localhost:8000`
5. For physical device, use your computer's local IP

### Issue: "Connection timeout"

**Solutions:**
1. Increase timeout in `api.config.ts`:
   ```typescript
   TIMEOUT: 60000, // 60 seconds
   ```
2. Check if backend is slow (story generation can take 5-10 seconds)

### Issue: CORS errors (web only)

Backend already has CORS enabled with `django-cors-headers`. If issues persist:

```python
# server/backend/settings.py
CORS_ALLOW_ALL_ORIGINS = True  # For development
```

### Issue: "No such table" errors

Run migrations:
```powershell
cd server
python manage.py makemigrations stories
python manage.py migrate
```

---

## Testing

### Test Backend Connection

```typescript
import { apiClient } from './services';

// In a component or useEffect
apiClient.healthCheck().then(isHealthy => {
  if (isHealthy) {
    console.log('✅ Backend is reachable');
  } else {
    console.log('❌ Cannot reach backend');
  }
});
```

### Test Story Generation

```typescript
import { StoryService } from './services';

const testGeneration = async () => {
  try {
    const result = await StoryService.generateStory(
      'Test Story',
      { name: 'Friendship', image: null },
      { name: 'Cat', image: null },
      { name: 'Forest', image: null },
      'Test Child',
      5
    );
    console.log('✅ Story generated:', result.story.generatedStory);
  } catch (error) {
    console.error('❌ Generation failed:', error);
  }
};
```

---

## Next Steps

1. **Replace placeholder assets** - Update your asset selection components to use real images
2. **Add audio playback** - Use `expo-av` to play generated audio files
3. **Implement story saving** - Save favorite stories locally with AsyncStorage
4. **Add loading states** - Show skeleton screens during generation
5. **Error handling** - Add retry buttons and user-friendly error messages
6. **Offline support** - Cache generated stories for offline viewing

---

## Production Checklist

Before deploying to production:

- [ ] Update `API_CONFIG.BASE_URL` with production URL
- [ ] Enable LLM integration (OpenAI/Anthropic)
- [ ] Set up proper error tracking (Sentry, etc.)
- [ ] Add request rate limiting
- [ ] Implement authentication if needed
- [ ] Test on both iOS and Android devices
- [ ] Add loading indicators for all async operations
- [ ] Handle network errors gracefully
- [ ] Add retry logic for failed requests
- [ ] Test with slow network conditions

---

## Support

If you encounter issues:
1. Check backend logs: `python manage.py runserver`
2. Check React Native logs: `npx expo start`
3. Test API directly: Use `server/test_api.py` or Postman
4. Review this guide's troubleshooting section
