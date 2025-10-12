# Adventure Cube Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Native Frontend                        │
│                      (adventure-cube/)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │   UI Layer     │  │  React Hooks   │  │  Services Layer  │  │
│  │                │  │                │  │                  │  │
│  │  • Components  │◄─│  • useStory    │◄─│  • StoryService  │  │
│  │  • Screens     │  │    Generation  │  │  • AssetsService │  │
│  │  • Assets      │  │  • useAudio    │  │  • API Client    │  │
│  └────────────────┘  │    Generation  │  └──────────────────┘  │
│                      └────────────────┘           │             │
│                                                    │             │
└────────────────────────────────────────────────────┼─────────────┘
                                                     │
                                                     │ HTTP/JSON
                                                     │ REST API
                                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Django Backend                              │
│                       (server/)                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     API Endpoints                        │   │
│  │  • POST /api/stories/generate/  - Generate story        │   │
│  │  • GET  /api/stories/           - List stories          │   │
│  │  • POST /api/tts/generate/      - Generate audio        │   │
│  │  • GET  /api/images/            - List images           │   │
│  │  • GET  /api/themes/            - Get themes            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│  ┌─────────────────────────┼──────────────────────────────┐    │
│  │          Business Logic │                              │    │
│  │  ┌──────────────────┐   │   ┌────────────────────┐    │    │
│  │  │ StoryGenerator   │   │   │   TTSService       │    │    │
│  │  │                  │   │   │                    │    │    │
│  │  │ • Templates      │   │   │ • gTTS (default)   │    │    │
│  │  │ • OpenAI (ready) │   │   │ • OpenAI (ready)   │    │    │
│  │  │ • Anthropic      │   │   │ • ElevenLabs       │    │    │
│  │  └──────────────────┘   │   └────────────────────┘    │    │
│  └─────────────────────────┼──────────────────────────────┘    │
│                            │                                     │
│  ┌─────────────────────────▼──────────────────────────────┐    │
│  │                  Database (SQLite)                      │    │
│  │  • stories_story   - Generated stories                 │    │
│  │  • stories_audiofile - Audio narrations                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow: Story Generation

```
User Action (UI)
     │
     ▼
┌────────────────────────┐
│ Component calls hook   │
│ useStoryGeneration()   │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Hook calls service     │
│ StoryService           │
│   .generateStory()     │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Service calls API      │
│ apiClient.fetch()      │
└───────────┬────────────┘
            │
            │ HTTP POST
            │ {theme, child_name, ...}
            ▼
┌────────────────────────┐
│ Django View receives   │
│ StoryViewSet.generate()│
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ StoryGenerator         │
│   .generate_story()    │
│   - Templates OR       │
│   - OpenAI/Anthropic   │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Save to Database       │
│ Story.objects.create() │
└───────────┬────────────┘
            │
            │ JSON Response
            │ {id, title, body, ...}
            ▼
┌────────────────────────┐
│ Service creates        │
│ Story object           │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Hook updates state     │
│ setGeneratedStory()    │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Component re-renders   │
│ Display story to user  │
└────────────────────────┘
```

## Request/Response Examples

### Story Generation

```
Frontend → Backend
────────────────────
POST /api/stories/generate/
{
  "theme": "friendship",
  "child_name": "Emma",
  "child_age": 6,
  "character": "Cat",
  "background": "Forest"
}

Backend → Frontend
────────────────────
200 OK
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Emma and the New Friend",
  "body": "Once upon a time in a magical forest...",
  "theme": "friendship",
  "child_name": "Emma",
  "child_age": 6,
  "model_source": "offline",
  "language": "en",
  "character": "Cat",
  "background": "Forest",
  "created_at": "2025-10-12T10:30:00Z"
}
```

### Audio Generation

```
Frontend → Backend
────────────────────
POST /api/tts/generate/
{
  "story_id": "550e8400-e29b-41d4-a716-446655440000",
  "language": "en"
}

Backend → Frontend
────────────────────
201 Created
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "story": "550e8400-e29b-41d4-a716-446655440000",
  "language": "en",
  "audio_url": "http://localhost:8000/media/audio/story_550e8400.mp3",
  "duration_seconds": 45.2,
  "created_at": "2025-10-12T10:31:00Z"
}
```

## Technology Stack

### Frontend
- **Framework**: React Native 0.81 + Expo
- **UI Library**: Tamagui
- **State Management**: React Hooks
- **HTTP Client**: Fetch API
- **Storage**: AsyncStorage

### Backend
- **Framework**: Django 4.2 + Django REST Framework
- **Database**: SQLite (dev), PostgreSQL (prod ready)
- **Story Generation**: Template-based (current), OpenAI/Anthropic (ready)
- **TTS**: gTTS (current), OpenAI TTS/ElevenLabs (ready)

## File Structure

```
Adventure_Cube/
├── adventure-cube/                      # React Native App
│   ├── app/                            # Expo Router screens
│   │   └── (tabs)/
│   │       ├── index.tsx              # Home
│   │       ├── story.tsx              # Story generation (integrate here)
│   │       ├── library.tsx            # Saved stories
│   │       └── ...
│   ├── services/                       # ⭐ NEW: API Integration
│   │   ├── api.client.ts              # HTTP client
│   │   ├── api.config.ts              # Configuration
│   │   ├── api.types.ts               # TypeScript types
│   │   ├── story.service.ts           # Story service
│   │   ├── assets.service.ts          # Assets service
│   │   └── index.ts                   # Exports
│   ├── hooks/                          # ⭐ NEW: React Hooks
│   │   ├── use-story-generation.ts
│   │   ├── use-audio-generation.ts
│   │   └── ...
│   ├── components/
│   │   └── examples/                   # ⭐ NEW: Example components
│   │       └── StoryGenerationExample.tsx
│   ├── types/
│   │   └── Story.ts                   # Story type definition
│   └── utils/
│       └── test-backend.ts            # ⭐ NEW: Testing utility
│
└── server/                             # Django Backend
    ├── backend/                        # Project config
    │   ├── settings.py                # Settings
    │   └── urls.py                    # URL routing
    ├── stories/                        # Stories app
    │   ├── models.py                  # Story, AudioFile models
    │   ├── views.py                   # API views
    │   ├── serializers.py             # DRF serializers
    │   ├── story_generator.py         # Story generation logic
    │   ├── tts_service.py             # TTS service
    │   └── urls.py                    # App URLs
    ├── manage.py                       # Django CLI
    ├── requirements.txt                # Python deps
    └── README.md                       # Backend docs
```

## Error Handling Flow

```
Component Error Display
        ▲
        │
Hook State (error)
        ▲
        │
Service catches & throws
        ▲
        │
API Client error handling
        ▲
        │
HTTP Response (4xx/5xx)
        ▲
        │
Django Exception Handler
```

## Security Considerations

### Current (Development)
- ✅ CORS enabled for all origins
- ✅ Debug mode on
- ✅ No authentication required
- ✅ Local SQLite database

### Production (TODO)
- [ ] Restrict CORS to specific origins
- [ ] Disable debug mode
- [ ] Add JWT/OAuth authentication
- [ ] Use PostgreSQL
- [ ] Add rate limiting
- [ ] Encrypt sensitive data
- [ ] HTTPS only
