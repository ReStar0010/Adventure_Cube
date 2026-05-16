# Adventure Cube — Frontend

React Native + Expo mobile app (iOS & Android). This is Part 1 of the Adventure Cube project — the user-facing app. It communicates with the Django backend (`../server/`) via HTTP.

---

## Quick Start

```bash
npm install
npx expo start
# Press i → iOS Simulator
# Press a → Android Emulator
# Scan QR → Expo Go on a real device
```

**Required:** Node.js 18+, Expo CLI (`npm install -g expo-cli`)

---

## Project Structure

```
adventure-cube/
├── app/
│   ├── _layout.tsx          # Root navigation layout
│   ├── login.tsx            # Login screen
│   ├── welcome.tsx          # Welcome / onboarding screen
│   └── (tabs)/              # Tab-based navigation
│       ├── _layout.tsx      # Tab bar configuration
│       ├── index.tsx        # Home screen
│       ├── story.tsx        # Story creation (select options + generate)
│       ├── library.tsx      # Saved stories list
│       ├── view-story.tsx   # Read a story / play audio
│       ├── character.tsx    # Character selection screen
│       ├── background.tsx   # Background selection screen
│       ├── theme.tsx        # Theme selection screen
│       ├── keyItems.tsx     # Key item selection screen
│       └── confirm-story.tsx# Confirmation before generating
│
├── services/
│   ├── api.config.ts        # Backend URL configuration
│   ├── api.client.ts        # HTTP client (all API calls go through here)
│   ├── api.types.ts         # TypeScript types matching Django models
│   ├── story.service.ts     # Story CRUD and generation
│   ├── assets.service.ts    # Fetch images / themes from backend
│   └── index.ts             # Barrel export
│
├── hooks/
│   ├── use-story-generation.ts  # Manages story generation state
│   └── use-audio-generation.ts  # Manages TTS audio state
│
├── components/              # Reusable UI components
├── types/                   # Shared TypeScript types
├── utils/
│   └── storage.ts           # AsyncStorage helpers
└── assets/images/           # App images
    ├── Characters/           # Character images
    ├── Background/           # Background images
    ├── Theme/                # Theme images
    ├── Key Items/            # Key item images
    └── Login/                # Login screen assets
```

---

## Connecting to the Backend

Edit [services/api.config.ts](services/api.config.ts):

```typescript
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8000/api',       // iOS Simulator
  // BASE_URL: 'http://10.0.2.2:8000/api',    // Android Emulator
  // BASE_URL: 'http://192.168.x.x:8000/api', // Physical device
};
```

For a physical device, use your computer's local IP address. Find it with:
```bash
# Mac
ipconfig getifaddr en0
# Windows
ipconfig | findstr IPv4
```

---

## User Flow

```
Login → Home → Select Character
                     ↓
               Select Background
                     ↓
               Select Theme + Key Items
                     ↓
               Confirm Story → Generate (API call)
                     ↓
               View Story (read text + play audio)
                     ↓
               Library (browse past stories)
```

---

## Tech Stack

| Library | Purpose |
|---|---|
| React Native + Expo | Cross-platform mobile app |
| Expo Router | File-based navigation |
| TypeScript | Type safety |
| Tamagui | UI component library |
| AsyncStorage | Local data persistence |

---

## Troubleshooting

**"Network request failed"**
- Make sure the Django backend is running (`python manage.py runserver 0.0.0.0:8000`)
- Check the `BASE_URL` in `api.config.ts` matches your setup
- On Android Emulator, use `10.0.2.2` instead of `localhost`

**"Module not found"**
```bash
npm install
npx expo install  # sync Expo SDK versions
```

**Expo Go version mismatch**
```bash
npx expo install --fix
```
