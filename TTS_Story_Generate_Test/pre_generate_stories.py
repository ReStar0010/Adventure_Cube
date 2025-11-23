#!/usr/bin/env python3
"""
Script to pre-generate stories from CSV prompts and save them for later use.
This allows test_TTS_speed.py to reuse stories without regenerating them.
"""

import csv
import sys
import re
import time
import json
from pathlib import Path
from typing import List, Dict, Tuple

# Try to import required libraries
HAS_GEMINI = False

def check_dependencies():
    """Check and import required dependencies."""
    global HAS_GEMINI, genai
    
    try:
        import google.generativeai as genai
        HAS_GEMINI = True
    except ImportError:
        print("❌ Error: google-generativeai not installed. Install with: pip install google-generativeai")
        sys.exit(1)


def clean_html_tags(text):
    """Convert HTML tags to plain text formatting."""
    if not text:
        return ''
    text = re.sub(r'<br>\s*<br>', '\n\n', text)
    text = re.sub(r'<br>', '\n', text)
    return text.strip()


def count_words_chinese(text: str) -> int:
    """Count words/characters in text, handling both Chinese and English."""
    if not text:
        return 0
    
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    
    if chinese_chars > english_words * 2:
        return chinese_chars + english_words
    elif english_words > chinese_chars * 2:
        return english_words
    else:
        return chinese_chars + english_words


def format_prompt_for_agent(row, clean_html=True):
    """Format a CSV row into context-engineering prompt format."""
    meta_instruction_prompt = row.get('Meta_Instruction_Prompt', '')
    prompt_instruction = row.get('', '') or row.get('Prompt_Instruction', '')
    
    if clean_html:
        meta_instruction_prompt = clean_html_tags(meta_instruction_prompt)
        prompt_instruction = clean_html_tags(prompt_instruction)
    
    formatted_prompt = f"""# system_prompt
{meta_instruction_prompt}

# user_prompt
{prompt_instruction}
"""
    
    return formatted_prompt


def fetch_latest_n_rows(csv_path: Path, n: int = 10) -> List[Dict]:
    """Fetch the latest N rows from CSV."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return rows[-n:] if len(rows) >= n else rows


def load_credentials(credential_path: Path) -> Dict:
    """Load API credentials from JSON file."""
    with open(credential_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_story_with_gemini(prompt: str, api_key: str, min_words: int = 1500) -> Tuple[str, float]:
    """Generate a story using Gemini API and measure the time."""
    if not HAS_GEMINI:
        check_dependencies()
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        enhanced_prompt = f"""{prompt}

**重要要求 (Important Requirement):**
請確保生成的故事內容至少包含 {min_words} 個字詞。故事應該詳細、豐富且完整。
Please ensure the generated story contains at least {min_words} words. The story should be detailed, rich, and complete.

