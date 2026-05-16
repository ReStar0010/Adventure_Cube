#!/usr/bin/env python3
"""
Simple command-line script to generate audio using Google Cloud Text-to-Speech API (Vertex AI).
Usage:
    python tts_vertex.py --text "Hello world" --credentials /path/to/credentials.json
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Optional


def chunk_text_by_bytes(text: str, max_bytes: int = 4500) -> List[str]:
    """
    Split text into chunks by UTF-8 byte count, trying to break at sentence boundaries.
    Vertex AI TTS has a 5000 byte limit, using 4500 for safety margin.
    
    Args:
        text: Text to chunk
        max_bytes: Maximum bytes per chunk (default: 4500)
        
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
    sentence_endings = re.compile(r'([。！？\n.]+)')
    
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
        
        sentence_bytes = len(sentence.encode('utf-8'))
        
        # If single sentence is too long, split by bytes
        if sentence_bytes > max_bytes:
            # Add current chunk if exists
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
                current_bytes = 0
            
            # Split the long sentence by bytes
            for char in sentence:
                char_bytes = len(char.encode('utf-8'))
                if current_bytes + char_bytes > max_bytes:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = char
                    current_bytes = char_bytes
                else:
                    current_chunk += char
                    current_bytes += char_bytes
        else:
            # Check if adding this sentence would exceed limit
            if current_bytes + sentence_bytes > max_bytes:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
                current_bytes = sentence_bytes
            else:
                current_chunk += sentence
                current_bytes += sentence_bytes
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def convert_azure_rate_to_vertex(azure_rate: float) -> float:
    """
    Convert Azure rate (0.5-2.0) to Vertex AI speaking_rate (0.25-4.0).
    Linear scaling: Azure 0.5-2.0 maps to Vertex 0.25-4.0.
    
    Args:
        azure_rate: Azure speaking rate (0.5-2.0)
        
    Returns:
        Vertex AI speaking_rate (0.25-4.0)
    """
    # Clamp to valid range
    azure_rate = max(0.5, min(2.0, azure_rate))
    
    # Linear mapping: Azure 0.5 -> Vertex 0.25, Azure 2.0 -> Vertex 4.0
    # Formula: vertex_rate = (azure_rate - 0.5) * (4.0 - 0.25) / (2.0 - 0.5) + 0.25
    vertex_rate = (azure_rate - 0.5) * 3.75 / 1.5 + 0.25
    return max(0.25, min(4.0, vertex_rate))


def convert_azure_pitch_to_vertex(azure_pitch: float) -> float:
    """
    Convert Azure pitch percentage (-50% to +50%) to Vertex AI pitch in semitones (-20 to +20).
    Approximate conversion: 1% ≈ 0.4 semitones.
    
    Args:
        azure_pitch: Azure pitch adjustment (-50 to +50)
        
    Returns:
        Vertex AI pitch in semitones (-20 to +20)
    """
    # Clamp to valid range
    azure_pitch = max(-50, min(50, azure_pitch))
    
    # Convert percentage to semitones (approximate: 1% ≈ 0.4 semitones)
    vertex_pitch = azure_pitch * 0.4
    return max(-20.0, min(20.0, vertex_pitch))


def convert_azure_volume_to_vertex(azure_volume: float) -> float:
    """
    Convert Azure volume percentage (-100% to +100%) to Vertex AI volume_gain_db (in dB).
    Approximate conversion: 1% ≈ 0.1 dB.
    
    Args:
        azure_volume: Azure volume adjustment (-100 to +100)
        
    Returns:
        Vertex AI volume_gain_db in dB
    """
    # Clamp to valid range
    azure_volume = max(-100, min(100, azure_volume))
    
    # Convert percentage to dB (approximate: 1% ≈ 0.1 dB)
    vertex_volume = azure_volume * 0.1
    return max(-96.0, min(16.0, vertex_volume))


