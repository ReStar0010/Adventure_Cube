#!/usr/bin/env python3
"""
Azure TTS Parameter Tuning Script
調整所有 Azure TTS 參數並生成單個 MP3 文件，用於測試不同設定。
"""

import os
import sys
import argparse
import time
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

# Try to import Azure TTS library
try:
    import azure.cognitiveservices.speech as speechsdk
    HAS_AZURE = True
except ImportError:
    print("❌ Error: azure-cognitiveservices-speech not installed.")
    print("   Install with: pip install azure-cognitiveservices-speech")
    sys.exit(1)


def load_azure_credentials(azure_key: Optional[str] = None, azure_region: str = "eastus") -> Dict:
    """
    Load Azure TTS credentials from arguments or environment variables.
    
    Args:
        azure_key: Azure TTS API key (or use AZURE_TTS_KEY env var)
        azure_region: Azure region (default: eastus)
        
    Returns:
        Dictionary containing credentials
    """
    credentials = {}
    key_source = "default (may be expired)"
    
    if azure_key:
        credentials['azure_key'] = azure_key
        key_source = "command line argument"
    elif os.environ.get('AZURE_TTS_KEY'):
        credentials['azure_key'] = os.environ.get('AZURE_TTS_KEY')
        key_source = "AZURE_TTS_KEY environment variable"
    elif os.environ.get('AZURE_SPEECH_KEY'):
        credentials['azure_key'] = os.environ.get('AZURE_SPEECH_KEY')
        key_source = "AZURE_SPEECH_KEY environment variable"
    else:
        # No credentials found
        print("\n❌ Error: No Azure credentials found!")
        print("\n💡 Please provide Azure credentials using one of these methods:")
        print("\n   Method 1: Environment Variables (Recommended)")
        print("   export AZURE_SPEECH_KEY='your_key_here'")
        print("   export AZURE_SPEECH_REGION='eastus'  # or your region")
        print("\n   Method 2: Command Line Arguments")
        print("   python3 tts_azure_tuned.py --azure-key YOUR_KEY --azure-region eastus")
        print("\n   Get your credentials from: https://portal.azure.com/")
        print("   → Speech Services → Keys and Endpoint")
        print("\n   Then run: python3 test_azure_credentials.py to verify")
        return None
    
    credentials['azure_region'] = azure_region or os.environ.get('AZURE_TTS_REGION') or os.environ.get('AZURE_SPEECH_REGION', 'eastus')
    credentials['key_source'] = key_source
    
    # Mask the key for display
    key = credentials['azure_key']
    if len(key) > 8:
        masked_key = key[:4] + "..." + key[-4:]
    else:
        masked_key = "***"
    
    print(f"   API Key: {masked_key} (from {key_source})")
    print(f"   Region: {credentials['azure_region']}")
    
    return credentials


