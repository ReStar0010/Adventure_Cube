#!/usr/bin/env python3
"""
Script to test Azure TTS generation speed.
Measures TTS generation time vs generated text length and creates a visualization.

Note: This script requires pre-generated stories. Run pre_generate_stories.py first.
"""

import sys
import re
import time
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Try to import required libraries (lazy loading)
HAS_PLOTTING = False
HAS_AZURE = False

def check_dependencies():
    """Check and import required dependencies."""
    global HAS_PLOTTING, HAS_AZURE
    global plt, np, speechsdk
    
    # Check for matplotlib and numpy
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        HAS_PLOTTING = True
    except ImportError:
        print("⚠️  Warning: matplotlib or numpy not installed. Chart generation will be skipped.")
        print("   Install with: pip install matplotlib numpy")
        HAS_PLOTTING = False
    
    # Check for Azure Speech SDK
    try:
        import azure.cognitiveservices.speech as speechsdk
        HAS_AZURE = True
    except ImportError:
        print("❌ Error: azure-cognitiveservices-speech not installed.")
        print("   Install with: pip install azure-cognitiveservices-speech")
        sys.exit(1)


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


def chunk_text_by_characters(text: str, max_chars: int = 9000) -> List[str]:
    """
    Split text into chunks by character count, trying to break at sentence boundaries.
    Azure TTS has a 10,000 character limit, so we use 9000 for safety margin.
    
    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk (default: 9000)
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Try to split at sentence boundaries (periods, exclamation marks, question marks)
    # For Chinese text, also consider Chinese punctuation
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
        
        # If single sentence is too long, split by character
        if len(sentence) > max_chars:
            # Add current chunk if exists
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # Split the long sentence by characters
            for char in sentence:
                if len(current_chunk) >= max_chars:
                    chunks.append(current_chunk)
                    current_chunk = char
                else:
                    current_chunk += char
        else:
            # Check if adding this sentence would exceed limit
            if len(current_chunk) + len(sentence) > max_chars:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def generate_tts_azure(text: str, credentials: Dict, language: str = 'zh-TW') -> Tuple[Optional[bytes], float]:
    """
    Generate TTS audio using Azure Cognitive Services and measure the time.
    Handles long texts by chunking them (Azure has a 10,000 character limit).
    
    Args:
        text: Text to convert to speech
        credentials: Dictionary containing credentials
        language: Language code (default: 'zh-TW' for Traditional Chinese)
        
    Returns:
        Tuple of (audio_bytes, generation_time_seconds)
    """
    if not HAS_AZURE:
        return None, 0.0
    
    try:
        azure_key = credentials.get('azureTts', '') or credentials.get('azureTTS', '')
        azure_region = credentials.get('azureRegion', 'eastus')  # Default to eastus if not specified
        
        if not azure_key:
            print("  ⚠️  Azure TTS key not found in credentials")
            return None, 0.0
        
        # Validate key format (Azure keys are typically 32 characters)
        if len(azure_key) < 20:
            print(f"  ⚠️  Azure TTS key appears invalid (too short: {len(azure_key)} chars)")
            print("     Please check your credentials")
        
        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=azure_key,
                region=azure_region
            )
        except Exception as config_error:
            print(f"  ❌ Failed to create Azure Speech config: {config_error}")
            print(f"     Region: {azure_region}, Key length: {len(azure_key)}")
            return None, 0.0
        
        voice_name = 'zh-TW-HsiaoYuNeural'  # Child-friendly voice
        speech_config.speech_synthesis_language = language
        speech_config.speech_synthesis_voice_name = voice_name
        
        # Check if text needs to be chunked (10,000 character limit, use 9000 for safety margin)
        needs_chunking = len(text) > 9000
        
        start_time = time.time()
        
        if needs_chunking:
            # Split text into chunks
            chunks = chunk_text_by_characters(text, max_chars=9000)
            print(f"    ℹ️  Text too long ({len(text)} chars), splitting into {len(chunks)} chunks")
            
            audio_parts = []
            for i, chunk in enumerate(chunks, 1):
                if len(chunk) > 10000:
                    print(f"    ⚠️  Warning: Chunk {i} is still too long ({len(chunk)} chars), truncating")
                    # Truncate if still too long (shouldn't happen with proper chunking, but safety check)
                    chunk = chunk[:9000]
                
                synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
                result = synthesizer.speak_text_async(chunk).get()
                
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    audio_parts.append(result.audio_data)
                elif result.reason == speechsdk.ResultReason.Canceled:
                    # Try to get cancellation details
                    error_msg = "Unknown cancellation reason"
                    try:
                        cancellation_details = speechsdk.CancellationDetails(result)
                        error_msg = str(cancellation_details.reason)
                        if cancellation_details.error_details:
                            error_msg += f": {cancellation_details.error_details}"
                    except Exception:
                        # If we can't get cancellation details, try to get error code
                        try:
                            error_msg = f"Result reason: {result.reason}"
                        except:
                            error_msg = "Unable to retrieve cancellation details"
                    
                    print(f"    ❌ Azure TTS chunk {i} canceled: {error_msg}")
                    print(f"       Possible causes: Invalid API key, wrong region, or authentication failure")
                    print(f"       Current region: {azure_region}, Key length: {len(azure_key)}")
                    return None, 0.0
                else:
                    print(f"    ❌ Azure TTS chunk {i} failed: {result.reason}")
                    # Try to get error details if available
                    try:
                        if hasattr(result, 'error_details') and result.error_details:
                            print(f"       Error: {result.error_details}")
                    except:
                        pass
                    return None, 0.0
            
            # Concatenate all audio parts
            audio_content = b''.join(audio_parts)
        else:
            # Single request for short text
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_content = result.audio_data
            elif result.reason == speechsdk.ResultReason.Canceled:
                # Try to get cancellation details
                error_msg = "Unknown cancellation reason"
                try:
                    cancellation_details = speechsdk.CancellationDetails(result)
                    error_msg = str(cancellation_details.reason)
                    if cancellation_details.error_details:
                        error_msg += f": {cancellation_details.error_details}"
                except Exception:
                    # If we can't get cancellation details, try to get error code
                    try:
                        error_msg = f"Result reason: {result.reason}"
                    except:
                        error_msg = "Unable to retrieve cancellation details"
                
                print(f"  ❌ Azure TTS canceled: {error_msg}")
                print(f"     Possible causes: Invalid API key, wrong region, or authentication failure")
                print(f"     Current region: {azure_region}, Key length: {len(azure_key)}")
                print(f"     Text length: {len(text)} characters")
                return None, 0.0
            else:
                print(f"  ❌ Azure TTS failed: {result.reason}")
                # Try to get error details if available
                try:
                    if hasattr(result, 'error_details') and result.error_details:
                        print(f"     Error: {result.error_details}")
                except:
                    pass
                return None, 0.0
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        return audio_content, generation_time
            
    except Exception as e:
        print(f"  ❌ Azure error: {e}")
        import traceback
        print(f"     Traceback: {traceback.format_exc()}")
        return None, 0.0


def test_azure_tts(stories: List[Dict], credentials: Dict) -> List[Dict]:
    """
    Test Azure TTS generation for each story.
    
    Args:
        stories: List of story dictionaries with 'text' and metadata
        credentials: Dictionary containing API credentials
        
    Returns:
        List of dictionaries with test results
    """
    results = []
    
    print(f"\n{'='*80}")
    print(f"Testing {len(stories)} stories with Azure TTS")
    print(f"{'='*80}\n")
    
    for story_idx, story_data in enumerate(stories, 1):
        story_text = story_data.get('generated_text', '')
        word_count = count_words_chinese(story_text)
        
        if not story_text:
            print(f"[{story_idx}/{len(stories)}] ⚠️  Skipping - no story text")
            continue
        
        print(f"[{story_idx}/{len(stories)}] Testing story: {word_count} words")
        print(f"  Phase_ID: {story_data.get('phase_id', 'N/A')}")
        print(f"  🎙️  Testing Azure TTS...")
        
        audio_bytes, generation_time = generate_tts_azure(story_text, credentials, language='zh-TW')
        
        if audio_bytes and generation_time > 0:
            audio_size = len(audio_bytes)
            result = {
                'story_index': story_idx,
                'phase_id': story_data.get('phase_id', 'N/A'),
                'platform': 'Azure',
                'word_count': word_count,
                'text_length': len(story_text),
                'generation_time': generation_time,
                'audio_size_bytes': audio_size,
                'audio_size_kb': audio_size / 1024,
                'story_text': story_text[:500] + "..." if len(story_text) > 500 else story_text  # Preview only
            }
            results.append(result)
            
            print(f"    ✅ Azure: {generation_time:.2f}s ({audio_size/1024:.1f} KB)")
        else:
            print(f"    ❌ Azure: Failed")
        
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
    
    # Extract data
    word_counts = [r['word_count'] for r in results]
    generation_times = [r['generation_time'] for r in results]
    labels = [f"#{r['story_index']}\n{r['phase_id'][:15]}" for r in results]
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Scatter plot
    plt.scatter(word_counts, generation_times, s=200, alpha=0.6, c='orange', 
               marker='^', label='Azure TTS', edgecolors='black', linewidths=1)
    
    # Add labels for each point
    for i, (x, y, label) in enumerate(zip(word_counts, generation_times, labels)):
        plt.annotate(label, (x, y), xytext=(5, 5), 
                    textcoords='offset points', fontsize=9, alpha=0.7)
    
    # Calculate and plot trend line
    if len(word_counts) > 1:
        z = np.polyfit(word_counts, generation_times, 1)
        p = np.poly1d(z)
        plt.plot(word_counts, p(word_counts), "r--", alpha=0.5, 
                label=f'Trend line (y={z[0]:.4f}x+{z[1]:.2f})')
        plt.legend()
    
    # Calculate correlation coefficient
    correlation = np.corrcoef(word_counts, generation_times)[0, 1]
    
    # Customize the plot
    plt.xlabel('Generated Text Length (words)', fontsize=12, fontweight='bold')
    plt.ylabel('TTS Generation Time (seconds)', fontsize=12, fontweight='bold')
    plt.title(f'Azure TTS Generation Speed Analysis\nCorrelation: {correlation:.3f}', 
              fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Add statistics text box
    stats_text = f"Total Tests: {len(results)}\n"
    stats_text += f"Avg Words: {np.mean(word_counts):.0f} words\n"
    stats_text += f"Avg Time: {np.mean(generation_times):.2f}s\n"
    stats_text += f"Avg Speed: {np.mean([w/t for w, t in zip(word_counts, generation_times) if t > 0]):.1f} words/s"
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
    Print a summary of the test results.
    
    Args:
        results: List of test result dictionaries
    """
    if not results:
        return
    
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    print(f"{'Story':<8} {'Words':<10} {'Time (s)':<12} {'Speed (words/s)':<15} {'Audio (KB)':<12}")
    print("-" * 80)
    
    for r in results:
        word_count = r['word_count']
        speed = word_count / r['generation_time'] if r['generation_time'] > 0 else 0
        print(f"#{r['story_index']:<7} {word_count:<10} {r['generation_time']:<12.2f} "
              f"{speed:<15.1f} {r['audio_size_kb']:<12.1f}")
    
    # Calculate averages
    word_counts = [r['word_count'] for r in results]
    generation_times = [r['generation_time'] for r in results]
    speeds = [w/t for w, t in zip(word_counts, generation_times) if t > 0]
    
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
    avg_time = sum(generation_times) / len(generation_times) if generation_times else 0
    avg_speed = sum(speeds) / len(speeds) if speeds else 0
    min_time = min(generation_times) if generation_times else 0
    max_time = max(generation_times) if generation_times else 0
    
    print("-" * 80)
    print(f"{'AVERAGE':<8} {avg_words:<10.0f} {avg_time:<12.2f} {avg_speed:<15.1f}")
    print(f"{'RANGE':<8} {'':<10} {min_time:.2f}s - {max_time:.2f}s")
    print(f"{'='*80}\n")


def main():
    """Main function."""
    # Check dependencies first
    check_dependencies()
    
    # Get script directory
    script_dir = Path(__file__).parent
    
    # File paths
    credential_path = script_dir / 'credential.json'
    stories_dir = script_dir / 'generated_stories'
    chart_output = script_dir / 'azure_tts_generation_speed_chart.png'
    results_output = script_dir / 'azure_tts_test_results.json'
    
    # Check if credential file exists
    if not credential_path.exists():
        print(f"❌ Error: Credential file not found at {credential_path}")
        sys.exit(1)
    
    # Load credentials
    print("🔑 Loading credentials...")
    credentials = load_credentials(credential_path)
    
    # Load pre-generated stories (required)
    print(f"\n📚 Loading pre-generated stories from {stories_dir.name}/...")
    stories = load_pre_generated_stories(stories_dir)
    
    if not stories:
        print("  ❌ Error: No pre-generated stories found!")
        print("  💡 Please run pre_generate_stories.py first to generate stories.")
        print(f"  📁 Expected directory: {stories_dir}")
        sys.exit(1)
    
    print(f"\n✅ Loaded {len(stories)} pre-generated stories\n")
    
    # Test Azure TTS
    results = test_azure_tts(stories, credentials)
    
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

