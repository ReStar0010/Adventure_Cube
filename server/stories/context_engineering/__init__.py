"""
Context Engineering module for loading and parsing story generation templates.
"""
from .templates import ContextTemplateLoader
from .structures import StoryStructure, ParagraphType

__all__ = ['ContextTemplateLoader', 'StoryStructure', 'ParagraphType']

