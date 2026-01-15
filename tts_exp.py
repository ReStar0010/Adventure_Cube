#!/usr/bin/env python3
"""
TTS Quality Experimentation Script
Systematically test and compare TTS quality parameters for Vertex AI and Azure TTS services.
Helps identify optimal settings to make TTS sound less robotic and more natural.
"""

import os
import sys
import json
import csv
import time
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from io import BytesIO
from dataclasses import dataclass, asdict
from datetime import datetime

# Try to import required libraries
HAS_VERTEX_AI = False
HAS_AZURE = False

try:
    from google.cloud import texttospeech
    HAS_VERTEX_AI = True
except ImportError:
    print("⚠️  Warning: google-cloud-texttospeech not installed. Vertex AI tests will be skipped.")
    print("   Install with: pip install google-cloud-texttospeech")

try:
    import azure.cognitiveservices.speech as speechsdk
    HAS_AZURE = True
except ImportError:
    print("⚠️  Warning: azure-cognitiveservices-speech not installed. Azure tests will be skipped.")
    print("   Install with: pip install azure-cognitiveservices-speech")


@dataclass
class TTSExperiment:
    """Data class for a single TTS experiment."""
    service: str
    voice: str
    speaking_rate: float
    pitch: Optional[float]
    text_id: int
    text: str
    audio_file: str
    generation_time: float
    audio_size_bytes: int
    success: bool
    error: Optional[str] = None


# Sample test texts for quality evaluation
SAMPLE_TEXTS = [
    # Short sentences (兒童故事風格)
    "從前，在一個遙遠的魔法森林裡，住著一隻勇敢的小兔子。",
    "小兔子每天都會去探險，尋找美麗的花朵和美味的果實。",
    "有一天，小兔子遇到了一隻迷路的小鳥，牠決定幫助小鳥找到回家的路。",
    
    # Questions and exclamations
    "你知道嗎？友誼是最珍貴的寶藏！",
    "哇！這真是太神奇了！",
    "你願意和我一起冒險嗎？",
    
    # Numbers and dates
    "今天是2024年3月15日，天氣晴朗，適合外出探險。",
    "小兔子收集了五朵美麗的花，三顆閃亮的星星，還有兩片特別的葉子。",
    
    # Emotional expressions
    "小兔子感到非常開心，因為牠幫助了需要幫助的朋友。",
    "雖然路上遇到了困難，但小兔子從不放棄，總是保持著樂觀的態度。",
    "當小鳥終於回到家時，牠們都感到無比的快樂和滿足。",
    
    # Longer narrative
    "在一個充滿魔法的村莊裡，住著許多友善的動物朋友。他們互相幫助，分享快樂，一起度過每一個美好的日子。每當有人需要幫助時，大家都會伸出援手，讓整個村莊充滿了溫暖和愛。",
]


def find_gcp_credentials_file() -> Optional[str]:
    """
    Search for GCP credentials file in common locations.
    
    Returns:
        Path to credentials file if found, None otherwise
    """
    # Check if already set in environment
    if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if os.path.exists(cred_path):
            return cred_path
    
    # Common locations to search
    search_paths = [
        Path(__file__).parent / 'TTS_scripts' / 'gcp_credentials.json',
        Path(__file__).parent / 'gcp_credentials.json',
        Path(__file__).parent / 'credentials.json',
        Path.home() / '.config' / 'gcloud' / 'application_default_credentials.json',
    ]
    
    for path in search_paths:
        if path.exists() and path.is_file():
            return str(path.absolute())
    
    return None


