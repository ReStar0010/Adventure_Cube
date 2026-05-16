# Adventure Cube

Adventure Cube is a children's storytelling app that lets kids customize characters, backgrounds, and themes to generate personalized stories with audio narration. The project is split into two independent parts:

| Part | Location | Purpose |
|---|---|---|
| **App** | `adventure-cube/` + `server/` | The live mobile app + REST API |
| **Story Generation** | `story_generation/` + `server/stories/*.py` | Offline pipeline for batch-creating story content |

---

## Part 1: The App

The app has two layers that talk to each other over HTTP:

```
[adventure-cube/]        [server/]
React Native (Expo)  ←→  Django REST API  ←→  SQLite DB
iOS / Android app        story API              stories & audio
```

### Frontend — `adventure-cube/`

A React Native + Expo app (TypeScript).

| Directory | What it is |
|---|---|
| `app/(tabs)/` | Screens: home, story creation, library, view story |
| `services/` | HTTP client + API calls (api.client.ts, story.service.ts) |
| `hooks/` | React state hooks for story & audio generation |
| `components/` | Reusable UI components |
| `assets/images/` | Character, background, theme, and key item images |

**Run the frontend:**
```bash
cd adventure-cube
npm install          # first time only
npx expo start
# press i for iOS simulator, a for Android emulator
# or scan QR code with Expo Go on a real device
```

**Configure the backend URL** in [adventure-cube/services/api.config.ts](adventure-cube/services/api.config.ts):
```typescript
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8000/api',   // iOS simulator
  // BASE_URL: 'http://10.0.2.2:8000/api', // Android emulator
  // BASE_URL: 'http://192.168.x.x:8000/api', // real device (use your machine's IP)
};
```

### Backend — `server/`

A Django REST Framework API (Python).

| Directory / File | What it is |
|---|---|
| `config/settings.py` | Django config: DB, CORS, TTS provider, etc. |
| `stories/models.py` | Database schema (Story, AudioFile) |
| `stories/views.py` | API endpoints |
| `stories/story_generator.py` | Template-based story generation (used at runtime) |
| `stories/tts_service.py` | Text-to-speech (gTTS / Azure / Vertex AI) |
| `stories/stories_*/` | Pre-generated story `.txt` files served by the API |
| `manage.py` | Django CLI entry point |
| `requirements.txt` | Python dependencies |

**Run the backend:**
```bash
cd server
python -m venv venv
source venv/bin/activate          # Mac/Linux
# or: .\venv\Scripts\Activate.ps1  # Windows

pip install -r requirements.txt
python manage.py migrate          # first time only
python manage.py runserver 0.0.0.0:8000
```

Server runs at `http://localhost:8000`. Admin UI at `http://localhost:8000/admin/`.

**Environment variables** — create `server/.env`:
```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True

# TTS provider: gtts | azure | vertex_ai | openai | elevenlabs
TTS_PROVIDER=gtts
AZURE_SPEECH_KEY=...
AZURE_SPEECH_REGION=eastus
GOOGLE_APPLICATION_CREDENTIALS=/path/to/creds.json
```

**Key API endpoints:**

| Method | Path | Description |
|---|---|---|
| POST | `/api/stories/generate/` | Generate a new story |
| GET | `/api/stories/` | List all saved stories |
| GET | `/api/stories/{id}/` | Get a specific story |
| DELETE | `/api/stories/{id}/` | Delete a story |
| POST | `/api/tts/generate/` | Generate audio for a story |
| GET | `/api/images/` | List available images |

See [server/README.md](server/README.md) for full API documentation.

---

## Part 2: Story Generation Pipeline

This is an **offline content-creation pipeline** — run once to batch-generate story text files and audio files. The output is stored in `server/stories/stories_*/` (picked up automatically by the Django app) and `story_generation/tts_scripts/audio_*/`.

```
[Gemini AI]
     ↓
short_story_generator.py        → stories_adventure_comedy_2/  *.txt
science_social_generator.py     → stories_Science_Social/      *.txt
     ↓
story_filter.py (clean text)
     ↓
[Azure TTS / Google TTS]
     ↓
tts_azure_tuned.py / tts_scripts/  → audio_*/  *.wav
```

See **[story_generation/README.md](story_generation/README.md)** for the full pipeline walkthrough.

---

## Project Structure

```
Adventure_Cube/
├── adventure-cube/            # Part 1 — React Native frontend
│   ├── app/(tabs)/            #   Screens
│   ├── services/              #   API client
│   ├── hooks/                 #   State hooks
│   └── assets/                #   Images
│
├── server/                    # Part 1 — Django backend
│   ├── config/                #   Django settings & URLs
│   ├── stories/               #   Main Django app
│   │   ├── models.py          #     DB models
│   │   ├── views.py           #     API endpoints
│   │   ├── story_generator.py #     Runtime story generation
│   │   ├── tts_service.py     #     TTS service
│   │   ├── short_story_generator.py   # [Pipeline] batch story gen
│   │   ├── science_social_generator.py# [Pipeline] batch story gen
│   │   ├── story_filter.py    #     [Pipeline] story cleaner
│   │   ├── prompt_0105/       #     Prompt templates & config JSONs
│   │   ├── stories_Nature/           # 296 Nature story .txt files
│   │   ├── stories_Nature_2/         # 154 Nature story .txt files
│   │   ├── stories_adventure_comedy/ # 36 Adventure Comedy .txt files
│   │   ├── stories_Sharing_2/        # 82 Sharing .txt files
│   │   └── stories_Science_Social/   # 20 Science & Social .txt files
│   ├── manage.py
│   └── requirements.txt
│
└── story_generation/          # Part 2 — Content generation tools
    ├── tts_azure_tuned.py     #   Single-story Azure TTS test
    ├── tts_exp.py             #   TTS experimentation script
    ├── audio_generator.py     #   Full story+audio generator (uses Django)
    ├── tts_scripts/           #   Batch TTS scripts & output audio
    ├── tts_tests/             #   TTS speed & quality tests
    ├── context_engineering/   #   Prompt engineering notes
    └── AZURE_TTS_SETUP.md     #   Azure TTS credential guide
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Mobile app | React Native, Expo, TypeScript, Tamagui |
| Backend API | Django 4.x, Django REST Framework, SQLite |
| Story AI | Google Gemini (batch generation) |
| TTS | Azure Cognitive Services / Google Vertex AI / gTTS |
