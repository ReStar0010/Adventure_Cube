from django.db import models
from django.utils import timezone
import uuid


class Story(models.Model):
    """
    Represents a generated story for a child.
    """
    MODEL_SOURCE_CHOICES = [
        ('online', 'Online AI'),
        ('offline', 'Offline Template'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    body = models.TextField()
    theme = models.CharField(max_length=100)
    child_name = models.CharField(max_length=100, blank=True, null=True)
    child_age = models.IntegerField(blank=True, null=True)
    model_source = models.CharField(
        max_length=20,
        choices=MODEL_SOURCE_CHOICES,
        default='offline'
    )
    language = models.CharField(max_length=10, default='en')
    character = models.CharField(max_length=100, blank=True, null=True)
    background = models.CharField(max_length=100, blank=True, null=True)
    key_items = models.JSONField(default=list, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stories'
    
    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d')})"


class AudioFile(models.Model):
    """
    Represents a TTS audio file for a story.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='audio_files')
    language = models.CharField(max_length=10, default='en')
    audio_file = models.FileField(upload_to='audio/')
    duration_seconds = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Audio for {self.story.title} ({self.language})"