def load_credentials(vertex_ai_key: Optional[str] = None, azure_key: Optional[str] = None, 
                    azure_region: str = "eastus", gcp_credentials_path: Optional[str] = None) -> Dict:
    """
    Load API credentials from arguments or environment variables.
    
    Args:
        vertex_ai_key: Vertex AI API key (deprecated - Vertex AI uses service account JSON)
        azure_key: Azure TTS API key (or use AZURE_TTS_KEY env var)
        azure_region: Azure region (default: eastus)
        gcp_credentials_path: Path to GCP service account JSON file
        
    Returns:
        Dictionary containing credentials
    """
    credentials = {}
    
    # Vertex AI credentials - requires service account JSON file
    gcp_cred_path = None
    if gcp_credentials_path:
        gcp_cred_path = gcp_credentials_path
    elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        gcp_cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    else:
        # Try to find credentials file automatically
        gcp_cred_path = find_gcp_credentials_file()
    
    if gcp_cred_path:
        if os.path.exists(gcp_cred_path):
            # Set environment variable for Google Cloud libraries
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = gcp_cred_path
            credentials['gcp_credentials_path'] = gcp_cred_path
            print(f"✅ Found GCP credentials: {gcp_cred_path}")
        else:
            print(f"⚠️  Warning: GCP credentials path specified but file not found: {gcp_cred_path}")
            credentials['gcp_credentials_path'] = None
    else:
        print("⚠️  Warning: GCP credentials not found. Vertex AI tests will be skipped.")
        print("   Set GOOGLE_APPLICATION_CREDENTIALS environment variable or use --gcp-credentials option")
        credentials['gcp_credentials_path'] = None
    
    # Azure credentials
    if azure_key:
        credentials['azure_key'] = azure_key
    elif os.environ.get('AZURE_TTS_KEY'):
        credentials['azure_key'] = os.environ.get('AZURE_TTS_KEY')
    else:
        # Use the provided key from plan
        credentials['azure_key'] = 'UMsGImykQR8T0qPbpG8gQAyMZ4uOP7vIoDvIgLzH95nZKYWf5YnHJQQJ99BKAC3pKaRXJ3w3AAAYACOG7d1p'
    
    credentials['azure_region'] = azure_region or os.environ.get('AZURE_TTS_REGION', 'eastus')
    
    return credentials


