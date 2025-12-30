"""
Story structure definitions for paragraph-based generation.
Supports both 5-stage and 7-stage story structures.
"""
from enum import Enum


class ParagraphType(Enum):
    """Enumeration of story paragraph types for 5-stage stories (5min_basic)."""
    INTRO_GOAL = ('intro_goal', 0, 'Intro Goal', '故事的開端(短篇)')
    PROBLEM_OBSTACLE = ('problem_obstacle', 1, 'Problem Obstacle', '出現了阻礙(短篇)')
    EFFORT_EFFORT_5 = ('effort_effort', 2, 'Effort Effort', '努力的過程(短篇)')
    CLIMAX_CLIMAX = ('climax_climax', 3, 'Climax Climax', '故事的高潮(短篇)')
    ENDING_ENDING_5 = ('ending_ending', 4, 'Ending Ending', '溫暖的結局(短篇)')
    
    def __init__(self, type_key, index, english_name, chinese_name):
        self.type_key = type_key
        self.index = index
        self.english_name = english_name
        self.chinese_name = chinese_name


class ParagraphType7(Enum):
    """Enumeration of story paragraph types for 7-stage stories (10min_basic, 1106metaprompt)."""
    INTRO = ('intro', 0, 'Intro', '故事的開端(短篇)')
    PROBLEM_GOAL = ('problem_goal', 1, 'Problem Goal', '出現了阻礙(短篇)')
    EFFORT_EFFORT_7 = ('effort_effort', 2, 'Effort Effort', '努力的過程(短篇)')
    RESULT_RESULT = ('result_result', 3, 'Result Result', '勝利的喜悅(短篇)')
    SURPRISE_SURPRISE = ('surprise_surprise', 4, 'Surprise Surprise', '晴天霹靂(短篇)')
    TURN_TURN = ('turn_turn', 5, 'Turn Turn', '寂靜中的頓悟(短篇)')
    ENDING_ENDING_7 = ('ending_ending', 6, 'Ending Ending', '溫暖如擁抱的結局(短篇)')
    
    def __init__(self, type_key, index, english_name, chinese_name):
        self.type_key = type_key
        self.index = index
        self.english_name = english_name
        self.chinese_name = chinese_name


def get_paragraph_type_by_index(index, template_name='5min_basic'):
    """
    Get paragraph type by index, based on template structure.
    
    Args:
        index: Paragraph index (0-based)
        template_name: Template name to determine structure (5-stage or 7-stage)
    
    Returns:
        ParagraphType or ParagraphType7 instance, or None if not found
    """
    is_7_stage = template_name in ('10min_basic', '1106metaprompt')
    
    if is_7_stage:
        for para_type in ParagraphType7:
            if para_type.index == index:
                return para_type
    else:
        for para_type in ParagraphType:
            if para_type.index == index:
                return para_type
    
    return None


def get_paragraph_type_by_key(key, template_name='5min_basic'):
    """
    Get paragraph type by key, based on template structure.
    
    Args:
        key: Paragraph type key (e.g., 'intro_goal', 'intro', 'problem_obstacle')
        template_name: Template name to determine structure
    
    Returns:
        ParagraphType or ParagraphType7 instance, or None if not found
    """
    is_7_stage = template_name in ('10min_basic', '1106metaprompt')
    
    if is_7_stage:
        for para_type in ParagraphType7:
            if para_type.type_key == key:
                return para_type
    else:
        for para_type in ParagraphType:
            if para_type.type_key == key:
                return para_type
    
    return None


class StoryStructure:
    """Defines story structure for both 5-paragraph and 7-paragraph stories."""
    
    @staticmethod
    def get_paragraph_count(template_name='5min_basic'):
        """Get the number of paragraphs for a given template."""
        if template_name in ('10min_basic', '1106metaprompt'):
            return 7
        return 5
    
    @staticmethod
    def get_all_paragraphs(template_name='5min_basic'):
        """Get all paragraph types in order for a given template."""
        if template_name in ('10min_basic', '1106metaprompt'):
            return [
                ParagraphType7.INTRO,
                ParagraphType7.PROBLEM_GOAL,
                ParagraphType7.EFFORT_EFFORT_7,
                ParagraphType7.RESULT_RESULT,
                ParagraphType7.SURPRISE_SURPRISE,
                ParagraphType7.TURN_TURN,
                ParagraphType7.ENDING_ENDING_7,
            ]
        else:
            return [
                ParagraphType.INTRO_GOAL,
                ParagraphType.PROBLEM_OBSTACLE,
                ParagraphType.EFFORT_EFFORT_5,
                ParagraphType.CLIMAX_CLIMAX,
                ParagraphType.ENDING_ENDING_5,
            ]
    
    @staticmethod
    def get_paragraph_instruction(para_type, language='zh-TW'):
        """Get instruction text for a paragraph type."""
        if language.startswith('zh'):
            return para_type.chinese_name
        return para_type.english_name
    
    @staticmethod
    def get_intro_paragraph_type(template_name='5min_basic'):
        """Get the intro paragraph type for a given template."""
        if template_name in ('10min_basic', '1106metaprompt'):
            return ParagraphType7.INTRO
        return ParagraphType.INTRO_GOAL
