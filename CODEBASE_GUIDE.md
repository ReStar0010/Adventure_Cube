# Adventure Cube Codebase Guide 📚

**A comprehensive guide to understanding how this codebase works**

---

## 🎯 What is Adventure Cube?

Adventure Cube is a **children's storytelling app** that:
- 🎨 Lets kids customize their story (characters, backgrounds, themes)
- 🤖 Generates personalized stories using AI
- 🔊 Creates audio narration (text-to-speech)
- 📚 Saves stories in a library

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│               MOBILE APP (React Native)               │
│              User sees and interacts here             │
└────────────────────┬─────────────────────────────────┘
                     │
                     │ HTTP Requests (JSON)
                     │
┌────────────────────▼─────────────────────────────────┐
│              BACKEND SERVER (Django)                  │
│         Generates stories & audio files               │
└────────────────────┬─────────────────────────────────┘
                     │
                     │
┌────────────────────▼─────────────────────────────────┐
│             DATABASE (SQLite)                         │
│         Stores generated stories & audio              │
└──────────────────────────────────────────────────────┘
```

---

## 📱 FRONTEND: React Native App

### Location
```
Adventure_Cube/adventure-cube/
```

### What It Does
The frontend is what **users see and interact with**. It's a mobile app built with React Native (runs on both iOS and Android).

### Key Structure

```
adventure-cube/
├── app/                    # 📱 SCREENS (what users see)
│   └── (tabs)/            
│       ├── index.tsx       # Home screen
│       ├── story.tsx       # Story creation screen
│       ├── library.tsx     # Saved stories
│       ├── character.tsx   # Choose character
│       ├── background.tsx  # Choose background
│       ├── theme.tsx       # Choose theme
│       └── view-story.tsx  # Read a story
│
├── services/              # 🔌 API CONNECTION (talks to backend)
│   ├── api.client.ts      # HTTP requests handler
│   ├── api.config.ts      # Backend URL configuration
│   ├── story.service.ts   # Story-specific API calls
│   └── assets.service.ts  # Image fetching
│
├── hooks/                 # 🎣 REACT HOOKS (business logic)
│   ├── use-story-generation.ts  # Generate story logic
│   └── use-audio-generation.ts  # Generate audio logic
│
├── components/            # 🧩 REUSABLE UI PARTS
│   ├── themed-text.tsx    # Styled text
│   └── examples/
│       └── StoryGenerationExample.tsx  # Working example
│
├── types/                 # 📝 TYPE DEFINITIONS
│   └── Story.ts           # What a Story object looks like
│
└── assets/                # 🎨 IMAGES & RESOURCES
    └── images/
        ├── Characters/    # Character images
        ├── Background/    # Background images
        ├── Theme/         # Theme images
        └── Key Items/     # Story prop images
```

### How Frontend Works (User Flow)

```
1. User opens app
   ↓
2. User selects: character, background, theme
   ↓
3. User clicks "Generate Story"
   ↓
4. Frontend calls hook: useStoryGeneration()
   ↓
5. Hook calls service: StoryService.generateStory()
   ↓
6. Service sends HTTP request to backend
   ↓
7. Backend responds with story text
   ↓
8. Service returns story to hook
   ↓
9. Hook updates UI state
   ↓
10. User sees the generated story! 🎉
```

### Key Frontend Files Explained

#### 1. **`app/(tabs)/story.tsx`** - Story Creation Screen
Where users create stories by selecting options.

#### 2. **`services/api.client.ts`** - API Client
```typescript
// Handles ALL communication with backend
// Example: Making a request
const response = await fetch('http://backend-url/api/stories/generate/', {
  method: 'POST',
  body: JSON.stringify({ theme: 'friendship', child_name: 'Emma' })
});
```

#### 3. **`hooks/use-story-generation.ts`** - Story Generation Hook
```typescript
// React hook that manages story generation state
const { isGenerating, generatedStory, generateStory } = useStoryGeneration();

// When user clicks "Generate"
await generateStory(title, theme, character, background);
```

#### 4. **`types/Story.ts`** - Story Type Definition
```typescript
// Defines what a Story looks like in TypeScript
class Story {
  id: string;
  title: string;
  generatedStory: string;
  theme: StoryAsset;
  character: StoryAsset;
  // ... more fields
}
```

---

## 🖥️ BACKEND: Django Server

### Location
```
Adventure_Cube/server/
```

### What It Does
The backend is a **REST API server** that:
- Generates stories (using templates or AI)
- Creates audio narration
- Stores stories in database
- Serves story data to frontend

### Key Structure

```
server/
├── config/                # ⚙️ DJANGO SETTINGS
│   ├── settings.py        # Main configuration
│   └── urls.py            # API route definitions
│
├── stories/               # 📖 MAIN APP (the core logic)
│   ├── models.py          # Database structure
│   ├── views.py           # API endpoints (handles requests)
│   ├── serializers.py     # Data validation & formatting
│   ├── story_generator.py # Story generation logic
│   ├── tts_service.py     # Text-to-speech service
│   └── urls.py            # App-specific routes
│
├── manage.py              # Django command-line tool
└── requirements.txt       # Python package dependencies
```

### How Backend Works (Request Flow)

```
1. Frontend sends HTTP request to /api/stories/generate/
   ↓
