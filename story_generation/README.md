# Story Generation Pipeline

This directory contains the offline tools for batch-generating story text and audio files used by the Adventure Cube app. This pipeline is **separate from the live app** — you run it once to produce content, then the Django backend serves that pre-generated content.

---

## Pipeline Overview

```
[Gemini AI API]
       │
       ▼
  short_story_generator.py          →  server/stories/stories_*/  *.txt
  science_social_generator.py       →  server/stories/stories_Science_Social/  *.txt
       │
       ▼
  story_filter.py  (clean & verify output)
       │
       ▼
  [Azure TTS / Gemini TTS]
       │
       ▼
  tts_scripts/google_ai_studio_batched.py  →  tts_scripts/audio_*/  *.wav
```

All story generators require a **Gemini API key** (free tier available at Google AI Studio).
All TTS generators require either a **Google Gemini API key** (for Gemini TTS) or an **Azure Speech key**.

---

## Story Types

| Type Code | Name | Generator | Output Folder |
|---|---|---|---|
| `ADV` | Adventure Comedy | `short_story_generator.py` | `server/stories/stories_adventure_comedy_2/` |
| `NAT` | Nature | `short_story_generator.py` | `server/stories/stories_Nature_2/` |
| `SOC` | Sharing/Social | `short_story_generator.py` | `server/stories/stories_Sharing_2/` |
| `SCI` | Science | `science_social_generator.py` | `server/stories/stories_Science_Social/` |
| `NEI` | Social/Neighbor | `science_social_generator.py` | `server/stories/stories_Science_Social/` |

---

## File Naming Convention

### Adventure / Nature / Sharing Stories
```
TYPE_CaaTab_CbbTbb_WwwAaa_Kpp_LANG_Vn.txt

ADV_C01T01_C02T01_W01A01_K01_TW_V1.txt
 │    │  │   │  │  │   │  │   │   │
 │    │  │   │  │  │   │  │   │   └── Version (V1)
 │    │  │   │  │  │   │  │   └────── Language (TW = Traditional Chinese)
 │    │  │   │  │  │   │  └────────── Prop/Key Item (K01, K02)
 │    │  │   │  │  └─────────────────  Location (A01, A02)
 │    │  │   │  └───────────────────── World (W01, W02)
 │    │  │   └──────────────────────── Character B Trait (T01, T02)
 │    │  └──────────────────────────── Character B ID (C02, C03, C04)
 │    └─────────────────────────────── Character A ID + Trait (C01T01)
 └──────────────────────────────────── Story type (ADV / NAT / SOC)
```

### Science / Social Stories
```
TYPE_CHAR_NN_LANG_Vn.txt

SCI_PRI_01_TW_V1.txt
 │    │   │   │   └── Version
 │    │   │   └────── Language
 │    │   └────────── Story number (01–20)
 │    └────────────── Character abbreviation (PRI=Princess, WIZ=Wizard, DRG=Dragon…)
 └─────────────────── Story type (SCI / NEI)
```

Audio files follow the same naming with `.wav` extension.

---

## Step 1: Generate Story Text

### Prerequisites

```bash
pip install google-generativeai
```

Set your Gemini API key inside the generator script (or as an env var):
```python
# At the top of short_story_generator.py and science_social_generator.py:
GEMINI_API_KEY = "your-key-here"
```

### Adventure Comedy / Nature / Sharing Stories

```bash
cd server/stories

# Generate all adventure comedy stories (full set — takes ~30–60 min)
python short_story_generator.py

# Regenerate only the failed/missing stories
python short_story_generator.py --retry-failed
```

The script reads configuration from `server/stories/prompt_0105/`:

| File | Purpose |
|---|---|
| `Character_Personas.json` | Character names, IDs, and personality traits |
| `Location.json` | World and area definitions |
| `Props.json` | Key item (prop) definitions |
| `Funny_incidents.json` | Comedy incident seeds |
| `短篇故事模板.json` | Story structure phases and word limits |
| `Logic.json` | Story logic rules |
| `META_prompt.md` | Master system prompt (Tier 1–4 rules) |
| `prompt_to_follow.md` | Per-story template with placeholders |

Each combination of (character A, trait A, character B, trait B, world, area, prop) produces one story. The full set is:
- 6 character pairs × 4 trait combos × 4 world/area combos × 2 props = **192 stories per type**

### Science / Social Stories

```bash
cd server/stories

# Generate all Science and Social stories (20 each)
python science_social_generator.py
```

Stories are driven by `prompt_0105/Story_Variables.json` which defines 20 combinations of topic, phenomenon, and experiment/action per story type.