**關於提示中的佔位符 (About Placeholders in the Prompt):**
如果提示中包含佔位符（如 [角色1], [角色2], [場景], [小道具] 等），請自行創建合適的角色名稱、場景描述和道具，並將這些佔位符替換為具體的內容。你可以自由發揮創意，選擇符合故事主題的角色、場景和道具。
If the prompt contains placeholders (such as [角色1], [角色2], [場景], [小道具], etc.), please create appropriate character names, scene descriptions, and props yourself, and replace these placeholders with specific content. You can freely use your creativity to choose characters, scenes, and props that fit the story theme.
"""
        
        start_time = time.time()
        response = model.generate_content(enhanced_prompt)
        end_time = time.time()
        
        generation_time = end_time - start_time
        generated_text = response.text if response.text else ""
        
        word_count = count_words_chinese(generated_text)
        
        if word_count < min_words:
            print(f"  ⚠️  Note: Generated {word_count} words/characters, less than requested {min_words}.")
        
        return generated_text, generation_time
        
    except Exception as e:
        print(f"❌ Error generating story: {e}")
        return "", 0.0


def save_story(story_data: Dict, stories_dir: Path):
    """Save a single story to a JSON file."""
    # Create filename from phase_id (sanitize for filesystem)
    phase_id = story_data.get('phase_id', f"story_{story_data['index']}")
    safe_phase_id = re.sub(r'[^\w\-_]', '_', phase_id)
    filename = f"{story_data['index']:02d}_{safe_phase_id}.json"
    filepath = stories_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    return filepath


def save_stories_index(stories: List[Dict], stories_dir: Path):
    """Save an index file with metadata about all stories."""
    # Prepare story entries
    story_entries = []
    for s in stories:
        # Sanitize phase_id for filename (extract regex to avoid f-string backslash issue)
        safe_phase_id = re.sub(r'[^\w\-_]', '_', s['phase_id'])
        filename = f"{s['index']:02d}_{safe_phase_id}.json"
        story_entries.append({
            'index': s['index'],
            'phase_id': s['phase_id'],
            'theme': s['theme'],
            'word_count': s['word_count'],
            'text_length': len(s['generated_text']),
            'story_generation_time': s['story_generation_time'],
            'filename': filename
        })
    
    index_data = {
        'total_stories': len(stories),
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'stories': story_entries
    }
    
    index_path = stories_dir / 'index.json'
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    return index_path


def main():
    """Main function."""
    check_dependencies()
    
    # Get script directory
    script_dir = Path(__file__).parent
    
    # File paths
    csv_path = script_dir / '1106_prompt.csv'
    credential_path = script_dir / 'credential.json'
    stories_dir = script_dir / 'generated_stories'
    
    # Check if files exist
    if not csv_path.exists():
        print(f"❌ Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    if not credential_path.exists():
        print(f"❌ Error: Credential file not found at {credential_path}")
        sys.exit(1)
    
    # Create stories directory
    stories_dir.mkdir(exist_ok=True)
    print(f"📁 Stories will be saved to: {stories_dir}\n")
    
    # Load credentials
    print("🔑 Loading credentials...")
    credentials = load_credentials(credential_path)
    
    api_key = credentials.get('googleApiKey', '')
    if not api_key:
        print("❌ Error: Google API key not found in credentials")
        sys.exit(1)
    
    # Fetch latest 10 rows
    print(f"📄 Fetching latest 10 prompts from {csv_path.name}...")
    prompts = fetch_latest_n_rows(csv_path, n=10)
    
    if not prompts:
        print("❌ Error: No prompts found in CSV")
        sys.exit(1)
    
    print(f"✅ Found {len(prompts)} prompts\n")
    
    # Generate stories
    print("📖 Generating stories (minimum 1500 words each)...")
    stories = []
    
    for idx, row in enumerate(prompts, 1):
        phase_id = row.get('Phase_ID', 'N/A')
        theme = row.get('Theme', 'N/A')
        dramatic_structure = row.get('Dramatic_Structure', 'N/A')
        
        print(f"  [{idx}/{len(prompts)}] Generating story for Phase_ID: {phase_id}")
        print(f"      Theme: {theme}, Structure: {dramatic_structure}")
        
        formatted_prompt = format_prompt_for_agent(row)
        generated_text, story_gen_time = generate_story_with_gemini(formatted_prompt, api_key, min_words=1500)
        
        if generated_text:
            word_count = count_words_chinese(generated_text)
            story_data = {
                'index': idx,
                'phase_id': phase_id,
                'theme': theme,
                'dramatic_structure': dramatic_structure,
                'generated_text': generated_text,
                'word_count': word_count,
                'text_length': len(generated_text),
                'story_generation_time': story_gen_time,
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            stories.append(story_data)
            
            # Save individual story file
            filepath = save_story(story_data, stories_dir)
            print(f"    ✅ Generated {word_count} words in {story_gen_time:.2f}s")
            print(f"    💾 Saved to: {filepath.name}")
        else:
            print(f"    ❌ Failed to generate story")
        
        print()
    
    if not stories:
        print("❌ Error: No stories generated")
        sys.exit(1)
    
    # Save index file
    index_path = save_stories_index(stories, stories_dir)
    
    # Print summary
    print(f"\n{'='*80}")
    print("GENERATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total stories generated: {len(stories)}")
    print(f"Stories directory: {stories_dir}")
    print(f"Index file: {index_path.name}")
    print(f"\nStory files:")
    for s in stories:
        print(f"  [{s['index']:2d}] {s['phase_id']:<30} {s['word_count']:>6} words  ({s['story_generation_time']:.2f}s)")
    print(f"{'='*80}\n")
    
    print("✅ Story generation completed successfully!")
    print(f"💡 You can now run test_TTS_speed.py to test TTS without regenerating stories.")


if __name__ == '__main__':
    main()