2. Django routes request to views.py → generate()
   ↓
3. views.py validates request data
   ↓
4. views.py calls StoryGenerator.generate_story()
   ↓
5. StoryGenerator creates story text
   ↓
6. Story is saved to database (models.py)
   ↓
7. views.py formats response (serializers.py)
   ↓
8. Backend sends JSON response back to frontend
```

### Key Backend Files Explained

#### 1. **`stories/models.py`** - Database Models
```python
# Defines what data we store in the database

class Story(models.Model):
    id = UUIDField()
    title = CharField()
    body = TextField()  # The actual story text
    theme = CharField()
    child_name = CharField()
    child_age = IntegerField()
    # ... more fields

class AudioFile(models.Model):
    story = ForeignKey(Story)  # Links to a Story
    audio_file = FileField()
    language = CharField()
    # ... more fields
```

#### 2. **`stories/views.py`** - API Endpoints
```python
# Handles all HTTP requests from frontend

@action(detail=False, methods=['post'])
def generate(self, request):
    """Generate a new story"""
    # 1. Validate request
    # 2. Generate story
    # 3. Save to database
    # 4. Return response
```

**Available Endpoints:**
- `POST /api/stories/generate/` - Generate new story
- `GET /api/stories/` - List all stories
- `GET /api/stories/{id}/` - Get specific story
- `DELETE /api/stories/{id}/` - Delete story
- `POST /api/tts/generate/` - Generate audio
- `GET /api/images/` - List available images
- `GET /api/themes/` - List themes

#### 3. **`stories/story_generator.py`** - Story Generator
```python
# Creates the actual story content

def generate_story(theme, child_name, child_age):
    # Option 1: Use templates (current, fast, free)
    story = template.format(name=child_name)
    
    # Option 2: Use AI (OpenAI/Anthropic, better quality)
    # story = openai.generate(prompt)
    
    return story
```

#### 4. **`stories/serializers.py`** - Data Validation
```python
# Validates and formats data between frontend and backend

class StoryGenerateRequestSerializer(serializers.Serializer):
    theme = serializers.CharField(required=True)
    child_name = serializers.CharField(required=False)
    child_age = serializers.IntegerField(required=False)
    # Ensures data is valid before processing
```

---

## 🔄 How Frontend & Backend Work Together

### Example: Generating a Story

**Step-by-step flow:**

```
┌─────────────────────┐
│ USER CLICKS BUTTON  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│ FRONTEND: app/(tabs)/story.tsx                  │
│                                                  │
│ handleGenerateStory() {                         │
│   const { generateStory } = useStoryGeneration()│
│   await generateStory(...)                      │
│ }                                                │
└──────────┬──────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│ FRONTEND: hooks/use-story-generation.ts         │
│                                                  │
│ const result = await StoryService.generateStory │
│   (title, theme, character, background)         │
└──────────┬──────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│ FRONTEND: services/story.service.ts             │
│                                                  │
│ const backendStory = await apiClient            │
│   .generateStory(request)                       │
└──────────┬──────────────────────────────────────┘
           │
           │ HTTP POST Request
           │ {
           │   "theme": "friendship",
           │   "child_name": "Emma",
           │   "child_age": 6
           │ }
           │
           ▼
┌─────────────────────────────────────────────────┐
│ BACKEND: stories/views.py                       │
│                                                  │
│ def generate(request):                          │
│   generator = StoryGenerator()                  │
│   story_data = generator.generate_story(...)    │
│   story = Story.objects.create(...)             │
│   return Response(story)                        │
└──────────┬──────────────────────────────────────┘
           │
           │ JSON Response
           │ {
           │   "id": "uuid",
           │   "title": "Emma's Adventure",
           │   "body": "Once upon a time...",
           │   "theme": "friendship"
           │ }
           │
           ▼
┌─────────────────────────────────────────────────┐
│ FRONTEND: Hook updates state                    │
│ setGeneratedStory(result.story)                 │
└──────────┬──────────────────────────────────────┘
           │
           ▼
