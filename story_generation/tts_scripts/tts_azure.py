#!/usr/bin/env python3
"""
Simple command-line script to generate audio using Azure Text-to-Speech API.
Usage:
    python tts_azure.py --text "Hello world" --key YOUR_KEY --region eastus
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional


def build_ssml(
    text: str,
    voice: str = 'zh-TW-HsiaoChenNeural',
    language_code: str = 'zh-TW',
    rate: Optional[float] = None,
    pitch: Optional[float] = None,
    volume: Optional[float] = None,
    express_as_style: Optional[str] = None,
    express_as_degree: Optional[str] = None,
) -> str:
    """
    Build SSML with Azure TTS parameters.
    
    Args:
        text: Text to convert to speech
        voice: Voice name (e.g., 'zh-TW-HsiaoChenNeural')
        language_code: Language code (e.g., 'zh-TW')
        rate: Speaking rate (0.5 to 2.0, default: 1.0)
        pitch: Pitch adjustment (-50 to +50%, default: 0)
        volume: Volume adjustment (-100 to +100%, default: 0)
        express_as_style: Express-as style (e.g., "cheerful", "sad", "gentle")
        express_as_degree: Express-as degree ("mild", "moderate", "strong")
        
    Returns:
        SSML string
    """
    # Build prosody attributes
    prosody_attrs = []
    
    if rate is not None:
        # Convert to percentage (rate 1.0 = 100%)
        rate_percent = int(rate * 100)
        rate_percent = max(50, min(200, rate_percent))
        prosody_attrs.append(f'rate="{rate_percent}%"')
    
    if pitch is not None:
        # Convert to percentage (pitch is in percentage, e.g., 5 means +5%)
        pitch_int = int(pitch)
        pitch_str = f"{pitch_int:+d}%"
        prosody_attrs.append(f'pitch="{pitch_str}"')
    
    if volume is not None:
        # Convert to percentage (volume is in percentage, e.g., 10 means +10%)
        volume_int = int(volume)
        volume_str = f"{volume_int:+d}%"
        prosody_attrs.append(f'volume="{volume_str}"')
    
    prosody_attr_str = " ".join(prosody_attrs)
    
    # Build SSML structure
    ssml_parts = [
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{language_code}">'
    ]
    
    # Add express-as if specified
    if express_as_style:
        # Map degree values: mild=0.01, moderate=1.0, strong=2.0
        degree_map = {'mild': '0.01', 'moderate': '1.0', 'strong': '2.0'}
        degree = degree_map.get(express_as_degree, '1.0')
        
        ssml_parts.append(f'<voice name="{voice}">')
        ssml_parts.append(f'<mstts:express-as style="{express_as_style}" styledegree="{degree}">')
        
        if prosody_attr_str:
            ssml_parts.append(f'<prosody {prosody_attr_str}>')
            ssml_parts.append(text)
            ssml_parts.append('</prosody>')
        else:
            ssml_parts.append(text)
        
        ssml_parts.append('</mstts:express-as>')
        ssml_parts.append('</voice>')
    else:
        # Standard structure
        ssml_parts.append(f'<voice name="{voice}">')
        if prosody_attr_str:
            ssml_parts.append(f'<prosody {prosody_attr_str}>')
            ssml_parts.append(text)
            ssml_parts.append('</prosody>')
        else:
            ssml_parts.append(text)
        ssml_parts.append('</voice>')
    
    ssml_parts.append('</speak>')
    
    return ''.join(ssml_parts)


def chunk_text_by_characters(text: str, max_chars: int = 5000) -> List[str]:
    """
    Split text into chunks by character count, trying to break at sentence boundaries.
    Azure TTS has a 10,000 character limit, using 5000 for safety margin.
    
    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk (default: 5000)
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    current_chunk = ""
    
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