def generate_audio(text: str, credentials_path: Optional[str] = None,
                   language: str = 'zh-TW', voice: Optional[str] = None,
                   rate: Optional[float] = None, pitch: Optional[float] = None,
                   volume: Optional[float] = None) -> Optional[bytes]:
    """
    Generate TTS audio using Google Cloud Text-to-Speech API with voice tuning parameters.
    Handles long texts by chunking them (Vertex AI has a 5000 byte limit).
    
    Args:
        text: Text to convert to speech
        credentials_path: Path to GCP service account JSON file (optional if GOOGLE_APPLICATION_CREDENTIALS is set)
        language: Language code (default: 'zh-TW', will be converted to 'cmn-TW' for Vertex AI)
        voice: Optional voice name (auto-selected if not provided)
        rate: Speaking rate (0.5-2.0, e.g., 0.9 for slower, 1.2 for faster)
        pitch: Pitch adjustment (-50 to +50, e.g., 5 for +5%, -10 for -10%)
        volume: Volume adjustment (-100 to +100, e.g., 10 for +10%)
        
    Returns:
        Audio bytes, or None if generation failed
    """
    try:
        from google.cloud import texttospeech
    except ImportError:
        print("❌ Error: google-cloud-texttospeech not installed.")
        print("   Install with: pip install google-cloud-texttospeech")
        sys.exit(1)
    
    # Set up credentials
    if credentials_path:
        if not os.path.exists(credentials_path):
            print(f"❌ Error: Credentials file not found: {credentials_path}")
            return None
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    elif not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("❌ Error: GCP credentials not found.")
        print("   Set GOOGLE_APPLICATION_CREDENTIALS environment variable or use --credentials")
        return None
    
    try:
        client = texttospeech.TextToSpeechClient()
    except Exception as config_error:
        print(f"❌ Failed to create Vertex AI TTS client: {config_error}")
        print("   Check that credentials are valid and Text-to-Speech API is enabled")
        return None
    
    # Language and voice mapping
    # Note: Vertex AI uses 'cmn-TW' for Traditional Chinese, not 'zh-TW'
    language_voice_map = {
        'zh-TW': ('cmn-TW', 'cmn-TW-Wavenet-A'),  # Traditional Chinese - warm female voice
        'cmn-TW': ('cmn-TW', 'cmn-TW-Wavenet-A'),  # Also accept cmn-TW directly
        'zh-CN': ('zh-CN', 'zh-CN-Neural2-A'),     # Simplified Chinese - expressive
        'en': ('en-US', 'en-US-Neural2-F'),       # English - warm, friendly female
        'en-US': ('en-US', 'en-US-Neural2-F'),
    }
    
    if language in language_voice_map:
        language_code, default_voice = language_voice_map[language]
    elif len(language) == 5 and '-' in language:
        language_code = language
        default_voice = voice or f"{language}-Standard-A"
    else:
        language_code = f"{language}-US" if len(language) == 2 else language
        default_voice = voice or 'en-US-Neural2-D'
    
    voice_name = voice or default_voice
    
    # Convert parameters from Azure format to Vertex AI format
    speaking_rate = None
    if rate is not None:
        speaking_rate = convert_azure_rate_to_vertex(rate)
    
    pitch_semitones = None
    if pitch is not None:
        pitch_semitones = convert_azure_pitch_to_vertex(pitch)
    
    volume_gain_db = None
    if volume is not None:
        volume_gain_db = convert_azure_volume_to_vertex(volume)
    
    # Check if text needs to be chunked (5000 byte limit, use 4500 for safety)
    text_bytes = text.encode('utf-8')
    needs_chunking = len(text_bytes) > 4500
    
    if needs_chunking:
        # Split text into chunks
        chunks = chunk_text_by_bytes(text, max_bytes=4500)
        print(f"ℹ️  Text too long ({len(text_bytes)} bytes), splitting into {len(chunks)} chunks")
        
        audio_parts = []
        for i, chunk in enumerate(chunks, 1):
            chunk_bytes = chunk.encode('utf-8')
            if len(chunk_bytes) > 5000:
                print(f"⚠️  Warning: Chunk {i} is still too long ({len(chunk_bytes)} bytes), truncating")
                # Truncate if still too long (shouldn't happen with proper chunking, but safety check)
                chunk = chunk_bytes[:4500].decode('utf-8', errors='ignore')
            
            # Set up synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=chunk)
            
            # Configure voice
            voice_config = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )
            
            # Configure audio with parameters
            audio_config_dict = {
                'audio_encoding': texttospeech.AudioEncoding.MP3
            }
            if speaking_rate is not None:
                audio_config_dict['speaking_rate'] = speaking_rate
            if pitch_semitones is not None:
                audio_config_dict['pitch'] = pitch_semitones
            if volume_gain_db is not None:
                audio_config_dict['volume_gain_db'] = volume_gain_db
            
            audio_config = texttospeech.AudioConfig(**audio_config_dict)
            
            # Perform synthesis
            try:
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice_config,
                    audio_config=audio_config
                )
                audio_parts.append(response.audio_content)
                print(f"✅ Generated chunk {i}/{len(chunks)}")
            except Exception as e:
                print(f"❌ Vertex AI TTS chunk {i} failed: {e}")
                return None
        
        # Concatenate all audio parts
        audio_content = b''.join(audio_parts)
    else:
        # Single request for short text
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Configure voice
        voice_config = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name
        )
        
        # Configure audio with parameters
        audio_config_dict = {
            'audio_encoding': texttospeech.AudioEncoding.MP3
        }
        if speaking_rate is not None:
            audio_config_dict['speaking_rate'] = speaking_rate
        if pitch_semitones is not None:
            audio_config_dict['pitch'] = pitch_semitones
        if volume_gain_db is not None:
            audio_config_dict['volume_gain_db'] = volume_gain_db
        
        audio_config = texttospeech.AudioConfig(**audio_config_dict)
        
        # Perform synthesis
        try:
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_config,
                audio_config=audio_config
            )
            audio_content = response.audio_content
        except Exception as e:
            print(f"❌ Vertex AI TTS failed: {e}")
            print(f"   Possible causes: Invalid credentials, unsupported voice, or API not enabled")
            return None
    
    return audio_content


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Generate audio using Google Cloud Text-to-Speech API (Vertex AI)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (using environment variable for credentials)
  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
  python tts_vertex.py --text "你好世界"
  
  # With credentials file
  python tts_vertex.py --text "你好世界" --credentials /path/to/credentials.json
  
  # With voice tuning parameters
  python tts_vertex.py --text "你好世界" -c /path/to/credentials.json --rate 0.9 --pitch 5 --volume 10
  
  # Full example with all parameters
  python tts_vertex.py --text "從前在一個遙遠的森林裡，住著一隻勇敢的小兔子。" \
    --credentials /path/to/credentials.json --language zh-TW \
    --rate 0.95 --pitch 3 --volume 8 --voice cmn-TW-Wavenet-B \
    --output story.mp3

