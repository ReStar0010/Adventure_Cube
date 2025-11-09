"""
Text-to-Speech service for story narration.
"""
import os
import hashlib
from pathlib import Path
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
    
    def generate_audio(self, text, language='en', voice=None):
        """
        Convert text to speech and return audio file.
        
        Args:
            text: Text to convert to speech
            language: Language code (e.g., 'en', 'es')
            voice: Optional voice identifier
            
        Returns:
            ContentFile: Audio file content
        """
        # Check cache first
        if self.cache_enabled:
            cache_key = self._get_cache_key(text, language, voice)
            cached_file = self._get_from_cache(cache_key)
            if cached_file:
                return cached_file
        
        # Generate audio based on provider
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
