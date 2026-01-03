# Adventure Cube Backend

Django REST API backend for the Adventure Cube children's storytelling app.

## Features

### 1. **Story Generation API** (`/api/stories/generate/`)
- Generates age-appropriate children's stories based on themes
- Currently uses template-based generation (fast, offline, free)
- Ready to integrate with LLM APIs (OpenAI, Anthropic) for production
- Supports 6 educational themes: caring, courage, friendship, honest, nature, share

### 2. **Text-to-Speech API** (`/api/tts/generate/`)
- Converts stories to audio narration
- Uses gTTS (Google Text-to-Speech) by default - free and good quality
- Ready to integrate premium TTS (OpenAI TTS, ElevenLabs) for better voices
- Caches generated audio to avoid regeneration

### 3. **Image Serving API** (`/api/images/`)
- Lists available images (characters, backgrounds, themes, key items)
- Serves image metadata from the frontend assets folder
- Allows client to dynamically fetch available options

## Setup

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Create virtual environment** (recommended):
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Initialize database**:
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create superuser** (for admin access):
   ```powershell
   python manage.py createsuperuser
   ```

5. **Run development server**:
   ```powershell
   python manage.py runserver
   ```

   Server will start at: `http://localhost:8000`

## API Endpoints

### Story Generation

**Generate a new story:**
```http
POST /api/stories/generate/
Content-Type: application/json

{
  "theme": "caring",
  "child_name": "Emma",
  "child_age": 6,
  "language": "en",
  "character": "Princess",
  "background": "Castle"
}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Emma and the Lost Puppy",
  "body": "Once upon a time...",
  "theme": "caring",
  "child_name": "Emma",
  "child_age": 6,
  "model_source": "offline",
  "language": "en",
  "character": "Princess",
  "background": "Castle",
  "created_at": "2025-10-11T12:00:00Z"
}
```

**List saved stories:**
```http
GET /api/stories/
```

**Get a specific story:**
```http
GET /api/stories/{story_id}/
```

**Delete a story:**
```http
DELETE /api/stories/{story_id}/
```

### Text-to-Speech

**Generate audio narration:**
```http
POST /api/tts/generate/
Content-Type: application/json

{
  "story_id": "uuid",
  "language": "en",
  "voice": "nova"
}
```

**Response:**
```json
{
  "id": "uuid",
  "story": "story_uuid",
  "language": "en",
  "audio_url": "http://localhost:8000/media/audio/story_uuid.mp3",
  "duration_seconds": 45.2,
  "created_at": "2025-10-11T12:00:00Z"
}
```

### Images

**List all available images:**
```http
GET /api/images/
```

**Filter by category:**
```http
GET /api/images/?category=characters
```

**Response:**
```json
{
  "characters": [
    {
      "name": "AC-Princess",
      "filename": "AC-Princess.png",
      "path": "/images/Characters/AC-Princess.png",
      "category": "characters"
    }
  ],
  "backgrounds": [...],
  "themes": [...],
  "key_items": [...]
}
```

### Themes

**Get available themes:**
```http
GET /api/themes/
```

**Response:**
```json
{
  "themes": [
    {
      "id": "caring",
      "name": "Caring",
      "description": "Stories about caring",
      "story_count": 2
    }
  ]
}
```

## Configuration

Create a `.env` file in the `server/` directory:

```env
# Django settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True

# LLM Provider (template, openai, anthropic)
LLM_PROVIDER=template
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# TTS Provider (gtts, openai, elevenlabs)
TTS_PROVIDER=gtts
```

### Enabling LLM Integration (Production)

1. **For OpenAI:**
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-...
   ```
   
   Install: `pip install openai`

2. **For Anthropic Claude:**
   ```env
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-...
   ```
   
   Install: `pip install anthropic`

### Enabling Premium TTS

**推薦：使用 Azure 或 Vertex AI 獲得更好的語音品質**

1. **Azure Cognitive Services (推薦):**
   ```env
   TTS_PROVIDER=azure
   AZURE_SPEECH_KEY=your-azure-key
   AZURE_SPEECH_REGION=eastus
   ```
   Install: `pip install azure-cognitiveservices-speech`
   - 高品質神經語音，聽起來更自然
   - 免費額度：每月 50 萬字符
   - 詳細配置請參考 `TTS_CONFIGURATION_GUIDE.md`

2. **Google Vertex AI:**
   ```env
   TTS_PROVIDER=vertex_ai
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
   VERTEX_AI_PROJECT_ID=your-project-id
   VERTEX_AI_LOCATION=us-central1
   ```
   Install: `pip install google-cloud-texttospeech`
   - 高品質 Neural2 語音
   - 免費額度：每月 400 萬字符
   - 詳細配置請參考 `TTS_CONFIGURATION_GUIDE.md`

3. **OpenAI TTS:**
   ```env
   TTS_PROVIDER=openai
   OPENAI_API_KEY=sk-...
   ```

4. **ElevenLabs:**
   ```env
   TTS_PROVIDER=elevenlabs
   ELEVENLABS_API_KEY=...
   ```
   Install: `pip install elevenlabs`

**注意**：默認的 `gTTS` 是免費但品質較低。要獲得更好的語音品質，強烈建議切換到 Azure 或 Vertex AI。

## Database

Uses SQLite by default (`db.sqlite3`). The database stores:
- Generated stories
- Audio files metadata
- Admin users

To reset the database:
```powershell
Remove-Item db.sqlite3
python manage.py migrate
```

## Admin Interface

Access Django admin at: `http://localhost:8000/admin/`