┌─────────────────────┐
│ USER SEES STORY! 🎉 │
└─────────────────────┘
```

---

## 🛠️ Technology Stack

### Frontend (Mobile App)
- **React Native** - Framework for iOS/Android apps
- **Expo** - Development platform for React Native
- **TypeScript** - JavaScript with type safety
- **Tamagui** - UI component library
- **Fetch API** - For HTTP requests

### Backend (Server)
- **Django** - Python web framework
- **Django REST Framework** - API toolkit
- **SQLite** - Database (development)
- **gTTS** - Google Text-to-Speech (free)
- **Python 3.8+**

### Optional Integrations
- **OpenAI** - AI story generation
- **Anthropic Claude** - AI story generation
- **ElevenLabs** - Premium text-to-speech

---

## 📂 Important Configuration Files

### Frontend Configuration

**`services/api.config.ts`** - Backend URL
```typescript
export const API_CONFIG = {
  BASE_URL: 'http://10.0.2.2:8000/api',  // Android Emulator
  // For iOS: 'http://localhost:8000/api'
  // For device: 'http://192.168.1.X:8000/api'
  TIMEOUT: 30000,
};
```

### Backend Configuration

**`server/config/settings.py`** - Django Settings
```python
# Key settings:
ALLOWED_HOSTS = ['*']  # Which domains can access
CORS_ALLOW_ALL_ORIGINS = True  # Allow frontend to connect
DATABASES = {...}  # Database configuration
```

**`server/.env`** (optional) - Environment Variables
```env
DJANGO_SECRET_KEY=your-secret-key
LLM_PROVIDER=template  # or 'openai', 'anthropic'
TTS_PROVIDER=gtts      # or 'openai', 'elevenlabs'
```

---

## 🚀 Quick Start Guide

### Running the Backend

```bash
# 1. Navigate to server directory
cd "Adventure_Cube/server"

# 2. Activate virtual environment
source venv/bin/activate  # Mac/Linux
# or
.\venv\Scripts\Activate.ps1  # Windows

# 3. Start server
python manage.py runserver 0.0.0.0:8000
```

Server runs at: `http://localhost:8000`

### Running the Frontend

```bash
# 1. Navigate to app directory
cd "Adventure_Cube/adventure-cube"

# 2. Install dependencies (first time only)
npm install

# 3. Start app
npx expo start
```

Then press:
- `i` for iOS Simulator
- `a` for Android Emulator
- Scan QR code with Expo Go app on phone

---

## 🧪 Testing Connection

### Test Backend Connection from Frontend

Add this to any component:

```typescript
import { testBackendConnection } from '../utils/test-backend';

// In useEffect or button handler
await testBackendConnection();
```

### Test Backend API Directly

```bash
cd server
python test_api.py
```

---

## 🎓 Understanding Common Tasks

### Task 1: Add a New Screen

**Location**: `adventure-cube/app/(tabs)/new-screen.tsx`

```typescript
import { View, Text } from 'react-native';

export default function NewScreen() {
  return (
    <View>
      <Text>New Screen</Text>
    </View>
  );
}
```

### Task 2: Add a New API Endpoint

**Location**: `server/stories/views.py`

```python
@api_view(['GET'])
@permission_classes([AllowAny])
def my_new_endpoint(request):
    data = {"message": "Hello!"}
    return Response(data)
```

**Add route**: `server/stories/urls.py`

```python
urlpatterns = [
    path('my-endpoint/', views.my_new_endpoint),
]
```

### Task 3: Modify Story Generation

**Location**: `server/stories/story_generator.py`

Edit the `generate_story()` method to change how stories are created.

---

## 📊 Data Flow Diagrams

### Story Creation Flow

```
User Input → Frontend Hook → Service → API Client
                                            ↓
                                    [HTTP REQUEST]
                                            ↓
Backend Views ← URL Router ← Django Server
     ↓
Story Generator
     ↓
Database Save
     ↓
Response
     ↓
[HTTP RESPONSE]
     ↓
Frontend Service → Hook → UI Update → User Sees Story
```

### Audio Generation Flow

```
User clicks "Play" → useAudioGeneration hook
                              ↓
                    POST /api/tts/generate/
                              ↓
                    Backend: tts_service.py
                              ↓
                    Generate MP3 file
                              ↓
                    Save to media/audio/
                              ↓
                    Return audio URL
                              ↓
                    Frontend plays audio
```

---

## 🗂️ Database Structure

### Story Table
```
┌──────────────────────────────────────────────┐
│ stories_story                                 │
├──────────────────────────────────────────────┤
│ id (UUID)                                     │
│ user_id (FK → auth_user)                     │
│ title (VARCHAR)                               │
│ body (TEXT)          ← The actual story      │
│ theme (VARCHAR)                               │
│ child_name (VARCHAR)                          │
│ child_age (INT)                               │
│ character (VARCHAR)                           │
│ background (VARCHAR)                          │
│ key_items (JSON)                              │
│ model_source (VARCHAR)  ← 'template' or 'ai' │
│ language (VARCHAR)                            │
│ created_at (DATETIME)                         │
└──────────────────────────────────────────────┘
```