def build_ssml(
    text: str,
    voice: str = 'zh-TW-HsiaoChenNeural',
    rate: Optional[float] = None,
    pitch: Optional[float] = None,
    volume: Optional[float] = None,
    break_before: Optional[str] = None,
    break_after: Optional[str] = None,
    emphasis_level: Optional[str] = None,
    emphasis_words: Optional[str] = None,
    express_as_style: Optional[str] = None,
    express_as_degree: Optional[str] = None,
    silence_before: Optional[str] = None,
    silence_after: Optional[str] = None,
) -> str:
    """
    Build SSML with all Azure TTS parameters.
    
    Args:
        text: Text to convert to speech
        voice: Voice name (e.g., 'zh-TW-HsiaoChenNeural')
        rate: Speaking rate (0.5 to 2.0, or percentage string like "90%", "slow", "medium", "fast")
        pitch: Pitch adjustment (-50% to +50%, or semitone string like "-2st", "+1st")
        volume: Volume adjustment (-100% to +100%, or string like "silent", "x-soft", "soft", "medium", "loud", "x-loud")
        break_before: Break before text (e.g., "500ms", "1s", "none", "x-weak", "weak", "medium", "strong", "x-strong")
        break_after: Break after text
        emphasis_level: Emphasis level ("reduced", "none", "moderate", "strong")
        emphasis_words: Words to emphasize (comma-separated, will wrap in <emphasis> tags)
        express_as_style: Express-as style (e.g., "cheerful", "sad", "angry", "fearful", "disgruntled", "serious", "affectionate", "gentle", "lyrical")
        express_as_degree: Express-as degree ("default", "mild", "moderate", "strong")
        silence_before: Silence before (ms, e.g., "500ms")
        silence_after: Silence after (ms, e.g., "500ms")
        
    Returns:
        SSML string
    """
    # Build prosody attributes
    prosody_attrs = []
    
    if rate is not None:
        if isinstance(rate, (int, float)):
            # Convert to percentage
            rate_percent = int(rate * 100)
            rate_percent = max(50, min(200, rate_percent))
            prosody_attrs.append(f'rate="{rate_percent}%"')
        else:
            prosody_attrs.append(f'rate="{rate}"')
    
    if pitch is not None:
        if isinstance(pitch, (int, float)):
            # Convert to percentage (pitch is already in percentage, e.g., 5 means +5%)
            pitch_int = int(pitch)
            pitch_str = f"{pitch_int:+d}%"
            prosody_attrs.append(f'pitch="{pitch_str}"')
        else:
            prosody_attrs.append(f'pitch="{pitch}"')
    
    if volume is not None:
        if isinstance(volume, (int, float)):
            # Convert to percentage (volume is already in percentage, e.g., 10 means +10%)
            volume_int = int(volume)
            volume_str = f"{volume_int:+d}%"
            prosody_attrs.append(f'volume="{volume_str}"')
        else:
            prosody_attrs.append(f'volume="{volume}"')
    
    prosody_attr_str = " ".join(prosody_attrs)
    
    # Build content with optional tags
    content = text
    
    # Add emphasis if specified
    if emphasis_words and emphasis_level:
        # Split words and wrap each in emphasis tag
        words = emphasis_words.split(',')
        for word in words:
            word = word.strip()
            if word in content:
                content = content.replace(
                    word,
                    f'<emphasis level="{emphasis_level}">{word}</emphasis>'
                )
    
    # Add breaks
    if break_before:
        content = f'<break time="{break_before}"/>' + content
    
    if break_after:
        content = content + f'<break time="{break_after}"/>'
    
    # Add silence (using mstts:silence)
    if silence_before:
        content = f'<mstts:silence type="Sentenceboundary" value="{silence_before}"/>' + content
    
    if silence_after:
        content = content + f'<mstts:silence type="Sentenceboundary" value="{silence_after}"/>'
    
    # Build SSML structure
    ssml_parts = [
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"',
        'xmlns:mstts="https://www.w3.org/2001/mstts"',
        'xml:lang="zh-TW">'
    ]
    
    # Add express-as if specified
    if express_as_style:
        # Always set degree to avoid issues
        degree = express_as_degree or 'default'
        
        ssml_parts.append(f'    <voice name="{voice}">')
        ssml_parts.append(f'        <mstts:express-as style="{express_as_style}" degree="{degree}">')
        
        if prosody_attr_str:
            ssml_parts.append(f'            <prosody {prosody_attr_str}>')
            ssml_parts.append(f'                {content}')
            ssml_parts.append(f'            </prosody>')
        else:
            ssml_parts.append(f'            {content}')
        
        ssml_parts.append(f'        </mstts:express-as>')
        ssml_parts.append(f'    </voice>')
    else:
        # Standard structure
        ssml_parts.append(f'    <voice name="{voice}">')
        if prosody_attr_str:
            ssml_parts.append(f'        <prosody {prosody_attr_str}>')
            ssml_parts.append(f'            {content}')
            ssml_parts.append(f'        </prosody>')
        else:
            ssml_parts.append(f'        {content}')
        ssml_parts.append(f'    </voice>')
    
    ssml_parts.append('</speak>')
    
    return '\n'.join(ssml_parts)


