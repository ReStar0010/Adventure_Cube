#!/usr/bin/env python3
"""
Script to test TTS generation speed for different platforms.
Measures TTS generation time vs generated text length and creates a visualization.
Tests multiple TTS platforms: gTTS and Vertex AI.

Note: This script requires pre-generated stories. Run pre_generate_stories.py first.
For Azure TTS testing, use test_azure_tts_speed.py separately.
"""

import sys
import re
import time
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from io import BytesIO

# Try to import required libraries (lazy loading)
HAS_PLOTTING = False
HAS_GTTS = False
HAS_VERTEX_AI = False

def check_dependencies():
    """Check and import required dependencies."""
    global HAS_PLOTTING, HAS_GTTS, HAS_VERTEX_AI
    global plt, np, gTTS, texttospeech
    
    # Check for matplotlib and numpy
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        HAS_PLOTTING = True
    except ImportError:
        print("⚠️  Warning: matplotlib or numpy not installed. Chart generation will be skipped.")
        print("   Install with: pip install matplotlib numpy")
        HAS_PLOTTING = False
    
    # Check for gTTS
    try:
        from gtts import gTTS
        HAS_GTTS = True
    except ImportError:
        print("⚠️  Warning: gTTS not installed. gTTS platform will be skipped.")
        print("   Install with: pip install gtts")
        HAS_GTTS = False
    
    # Check for Google Cloud Text-to-Speech
    try:
        from google.cloud import texttospeech
        HAS_VERTEX_AI = True
    except ImportError:
        print("⚠️  Warning: google-cloud-texttospeech not installed. Vertex AI platform will be skipped.")
        print("   Install with: pip install google-cloud-texttospeech")
        HAS_VERTEX_AI = False


def count_words_chinese(text: str) -> int:
    """
    Count words/characters in text, handling both Chinese and English.
    For Chinese text, counts characters (字).
    For English text, counts words separated by spaces.
    For mixed text, uses a hybrid approach.
    
    Args:
        text: Input text (can be Chinese, English, or mixed)
        
    Returns:
        Word/character count
    """
    if not text:
        return 0
    
    # Remove markdown formatting and extra whitespace
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold markers
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Remove code markers
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = text.strip()
    
    # Count Chinese characters (CJK Unified Ideographs)
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    
    # Count English words (sequences of letters separated by spaces/punctuation)
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    
    # For Chinese-dominant text, count characters
    # For English-dominant text, count words
    if chinese_chars > english_words * 2:
        return chinese_chars + english_words
    elif english_words > chinese_chars * 2:
        return english_words
    else:
        return chinese_chars + english_words


