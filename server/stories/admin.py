from django.contrib import admin
from .models import Story, AudioFile


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'theme', 'child_name', 'model_source', 'created_at')
    list_filter = ('model_source', 'theme', 'language')
    search_fields = ('title', 'body', 'child_name')
    readonly_fields = ('id', 'created_at')


@admin.register(AudioFile)
class AudioFileAdmin(admin.ModelAdmin):
    list_display = ('story', 'language', 'duration_seconds', 'created_at')
    list_filter = ('language',)
    readonly_fields = ('id', 'created_at')
