# Getting Started

This guide takes you from a fresh clone to a fully running Adventure Cube app. Follow the steps in order.

---

## Prerequisites

Make sure these are installed before you begin:

| Tool | Version | Check |
|---|---|---|
| Python | 3.10 + | `python --version` |
| Node.js | 18 + | `node --version` |
| npm | 9 + | `npm --version` |
| Expo CLI | latest | `npm install -g expo-cli` |
| Expo Go app | latest | Install on your phone from App Store / Google Play |

You will also need:
- A **Google Gemini API key** — get one free at [aistudio.google.com](https://aistudio.google.com)  
  *(Required for AI story generation at runtime)*
- An **Azure Speech key** *(optional — only if you want high-quality TTS voices)*

---

## Part 1: Run the Backend (Django)

All commands below are run from the **`server/`** directory.

### Step 1 — Create a virtual environment

```bash
cd server
python -m venv venv
```

Activate it:
```bash
# Mac / Linux
source venv/bin/activate

# Windows
.\venv\Scripts\Activate.ps1
```

> You should see `(venv)` in your terminal prompt. Re-run the activate command every time you open a new terminal.

### Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Create the `.env` file

Create a file named `.env` inside the `server/` directory:

```env
DJANGO_SECRET_KEY=any-long-random-string-here
DJANGO_DEBUG=True

# AI story generation (required)
GEMINI_API_KEY=your-gemini-api-key-here

# TTS provider — start with gtts (free, no setup needed)
# Switch to azure or vertex_ai for higher quality voices
TTS_PROVIDER=gtts
```

> For Azure TTS setup, see [`story_generation/AZURE_TTS_SETUP.md`](story_generation/AZURE_TTS_SETUP.md).

### Step 4 — Set up the database

```bash
python manage.py migrate
```

This creates `db.sqlite3` with all the required tables.

### Step 5 — Create an admin account

```bash
python manage.py createsuperuser
```

Enter a username, email, and password when prompted. You'll use these to log into the app.

### Step 6 — Start the backend

```bash
python manage.py runserver 0.0.0.0:8000
```

The backend is now running at **`http://localhost:8000`**.

**Verify it works:**
```bash
curl http://localhost:8000/api/themes/
# Should return a JSON list of story themes
```

Or open `http://localhost:8000/admin/` in a browser and log in with your superuser credentials.

---

## Part 2: Run the Frontend (React Native)

Open a **new terminal** for these steps. Keep the backend terminal running.

### Step 1 — Install JavaScript dependencies

```bash
cd adventure-cube
npm install
```

### Step 2 — Configure the backend URL

Open [`adventure-cube/services/api.config.ts`](adventure-cube/services/api.config.ts) and set `BASE_URL`:

```typescript
export const API_CONFIG = {
  // Pick ONE of these based on how you're running the app:

  BASE_URL: 'http://localhost:8000/api',      // iOS Simulator
  // BASE_URL: 'http://10.0.2.2:8000/api',   // Android Emulator
  // BASE_URL: 'http://192.168.x.x:8000/api', // Physical device (use your machine's IP)
};
```

**Finding your machine's IP** (needed for physical devices):
```bash
# Mac
ipconfig getifaddr en0

# Windows
ipconfig   # look for "IPv4 Address"
```

### Step 3 — Start the app

```bash
npx expo start
```

Then:
- Press **`i`** → opens in iOS Simulator
- Press **`a`** → opens in Android Emulator  
- Scan the QR code with **Expo Go** on your phone

---

## Verify Everything Works End-to-End

1. Open the app and log in with the superuser credentials you created in backend Step 5.
2. On the home screen, select a character, background, and theme.
3. Tap **Generate Story** — the backend should return a story within a few seconds.
4. Tap the play button to hear the story read aloud (TTS).

If story generation fails, check the Django terminal for error output.

---

## Project Layout Reference

```
Adventure_Cube/
├── adventure-cube/          ← React Native app (frontend)
├── server/                  ← Django REST API (backend)
└── story_generation/        ← Offline tools for batch story & audio creation
```

For a full architecture overview see [`README.md`](README.md).  
For the story generation pipeline see [`story_generation/README.md`](story_generation/README.md).

---

## Common Problems

### "Network request failed" in the app

The frontend can't reach the backend. Check:
1. The backend is actually running (`python manage.py runserver 0.0.0.0:8000`)
2. `BASE_URL` in `api.config.ts` matches your setup (see the table in Step 2 above)
3. On a physical device, both phone and computer are on the same Wi-Fi network

### "No module named 'rest_framework'" or similar import errors

Dependencies weren't installed, or the virtual environment isn't active:
```bash
source venv/bin/activate   # activate venv first
pip install -r requirements.txt
```

### "django.db.utils.OperationalError: no such table"

The database hasn't been migrated:
```bash
python manage.py migrate
```

### "401 Unauthorized" from the API

The app requires a logged-in user. Make sure you created a superuser (backend Step 5) and logged in through the app login screen.

### Expo: "SDK version mismatch"

```bash
npx expo install --fix
```

### Port 8000 already in use

```bash
python manage.py runserver 0.0.0.0:8001
# Then update BASE_URL in api.config.ts to use port 8001
```

---

## What's Next

| Goal | Where to look |
|---|---|
| Change which TTS voice is used | [`server/TTS_CONFIGURATION_GUIDE.md`](server/TTS_CONFIGURATION_GUIDE.md) |
| Generate more story content (batch) | [`story_generation/README.md`](story_generation/README.md) |
| Add a new API endpoint | [`server/stories/views.py`](server/stories/views.py) |
| Add a new screen to the app | [`adventure-cube/app/(tabs)/`](adventure-cube/app/(tabs)/) |
| Full API reference | [`server/README.md`](server/README.md) |