def setup_output_directory(base_dir: Path = Path('tts_experiments')) -> Tuple[Path, Path]:
    """
    Create output directory structure for experiments.
    
    Args:
        base_dir: Base directory for experiments
        
    Returns:
        Tuple of (audio_dir, results_dir)
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = base_dir / 'audio'
    audio_dir.mkdir(parents=True, exist_ok=True)
    results_dir = base_dir / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    return audio_dir, results_dir


def list_available_voices(language_code: str = 'cmn-TW', credentials: Optional[Dict] = None) -> List[str]:
    """
    List available voices for a given language code.
    
    Args:
        language_code: Language code (e.g., 'zh-TW')
        credentials: Optional credentials dictionary
        
    Returns:
        List of available voice names
    """
    if not HAS_VERTEX_AI:
        return []
    
    # Check if credentials are available
    if credentials:
        if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
            cred_path = credentials.get('gcp_credentials_path')
            if cred_path and os.path.exists(cred_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
    
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        return []
    
    try:
        client = texttospeech.TextToSpeechClient()
        voices = client.list_voices(language_code=language_code)
        return [voice.name for voice in voices.voices]
    except Exception as e:
        print(f"⚠️  Warning: Could not list voices: {e}")
        return []


def create_test_matrix() -> List[Dict]:
    """
    Create comprehensive test parameter matrix.
    
    Returns:
        List of parameter combinations to test
    """
    test_matrix = []
    
    # Vertex AI test parameters
    # Note: For Traditional Chinese, use 'cmn-TW' language code, not 'zh-TW'
    vertex_ai_voices = [
        'cmn-TW-Wavenet-A',       # Wavenet female voice (high quality)
        'cmn-TW-Wavenet-B',       # Wavenet female voice variant
    ]
    
    # Azure test parameters
    azure_voices = [
        'zh-TW-HsiaoChenNeural',
        'zh-TW-HsiaoYuNeural',
        'zh-TW-YunJheNeural',
    ]
    
    # Speaking rates to test
    speaking_rates = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]
    
    # Pitch adjustments (for Vertex AI, in semitones)
    pitch_values = [-2, -1, 0, 1, 2]
    
    # Create Vertex AI test combinations
    for voice in vertex_ai_voices:
        for rate in speaking_rates:
            for pitch in pitch_values:
                test_matrix.append({
                    'service': 'vertex_ai',
                    'voice': voice,
                    'speaking_rate': rate,
                    'pitch': pitch,
                })
    
    # Create Azure test combinations
    for voice in azure_voices:
        for rate in speaking_rates:
            # Azure uses SSML for pitch, test a few key values
            for pitch in [-10, -5, 0, 5, 10]:  # Percentage-based for Azure
                test_matrix.append({
                    'service': 'azure',
                    'voice': voice,
                    'speaking_rate': rate,
                    'pitch': pitch,
                })
    
    return test_matrix


def generate_vertex_ai_tts(text: str, voice: str, speaking_rate: float, 
                           pitch: float, credentials: Dict) -> Tuple[Optional[bytes], float, Optional[str]]:
    """
    Generate TTS audio using Vertex AI with specified parameters.
    
    Args:
        text: Text to convert to speech
        voice: Voice name (e.g., 'zh-TW-Neural2-A')
        speaking_rate: Speaking rate (0.25 to 4.0)
        pitch: Pitch adjustment in semitones (-20 to 20)
        credentials: Dictionary containing API credentials
        
    Returns:
        Tuple of (audio_bytes, generation_time, error_message)
    
    Note:
        Vertex AI Text-to-Speech requires service account credentials.
        Set GOOGLE_APPLICATION_CREDENTIALS environment variable to path of JSON file,
        or ensure credentials are configured via gcloud CLI.
    """
    if not HAS_VERTEX_AI:
        return None, 0.0, "google-cloud-texttospeech not installed"
    
    # Check if credentials are available
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        cred_path = credentials.get('gcp_credentials_path')
        if cred_path and os.path.exists(cred_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
        else:
            return None, 0.0, "GCP credentials not found. Set GOOGLE_APPLICATION_CREDENTIALS or use --gcp-credentials"
    
    try:
        start_time = time.time()
        
        # Initialize client (will use GOOGLE_APPLICATION_CREDENTIALS from environment)
        client = texttospeech.TextToSpeechClient()
        
        # Parse voice name to get language code
        # For Traditional Chinese, Google Cloud uses 'cmn-TW', not 'zh-TW'
        if voice.startswith('cmn-TW'):
            language_code = 'cmn-TW'
        elif voice.startswith('zh-TW'):
            language_code = 'cmn-TW'  # Convert zh-TW to cmn-TW
        else:
            language_code = 'cmn-TW'  # Default to Traditional Chinese
        
        # Set up synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Configure voice - don't specify ssml_gender if voice name is provided
        # The voice name already determines the gender
        voice_config = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice
        )
        
        # Configure audio with parameters
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch
        )
        
        # Perform synthesis
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_config,
            audio_config=audio_config
        )
        
        generation_time = time.time() - start_time
        
        return response.audio_content, generation_time, None
        
    except Exception as e:
        error_msg = str(e)
        return None, 0.0, error_msg


def generate_azure_tts(text: str, voice: str, speaking_rate: float, 
                      pitch: float, credentials: Dict) -> Tuple[Optional[bytes], float, Optional[str]]:
    """
    Generate TTS audio using Azure TTS with SSML support.
    
    Args:
        text: Text to convert to speech
        voice: Voice name (e.g., 'zh-TW-HsiaoChenNeural')
        speaking_rate: Speaking rate (0.5 to 2.0, as multiplier)
        pitch: Pitch adjustment in percentage (-50 to 50)
        credentials: Dictionary containing API credentials
        
    Returns:
        Tuple of (audio_bytes, generation_time, error_message)
    """
    if not HAS_AZURE:
        return None, 0.0, "azure-cognitiveservices-speech not installed"
    
    try:
        start_time = time.time()
        
        azure_key = credentials.get('azure_key')
        azure_region = credentials.get('azure_region', 'eastus')
        
        if not azure_key:
            return None, 0.0, "Azure credentials not provided"
        
        # Configure speech synthesizer
        speech_config = speechsdk.SpeechConfig(
            subscription=azure_key,
            region=azure_region
        )
        
        # Set language and voice
        speech_config.speech_synthesis_language = 'zh-TW'
        speech_config.speech_synthesis_voice_name = voice
        
        # Create SSML with prosody parameters
        # Convert speaking_rate to percentage (Azure uses percentage: 50% to 200%)
        rate_percent = int(speaking_rate * 100)
        rate_percent = max(50, min(200, rate_percent))  # Clamp to valid range
        
        # Convert pitch to percentage string
        pitch_str = f"{pitch:+d}%"
        
        # Build SSML
        ssml_text = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-TW">
    <voice name="{voice}">
        <prosody rate="{rate_percent}%" pitch="{pitch_str}">
            {text}
        </prosody>
    </voice>
</speak>'''
        
        # Create synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        
        # Synthesize using SSML
        result = synthesizer.speak_ssml_async(ssml_text).get()
        
        generation_time = time.time() - start_time
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data, generation_time, None
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speechsdk.CancellationDetails(result)
            error_msg = f"Canceled: {cancellation_details.reason}"
            if cancellation_details.error_details:
                error_msg += f" - {cancellation_details.error_details}"
            return None, generation_time, error_msg
        else:
            return None, generation_time, f"Failed: {result.reason}"
            
    except Exception as e:
        error_msg = str(e)
        return None, 0.0, error_msg


def run_experiments(test_matrix: List[Dict], sample_texts: List[str], 
                   credentials: Dict, audio_dir: Path, 
                   max_tests: Optional[int] = None) -> List[TTSExperiment]:
    """
    Run all TTS experiments.
    
    Args:
        test_matrix: List of parameter combinations to test
        sample_texts: List of sample texts to test
        credentials: API credentials
        audio_dir: Directory to save audio files
        max_tests: Maximum number of tests to run (None for all)
        
    Returns:
        List of experiment results
    """
    results = []
    total_tests = len(test_matrix) * len(sample_texts)
    if max_tests:
        total_tests = min(total_tests, max_tests)
    
    test_count = 0
    
    print(f"\n{'='*80}")
    print(f"Running TTS Quality Experiments")
    print(f"{'='*80}")
    print(f"Total parameter combinations: {len(test_matrix)}")
    print(f"Sample texts: {len(sample_texts)}")
    print(f"Total experiments: {total_tests}")
    if max_tests:
        print(f"Limited to: {max_tests} tests")
    print(f"{'='*80}\n")
    
    for param_idx, params in enumerate(test_matrix):
        if max_tests and test_count >= max_tests:
            break
            
        service = params['service']
        voice = params['voice']
        rate = params['speaking_rate']
        pitch = params['pitch']
        
        print(f"[{param_idx + 1}/{len(test_matrix)}] Testing {service} - {voice} (rate={rate}, pitch={pitch})")
        
        for text_idx, text in enumerate(sample_texts):
            if max_tests and test_count >= max_tests:
                break
            
            test_count += 1
            
            # Generate audio
            if service == 'vertex_ai':
                audio_bytes, gen_time, error = generate_vertex_ai_tts(
                    text, voice, rate, pitch, credentials
                )
            elif service == 'azure':
                audio_bytes, gen_time, error = generate_azure_tts(
                    text, voice, rate, pitch, credentials
                )
            else:
                continue
            
            # Create filename
            safe_voice = voice.replace('-', '_').replace(' ', '_')
            filename = f"{service}_{safe_voice}_r{rate}_p{pitch}_t{text_idx}.mp3"
            audio_path = audio_dir / filename
            
            # Save audio if successful
            success = audio_bytes is not None and error is None
            audio_size = len(audio_bytes) if audio_bytes else 0
            
            if success:
                with open(audio_path, 'wb') as f:
                    f.write(audio_bytes)
            
            # Create experiment record
            experiment = TTSExperiment(
                service=service,
                voice=voice,
                speaking_rate=rate,
                pitch=pitch,
                text_id=text_idx,
                text=text[:100] + "..." if len(text) > 100 else text,  # Truncate for storage
                audio_file=str(audio_path),
                generation_time=gen_time,
                audio_size_bytes=audio_size,
                success=success,
                error=error
            )
            
            results.append(experiment)
            
            # Print status
            if success:
                print(f"  ✅ Text {text_idx + 1}: {gen_time:.2f}s ({audio_size/1024:.1f} KB)")
            else:
                print(f"  ❌ Text {text_idx + 1}: {error}")
        
        print()
    
    print(f"\n✅ Completed {test_count} experiments")
    return results


def save_results_json(results: List[TTSExperiment], output_path: Path):
    """
    Save experiment results to JSON file.
    
    Args:
        results: List of experiment results
        output_path: Path to save JSON file
    """
    data = {
        'timestamp': datetime.now().isoformat(),
        'total_experiments': len(results),
        'successful': sum(1 for r in results if r.success),
        'failed': sum(1 for r in results if not r.success),
        'experiments': [asdict(r) for r in results]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 JSON results saved to: {output_path}")


def save_results_csv(results: List[TTSExperiment], output_path: Path):
    """
    Save experiment results to CSV file.
    
    Args:
        results: List of experiment results
        output_path: Path to save CSV file
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'service', 'voice', 'speaking_rate', 'pitch', 'text_id', 
            'text_preview', 'audio_file', 'generation_time', 
            'audio_size_bytes', 'audio_size_kb', 'success', 'error'
        ])
        
        writer.writeheader()
        
        for r in results:
            writer.writerow({
                'service': r.service,
                'voice': r.voice,
                'speaking_rate': r.speaking_rate,
                'pitch': r.pitch,
                'text_id': r.text_id,
                'text_preview': r.text,
                'audio_file': r.audio_file,
                'generation_time': r.generation_time,
                'audio_size_bytes': r.audio_size_bytes,
                'audio_size_kb': r.audio_size_bytes / 1024,
                'success': r.success,
                'error': r.error or ''
            })
    
    print(f"💾 CSV results saved to: {output_path}")