def generate_audio(text: str, azure_key: str, azure_region: str, 
                   language: str = 'zh-TW', voice: Optional[str] = None,
                   rate: Optional[float] = None, pitch: Optional[float] = None,
                   volume: Optional[float] = None, express_as_style: Optional[str] = None,
                   express_as_degree: Optional[str] = None) -> Optional[bytes]:
    """
    Generate TTS audio using Azure Cognitive Services with voice tuning parameters.
    Handles long texts by chunking them (Azure has a 10,000 character limit).
    
    Args:
        text: Text to convert to speech
        azure_key: Azure Speech API key
        azure_region: Azure region (e.g., 'eastus', 'westus2')
        language: Language code (default: 'zh-TW')
        voice: Optional voice name (auto-selected if not provided)
        rate: Speaking rate (0.5-2.0, e.g., 0.9 for slower, 1.2 for faster)
        pitch: Pitch adjustment (-50 to +50%, e.g., 5 for +5%, -10 for -10%)
        volume: Volume adjustment (-100 to +100%, e.g., 10 for +10%)
        express_as_style: Emotion style (e.g., "cheerful", "sad", "gentle")
        express_as_degree: Emotion intensity ("mild", "moderate", "strong")
        
    Returns:
        Audio bytes, or None if generation failed
    """
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError:
        print("❌ Error: azure-cognitiveservices-speech not installed.")
        print("   Install with: pip install azure-cognitiveservices-speech")
        sys.exit(1)
    
    # Validate key format
    if not azure_key or len(azure_key) < 20:
        print(f"❌ Error: Azure TTS key appears invalid (length: {len(azure_key) if azure_key else 0})")
        return None
    
    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=azure_key,
            region=azure_region
        )
    except Exception as config_error:
        print(f"❌ Failed to create Azure Speech config: {config_error}")
        return None
    
    # Language and voice mapping
    language_voice_map = {
        'zh-TW': ('zh-TW', 'zh-TW-HsiaoChenNeural'),  # Warm, friendly female voice
        'zh-CN': ('zh-CN', 'zh-CN-XiaoxiaoNeural'),    # Expressive female voice
        'en': ('en-US', 'en-US-AriaNeural'),          # Warm, natural female voice
        'en-US': ('en-US', 'en-US-AriaNeural'),
    }
    
    if language in language_voice_map:
        language_code, default_voice = language_voice_map[language]
    elif len(language) == 5 and '-' in language:
        language_code = language
        default_voice = voice or 'en-US-AriaNeural'
    else:
        language_code = f"{language}-US" if len(language) == 2 else language
        default_voice = voice or 'en-US-AriaNeural'
    
    voice_name = voice or default_voice
    
    speech_config.speech_synthesis_language = language_code
    speech_config.speech_synthesis_voice_name = voice_name
    
    # Determine if we should use SSML (if any voice parameters are specified)
    use_ssml = any([rate, pitch, volume, express_as_style])
    
    # Check if text needs to be chunked (10,000 character limit, use 5000 for safety)
    needs_chunking = len(text) > 5000
    
    if needs_chunking:
        # Split text into chunks
        chunks = chunk_text_by_characters(text, max_chars=5000)
        print(f"ℹ️  Text too long ({len(text)} chars), splitting into {len(chunks)} chunks")
        
        audio_parts = []
        for i, chunk in enumerate(chunks, 1):
            if len(chunk) > 10000:
                print(f"⚠️  Warning: Chunk {i} is still too long ({len(chunk)} chars), truncating")
                chunk = chunk[:5000]
            
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
            
            # Use SSML if voice parameters are specified
            if use_ssml:
                ssml_text = build_ssml(
                    text=chunk,
                    voice=voice_name,
                    language_code=language_code,
                    rate=rate,
                    pitch=pitch,
                    volume=volume,
                    express_as_style=express_as_style,
                    express_as_degree=express_as_degree
                )
                result = synthesizer.speak_ssml_async(ssml_text).get()
            else:
                result = synthesizer.speak_text_async(chunk).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_parts.append(result.audio_data)
                print(f"✅ Generated chunk {i}/{len(chunks)}")
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                print(f"❌ Azure TTS chunk {i} canceled")
                print(f"   Reason: {cancellation.reason}")
                if cancellation.error_details:
                    print(f"   Error: {cancellation.error_details}")
                return None
            else:
                print(f"❌ Azure TTS chunk {i} failed: {result.reason}")
                return None
        
        # Concatenate all audio parts
        audio_content = b''.join(audio_parts)
    else:
        # Single request for short text
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        
        # Use SSML if voice parameters are specified
        if use_ssml:
            ssml_text = build_ssml(
                text=text,
                voice=voice_name,
                language_code=language_code,
                rate=rate,
                pitch=pitch,
                volume=volume,
                express_as_style=express_as_style,
                express_as_degree=express_as_degree
            )
            print(f"🔍 Generated SSML:")
            print(ssml_text)
            print()
            result = synthesizer.speak_ssml_async(ssml_text).get()
        else:
            result = synthesizer.speak_text_async(text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_content = result.audio_data
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            print(f"❌ Azure TTS canceled")
            print(f"   Reason: {cancellation.reason}")
            if cancellation.error_details:
                print(f"   Error: {cancellation.error_details}")
            print(f"   Possible causes: Invalid SSML, unsupported voice style, or authentication failure")
            return None
        else:
            print(f"❌ Azure TTS failed: {result.reason}")
            return None
    
    return audio_content


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Generate audio using Azure Text-to-Speech API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python tts_azure.py --text "你好世界" --key YOUR_KEY --region eastasia
  
  # With voice tuning parameters
  python tts_azure.py --text "你好世界" -k YOUR_KEY -r eastasia --rate 0.9 --pitch 5 --volume 10
  
  # With emotion style
  python tts_azure.py --text "你好世界" -k YOUR_KEY -r eastasia --style cheerful --style-degree moderate
  
  # Full example with all parameters
  python tts_azure.py --text "從前在一個遙遠的森林裡，住著一隻勇敢的小兔子。" \
    --key YOUR_KEY --region eastasia --language zh-TW \
    --rate 0.95 --pitch 3 --volume 8 --style gentle --style-degree mild \
    --output story.mp3

Available emotion styles: cheerful, sad, gentle, angry, fearful, disgruntled, serious, affectionate
Note: For Taiwan/Asia users, use --region eastasia or southeastasia instead of eastus
        """
    )
    
    parser.add_argument(
        '--text', '-t',
        required=True,
        help='Text to convert to speech'
    )
    
    parser.add_argument(
        '--key', '-k',
        required=True,
        help='Azure Speech API key'
    )
    
    parser.add_argument(
        '--region', '-r',
        required=True,
        help='Azure region (e.g., eastus, eastasia, southeastasia). For Taiwan/Asia, use eastasia or southeastasia'
    )
    
    parser.add_argument(
        '--language', '-l',
        default='zh-TW',
        help='Language code (default: zh-TW)'
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
        '--style',
        default=None,
        help='Emotion style (e.g., cheerful, sad, gentle, angry, fearful)'
    )
    
    parser.add_argument(
        '--style-degree',
        default=None,
        help='Emotion intensity (mild, moderate, strong)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='output.mp3',
        help='Output file path (default: output.mp3)'
    )
    
    args = parser.parse_args()
    
    # Generate audio
    print(f"🎙️  Generating audio for text ({len(args.text)} characters)...")
    print(f"   Language: {args.language}")
    print(f"   Region: {args.region}")
    
    # Show voice parameters if specified
    if args.rate:
        print(f"   Rate: {args.rate}x")
    if args.pitch:
        print(f"   Pitch: {args.pitch:+.0f}%")
    if args.volume:
        print(f"   Volume: {args.volume:+.0f}%")
    if args.style:
        print(f"   Style: {args.style}" + (f" ({args.style_degree})" if args.style_degree else ""))
    
    audio_content = generate_audio(
        text=args.text,
        azure_key=args.key,
        azure_region=args.region,
        language=args.language,
        voice=args.voice,
        rate=args.rate,
        pitch=args.pitch,
        volume=args.volume,
        express_as_style=args.style,
        express_as_degree=args.style_degree
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
