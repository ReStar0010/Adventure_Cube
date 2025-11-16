"""
Text-to-Speech service for story narration.
"""
import os
import hashlib
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile


class TTSService:
    """
    Handles text-to-speech conversion for stories.
    Supports multiple TTS providers with caching.
    """
    
    def __init__(self):
        self.provider = settings.TTS_PROVIDER
        self.cache_enabled = settings.TTS_CACHE_ENABLED
        self.cache_dir = settings.TTS_CACHE_DIR
        
        # Ensure cache directory exists
        if self.cache_enabled:
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
    
    def generate_audio(self, text, language='en', voice=None, parallel=True, min_paragraph_length=50):
        """
        Convert text to speech and return audio file.
        
        Args:
            text: Text to convert to speech
            language: Language code (e.g., 'en', 'es')
            voice: Optional voice identifier
            parallel: Whether to use parallel generation for multiple paragraphs (default: True)
            min_paragraph_length: Minimum character length to consider splitting (default: 50)
            
        Returns:
            ContentFile: Audio file content
        """
        # Check cache first
        if self.cache_enabled:
            cache_key = self._get_cache_key(text, language, voice)
            cached_file = self._get_from_cache(cache_key)
            if cached_file:
                return cached_file
        
        # Split text into paragraphs if parallel mode is enabled
        paragraphs = self._split_into_paragraphs(text, min_paragraph_length) if parallel else [text]
        
        # Use parallel generation if multiple paragraphs and parallel mode is enabled
        if len(paragraphs) > 1 and parallel:
            audio_content = self._generate_parallel(paragraphs, language, voice)
        else:
            # Generate audio based on provider (single request)
            if self.provider == 'gtts':
                audio_content = self._generate_with_gtts(text, language)
            elif self.provider == 'vertex_ai':
                audio_content = self._generate_with_vertex_ai(text, language, voice)
            elif self.provider == 'azure':
                audio_content = self._generate_with_azure(text, language, voice)
            else:
                raise ValueError(f"Unknown TTS provider: {self.provider}")
        
        # Cache the result
        if self.cache_enabled and audio_content:
            self._save_to_cache(cache_key, audio_content)
        
        return audio_content
    
    def _split_into_paragraphs(self, text, min_length=50):
        """
        Split text into paragraphs for parallel processing.
        
        Args:
            text: Text to split
            min_length: Minimum character length for a paragraph to be processed separately
            
        Returns:
            List of paragraph strings
        """
        # Split by double newlines, single newlines, or periods followed by space
        # This handles various paragraph formats
        paragraphs = re.split(r'\n\s*\n|\n(?=[A-Z])|\.\s+(?=[A-Z])', text)
        
        # Filter out empty paragraphs and very short ones
        filtered = [p.strip() for p in paragraphs if p.strip() and len(p.strip()) >= min_length]
        
        # If no paragraphs meet the criteria, return the original text
        if not filtered:
            return [text]
        
        # Merge very short paragraphs with the previous one
        result = []
        for para in filtered:
            if result and len(para) < min_length:
                result[-1] += ' ' + para
            else:
                result.append(para)
        
        return result if result else [text]
    
    def _generate_parallel(self, paragraphs, language='en', voice=None):
        """
        Generate audio for multiple paragraphs in parallel and merge them.
        
        Args:
            paragraphs: List of paragraph strings
            language: Language code
            voice: Optional voice identifier
            
        Returns:
            ContentFile: Merged audio file content
        """
        print(f"🎙️ 並行生成 {len(paragraphs)} 個段落的音訊...")
        
        # Determine max workers (limit to avoid overwhelming the API)
        max_workers = min(len(paragraphs), 5)  # Limit to 5 concurrent requests
        
        audio_segments = []
        
        def generate_single_paragraph(para_text, index):
            """Generate audio for a single paragraph."""
            try:
                if self.provider == 'gtts':
                    return self._generate_with_gtts(para_text, language), index
                elif self.provider == 'vertex_ai':
                    return self._generate_with_vertex_ai(para_text, language, voice), index
                elif self.provider == 'azure':
                    return self._generate_with_azure(para_text, language, voice), index
                else:
                    raise ValueError(f"Unknown TTS provider: {self.provider}")
            except Exception as e:
                print(f"❌ 段落 {index + 1} 生成失敗: {e}")
                return None, index
        
        # Generate audio segments in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(generate_single_paragraph, para, idx): idx
                for idx, para in enumerate(paragraphs)
            }
            
            # Collect results as they complete
            results = {}
            for future in as_completed(future_to_index):
                audio_content, index = future.result()
                if audio_content:
                    results[index] = audio_content
        
        # Sort results by index to maintain paragraph order
        audio_segments = [results[i] for i in sorted(results.keys())]
        
        if not audio_segments:
            print("❌ 所有段落生成都失敗，回退到單一請求模式")
            # Fallback to single request
            full_text = ' '.join(paragraphs)
            return self._generate_audio_fallback(full_text, language, voice)
        
        print(f"✅ 成功生成 {len(audio_segments)}/{len(paragraphs)} 個段落，正在合併...")
        
        # Merge audio segments
        return self._merge_audio_segments(audio_segments)
    
    def _generate_audio_fallback(self, text, language, voice):
        """Fallback method for generating audio when parallel generation fails."""
        if self.provider == 'gtts':
            return self._generate_with_gtts(text, language)
        elif self.provider == 'vertex_ai':
            return self._generate_with_vertex_ai(text, language, voice)
        elif self.provider == 'azure':
            return self._generate_with_azure(text, language, voice)
        else:
            raise ValueError(f"Unknown TTS provider: {self.provider}")
    
    def _merge_audio_segments(self, audio_segments):
        """
        Merge multiple audio ContentFiles into a single audio file.
        
        Args:
            audio_segments: List of ContentFile objects containing audio data
            
        Returns:
            ContentFile: Merged audio file content
        """
        print(f"🔗 開始合併 {len(audio_segments)} 個音訊片段...")
        
        try:
            from pydub import AudioSegment
            
            # Load all audio segments
            segments = []
            for i, audio_content in enumerate(audio_segments, 1):
                try:
                    # Reset file pointer
                    audio_content.seek(0)
                    # Load audio segment
                    audio_bytes = audio_content.read()
                    print(f"   段落 {i}: {len(audio_bytes)} bytes")
                    audio_segment = AudioSegment.from_mp3(BytesIO(audio_bytes))
                    print(f"   段落 {i}: {len(audio_segment)/1000:.2f} 秒")
                    segments.append(audio_segment)
                except Exception as e:
                    print(f"⚠️  載入段落 {i} 時發生錯誤: {e}")
                    # 繼續處理其他段落
                    continue
            
            if not segments:
                print("❌ 沒有成功載入任何音訊段落")
                return audio_segments[0] if audio_segments else None
            
            print(f"✅ 成功載入 {len(segments)} 個段落")
            
            # Add a small silence between segments for natural flow (500ms)
            silence = AudioSegment.silent(duration=500)
            merged = segments[0]
            for i, segment in enumerate(segments[1:], 2):
                print(f"   合併段落 {i}...")
                merged += silence + segment
            
            total_duration = len(merged) / 1000
            print(f"✅ 合併完成，總長度: {total_duration:.2f} 秒")
            
            # Export to bytes
            print("📤 正在導出 MP3...")
            output_buffer = BytesIO()
            merged.export(output_buffer, format='mp3')
            output_buffer.seek(0)
            
            audio_data = output_buffer.read()
            print(f"✅ 導出完成，檔案大小: {len(audio_data) / 1024:.2f} KB")
            
            return ContentFile(audio_data, name='story_audio.mp3')
            
        except ImportError as e:
            print(f"❌ pydub 未安裝或導入失敗: {e}")
            print("⚠️  請執行: pip install pydub")
            print("⚠️  Windows 用戶可能還需要安裝 ffmpeg")
            print("⚠️  回退到單一段落模式...")
            # Fallback: return the first segment (not ideal but better than failing)
            return audio_segments[0] if audio_segments else None
        except Exception as e:
            print(f"❌ 合併音訊時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            print("⚠️  回退到單一段落模式...")
            # Fallback: return the first segment
            return audio_segments[0] if audio_segments else None
    
    def _generate_with_gtts(self, text, language):
        """
        Generate audio using Google Text-to-Speech (gTTS).
        Free, offline-capable, good quality.
        """
        try:
            from gtts import gTTS
            from io import BytesIO
            
            # Create TTS object
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save to bytes buffer
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            # Return as ContentFile
            return ContentFile(audio_buffer.read(), name='story_audio.mp3')
            
        except Exception as e:
            print(f"gTTS generation failed: {e}")
            return None
    
    def _generate_with_vertex_ai(self, text, language='en', voice=None):
        """
        Generate audio using Google Vertex AI Text-to-Speech API.
        High quality, natural-sounding voices with neural network models.
        
        To implement:
        1. pip install google-cloud-texttospeech
        2. Set GOOGLE_APPLICATION_CREDENTIALS environment variable or configure credentials
        3. Set VERTEX_AI_PROJECT_ID and VERTEX_AI_LOCATION in settings
        """
        try:
            from google.cloud import texttospeech
            from io import BytesIO
            
            # Initialize client
            client = texttospeech.TextToSpeechClient()
            
            # Configure voice selection
            # Default to child-friendly voices
            voice_name = voice or 'en-US-Neural2-D'  # Child-friendly voice
            language_code = language if len(language) == 5 else f"{language}-US"
            
            # Set up the input text
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure voice parameters
            voice_config = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            
            # Configure audio output
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0.0
            )
            
            # Perform the text-to-speech request
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_config,
                audio_config=audio_config
            )
            
            # Convert to ContentFile
            audio_buffer = BytesIO(response.audio_content)
            return ContentFile(audio_buffer.read(), name='story_audio.mp3')
            
        except Exception as e:
            print(f"Vertex AI TTS generation failed: {e}. Falling back to gTTS.")
            return self._generate_with_gtts(text, language)
    
    def _generate_with_azure(self, text, language='en', voice=None):
        """
        Generate audio using Azure Cognitive Services Text-to-Speech API.
        High quality, natural-sounding voices with SSML support.
        
        To implement:
        1. pip install azure-cognitiveservices-speech
        2. Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in settings
        """
        try:
            import azure.cognitiveservices.speech as speechsdk
            from io import BytesIO
            
            # Get Azure credentials from settings
            azure_key = getattr(settings, 'AZURE_SPEECH_KEY', None)
            azure_region = getattr(settings, 'AZURE_SPEECH_REGION', None)
            
            if not azure_key or not azure_region:
                raise ValueError("Azure Speech credentials not configured")
            
            # Configure speech synthesizer
            speech_config = speechsdk.SpeechConfig(
                subscription=azure_key,
                region=azure_region
            )
            
            # Set language and voice
            language_code = language if len(language) == 5 else f"{language}-US"
            voice_name = voice or 'en-US-AriaNeural'  # Child-friendly voice
            
            speech_config.speech_synthesis_language = language_code
            speech_config.speech_synthesis_voice_name = voice_name
            
            # Create synthesizer without audio config (will use result.audio_data)
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
            
            # Synthesize speech
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Convert audio data to ContentFile
                audio_buffer = BytesIO(result.audio_data)
                return ContentFile(audio_buffer.read(), name='story_audio.mp3')
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = speechsdk.CancellationDetails(result)
                raise Exception(f"Azure TTS canceled: {cancellation_details.reason}")
            else:
                raise Exception(f"Azure TTS failed: {result.reason}")
            
        except Exception as e:
            print(f"Azure TTS generation failed: {e}. Falling back to gTTS.")
            return self._generate_with_gtts(text, language)
    
    def _get_cache_key(self, text, language, voice):
        """Generate cache key from text and parameters."""
        content = f"{text}:{language}:{voice or 'default'}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key):
        """Retrieve audio from cache if exists."""
        cache_file = self.cache_dir / f"{cache_key}.mp3"
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return ContentFile(f.read(), name='story_audio.mp3')
        return None
    
    def _save_to_cache(self, cache_key, audio_content):
        """Save audio to cache."""
        cache_file = self.cache_dir / f"{cache_key}.mp3"
        with open(cache_file, 'wb') as f:
            f.write(audio_content.read())
            audio_content.seek(0)  # Reset for further use