def print_summary(results: List[TTSExperiment]):
    """
    Print summary statistics of experiments.
    
    Args:
        results: List of experiment results
    """
    if not results:
        print("No results to summarize")
        return
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    print(f"\n{'='*80}")
    print("EXPERIMENT SUMMARY")
    print(f"{'='*80}")
    print(f"Total experiments: {len(results)}")
    print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    
    if successful:
        avg_time = sum(r.generation_time for r in successful) / len(successful)
        avg_size = sum(r.audio_size_bytes for r in successful) / len(successful)
        
        print(f"\nAverage generation time: {avg_time:.2f}s")
        print(f"Average audio size: {avg_size/1024:.1f} KB")
        
        # Group by service
        print(f"\nBy Service:")
        for service in ['vertex_ai', 'azure']:
            service_results = [r for r in successful if r.service == service]
            if service_results:
                print(f"  {service}: {len(service_results)} successful")
                avg_time = sum(r.generation_time for r in service_results) / len(service_results)
                print(f"    Average time: {avg_time:.2f}s")
        
        # Group by voice
        print(f"\nBy Voice:")
        voices = set(r.voice for r in successful)
        for voice in sorted(voices):
            voice_results = [r for r in successful if r.voice == voice]
            if voice_results:
                print(f"  {voice}: {len(voice_results)} successful")
    
    if failed:
        print(f"\nFailed Experiments:")
        error_counts = {}
        for r in failed:
            error = r.error or "Unknown error"
            error_counts[error] = error_counts.get(error, 0) + 1
        
        for error, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            print(f"  {error}: {count}")
    
    print(f"{'='*80}\n")


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='TTS Quality Experimentation Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all experiments with default credentials
  python tts_exp.py
  
  # Run limited number of tests (for quick testing)
  python tts_exp.py --max-tests 50
  
  # Test only specific text sample
  python tts_exp.py --text-only 0
  
  # Use custom credentials
  python tts_exp.py --vertex-key YOUR_KEY --azure-key YOUR_KEY --azure-region eastus
  
  # Use environment variables
  export VERTEX_AI_API_KEY=your_key
  export AZURE_TTS_KEY=your_key
  python tts_exp.py

