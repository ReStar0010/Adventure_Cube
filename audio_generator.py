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
from stories.story_generator import StoryGenerator
from stories.tts_service import TTSService
from stories.context_engineering import get_paragraph_type_by_index, StoryStructure


class AudioGenerator:
    """
    Generates complete story and audio files in one go.
    """
    
    def __init__(self, output_dir='./audio_output'):
        self.story_generator = StoryGenerator()
        self.tts_service = TTSService()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory: {self.output_dir.absolute()}")
    
    def generate_complete_story_with_audio(
        self,
        theme,
        child_name=None,
        child_age=None,
        context_template='1106_prompt',
        language='zh-TW',
        output_prefix='story',
        **kwargs
    ):
        """
        Generate complete story (all 5 paragraphs) and convert to audio files.
        
        Args:
            theme: Story theme
            child_name: Optional child's name
            child_age: Optional child's age
            context_template: Template name (default: '5min_basic')
            language: Language for TTS (default: 'zh-TW')
            output_prefix: Prefix for output files (default: 'story')
            **kwargs: Additional story elements (character, background, key_items)
        
        Returns:
            dict: {
                'title': str,
                'paragraphs': [
                    {
                        'index': int,
                        'type': str,
                        'text': str,
                        'audio_file': str  # Path to audio file
                    },
                    ...
                ],
                'full_story_text': str,
                'output_dir': str
            }
        """
        print("=" * 80)
        print("🎬 Starting Complete Story Generation with Audio")
        print("=" * 80)
        
        # Start timing
        start_time = time.time()
        
        # Load context template
        try:
            print(f"📖 Loading context template: {context_template}")
            from stories.context_engineering import ContextTemplateLoader
            template_loader = ContextTemplateLoader()
            template_data = template_loader.load_template(context_template)
            print(f"✅ Template loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load template: {e}")
            raise
        
        # Generate all paragraphs sequentially
        paragraphs = []
        previous_paragraphs = []  # Track generated paragraphs for context
        
        print("\n" + "=" * 80)
        print("📝 Generating Story Paragraphs")
        print("=" * 80)
        
        # Generate all paragraphs based on template
        paragraph_count = StoryStructure.get_paragraph_count(context_template)
        for para_index in range(paragraph_count):
            para_type = get_paragraph_type_by_index(para_index, context_template)
            print(f"\n📄 Generating paragraph {para_index + 1}/{paragraph_count}: {para_type.chinese_name}")
            
            try:
                if para_index == 0:
                    # First paragraph (intro) - uses generate_intro_paragraph
                    result = self.story_generator.generate_intro_paragraph(
                        theme=theme,
                        child_name=child_name,
                        child_age=child_age,
                        context_template=context_template,
                        **kwargs
                    )
                else:
                    # Remaining paragraphs - uses generate_paragraph
                    # Note: story parameter is optional and not used, so we can pass None
                    result = self.story_generator.generate_paragraph(
                        paragraph_index=para_index,
                        previous_paragraphs=previous_paragraphs,
                        theme=theme,
                        child_name=child_name,
                        child_age=child_age,
                        context_template=context_template,
                        story=None,  # Not needed for generation, kept for API compatibility
                        **kwargs
                    )
                
                paragraph_text = result['paragraph_text']
                title = result.get('title')
                
                # Store paragraph info
                para_info = {
                    'index': para_index,
                    'type': para_type.type_key,
                    'type_name': para_type.chinese_name,
                    'text': paragraph_text
                }
                
                if title and para_index == 0:
                    para_info['title'] = title
                
                paragraphs.append(para_info)
                
                # Create a mock paragraph object for next iteration
                # Must match StoryParagraph model structure: paragraph_index, paragraph_type, text
                class MockParagraph:
                    def __init__(self, index, para_type_key, text):
                        self.paragraph_index = index
                        self.paragraph_type = para_type_key
                        self.text = text
                
                previous_paragraphs.append(
                    MockParagraph(para_index, para_type.type_key, paragraph_text)
                )
                
                print(f"✅ Paragraph {para_index + 1} generated: {len(paragraph_text)} chars")
                
            except Exception as e:
                print(f"❌ Failed to generate paragraph {para_index + 1}: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # Get title from first paragraph
        title = paragraphs[0].get('title', 'Untitled Story')
        
        # Build full story text
        full_story_text = f"{title}\n\n" + "\n\n".join([p['text'] for p in paragraphs])
        
        print("\n" + "=" * 80)
        print("🎙️  Generating Audio Files")
        print("=" * 80)
        
        # Generate full story audio (all paragraphs combined)
        print(f"\n🎵 Generating full story audio...")
        print(f"   Full story text length: {len(full_story_text)} chars")
        print(f"   Preview: {full_story_text[:100]}...")
        full_audio_path = None
        try:
            # Use parallel=False to generate full story as one continuous audio
            # parallel=True splits by paragraphs which might cause issues
            full_audio_content = self.tts_service.generate_audio(
                text=full_story_text,
                language=language,
                parallel=False  # Generate as single continuous audio
            )
            
            if full_audio_content:
                full_audio_filename = f"{output_prefix}_full.mp3"
                full_audio_path = self.output_dir / full_audio_filename
                
                with open(full_audio_path, 'wb') as f:
                    full_audio_content.seek(0)
                    f.write(full_audio_content.read())
                
                file_size = full_audio_path.stat().st_size
                print(f"✅ Full story audio saved: {full_audio_path.name} ({file_size / 1024:.2f} KB)")
            else:
                print("⚠️  No full story audio generated")
        except Exception as e:
            print(f"❌ Failed to generate full story audio: {e}")
            import traceback
            traceback.print_exc()
        
        # Save story text to file
        story_text_path = self.output_dir / f"{output_prefix}_story.txt"
        with open(story_text_path, 'w', encoding='utf-8') as f:
            f.write(full_story_text)
        print(f"✅ Story text saved: {story_text_path.name}")
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Print summary
        print("\n" + "=" * 80)
        print("✅ Generation Complete!")
        print("=" * 80)
        print(f"📖 Title: {title}")
        print(f"📝 Total paragraphs: {len(paragraphs)}")
        print(f"🎵 Audio files generated: {len([p for p in paragraphs if p.get('audio_file')])}/{len(paragraphs)}")
        print(f"📁 Output directory: {self.output_dir.absolute()}")
        print(f"\n⏱️  Total generation time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        print(f"\n📄 Files created:")
        for para_info in paragraphs:
            audio_file = para_info.get('audio_file')
            if audio_file:
                print(f"   - {Path(audio_file).name}")
        if full_audio_path:
            print(f"   - {full_audio_path.name}")
        print(f"   - {story_text_path.name}")
        
        return {
            'title': title,
            'paragraphs': paragraphs,
            'full_story_text': full_story_text,
            'output_dir': str(self.output_dir.absolute()),
            'full_audio_file': str(full_audio_path) if full_audio_path else None,
            'total_time': total_time
        }


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate complete story with audio files')
    parser.add_argument('--theme', type=str, default='caring', help='Story theme (e.g., caring, courage)')
    parser.add_argument('--character', type=str, default='Cat', help='Character name (default: Cat)')
    parser.add_argument('--background', type=str, default='Castle', help='Background name (default: Castle)')
    parser.add_argument('--key-items', nargs='*', default=[], help='Key items (e.g., Magic Key)')
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
    result = generator.generate_complete_story_with_audio(
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
    return result


if __name__ == '__main__':
    main()

