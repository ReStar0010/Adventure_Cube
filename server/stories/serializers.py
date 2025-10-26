"""
Serializers for Story API.
"""
from rest_framework import serializers
from .models import Story, AudioFile


class StorySerializer(serializers.ModelSerializer):
    """Serializer for Story model."""
    
    class Meta:
        model = Story
        fields = [
            'id', 'title', 'body', 'theme', 'child_name', 'child_age',
            'model_source', 'language', 'character', 'background', 'key_items', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StoryGenerateRequestSerializer(serializers.Serializer):
    """Serializer for story generation request."""
    
    theme = serializers.CharField(required=True, max_length=100)
    child_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    child_age = serializers.IntegerField(required=False, min_value=1, max_value=15)
    language = serializers.CharField(required=False, default='en', max_length=10)
    character = serializers.CharField(required=False, allow_blank=True, max_length=100)
    background = serializers.CharField(required=False, allow_blank=True, max_length=100)
    key_items = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        allow_empty=True
    )


class AudioFileSerializer(serializers.ModelSerializer):
    """Serializer for AudioFile model."""
    
    audio_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AudioFile
        fields = ['id', 'story', 'language', 'audio_url', 'duration_seconds', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_audio_url(self, obj):
        """Get full URL for audio file."""
        request = self.context.get('request')
        if obj.audio_file and hasattr(obj.audio_file, 'url'):
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            return obj.audio_file.url
        return None


class TTSRequestSerializer(serializers.Serializer):
    """Serializer for TTS generation request."""
    
    story_id = serializers.UUIDField(required=True)
    language = serializers.CharField(required=False, default='en', max_length=10)
    voice = serializers.CharField(required=False, allow_blank=True, max_length=50)