Note on Vertex AI:
  Vertex AI Text-to-Speech requires service account credentials (JSON file).
  Options:
    1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable:
       export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
    2. Use --gcp-credentials option:
       python tts_exp.py --gcp-credentials /path/to/service-account.json
    3. Place credentials.json in TTS_scripts/ directory (auto-detected)
    4. Skip Vertex AI tests: python tts_exp.py --skip-vertex
        """
    )
    
    parser.add_argument('--vertex-key', type=str, help='Vertex AI API key (deprecated - use --gcp-credentials instead)')
    parser.add_argument('--gcp-credentials', type=str, help='Path to GCP service account JSON credentials file')
    parser.add_argument('--azure-key', type=str, help='Azure TTS API key')
    parser.add_argument('--azure-region', type=str, default='eastus', help='Azure region (default: eastus)')
    parser.add_argument('--output-dir', type=str, default='tts_experiments', help='Output directory (default: tts_experiments)')
    parser.add_argument('--max-tests', type=int, help='Maximum number of tests to run (for quick testing)')
    parser.add_argument('--text-only', type=int, help='Test only specific text index (0-based)')
    parser.add_argument('--skip-vertex', action='store_true', help='Skip Vertex AI tests (useful if credentials not available)')
    parser.add_argument('--list-voices', action='store_true', help='List available voices and exit')
    
    args = parser.parse_args()
    
    # If --list-voices is specified, list voices and exit
    if args.list_voices:
        print("🔍 Listing available voices...")
        credentials = load_credentials(
            vertex_ai_key=args.vertex_key,
            azure_key=args.azure_key,
            azure_region=args.azure_region,
            gcp_credentials_path=args.gcp_credentials
        )
        
        if credentials.get('gcp_credentials_path'):
            print("\n📢 Available cmn-TW (Traditional Chinese) voices in Vertex AI:")
            voices = list_available_voices('cmn-TW', credentials)
            if not voices:
                # Also try zh-TW in case it's supported
                print("\n📢 Also checking zh-TW voices:")
                voices = list_available_voices('zh-TW', credentials)
            if voices:
                for voice in sorted(voices):
                    print(f"  - {voice}")
            else:
                print("  ⚠️  Could not retrieve voice list")
        else:
            print("  ⚠️  GCP credentials not found")
        
        sys.exit(0)
    
    # Load credentials
    print("🔑 Loading credentials...")
    credentials = load_credentials(
        vertex_ai_key=args.vertex_key,
        azure_key=args.azure_key,
        azure_region=args.azure_region,
        gcp_credentials_path=args.gcp_credentials
    )
    
    # Setup output directories
    output_dir = Path(args.output_dir)
    audio_dir, results_dir = setup_output_directory(output_dir)
    
    # Prepare sample texts
    sample_texts = SAMPLE_TEXTS
    if args.text_only is not None:
        if 0 <= args.text_only < len(sample_texts):
            sample_texts = [sample_texts[args.text_only]]
            print(f"📝 Testing only text index {args.text_only}")
        else:
            print(f"⚠️  Invalid text index {args.text_only}, using all texts")
    
    # Create test matrix
    print("📊 Creating test parameter matrix...")
    test_matrix = create_test_matrix()
    
    # Filter out Vertex AI tests if skipping or credentials not available
    if args.skip_vertex or not credentials.get('gcp_credentials_path'):
        print("⚠️  Skipping Vertex AI tests (credentials not available or --skip-vertex specified)")
        test_matrix = [t for t in test_matrix if t['service'] != 'vertex_ai']
    
    print(f"   Generated {len(test_matrix)} parameter combinations")
    
    # Run experiments
    results = run_experiments(
        test_matrix=test_matrix,
        sample_texts=sample_texts,
        credentials=credentials,
        audio_dir=audio_dir,
        max_tests=args.max_tests
    )
    
    if not results:
        print("❌ No experiments completed")
        sys.exit(1)
    
    # Save results
    print("\n💾 Saving results...")
    json_path = results_dir / 'results.json'
    csv_path = results_dir / 'comparison.csv'
    
    save_results_json(results, json_path)
    save_results_csv(results, csv_path)
    
    # Print summary
    print_summary(results)
    
    print(f"\n✅ Experimentation complete!")
    print(f"📁 Audio files: {audio_dir}")
    print(f"📊 Results: {results_dir}")
    print(f"\n💡 Tip: Listen to the audio files to compare quality and identify the best settings.")


if __name__ == '__main__':
    main()