Note: 
  - Vertex AI uses 'cmn-TW' for Traditional Chinese (zh-TW is automatically converted)
  - For emotion/styles, select different voice models (e.g., Wavenet-A vs Wavenet-B)
  - Set GOOGLE_APPLICATION_CREDENTIALS environment variable or use --credentials
        """
    )
    
    parser.add_argument(
        '--text', '-t',
        required=True,
        help='Text to convert to speech'
    )
    
    parser.add_argument(
        '--credentials', '-c',
        default=None,
        help='Path to GCP service account JSON file (optional if GOOGLE_APPLICATION_CREDENTIALS is set)'
    )
    
    parser.add_argument(
        '--language', '-l',
        default='zh-TW',
        help='Language code (default: zh-TW, will be converted to cmn-TW for Vertex AI)'
    )
    
    parser.add_argument(
        '--voice', '-v',
        default=None,
        help='Voice name (optional, auto-selected based on language if not provided)'
    )
    
    parser.add_argument(
        '--rate',
        type=float,
        default=None,
        help='Speaking rate (0.5-2.0, e.g., 0.9 for slower, 1.2 for faster)'
    )
    
    parser.add_argument(
        '--pitch',
        type=float,
        default=None,
        help='Pitch adjustment (-50 to +50, e.g., 5 for +5%%, -10 for -10%%)'
    )
    
    parser.add_argument(
        '--volume',
        type=float,
        default=None,
        help='Volume adjustment (-100 to +100, e.g., 10 for +10%%)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='output.mp3',
        help='Output file path (default: output.mp3)'
    )
    
    args = parser.parse_args()
    
    # Validate parameters
    if args.rate is not None and (args.rate < 0.5 or args.rate > 2.0):
        print(f"⚠️  Warning: Rate {args.rate} is outside recommended range (0.5-2.0), clamping")
    
    if args.pitch is not None and (args.pitch < -50 or args.pitch > 50):
        print(f"⚠️  Warning: Pitch {args.pitch} is outside recommended range (-50 to +50), clamping")
    
    if args.volume is not None and (args.volume < -100 or args.volume > 100):
        print(f"⚠️  Warning: Volume {args.volume} is outside recommended range (-100 to +100), clamping")
    
    # Generate audio
    text_bytes = len(args.text.encode('utf-8'))
    print(f"🎙️  Generating audio for text ({text_bytes} bytes, {len(args.text)} characters)...")
    print(f"   Language: {args.language}")
    
    # Show voice parameters if specified
    if args.rate:
        print(f"   Rate: {args.rate}x")
    if args.pitch:
        print(f"   Pitch: {args.pitch:+.0f}%")
    if args.volume:
        print(f"   Volume: {args.volume:+.0f}%")
    if args.voice:
        print(f"   Voice: {args.voice}")
    
    audio_content = generate_audio(
        text=args.text,
        credentials_path=args.credentials,
        language=args.language,
        voice=args.voice,
        rate=args.rate,
        pitch=args.pitch,
        volume=args.volume
    )
    
    if not audio_content:
        print("❌ Failed to generate audio")
        sys.exit(1)
    
    # Save to file
    output_path = Path(args.output)
    try:
        with open(output_path, 'wb') as f:
            f.write(audio_content)
        
        file_size = len(audio_content) / 1024
        print(f"✅ Audio saved to: {output_path}")
        print(f"   File size: {file_size:.2f} KB")
    except Exception as e:
        print(f"❌ Failed to save audio file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