Features:
- View all generated stories
- Manage audio files
- Monitor usage

## Image Serving Approach: Analysis

### Current Implementation
The backend reads image metadata from the frontend's `assets/images/` folder and returns JSON listings to the client.

### ✅ Pros:
1. **Dynamic updates**: New images added to assets are immediately available
2. **Single source of truth**: Assets folder is the definitive image repository
3. **Flexible**: Easy to add new categories or images
4. **Lightweight**: No database storage needed for image metadata

### ⚠️ Cons:
1. **Tight coupling**: Backend depends on frontend folder structure
2. **Performance**: File system reads on every request (can be cached)
3. **Deployment complexity**: Both frontend assets and backend must be deployed together
4. **No versioning**: Client can't specify which version of images to use

### 🎯 Better Approaches:

**Option 1: Static API with versioning** (Recommended for your use case)
- Backend serves a static JSON manifest of images
- Update manifest when assets change
- Add version field for cache busting
- **Pros**: Fast, cacheable, no file system reads
- **Cons**: Manual manifest updates

**Option 2: Dedicated CDN**
- Upload images to cloud storage (S3, Firebase Storage, Cloudinary)
- Backend returns CDN URLs
- **Pros**: Scalable, global delivery, image optimization
- **Cons**: Additional cost, more complex deployment

**Option 3: Bundle with app** (Simplest for now)
- Ship images with the mobile app
- No API needed for images
- **Pros**: Offline-first, fast, simple
- **Cons**: App size increases, requires app update for new images

### 💡 Recommendation:
For your current phase, **keep the current approach** but add:
1. Response caching (Django cache framework)
2. Error handling if assets folder missing
3. Consider bundling images with the app later for offline-first experience

## Testing

### Test story generation:
```powershell
curl -X POST http://localhost:8000/api/stories/generate/ `
  -H "Content-Type: application/json" `
  -d '{\"theme\": \"friendship\", \"child_name\": \"Alex\", \"child_age\": 5}'
```

### Test TTS:
```powershell
# First generate a story, then use its ID:
curl -X POST http://localhost:8000/api/tts/generate/ `
  -H "Content-Type: application/json" `
  -d '{\"story_id\": \"your-story-uuid\"}'
```

### Test image listing:
```powershell
curl http://localhost:8000/api/images/
```

## Project Structure

```
server/
├── backend/                 # Django project settings
│   ├── settings.py         # Configuration
│   ├── urls.py             # Main URL routing
│   └── wsgi.py             # WSGI entry point
├── stories/                # Main app
│   ├── models.py           # Story and AudioFile models
│   ├── views.py            # API endpoints
│   ├── serializers.py      # DRF serializers
│   ├── story_generator.py  # Story generation logic
│   ├── tts_service.py      # Text-to-speech service
│   └── urls.py             # App URL routing
├── manage.py               # Django CLI
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Next Steps

1. ✅ **Current Phase**: Template-based stories + gTTS (working offline, free)
2. 🔜 **Phase 2**: Integrate OpenAI for better story quality
3. 🔜 **Phase 3**: Add premium TTS for more realistic voices
4. 🔜 **Phase 4**: User authentication and story saving per user
5. 🔜 **Phase 5**: Analytics and parental controls

## Troubleshooting

**Import errors for `rest_framework`:**
```powershell
pip install djangorestframework django-cors-headers
```

**gTTS not installed:**
```powershell
pip install gTTS
```

**Port already in use:**
```powershell
python manage.py runserver 8001
```

**Database locked error:**
- Close any other processes accessing `db.sqlite3`
- Delete `db.sqlite3` and run migrations again

## Production Deployment

For production deployment:

1. Set `DJANGO_DEBUG=False`
2. Set strong `DJANGO_SECRET_KEY`
3. Configure `ALLOWED_HOSTS` properly
4. Use PostgreSQL instead of SQLite
5. Set up proper CORS origins (not `CORS_ALLOW_ALL_ORIGINS`)
6. Use gunicorn or similar WSGI server
7. Serve static/media files via nginx or CDN
8. Enable HTTPS
9. Set up environment variables securely

Example production command:
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## License

Part of the Adventure Cube project.