def generate_azure_tts(
    text: str,
    output_path: str,
    credentials: Dict,
    voice: str = 'zh-TW-HsiaoChenNeural',
    rate: Optional[float] = None,
    pitch: Optional[float] = None,
    volume: Optional[float] = None,
    break_before: Optional[str] = None,
    break_after: Optional[str] = None,
    emphasis_level: Optional[str] = None,
    emphasis_words: Optional[str] = None,
    express_as_style: Optional[str] = None,
    express_as_degree: Optional[str] = None,
    silence_before: Optional[str] = None,
    silence_after: Optional[str] = None,
) -> bool:
    """
    Generate Azure TTS audio with all parameters.
    
    Returns:
        True if successful, False otherwise
    """
    azure_key = credentials.get('azure_key')
    azure_region = credentials.get('azure_region', 'eastus')
    
    if not azure_key:
        print("❌ Error: Azure credentials not provided")
        return False
    
    try:
        print("🎙️  Generating audio with Azure TTS...")
        start_time = time.time()
        
        # Configure speech synthesizer
        speech_config = speechsdk.SpeechConfig(
            subscription=azure_key,
            region=azure_region
        )
        
        # Set language and voice
        speech_config.speech_synthesis_language = 'zh-TW'
        speech_config.speech_synthesis_voice_name = voice
        
        # Build SSML
        ssml_text = build_ssml(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
            break_before=break_before,
            break_after=break_after,
            emphasis_level=emphasis_level,
            emphasis_words=emphasis_words,
            express_as_style=express_as_style,
            express_as_degree=express_as_degree,
            silence_before=silence_before,
            silence_after=silence_after,
        )
        
        # Print SSML for debugging
        print("\n📝 Generated SSML:")
        print("-" * 80)
        print(ssml_text)
        print("-" * 80)
        
        # Create synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        
        # Synthesize using SSML
        result = synthesizer.speak_ssml_async(ssml_text).get()
        
        generation_time = time.time() - start_time
        
        # Debug: Print result reason
        print(f"\n🔍 Result reason: {result.reason}")
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Save audio file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'wb') as f:
                f.write(result.audio_data)
            
            file_size = len(result.audio_data)
            print(f"\n✅ Audio generated successfully!")
            print(f"   📁 File: {output_file.absolute()}")
            print(f"   ⏱️  Generation time: {generation_time:.2f}s")
            print(f"   📊 File size: {file_size/1024:.1f} KB")
            return True
            
        elif result.reason == speechsdk.ResultReason.Canceled:
            # Try to get cancellation details safely
            try:
                cancellation_details = result.cancellation_details
                error_msg = f"Canceled: {cancellation_details.reason}"
                if cancellation_details.error_details:
                    error_msg += f"\n   Details: {cancellation_details.error_details}"
                print(f"❌ Error: {error_msg}")
                
                # Provide helpful hints based on the error
                if "401" in str(cancellation_details.error_details) or "Authentication" in str(cancellation_details.error_details):
                    print("\n💡 Authentication Error (401) - Possible solutions:")
                    print("   1. Check your Azure API key is valid and not expired")
                    print("   2. Verify the region is correct (current: {})".format(azure_region))
                    print("   3. Set environment variable: export AZURE_TTS_KEY='your_valid_key'")
                    print("   4. Or use command line: --azure-key YOUR_KEY --azure-region YOUR_REGION")
                    print("\n   Get your credentials from: https://portal.azure.com/")
                    print("   → Speech Services → Keys and Endpoint")
            except Exception as detail_error:
                print(f"❌ Error: Synthesis was canceled (could not get details: {detail_error})")
            return False
        else:
            print(f"❌ Error: Synthesis failed with reason: {result.reason}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Azure TTS Parameter Tuning Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default text
  python tts_azure_tuned.py --text "從前，在一個遙遠的魔法森林裡，住著一隻勇敢的小兔子。"
  
  # Adjust rate and pitch
  python tts_azure_tuned.py --text "你好" --rate 0.9 --pitch 5
  
  # Use express-as for emotion
  python tts_azure_tuned.py --text "太棒了！" --express-as-style cheerful --express-as-degree strong
  
  # Add breaks and emphasis
  python tts_azure_tuned.py --text "注意！這很重要。" --break-before "500ms" --emphasis-words "注意,重要" --emphasis-level strong
  
  # Full example with all parameters
  python tts_azure_tuned.py \\
    --text "從前，在一個遙遠的魔法森林裡，住著一隻勇敢的小兔子。" \\
    --voice zh-TW-HsiaoChenNeural \\
    --rate 0.9 \\
    --pitch 5 \\
    --volume 10 \\
    --break-after "1s" \\
    --express-as-style cheerful \\
    --output test_audio.mp3
  
  # Test with recommended voices
  python tts_azure_tuned.py --text "測試文本" --voice zh-TW-HsiaoChenNeural
  python tts_azure_tuned.py --text "測試文本" --voice zh-TW-HsiaoYuNeural

Available Voices (Recommended):
  --voice: zh-TW-HsiaoChenNeural (default, warm female)
           zh-TW-HsiaoYuNeural (friendly female)
           zh-TW-YunJheNeural (friendly male)

Parameter Ranges:
  --rate: 0.5 to 2.0 (or "slow", "medium", "fast", "x-slow", "x-fast")
  --pitch: -50 to 50 (percentage) or semitones like "-2st", "+1st"
  --volume: -100 to 100 (percentage) or "silent", "x-soft", "soft", "medium", "loud", "x-loud"
  --break-before/after: "500ms", "1s", "none", "x-weak", "weak", "medium", "strong", "x-strong"
  --emphasis-level: "reduced", "none", "moderate", "strong"
  --express-as-style: "cheerful", "sad", "angry", "fearful", "disgruntled", "serious", "affectionate", "gentle", "lyrical"
  --express-as-degree: "default", "mild", "moderate", "strong"
        """
    )
    
    # Text input
    parser.add_argument('--text', type=str, 
                       default="從前，在一個遙遠的魔法森林裡，住著一隻勇敢的小兔子。小兔子每天都會去探險，尋找美麗的花朵和美味的果實。",
                       help='Text to convert to speech (default: sample story text)')
    parser.add_argument('--text-file', type=str, help='Read text from file instead of --text')
    
    # Voice selection
    # Recommended voices: zh-TW-HsiaoChenNeural, zh-TW-HsiaoYuNeural
    parser.add_argument('--voice', type=str, default='zh-TW-HsiaoChenNeural',
                       help='Voice name (default: zh-TW-HsiaoChenNeural). Recommended: zh-TW-HsiaoChenNeural, zh-TW-HsiaoYuNeural')
    
    # Prosody parameters
    parser.add_argument('--rate', type=float, help='Speaking rate (0.5-2.0, or string like "slow", "medium", "fast")')
    parser.add_argument('--pitch', type=float, help='Pitch adjustment (-50 to 50%%, or semitones like "-2st")')
    parser.add_argument('--volume', type=float, help='Volume adjustment (-100 to 100%%, or string like "loud", "soft")')
    
    # Break parameters
    parser.add_argument('--break-before', type=str, help='Break before text (e.g., "500ms", "1s", "strong")')
    parser.add_argument('--break-after', type=str, help='Break after text (e.g., "500ms", "1s", "strong")')
    
    # Emphasis parameters
    parser.add_argument('--emphasis-level', type=str, choices=['reduced', 'none', 'moderate', 'strong'],
                       help='Emphasis level for emphasized words')
    parser.add_argument('--emphasis-words', type=str, 
                       help='Words to emphasize (comma-separated, e.g., "重要,注意")')
    
    # Express-as parameters (emotion)
    parser.add_argument('--express-as-style', type=str,
                       choices=['cheerful', 'sad', 'angry', 'fearful', 'disgruntled', 'serious', 
                               'affectionate', 'gentle', 'lyrical'],
                       help='Express-as style (emotion)')
    parser.add_argument('--express-as-degree', type=str, 
                       choices=['default', 'mild', 'moderate', 'strong'],
                       help='Express-as degree (intensity)')
    
    # Silence parameters
    parser.add_argument('--silence-before', type=str, help='Silence before (e.g., "500ms")')
    parser.add_argument('--silence-after', type=str, help='Silence after (e.g., "500ms")')
    
    # Output
    parser.add_argument('--output', '-o', type=str, default=None,
                       help='Output file path (default: auto-generated with timestamp)')
    
    # Credentials
    parser.add_argument('--azure-key', type=str, help='Azure TTS API key (or use AZURE_TTS_KEY env var)')
    parser.add_argument('--azure-region', type=str, default='eastus', 
                       help='Azure region (default: eastus)')
    
    args = parser.parse_args()
    
    # Load text from file if specified
    text = args.text
    if args.text_file:
        text_file = Path(args.text_file)
        if text_file.exists():
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            print(f"❌ Error: Text file not found: {text_file}")
            sys.exit(1)
    
    # Load credentials
    print("🔑 Loading Azure credentials...")
    credentials = load_azure_credentials(
        azure_key=args.azure_key,
        azure_region=args.azure_region
    )
    
    if credentials is None:
        sys.exit(1)
    
    # Generate output filename if not specified
    if args.output:
        output_path = args.output
    else:
        # Auto-generate filename with parameters
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        params = []
        if args.rate:
            params.append(f"r{args.rate}")
        if args.pitch:
            params.append(f"p{args.pitch}")
        if args.volume:
            params.append(f"v{args.volume}")
        if args.express_as_style:
            params.append(f"e{args.express_as_style}")
        
        param_str = "_".join(params) if params else "default"
        output_path = f"azure_tts_{timestamp}_{param_str}.mp3"
    
    # Print configuration
    print("\n📋 Configuration:")
    print(f"   Voice: {args.voice}")
    print(f"   Text length: {len(text)} characters")
    if args.rate:
        print(f"   Rate: {args.rate}")
    if args.pitch:
        print(f"   Pitch: {args.pitch}")
    if args.volume:
        print(f"   Volume: {args.volume}")
    if args.express_as_style:
        print(f"   Express-as: {args.express_as_style} ({args.express_as_degree or 'default'})")
    print()
    
    # Generate audio
    success = generate_azure_tts(
        text=text,
        output_path=output_path,
        credentials=credentials,
        voice=args.voice,
        rate=args.rate,
        pitch=args.pitch,
        volume=args.volume,
        break_before=args.break_before,
        break_after=args.break_after,
        emphasis_level=args.emphasis_level,
        emphasis_words=args.emphasis_words,
        express_as_style=args.express_as_style,
        express_as_degree=args.express_as_degree,
        silence_before=args.silence_before,
        silence_after=args.silence_after,
    )
    
    if success:
        print(f"\n🎉 Done! Listen to the audio file to evaluate the settings.")
    else:
        print(f"\n❌ Failed to generate audio.")
        sys.exit(1)


if __name__ == '__main__':
    main()