---

## Step 2: Filter & Clean Stories

After generation, run the filter to strip metadata headers and normalize formatting:

```bash
cd server/stories
python story_filter.py
```

This removes `[Story Start]` / `[Story End]` markers, setup blocks, and bullet-point metadata, leaving only the clean narrative text that TTS will read.

---

## Step 3: Generate Audio (TTS)

Choose one of the two TTS options:

### Option A: Gemini TTS (Recommended — same API key as story gen)

```bash
pip install google-genai
export GEMINI_API_KEY="your-key-here"

cd story_generation/tts_scripts

# Batch convert a folder of .txt files to .wav
python google_ai_studio_batched.py \
  --input-dir ../path/to/stories_folder \
  --output-dir audio_adventure_comedy_2

# Options:
#   --voice "Puck"              # voice name (default varies)
#   --style "溫暖且友好"          # speaking style
#   --model gemini-2.5-pro-preview-tts
```

Single-file test:
```bash
python google_ai_studio.py --text "從前，在一個遙遠的魔法森林裡..." --output test.wav
```

### Option B: Azure TTS (Higher quality voices)

First, set up Azure credentials (see [AZURE_TTS_SETUP.md](AZURE_TTS_SETUP.md)):
```bash
export AZURE_SPEECH_KEY="your-azure-key"
export AZURE_SPEECH_REGION="eastus"
```

Single-story test:
```bash
python tts_azure_tuned.py \
  --text "故事內容..." \
  --voice zh-TW-HsiaoChenNeural \
  --rate 0.9 \
  --output test.wav
```

Batch TTS:
```bash
pip install azure-cognitiveservices-speech
cd story_generation/tts_scripts
python tts_azure.py  # processes stories from a configured input directory
```

**Azure voice options for Traditional Chinese:**
- `zh-TW-HsiaoChenNeural` — warm female voice (recommended for stories)
- `zh-TW-YunJheNeural` — male voice
- `zh-TW-HsiaoYuNeural` — young female voice

---

## Audio Output

Batch-generated audio is stored in `story_generation/tts_scripts/audio_*/`:

| Folder | Content |
|---|---|
| `audio_adventure_comedy_2/` | ADV story audio (batch 2) |
| `audio_Nature_2/` | NAT story audio (batch 2) |
| `audio_Nature_2-fail/` | NAT files that failed TTS — retry these |
| `audio_Social_Science/` | SCI/NEI story audio |

---

## This Directory: Files & Scripts

| File / Folder | Purpose |
|---|---|
| `tts_azure_tuned.py` | Single-story Azure TTS with parameter tuning |
| `tts_exp.py` | TTS experimentation and comparison script |
| `audio_generator.py` | Integrated story+audio generator (uses Django) |
| `tts_scripts/` | Batch TTS scripts (Google AI Studio, Azure, Vertex AI) |
| `tts_tests/` | Speed and quality benchmark tests |
| `context_engineering/` | Prompt engineering notes and drafts |
| `audio_output/` | Output directory for `audio_generator.py` |
| `AZURE_TTS_SETUP.md` | Step-by-step Azure credential guide |
| `Prompt.md` | High-level prompt design notes |

---

## Story Generation Scripts Location

The actual story generator Python scripts live inside the Django backend because they write output that the Django app reads:

```
server/stories/
├── short_story_generator.py      ← generates ADV / NAT / SOC stories
├── science_social_generator.py   ← generates SCI / NEI stories
├── story_filter.py               ← cleans generated .txt files
├── batch_generate_stories.py     ← simple batch wrapper (older)
├── replace_chinese_terms.py      ← post-processing: normalize Chinese terms
├── prompt_0105/                  ← all prompt templates and JSON config
├── stories_Nature/               ← 296 Nature stories
├── stories_Nature_2/             ← 154 Nature stories (batch 2)
├── stories_adventure_comedy/     ← 36 Adventure Comedy stories
├── stories_Sharing_2/            ← 82 Sharing stories
└── stories_Science_Social/       ← 20 Science & Social stories
```

---

## Quick Reference

```bash
# 1. Generate all adventure comedy stories
cd server/stories && python short_story_generator.py

# 2. Filter/clean the output
python story_filter.py

# 3. Batch TTS with Gemini (run from story_generation/tts_scripts/)
export GEMINI_API_KEY="..."
cd story_generation/tts_scripts
python google_ai_studio_batched.py \
  --input-dir ../../server/stories/stories_adventure_comedy \
  --output-dir audio_adventure_comedy_2
```
