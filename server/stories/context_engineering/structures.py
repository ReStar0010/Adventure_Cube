"""
Story structure definitions for paragraph-based generation.
"""
from enum import Enum


class ParagraphType(Enum):
    """Enumeration of story paragraph types."""
    INTRO_GOAL = ('intro_goal', 0, 'Intro Goal', '故事的開端(短篇)')
    PROBLEM_OBSTACLE = ('problem_obstacle', 1, 'Problem Obstacle', '出現了阻礙(短篇)')
    EFFORT_EFFORT = ('effort_effort', 2, 'Effort Effort', '努力的過程(短篇)')
    CLIMAX_CLIMAX = ('climax_climax', 3, 'Climax Climax', '故事的高潮(短篇)')
    ENDING_ENDING = ('ending_ending', 4, 'Ending Ending', '溫暖的結局(短篇)')
    
    def __init__(self, type_key, index, english_name, chinese_name):
        self.type_key = type_key
        self.index = index
        self.english_name = english_name
        self.chinese_name = chinese_name
    
    @classmethod
    def get_by_index(cls, index):
        """Get paragraph type by index."""
        for para_type in cls:
            if para_type.index == index:
                return para_type
        return None
    
    @classmethod
    def get_by_key(cls, key):
        """Get paragraph type by key."""
        for para_type in cls:
            if para_type.type_key == key:
                return para_type
        return None


class StoryStructure:
    """Defines the 5-paragraph story structure."""
    
    PARAGRAPH_COUNT = 5
    
    @staticmethod
    def get_all_paragraphs():
        """Get all paragraph types in order."""
        return [
            ParagraphType.INTRO_GOAL,
            ParagraphType.PROBLEM_OBSTACLE,
            ParagraphType.EFFORT_EFFORT,
            ParagraphType.CLIMAX_CLIMAX,
            ParagraphType.ENDING_ENDING,
        ]
    
    @staticmethod
    def get_paragraph_instruction(para_type, language='zh-TW'):
        """Get instruction text for a paragraph type."""
        if language.startswith('zh'):
            return para_type.chinese_name
        return para_type.english_name