### AudioFile Table
```
┌──────────────────────────────────────────────┐
│ stories_audiofile                             │
├──────────────────────────────────────────────┤
│ id (UUID)                                     │
│ story_id (FK → stories_story)                │
│ audio_file (FILE)    ← Path to MP3 file      │
│ language (VARCHAR)                            │
│ duration_seconds (FLOAT)                      │
│ created_at (DATETIME)                         │
└──────────────────────────────────────────────┘
```

---

## 🔐 Authentication

### Current Status
- ✅ Backend has authentication endpoints
- ✅ Token-based authentication (Django Token Auth)
- ⚠️ Frontend not yet integrated with auth

### Auth Endpoints
- `POST /api/auth/register/` - Create account
- `POST /api/auth/login/` - Login (get token)
- `POST /api/auth/logout/` - Logout (delete token)

### How Auth Works
```
1. User registers/logs in
   ↓
2. Backend generates auth token
   ↓
3. Frontend stores token
   ↓
4. Frontend includes token in all requests:
   Headers: { Authorization: 'Token abc123...' }
   ↓
5. Backend verifies token and returns user's data
```

---

## 🎯 Key Concepts

### 1. **Services Layer**
Think of services as **translators** between your UI and the backend.
- UI speaks "user language" (buttons, forms)
- Backend speaks "data language" (JSON, HTTP)
- Services translate between them

### 2. **Hooks**
React hooks are **reusable state management**.
- Instead of writing the same loading/error/success logic everywhere
- Write it once in a hook
- Use it anywhere: `const { data, loading } = useMyHook()`

### 3. **API Client**
The API client is your **single point of contact** with the backend.
- All HTTP requests go through it
- Handles errors consistently
- Sets headers, timeouts, etc.

### 4. **Serializers**
Serializers **validate and format** data.
- Frontend sends data → Serializer checks it's valid
- Database data → Serializer formats it for JSON
- Like a security guard and translator combined

---

## 🐛 Common Issues & Solutions

### "Network request failed"
**Problem**: Frontend can't reach backend

**Solutions**:
1. Check backend is running: `python manage.py runserver`
2. Verify URL in `api.config.ts`:
   - Android Emulator: `http://10.0.2.2:8000/api`
   - iOS Simulator: `http://localhost:8000/api`
   - Real Device: `http://YOUR_COMPUTER_IP:8000/api`

### "No such table: stories_story"
**Problem**: Database not set up

**Solution**:
```bash
cd server
python manage.py makemigrations
python manage.py migrate
```

### "Module not found"
**Problem**: Dependencies not installed

**Solutions**:
```bash
# Frontend
cd adventure-cube
npm install

# Backend
cd server
pip install -r requirements.txt
```

---

## 📚 Further Reading

- **ARCHITECTURE.md** - Detailed architecture diagrams
- **INTEGRATION_GUIDE.md** - Integration instructions
- **server/README.md** - Backend API documentation
- **BACKEND_INTEGRATION_COMPLETE.md** - Quick reference

---

## 💡 Pro Tips

1. **Start with Examples**: Check `components/examples/StoryGenerationExample.tsx` to see working code

2. **Use TypeScript**: It catches errors before runtime
   ```typescript
   // TypeScript will warn if you forget a field
   const story: Story = {
     id: '123',
     title: 'My Story',
     // Error: Missing required fields!
   }
   ```

3. **Check Console Logs**: Both frontend and backend log useful info
   - Frontend: React Native debugger
   - Backend: Terminal where Django runs

4. **Test Backend First**: Use `python test_api.py` before connecting frontend

5. **Read Error Messages**: They usually tell you exactly what's wrong!

---

## 🎉 Summary

### Frontend (adventure-cube/)
- **Purpose**: User interface (mobile app)
- **Key Files**: 
  - `app/` - Screens
  - `services/` - API connection
  - `hooks/` - Business logic
- **Tech**: React Native, TypeScript, Expo

### Backend (server/)
- **Purpose**: Generate stories, handle data
- **Key Files**:
  - `stories/views.py` - API endpoints
  - `stories/models.py` - Database
  - `stories/story_generator.py` - Story creation
- **Tech**: Django, Python, SQLite

### They Connect Via:
- HTTP requests (JSON format)
- RESTful API endpoints
- Request/Response cycle

---

**Questions?** Check the other documentation files or examine the code with this guide as reference!

Happy coding! 🚀

