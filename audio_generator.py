#!/usr/bin/env python3
"""
Audio Generator: Generate complete story at once and convert to audio files.
This script generates all 5 paragraphs sequentially, then uses TTS to create audio files.
"""
import os
import sys
import time
from pathlib import Path

# Add server directory to Python path
server_dir = Path(__file__).parent / 'server'
if server_dir.exists():
    sys.path.insert(0, str(server_dir))

# Setup Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from stories.story_generator import StoryGenerator, CHARACTER_PERSONALITIES, CHARACTER_NAMES_ZH, BACKGROUND_NAMES_ZH, THEME_NAMES_ZH, KEY_ITEMS_NAMES_ZH
from stories.tts_service import TTSService
from stories.context_engineering import get_paragraph_type_by_index, StoryStructure, ContextTemplateLoader
import google.generativeai as genai


class AudioGenerator:
    """
    Generates complete story and audio files in one go.
    """

    def __init__(self, output_dir='./audio_output'):
        self.story_generator = StoryGenerator()
        self.tts_service = TTSService()
        self.template_loader = ContextTemplateLoader()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory: {self.output_dir.absolute()}")

    def _translate_to_chinese(self, english_name, mapping_dict, default=None):
        """Translate English name to Chinese using the provided mapping."""
        if not english_name:
            return default or ''
        key = english_name.lower().strip()
        chinese = mapping_dict.get(key)
        if chinese:
            return chinese
        for eng_key, zh_value in mapping_dict.items():
            if eng_key in key or key in eng_key:
                return zh_value
        return default if default is not None else english_name

    def _generate_complete_story_single_call(
        self,
        theme,
        child_name=None,
        child_age=None,
        context_template='1106_prompt',
        **kwargs
    ):
        print("🚀 Generating complete story in a single API call...")
        start_time = time.time()

        # Load template
        template_data = self.template_loader.load_template(context_template)

        # Get story parameters
        name = child_name or "小英雄"
        age = child_age or 5
        age = max(3, min(age, 10))

        character_en = kwargs.get('character', 'an adventurer')
        background_en = kwargs.get('background', 'a magical place')
        key_items_en = kwargs.get('key_items', [])

        # Translate to Chinese
        character_zh = self._translate_to_chinese(character_en, CHARACTER_NAMES_ZH, '冒險家')
        background_zh = self._translate_to_chinese(background_en, BACKGROUND_NAMES_ZH, '魔法之地')
        theme_zh = self._translate_to_chinese(theme, THEME_NAMES_ZH, theme)

        key_items_zh = []
        for item in key_items_en:
            if isinstance(item, str):
                key_items_zh.append(self._translate_to_chinese(item, KEY_ITEMS_NAMES_ZH, item))
            else:
                item_name = item.get('name', item) if isinstance(item, dict) else str(item)
                key_items_zh.append(self._translate_to_chinese(item_name, KEY_ITEMS_NAMES_ZH, item_name))

        items_text = "、".join(key_items_zh) if key_items_zh else "沒有特殊道具"

        # Get personality traits
        char_key = character_en.lower().strip() if character_en else ''
        personalities = CHARACTER_PERSONALITIES.get(char_key, [])
        personality_text = f"角色性格特質：{'、'.join(personalities)}" if personalities else ""

        # Get paragraph count and types
        paragraph_count = StoryStructure.get_paragraph_count(context_template)

        # Build user prompt from template
        user_prompt = template_data['user_prompt_template']
        user_prompt = user_prompt.replace('[請在此填入故事希望傳達的中心思想，例如：互相合作、勇敢面對恐懼、分享的快樂]', theme_zh)
        user_prompt = user_prompt.replace('[請在此填入主角1的中文名字，例如：小老鼠「吱吱」]', character_zh)
        user_prompt = user_prompt.replace('[請在此填入主角2的中文名字，例如：小松鼠「果果」]', name)
        user_prompt = user_prompt.replace('[請在此填入一個充滿童趣的中文地點名稱，例如：「棉花糖雲朵」的柔軟森林]', background_zh)
        user_prompt = user_prompt.replace('[主角1]', character_zh)
        user_prompt = user_prompt.replace('[主角2]', name)
        user_prompt = user_prompt.replace('[個性]', personality_text)
        user_prompt = user_prompt.replace('[小道具]', items_text)
        

        # Build complete prompt by combining system and user prompts
        # (More reliable than using system_instruction parameter)
        system_prompt = template_data['system_prompt']
        complete_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)

        generation_config = genai.types.GenerationConfig(
            temperature=0.8,
            max_output_tokens=2000,  # Higher limit for complete story
        )

        # Create model without system_instruction (we combine prompts instead)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            complete_prompt,
            generation_config=generation_config
        )

        if not response.candidates or len(response.candidates) == 0:
            raise ValueError("Gemini API returned no candidates")

        full_response = response.candidates[0].content.parts[0].text.strip()
        print(f"✅ Received complete story response: {len(full_response)} chars")
        
        story_text_path = self.output_dir / f"story.txt"
        with open(story_text_path, 'w', encoding='utf-8') as f:
            f.write(full_response)
        
        
        full_audio_content = self.tts_service.generate_audio(
            text=full_response,
            language='zh-TW',
            voice='cmn-TW-Wavenet-A',
            speaking_rate=1.2,
            parallel=False  # Generate as single continuous audio
        )
        
        if full_audio_content:
            full_audio_filename = f"story_full.mp3"
            full_audio_path = self.output_dir / full_audio_filename
            
            with open(full_audio_path, 'wb') as f:
                full_audio_content.seek(0)
                f.write(full_audio_content.read())
            
        total_time = time.time() - start_time
        print(f"✅ Total generation time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")

        return

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate complete story with audio files')
    parser.add_argument('--theme', type=str, default='friendship', help='Story theme (e.g., caring, courage)')
    parser.add_argument('--character', type=str, default='robot', help='Character name (default: Cat)')
    parser.add_argument('--background', type=str, default='magic village', help='Background name (default: Castle)')
    parser.add_argument('--key-items', nargs='*', default=['ancient scroll'], help='Key items (e.g., Magic Key)')
    parser.add_argument('--child-name', type=str, help='Child name (optional)')
    parser.add_argument('--child-age', type=int, help='Child age (optional)')
    parser.add_argument('--template', type=str, default='1106_prompt', help='Context template (default: 1106_prompt)')
    parser.add_argument('--language', type=str, default='zh-TW', help='TTS language (default: zh-TW)')
    parser.add_argument('--output-dir', type=str, default='./audio_output', help='Output directory (default: ./audio_output)')
    parser.add_argument('--output-prefix', type=str, default='story', help='Output file prefix (default: story)')
    
    args = parser.parse_args()
    
    # Create generator
    generator = AudioGenerator(output_dir=args.output_dir)
    
    # Generate story with audio
    generator._generate_complete_story_single_call(
        theme=args.theme,
        child_name=args.child_name,
        child_age=args.child_age,
        context_template=args.template,
        language=args.language,
        output_prefix=args.output_prefix,
        character=args.character,
        background=args.background,
        key_items=args.key_items
    )
    
    print("\n🎉 All done!")

if __name__ == '__main__':
    main()

