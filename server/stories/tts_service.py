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
        elif self.provider == 'openai':
            audio_content = self._generate_with_openai(text, voice)
        elif self.provider == 'elevenlabs':
            audio_content = self._generate_with_elevenlabs(text, voice)
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
    
    def _generate_with_openai(self, text, voice=None):
        """
        Generate audio using OpenAI TTS API.
        High quality, realistic voices.
        
        To implement:
        1. pip install openai
        2. Use openai.audio.speech.create()
        """
        try:
            import openai
            from io import BytesIO
            
            openai.api_key = settings.OPENAI_API_KEY
            
            # Available voices: alloy, echo, fable, onyx, nova, shimmer
            voice_name = voice or 'nova'
            
            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice_name,
                input=text
            )
            
            audio_buffer = BytesIO()
            for chunk in response.iter_bytes():
                audio_buffer.write(chunk)
            audio_buffer.seek(0)
            
            return ContentFile(audio_buffer.read(), name='story_audio.mp3')
            
        except Exception as e:
            print(f"OpenAI TTS generation failed: {e}. Falling back to gTTS.")
            return self._generate_with_gtts(text, 'en')
    
    def _generate_with_elevenlabs(self, text, voice=None):
        """
        Generate audio using ElevenLabs API.
        Premium quality, very realistic voices.
        
        To implement:
        1. pip install elevenlabs
        2. Configure voice IDs
        """
        try:
            from elevenlabs import generate, save
            from io import BytesIO
            
            voice_name = voice or "Bella"  # Child-friendly voice
            
            audio = generate(
                text=text,
                voice=voice_name,
                model="eleven_monolingual_v1"
            )
            
            audio_buffer = BytesIO(audio)
            return ContentFile(audio_buffer.read(), name='story_audio.mp3')
            
        except Exception as e:
            print(f"ElevenLabs TTS generation failed: {e}. Falling back to gTTS.")
            return self._generate_with_gtts(text, 'en')
    
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
