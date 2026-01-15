"""
Context Engineering module for loading and parsing story generation templates.
"""
from .templates import ContextTemplateLoader
from .structures import (
    StoryStructure, 
    ParagraphType,
    ParagraphType7,
    get_paragraph_type_by_index,
    get_paragraph_type_by_key
)

__all__ = [
    'ContextTemplateLoader', 
    'StoryStructure', 
    'ParagraphType',
    'ParagraphType7',
    'get_paragraph_type_by_index',
    'get_paragraph_type_by_key'
]

