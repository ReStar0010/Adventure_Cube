from django.db import models
from django.utils import timezone
from django.conf import settings
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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stories',
        null=True,
        blank=True
    )
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
    generation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('generating_intro', 'Generating Intro'),
            ('intro_ready', 'Intro Ready'),
            ('generating_remaining', 'Generating Remaining'),
            ('completed', 'Completed'),
        ],
        default='pending'
    )
    context_template = models.CharField(max_length=100, default='5min_basic')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stories'
    
    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d')})"


class StoryParagraph(models.Model):
    """
    Represents a single paragraph of a story with its TTS.
    """
    PARAGRAPH_TYPE_CHOICES = [
        ('intro_goal', 'Intro Goal'),
        ('problem_obstacle', 'Problem Obstacle'),
        ('effort_effort', 'Effort Effort'),
        ('climax_climax', 'Climax Climax'),
        ('ending_ending', 'Ending Ending'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='paragraphs')
    paragraph_index = models.IntegerField()  # 0-4 (5 paragraphs)
    paragraph_type = models.CharField(max_length=50, choices=PARAGRAPH_TYPE_CHOICES)
    text = models.TextField()
    tts_audio_file = models.FileField(upload_to='audio/paragraphs/', null=True, blank=True)
    tts_duration_seconds = models.FloatField(null=True, blank=True)
    is_generated = models.BooleanField(default=False)
    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['story', 'paragraph_index']
        unique_together = ['story', 'paragraph_index']
    
    def __str__(self):
        return f"Paragraph {self.paragraph_index} ({self.paragraph_type}) of {self.story.title}"


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