def load_credentials(credential_path: Path) -> Dict:
    """
    Load API credentials from JSON file.
    
    Args:
        credential_path: Path to credential.json
        
    Returns:
        Dictionary containing credentials
    """
    with open(credential_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_tts_gtts(text: str, language: str = 'zh-tw') -> Tuple[Optional[bytes], float]:
    """
    Generate TTS audio using gTTS and measure the time.
    
    Args:
        text: Text to convert to speech
        language: Language code (default: 'zh-tw' for Traditional Chinese)
        
    Returns:
        Tuple of (audio_bytes, generation_time_seconds)
    """
    if not HAS_GTTS:
        return None, 0.0
    
    try:
        start_time = time.time()
        tts = gTTS(text=text, lang=language, slow=False)
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_bytes = audio_buffer.read()
        end_time = time.time()
        
        generation_time = end_time - start_time
        return audio_bytes, generation_time
        
    except Exception as e:
        print(f"  ❌ gTTS error: {e}")
        return None, 0.0


def chunk_text_for_tts(text: str, max_bytes: int = 4500) -> List[str]:
    """
    Split text into chunks that are under the byte limit, trying to break at sentence boundaries.
    
    Args:
        text: Text to chunk
        max_bytes: Maximum bytes per chunk (default: 4500 to leave some margin)
        
    Returns:
        List of text chunks
    """
    text_bytes = text.encode('utf-8')
    if len(text_bytes) <= max_bytes:
        return [text]
    
    chunks = []
    current_chunk = ""
    current_bytes = 0
    
    # Try to split at sentence boundaries (periods, exclamation marks, question marks)
    # For Chinese text, also consider Chinese punctuation
    # Split by sentence endings but keep the punctuation with the sentence
    sentence_endings = re.compile(r'([。！？\n]+)')
    
    # Split text, keeping delimiters
    parts = sentence_endings.split(text)
    
    i = 0
    while i < len(parts):
        # Get sentence and its punctuation
        sentence = parts[i]
        if i + 1 < len(parts):
            sentence += parts[i + 1]  # Include the punctuation
            i += 2
        else:
            i += 1
        
        sentence_bytes = sentence.encode('utf-8')
        
        # If single sentence is too long, split by character
        if len(sentence_bytes) > max_bytes:
            # Add current chunk if exists
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
                current_bytes = 0
            
            # Split the long sentence by characters
            for char in sentence:
                char_bytes = char.encode('utf-8')
                if current_bytes + len(char_bytes) > max_bytes:
                    chunks.append(current_chunk)
                    current_chunk = char
                    current_bytes = len(char_bytes)
                else:
                    current_chunk += char
                    current_bytes += len(char_bytes)
        else:
            # Check if adding this sentence would exceed limit
            if current_bytes + len(sentence_bytes) > max_bytes:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
                current_bytes = len(sentence_bytes)
            else:
                current_chunk += sentence
                current_bytes += len(sentence_bytes)
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def generate_tts_vertex_ai(text: str, credentials: Dict, language: str = 'cmn-TW') -> Tuple[Optional[bytes], float]:
    """
    Generate TTS audio using Google Vertex AI and measure the time.
    Handles long texts by chunking them (Vertex AI has a 5000 byte limit).
    
    Args:
        text: Text to convert to speech
        credentials: Dictionary containing credentials
        language: Language code (default: 'cmn-TW' for Traditional Chinese)
        
    Returns:
        Tuple of (audio_bytes, generation_time_seconds)
    """
    if not HAS_VERTEX_AI:
        return None, 0.0
    
    try:
        # Set up credentials if provided
        gcp_credentials_path = credentials.get('gcp_credentials_path')
        if gcp_credentials_path and os.path.exists(gcp_credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = gcp_credentials_path
        
        client = texttospeech.TextToSpeechClient()
        
        voice = texttospeech.VoiceSelectionParams(
            language_code=language,
            name="cmn-TW-Wavenet-A",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # Check if text needs to be chunked (5000 byte limit, use 4500 for safety margin)
        text_bytes = text.encode('utf-8')
        needs_chunking = len(text_bytes) > 4500
        
        start_time = time.time()
        
        if needs_chunking:
            # Split text into chunks
            chunks = chunk_text_for_tts(text, max_bytes=4500)
            print(f"    ℹ️  Text too long ({len(text_bytes)} bytes), splitting into {len(chunks)} chunks")
            
            audio_parts = []
            for i, chunk in enumerate(chunks, 1):
                chunk_bytes = chunk.encode('utf-8')
                if len(chunk_bytes) > 5000:
                    print(f"    ⚠️  Warning: Chunk {i} is still too long ({len(chunk_bytes)} bytes), truncating")
                    # Truncate if still too long (shouldn't happen with proper chunking, but safety check)
                    chunk = chunk[:4500].encode('utf-8').decode('utf-8', errors='ignore')
                
                synthesis_input = texttospeech.SynthesisInput(text=chunk)
                response = client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=audio_config
                )
                audio_parts.append(response.audio_content)
            
            # Concatenate all audio parts
            audio_content = b''.join(audio_parts)
        else:
            # Single request for short text
            synthesis_input = texttospeech.SynthesisInput(text=text)
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            audio_content = response.audio_content
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        return audio_content, generation_time
        
    except Exception as e:
        print(f"  ❌ Vertex AI error: {e}")
        return None, 0.0


def test_tts_platforms(stories: List[Dict], credentials: Dict) -> List[Dict]:
    """
    Test TTS generation for each story on all available platforms.
    
    Args:
        stories: List of story dictionaries with 'text' and metadata
        credentials: Dictionary containing API credentials
        
    Returns:
        List of dictionaries with test results
    """
    results = []
    
    # Determine available platforms
    platforms = []
    if HAS_GTTS:
        platforms.append('gTTS')
    if HAS_VERTEX_AI:
        platforms.append('Vertex AI')
    
    if not platforms:
        print("❌ Error: No TTS platforms available. Please install at least one TTS library.")
        return results
    
    print(f"\n{'='*80}")
    print(f"Testing {len(stories)} stories on {len(platforms)} platform(s): {', '.join(platforms)}")
    print(f"{'='*80}\n")
    
    for story_idx, story_data in enumerate(stories, 1):
        story_text = story_data.get('generated_text', '')
        word_count = count_words_chinese(story_text)
        
        if not story_text:
            print(f"[{story_idx}/{len(stories)}] ⚠️  Skipping - no story text")
            continue
        
        print(f"[{story_idx}/{len(stories)}] Testing story: {word_count} words")
        print(f"  Phase_ID: {story_data.get('phase_id', 'N/A')}")
        
        # Test each platform
        for platform in platforms:
            print(f"  🎙️  Testing {platform}...")
            
            audio_bytes = None
            generation_time = 0.0
            
            if platform == 'gTTS':
                audio_bytes, generation_time = generate_tts_gtts(story_text, language='zh-tw')
            elif platform == 'Vertex AI':
                audio_bytes, generation_time = generate_tts_vertex_ai(story_text, credentials, language='cmn-TW')
            
            if audio_bytes and generation_time > 0:
                audio_size = len(audio_bytes)
                result = {
                    'story_index': story_idx,
                    'phase_id': story_data.get('phase_id', 'N/A'),
                    'platform': platform,
                    'word_count': word_count,
                    'text_length': len(story_text),
                    'generation_time': generation_time,
                    'audio_size_bytes': audio_size,
                    'audio_size_kb': audio_size / 1024,
                    'story_text': story_text[:500] + "..." if len(story_text) > 500 else story_text  # Preview only
                }
                results.append(result)
                
                print(f"    ✅ {platform}: {generation_time:.2f}s ({audio_size/1024:.1f} KB)")
            else:
                print(f"    ❌ {platform}: Failed")
        
        print()
    
    return results


def save_results(results: List[Dict], output_path: Path):
    """
    Save test results to JSON file.
    
    Args:
        results: List of test result dictionaries
        output_path: Path to save the JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"💾 Results saved to: {output_path}")


def create_chart(results: List[Dict], output_path: Path):
    """
    Create a scatter plot showing correlation between word length and TTS generation time.
    Different platforms are shown with different colors/markers.
    
    Args:
        results: List of test result dictionaries
        output_path: Path to save the chart
    """
    if not HAS_PLOTTING:
        print("⚠️  Skipping chart generation (matplotlib/numpy not available)")
        return
    
    if not results:
        print("❌ No results to plot")
        return
    
    # Group results by platform
    platforms = {}
    for r in results:
        platform = r['platform']
        if platform not in platforms:
            platforms[platform] = {'word_counts': [], 'times': [], 'indices': []}
        platforms[platform]['word_counts'].append(r['word_count'])
        platforms[platform]['times'].append(r['generation_time'])
        platforms[platform]['indices'].append(r['story_index'])
    
    # Create the plot
    plt.figure(figsize=(14, 10))
    
    # Color and marker mapping for platforms
    colors = {'gTTS': 'blue', 'Vertex AI': 'green'}
    markers = {'gTTS': 'o', 'Vertex AI': 's'}
    
    # Plot each platform
    for platform, data in platforms.items():
        color = colors.get(platform, 'gray')
        marker = markers.get(platform, 'o')
        plt.scatter(data['word_counts'], data['times'], 
                   s=200, alpha=0.6, c=color, marker=marker, 
                   label=platform, edgecolors='black', linewidths=1)
        
        # Add labels for each point
        for i, (x, y, idx) in enumerate(zip(data['word_counts'], data['times'], data['indices'])):
            plt.annotate(f"#{idx}", (x, y), xytext=(5, 5), 
                        textcoords='offset points', fontsize=8, alpha=0.7)
    
    # Calculate and plot trend lines for each platform
    for platform, data in platforms.items():
        if len(data['word_counts']) > 1:
            z = np.polyfit(data['word_counts'], data['times'], 1)
            p = np.poly1d(z)
            color = colors.get(platform, 'gray')
            plt.plot(data['word_counts'], p(data['word_counts']), 
                    "--", alpha=0.4, color=color, linewidth=2,
                    label=f'{platform} trend (y={z[0]:.4f}x+{z[1]:.2f})')
    
    # Calculate overall correlation
    all_word_counts = [r['word_count'] for r in results]
    all_times = [r['generation_time'] for r in results]
    correlation = np.corrcoef(all_word_counts, all_times)[0, 1]
    
    # Customize the plot
    plt.xlabel('Generated Text Length (words)', fontsize=12, fontweight='bold')
    plt.ylabel('TTS Generation Time (seconds)', fontsize=12, fontweight='bold')
    plt.title(f'TTS Generation Speed Analysis by Platform\nOverall Correlation: {correlation:.3f}', 
              fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='best', fontsize=10)
    
    # Add statistics text box
    stats_text = f"Total Tests: {len(results)}\n"
    stats_text += f"Platforms: {', '.join(platforms.keys())}\n"
    stats_text += f"Avg Words: {np.mean(all_word_counts):.0f} words\n"
    stats_text += f"Avg Time: {np.mean(all_times):.2f}s\n"
    stats_text += f"Avg Speed: {np.mean([w/t for w, t in zip(all_word_counts, all_times) if t > 0]):.1f} words/s"
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
             fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Save the chart
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"📊 Chart saved to: {output_path}")
    
    # Also display the chart (comment out if running headless)
    try:
        plt.show()
    except:
        print("⚠️  Could not display chart (running in headless mode?)")


def load_pre_generated_stories(stories_dir: Path) -> Optional[List[Dict]]:
    """
    Load pre-generated stories from the stories directory.
    
    Args:
        stories_dir: Path to the directory containing generated stories
        
    Returns:
        List of story dictionaries, or None if stories don't exist
    """
    index_path = stories_dir / 'index.json'
    
    if not index_path.exists():
        return None
    
    try:
        # Load index to get list of story files
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        stories = []
        for story_info in index_data.get('stories', []):
            story_file = stories_dir / story_info['filename']
            if story_file.exists():
                with open(story_file, 'r', encoding='utf-8') as f:
                    story_data = json.load(f)
                    stories.append(story_data)
            else:
                print(f"  ⚠️  Warning: Story file not found: {story_file.name}")
        
        if stories:
            print(f"  ✅ Loaded {len(stories)} pre-generated stories")
            print(f"  📅 Generated at: {index_data.get('generated_at', 'Unknown')}")
            return stories
        
    except Exception as e:
        print(f"  ⚠️  Error loading pre-generated stories: {e}")
        return None
    
    return None


def print_summary(results: List[Dict]):
    """
    Print a summary of the test results with platform comparisons.
    
    Args:
        results: List of test result dictionaries
    """
    if not results:
        return
    
    # Group results by story index
    stories_dict = {}
    for r in results:
        story_idx = r['story_index']
        if story_idx not in stories_dict:
            stories_dict[story_idx] = {
                'phase_id': r['phase_id'],
                'word_count': r['word_count'],
                'platforms': {}
            }
        stories_dict[story_idx]['platforms'][r['platform']] = r
    
    # Get all platforms
    all_platforms = sorted(set(r['platform'] for r in results))
    
    print(f"\n{'='*100}")
    print("PLATFORM COMPARISON BY STORY")
    print(f"{'='*100}")
    
    # Print header
    header = f"{'Story':<8} {'Words':<10} "
    for platform in all_platforms:
        header += f"{platform:<20} "
    print(header)
    print("-" * 100)
    
    # Print each story with platform comparisons
    for story_idx in sorted(stories_dict.keys()):
        story_data = stories_dict[story_idx]
        row = f"#{story_idx:<7} {story_data['word_count']:<10} "
        
        for platform in all_platforms:
            if platform in story_data['platforms']:
                r = story_data['platforms'][platform]
                speed = r['word_count'] / r['generation_time'] if r['generation_time'] > 0 else 0
                row += f"{r['generation_time']:.2f}s ({speed:.1f}w/s)  "
            else:
                row += f"{'N/A':<20} "
        
        print(row)
    
    # Print platform averages
    print("-" * 100)
    print("PLATFORM AVERAGES:")
    
    platform_stats = {}
    for r in results:
        platform = r['platform']
        if platform not in platform_stats:
            platform_stats[platform] = {'times': [], 'word_counts': [], 'speeds': []}
        platform_stats[platform]['times'].append(r['generation_time'])
        platform_stats[platform]['word_counts'].append(r['word_count'])
        speed = r['word_count'] / r['generation_time'] if r['generation_time'] > 0 else 0
        platform_stats[platform]['speeds'].append(speed)
    
    for platform in sorted(platform_stats.keys()):
        stats = platform_stats[platform]
        avg_time = sum(stats['times']) / len(stats['times'])
        avg_words = sum(stats['word_counts']) / len(stats['word_counts'])
        avg_speed = sum(stats['speeds']) / len(stats['speeds'])
        min_time = min(stats['times'])
        max_time = max(stats['times'])
        print(f"  {platform:<15} Avg: {avg_time:.2f}s | Speed: {avg_speed:.1f} words/s | Range: {min_time:.2f}s - {max_time:.2f}s")
    
    # Find fastest platform for each story
    print("\nFASTEST PLATFORM BY STORY:")
    for story_idx in sorted(stories_dict.keys()):
        story_data = stories_dict[story_idx]
        fastest_platform = None
        fastest_time = float('inf')
        
        for platform, r in story_data['platforms'].items():
            if r['generation_time'] < fastest_time:
                fastest_time = r['generation_time']
                fastest_platform = platform
        
        if fastest_platform:
            print(f"  Story #{story_idx}: {fastest_platform} ({fastest_time:.2f}s)")
    
    print(f"{'='*100}\n")


def main():
    """Main function."""
    # Check dependencies first
    check_dependencies()
    
    # Get script directory
    script_dir = Path(__file__).parent
    
    # File paths
    credential_path = script_dir / 'credential.json'
    gcp_credentials_path = script_dir.parent / 'TTS_scripts' / 'gcp_credentials.json'
    stories_dir = script_dir / 'generated_stories'
    chart_output = script_dir / 'tts_generation_speed_chart.png'
    results_output = script_dir / 'tts_test_results.json'
    
    # Check if credential file exists
    if not credential_path.exists():
        print(f"❌ Error: Credential file not found at {credential_path}")
        sys.exit(1)
    
    # Load credentials
    print("🔑 Loading credentials...")
    credentials = load_credentials(credential_path)
    
    # Add GCP credentials path if it exists
    if gcp_credentials_path.exists():
        credentials['gcp_credentials_path'] = str(gcp_credentials_path)
        print(f"  ✅ Found GCP credentials at {gcp_credentials_path}")
    else:
        print(f"  ⚠️  GCP credentials not found at {gcp_credentials_path}")
    
    # Load pre-generated stories (required)
    print(f"\n📚 Loading pre-generated stories from {stories_dir.name}/...")
    stories = load_pre_generated_stories(stories_dir)
    
    if not stories:
        print("  ❌ Error: No pre-generated stories found!")
        print("  💡 Please run pre_generate_stories.py first to generate stories.")
        print(f"  📁 Expected directory: {stories_dir}")
        sys.exit(1)
    
    print(f"\n✅ Loaded {len(stories)} pre-generated stories\n")
    
    # Test TTS on all platforms
    results = test_tts_platforms(stories, credentials)
    
    if not results:
        print("❌ Error: No TTS results generated")
        sys.exit(1)
    
    # Save results
    print("💾 Saving results...")
    save_results(results, results_output)
    
    # Print summary
    print_summary(results)
    
    # Create chart
    print("📊 Creating visualization...")
    create_chart(results, chart_output)
    
    print("\n✅ Test completed successfully!")


if __name__ == '__main__':
    main()

