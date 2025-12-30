"""
Story generation service using Gemini API with Context Engineering templates.
"""
from django.conf import settings
from .context_engineering import (
    ContextTemplateLoader, 
    StoryStructure, 
    ParagraphType,
    ParagraphType7,
    get_paragraph_type_by_index,
    get_paragraph_type_by_key
)


# Character personalities mapping (Traditional Chinese)
CHARACTER_PERSONALITIES = {
    'angel': ['恐高症的守護者', '愛抱怨的治癒者', '不喜歡甜食的使者', '完美主義的搗蛋鬼', '熱愛地獄搖滾的聖潔者'],
    'cat': ['親人的獨行俠', '愛水的貓', '懶惰的運動健將', '愛說話的安靜者', '潔癖的冒險家'],
    'dog': ['害怕小東西的勇士', '愛乾淨的流浪者', '嚴肅的喜劇演員', '愛說悄悄話的說書人', '喜歡收集襪子的發明家'],
    'dragon': ['有鱗的愛哭鬼', '怕高的飛行員', '愛乾淨的收藏家', '素食主義的肉食者', '安靜的吟遊詩人'],
    'elf': ['懶惰的自然守護者', '不善言辭的魔法師', '喜愛噪音的聽覺者', '沒有方向感的嚮導', '不相信魔法的精靈'],
    'fairy': ['力大無窮的笨手笨腳者', '沒自信的治癒者', '愛吃垃圾食物的仙子', '充滿熱情的書呆子', '熱愛搖滾樂的舞蹈家'],
    'knight': ['害怕黑暗的守護者', '沉穩的冒失鬼', '嚴肅的廚師', '愛說悄悄話的演講者', '充滿熱情的書呆子'],
    'lion': ['沒自信的領導者', '愛哭的大隻佬', '膽小的勇士', '素食主義的肉食者', '愛說話的安靜者'],
    'mouse': ['膽小的冒險家', '強壯的膽小鬼', '愛乾淨的修理工', '充滿好奇心的智者', '喜歡捉弄人的小不點'],
    'prince': ['熱愛烹飪的王子', '害怕馬的王子', '喜歡園藝的王子', '害羞的演說家', '夢想成為騎士的詩人'],
    'princess': ['討厭裙子的公主', '夢想成為發明家的公主', '力氣很大的公主', '害怕青蛙的公主', '喜歡睡懶覺的公主'],
    'robot': ['渴望感受情感的邏輯機器人', '愛講冷笑話的計算機', '害怕水的清潔機器人', '夢想成為蝴蝶的工業機器人', '喜歡收集羽毛的守衛'],
    'unicorn': ['笨手笨腳的獨角獸', '不會飛的獨角獸', '愛吃鹹食的獨角獸', '毛色是灰色的獨角獸', '討厭彩虹的獨角獸'],
    'witch': ['喜歡收集閃亮東西的善良女巫', '討厭飛行的女巫', '健忘的女巫', '害怕黑貓的女巫', '只會做治療藥水的女巫'],
    'wizard': ['記憶力很差的偉大巫師', '害怕自己鬍子的巫師', '討厭魔法的巫師', '喜歡用科學做實驗的巫師', '夢想成為歌手的巫師']
}

# English to Chinese mappings for story elements
CHARACTER_NAMES_ZH = {
    'angel': '天使',
    'cat': '小貓',
    'dog': '小狗',
    'dragon': '小龍',
    'elf': '精靈',
    'fairy': '小仙子',
    'knight': '騎士',
    'lion': '小獅子',
    'mouse': '小老鼠',
    'prince': '王子',
    'princess': '公主',
    'robot': '機器人',
    'unicorn': '獨角獸',
    'witch': '女巫',
    'wizard': '巫師'
}

BACKGROUND_NAMES_ZH = {
    'castle': '城堡',
    'castel': '城堡',  # Handle typo in filename
    'chocolate lava': '巧克力熔岩',
    'dessert town': '甜點小鎮',
    'forest': '森林',
    'magic village': '魔法村莊'
}

THEME_NAMES_ZH = {
    'caring': '關懷',
    'courage': '勇氣',
    'friendship': '友誼',
    'honest': '誠實',
    'nature': '自然',
    'share': '分享'
}

KEY_ITEMS_NAMES_ZH = {
    # Frontend names
    'magic key': '魔法鑰匙',
    'ancient scroll': '古老卷軸',
    'crystal orb': '水晶球',
    'magic lamp': '神燈',
    'talking book': '會說話的書',
    'treasure map': '藏寶圖',
    # Image file names (for backward compatibility)
    'crystal key': '水晶鑰匙',
    'holy grail': '聖杯',
    'magic crown': '魔法皇冠'
}


class StoryGenerator:
    """
    Handles story generation using Gemini API with Context Engineering templates.
    """
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.template_loader = ContextTemplateLoader()
    
    def _get_character_personalities(self, character_name):
        """Get personality traits for a character."""
        if not character_name:
            return []
        
        # Normalize character name to lowercase for lookup
        char_key = character_name.lower().strip()
        return CHARACTER_PERSONALITIES.get(char_key, [])
    
    def _translate_to_chinese(self, english_name, mapping_dict, default=None):
        """
        Translate English name to Chinese using the provided mapping.
        
        Args:
            english_name: English name to translate
            mapping_dict: Dictionary mapping English to Chinese
            default: Default value if translation not found (returns original if None)
        
        Returns:
            Chinese translation or default/original name
        """
        if not english_name:
            return default or ''
        
        # Normalize: lowercase and strip
        key = english_name.lower().strip()
        chinese = mapping_dict.get(key)
        
        if chinese:
            return chinese
        
        # Try partial matches for compound names
        for eng_key, zh_value in mapping_dict.items():
            if eng_key in key or key in eng_key:
                return zh_value
        
        # Return default or original if no match found
        return default if default is not None else english_name
    
    def _translate_character(self, character_name):
        """Translate character name from English to Chinese."""
        return self._translate_to_chinese(character_name, CHARACTER_NAMES_ZH, '冒險家')
    
    def _translate_background(self, background_name):
        """Translate background name from English to Chinese."""
        return self._translate_to_chinese(background_name, BACKGROUND_NAMES_ZH, '魔法之地')
    
    def _translate_theme(self, theme_name):
        """Translate theme name from English to Chinese."""
        return self._translate_to_chinese(theme_name, THEME_NAMES_ZH, theme_name)
    
    def _translate_key_items(self, key_items):
        """Translate key items list from English to Chinese."""
        if not key_items:
            return []
        
        translated = []
        for item in key_items:
            if isinstance(item, str):
                translated_item = self._translate_to_chinese(item, KEY_ITEMS_NAMES_ZH, item)
                translated.append(translated_item)
            else:
                # If it's a dict with 'name' key (from frontend)
                item_name = item.get('name', item) if isinstance(item, dict) else str(item)
                translated_item = self._translate_to_chinese(item_name, KEY_ITEMS_NAMES_ZH, item_name)
                translated.append(translated_item)
        
        return translated
    
    def generate_intro_paragraph(self, theme, child_name=None, child_age=None, context_template='5min_basic', **kwargs):
        """
        Generate only the first paragraph (Intro Goal) immediately.
        
        Args:
            theme: Story theme
            child_name: Optional child's name
            child_age: Optional child's age
            context_template: Template name (default: '5min_basic')
            **kwargs: Additional story elements (character, background, key_items)
        
        Returns:
            dict: {
                'title': str,
                'paragraph_text': str,
                'paragraph_type': 'intro_goal',
                'paragraph_index': 0
            }
        """
        # Load context template
        try:
            print(f"📖 Loading context template: {context_template}")
            template_data = self.template_loader.load_template(context_template)
            print(f"template_data: {template_data}")
            print(f"✅ Template loaded successfully")
            print(f"   System prompt: {len(template_data['system_prompt'])} chars")
            print(f"   User prompt template: {len(template_data['user_prompt_template'])} chars")
            print(f"   Structure keys: {list(template_data['structure'].keys())}")
        except Exception as e:
            print(f"❌ Failed to load template {context_template}: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to load context template '{context_template}': {e}")
        
        # Build prompt for intro paragraph
        prompt = self._build_intro_prompt(theme, child_name, child_age, context_template, template_data, **kwargs)
        print(f"prompt: {prompt}")
        # Check if Gemini is configured
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set. Please configure it in your environment variables.")
        
        if self.provider != 'gemini':
            print(f"⚠️  WARNING: LLM_PROVIDER is set to '{self.provider}', but only Gemini is supported.")
            print(f"   Setting provider to 'gemini' for this generation.")
        
        # Generate using Gemini
        print("🚀 Using Gemini for paragraph generation with Context Engineering template")
        # Get the correct intro paragraph type based on template
        intro_para_type = StoryStructure.get_intro_paragraph_type(context_template)
        result = self._generate_paragraph_with_gemini(prompt, template_data['system_prompt'], intro_para_type)
        
        return result
    
    def generate_paragraph(self, paragraph_index, previous_paragraphs, theme, child_name=None, child_age=None, context_template='5min_basic', story=None, **kwargs):
        """
        Generate a specific paragraph using previous paragraphs as context.
        
        Args:
            paragraph_index: Index of paragraph to generate (1-6 for 7-stage, 1-4 for 5-stage)
            previous_paragraphs: List of StoryParagraph instances (already generated)
            theme: Story theme
            child_name: Optional child's name
            child_age: Optional child's age
            context_template: Template name
            story: Story model instance (optional, kept for backward compatibility but not used)
            **kwargs: Additional story elements
        
        Returns:
            dict: {
                'paragraph_text': str,
                'paragraph_type': str,
                'paragraph_index': int
            }
        """
        para_type = get_paragraph_type_by_index(paragraph_index, context_template)
        if not para_type:
            max_index = StoryStructure.get_paragraph_count(context_template) - 1
            raise ValueError(f"Invalid paragraph_index: {paragraph_index} (must be 0-{max_index} for template '{context_template}')")
        
        # Load context template
        try:
            template_data = self.template_loader.load_template(context_template)
        except Exception as e:
            print(f"Failed to load template {context_template}: {e}")
            raise
        
        # Build prompt for this paragraph
        prompt = self._build_paragraph_prompt(
            para_type, previous_paragraphs, theme, child_name, child_age, context_template, template_data, **kwargs
        )
        
        # Check if Gemini is configured
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set. Please configure it in your environment variables.")
        
        # Generate using Gemini
        result = self._generate_paragraph_with_gemini(prompt, template_data['system_prompt'], para_type)
        
        return result
    
    def _build_intro_prompt(self, theme, child_name, child_age, context_template, template_data, **kwargs):
        """Build prompt for intro paragraph generation."""
        name = child_name or "小英雄"
        age = child_age or 5
        age = max(3, min(age, 10))
        
        # Get English names from kwargs
        character_en = kwargs.get('character', 'an adventurer')
        background_en = kwargs.get('background', 'a magical place')
        key_items_en = kwargs.get('key_items', [])
        
        # Translate to Chinese
        character_zh = self._translate_character(character_en)
        background_zh = self._translate_background(background_en)
        theme_zh = self._translate_theme(theme)
        key_items_zh = self._translate_key_items(key_items_en)
        
        # Debug: Print translations
        print(f"🌐 Translations (intro):")
        print(f"   Character: '{character_en}' -> '{character_zh}'")
        print(f"   Background: '{background_en}' -> '{background_zh}'")
        print(f"   Theme: '{theme}' -> '{theme_zh}'")
        print(f"   Key Items: {key_items_en} -> {key_items_zh}")
        
        # Get character personalities (using English name for lookup)
        personalities = self._get_character_personalities(character_en)
        items_text = "、".join(key_items_zh) if key_items_zh else "沒有特殊道具"
        
        personality_text = ""
        if personalities:
            personality_list = "、".join(personalities)
            personality_text = f"\n角色性格特質：{personality_list}"
        
        # Get structure instruction for intro based on template
        is_7_stage = context_template in ('10min_basic', '1106metaprompt')
        intro_structure_key = 'intro' if is_7_stage else 'intro_goal'
        structure_instruction = template_data['structure'].get(intro_structure_key, '故事的開端(短篇)')
        
        # Build user prompt - replace placeholders manually since template uses [請在此填入...] format
        user_prompt = template_data['user_prompt_template']
        user_prompt = user_prompt.replace('[請在此填入故事希望傳達的中心思想，例如：互相合作、勇敢面對恐懼、分享的快樂]', theme_zh)
        user_prompt = user_prompt.replace('[請在此填入主角1的中文名字，例如：小老鼠「吱吱」]', character_zh)
        user_prompt = user_prompt.replace('[請在此填入主角2的中文名字，例如：小松鼠「果果」]', name)
        user_prompt = user_prompt.replace('[請在此填入一個充滿童趣的中文地點名稱，例如：「棉花糖雲朵」的柔軟森林]', background_zh)
        user_prompt = user_prompt.replace('[請在此填入主角們要去達成的具體目標]', 
                                       f"探索{background_zh}並找到{items_text}" if key_items_zh else f"在{background_zh}中冒險")
        # Replace [主角1] and [主角2] references in the structure section
        user_prompt = user_prompt.replace('[主角1]', character_zh)
        user_prompt = user_prompt.replace('[主角2]', name)
        
        # Add specific instruction for intro paragraph
        intro_label = 'Intro' if is_7_stage else 'Intro Goal'
        prompt = f"""{user_prompt}

**現在請生成第一段（{intro_label}）：**
- {structure_instruction}
- 建立世界並介紹角色
- 確立目標
- 保持2-4個句子的長度
- 使用適合兒童的簡單詞彙
- 嚴格使用繁體中文"""
        
        return prompt
    
    def _clean_paragraph_text(self, text, para_type):
        """
        Clean up paragraph text by removing any instruction prefixes or labels
        that the LLM might have accidentally included.
        """
        import re
        
        # Patterns to remove from the beginning of paragraphs
        patterns_to_remove = [
            # Remove "段落 X (type):" or "段落 X (type)：" patterns
            r'^段落\s*\d+\s*\([^)]+\)\s*[:：]?\s*',
            # Remove "**段落 X**:" patterns
            r'^\*{0,2}段落\s*\d+\*{0,2}\s*[:：]?\s*',
            # Remove paragraph type labels like "(problem_obstacle):" or "(出現了阻礙):"
            r'^\([^)]+\)\s*[:：]?\s*',
            # Remove type labels at the start like "Problem Obstacle:" or "出現了阻礙："
            r'^(intro_goal|intro|problem_obstacle|problem_goal|effort_effort|climax_climax|result_result|surprise_surprise|turn_turn|ending_ending)\s*[:：]?\s*',
            r'^(故事的開端|出現了阻礙|努力的過程|故事的高潮|溫暖的結局|寂靜中的頓悟|晴天霹靂|勝利的喜悅|第一次充滿創意的嘗試|打破這份平靜|溫暖如擁抱的結局|用生動的文字作畫|確立主角與[小道具]的關係|易懂獨特且生動的比喻)\s*[:：]?\s*',
            # Remove bullet points or numbering at the start
            r'^[-•]\s*',
            r'^\d+\.\s*',
        ]
        
        cleaned = text.strip()
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        # Also clean up any leading/trailing whitespace or newlines
        cleaned = cleaned.strip()
        
        # If cleaning removed everything, return original
        if not cleaned:
            return text.strip()
        
        return cleaned
    
    def _build_paragraph_prompt(self, para_type, previous_paragraphs, theme, child_name, child_age, context_template, template_data, **kwargs):
        """Build prompt for generating a specific paragraph."""
        name = child_name or "小英雄"
        age = child_age or 5
        age = max(3, min(age, 10))
        
        # Get English names from kwargs
        character_en = kwargs.get('character', 'an adventurer')
        background_en = kwargs.get('background', 'a magical place')
        key_items_en = kwargs.get('key_items', [])
        
        # Translate to Chinese
        character_zh = self._translate_character(character_en)
        background_zh = self._translate_background(background_en)
        theme_zh = self._translate_theme(theme)
        key_items_zh = self._translate_key_items(key_items_en)
        
        # Debug: Print translations
        print(f"🌐 Translations (paragraph {para_type.index + 1}):")
        print(f"   Character: '{character_en}' -> '{character_zh}'")
        print(f"   Background: '{background_en}' -> '{background_zh}'")
        print(f"   Theme: '{theme}' -> '{theme_zh}'")
        print(f"   Key Items: {key_items_en} -> {key_items_zh}")
        
        # Get character personalities (using English name for lookup)
        personalities = self._get_character_personalities(character_en)
        items_text = "、".join(key_items_zh) if key_items_zh else "沒有特殊道具"
        
        personality_text = ""
        if personalities:
            personality_list = "、".join(personalities)
            personality_text = f"\n角色性格特質：{personality_list}"
        
        # Build original user prompt - replace placeholders manually
        user_prompt = template_data['user_prompt_template']
        user_prompt = user_prompt.replace('[請在此填入故事希望傳達的中心思想，例如：互相合作、勇敢面對恐懼、分享的快樂]', theme_zh)
        user_prompt = user_prompt.replace('[請在此填入主角1的中文名字，例如：小老鼠「吱吱」]', character_zh)
        user_prompt = user_prompt.replace('[請在此填入主角2的中文名字，例如：小松鼠「果果」]', name)
        user_prompt = user_prompt.replace('[請在此填入一個充滿童趣的中文地點名稱，例如：「棉花糖雲朵」的柔軟森林]', background_zh)
        user_prompt = user_prompt.replace('[請在此填入主角們要去達成的具體目標]', 
                                       f"探索{background_zh}並找到{items_text}" if key_items_zh else f"在{background_zh}中冒險")
        # Replace [主角1] and [主角2] references in the structure section
        user_prompt = user_prompt.replace('[主角1]', character_zh)
        user_prompt = user_prompt.replace('[主角2]', name)
        
        # Build previous paragraphs context
        previous_text = "\n\n".join([
            f"段落 {p.paragraph_index} ({p.paragraph_type}):\n{p.text}"
            for p in sorted(previous_paragraphs, key=lambda x: x.paragraph_index)
        ])
        
        # Get structure instruction for this paragraph
        structure_key = para_type.type_key
        structure_instruction = template_data['structure'].get(structure_key, para_type.chinese_name)
        
        # Build paragraph-specific instruction based on template
        is_7_stage = context_template in ('10min_basic', '1106metaprompt')
        if is_7_stage:
            para_instructions = {
                'problem_goal': '直接描述一個具體發生的事件作為阻礙',
                'effort_effort': '描寫主角們想出的計畫和努力的過程',
                'result_result': '這是克服困難的關鍵時刻',
                'surprise_surprise': '就在主角們沉浸在勝利喜悅的頂點時，一個天翻覆地的意外發生了',
                'turn_turn': '在經歷了滑稽的失敗後，主角們終於恍然大悟',
                'ending_ending': '描寫一個溫暖、有趣且充滿啟發的收尾'
            }
        else:
            para_instructions = {
                'problem_obstacle': '直接描述一個具體發生的事件作為阻礙',
                'effort_effort': '描寫主角們想出的計畫和努力的過程',
                'climax_climax': '這是克服困難的關鍵時刻',
                'ending_ending': '描寫一個溫暖、有趣且充滿啟發的收尾'
            }
        specific_instruction = para_instructions.get(structure_key, '')
        
        prompt = f"""{user_prompt}

**已生成的段落：**
{previous_text}

**現在請生成段落 {para_type.index + 1} ({para_type.chinese_name})：**
- {structure_instruction}
- {specific_instruction}
- 基於前面的段落繼續發展故事
- 保持2-4個句子的長度
- 使用適合兒童的簡單詞彙
- 嚴格使用繁體中文"""
        
        return prompt
    
    def _generate_paragraph_with_gemini(self, prompt, system_prompt, para_type):
        """Generate a paragraph using Gemini."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Use system_instruction for better prompt handling in Gemini
            # This ensures the system prompt is properly recognized
            print(f"🔵 Using Context Engineering template with Gemini")
            print(f"System prompt length: {len(system_prompt)} chars")
            print(f"User prompt length: {len(prompt)} chars")
            # Debug: Print first 200 chars of prompt to see what's being sent
            print(f"🔍 Prompt preview (first 200 chars): {prompt[:200]}...")

            # DEBUG: Save full prompts to file for inspection
            import os
            debug_dir = '/tmp/gemini_debug'
            os.makedirs(debug_dir, exist_ok=True)
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            with open(f'{debug_dir}/system_prompt_{timestamp}.txt', 'w', encoding='utf-8') as f:
                f.write(system_prompt)
            with open(f'{debug_dir}/user_prompt_{timestamp}.txt', 'w', encoding='utf-8') as f:
                f.write(prompt)
            print(f"💾 Saved full prompts to {debug_dir}/system_prompt_{timestamp}.txt and user_prompt_{timestamp}.txt")
            
            # Create model with system instruction
            # Configure safety settings to be less strict for children's stories
            # Options: BLOCK_NONE, BLOCK_ONLY_HIGH, BLOCK_MEDIUM_AND_ABOVE, BLOCK_LOW_AND_ABOVE
            # Current: BLOCK_NONE (safety filters disabled for testing)
            try:
                from google.generativeai.types import HarmCategory, HarmBlockThreshold
                safety_settings = {
                    # DISABLED for testing - no safety filters
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
                print(f"🔒 Safety settings configured: BLOCK_NONE (all filters disabled for testing)")
            except (ImportError, AttributeError):
                # Fallback: use default safety settings (model default)
                safety_settings = None
                print("⚠️  Could not import safety settings enums, using model defaults")
            
            generation_config = genai.types.GenerationConfig(
                temperature=0.8,
                max_output_tokens=500,
            )
            
            # Create model with system instruction and safety settings
            if safety_settings:
                model = genai.GenerativeModel(
                    'gemini-2.0-flash',
                    system_instruction=system_prompt,
                    safety_settings=safety_settings
                )
            else:
                model = genai.GenerativeModel(
                    'gemini-2.0-flash',
                    system_instruction=system_prompt
                )
            
            # Generate with the user prompt (system prompt is already set)
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )

            # Check if response was blocked by safety filters
            if not response.candidates or len(response.candidates) == 0:
                print("❌ DEBUG: No candidates in response")
                print(f"   Response object: {response}")

                # Check prompt_feedback for detailed block information
                if hasattr(response, 'prompt_feedback'):
                    feedback = response.prompt_feedback
                    print(f"   Prompt feedback: {feedback}")

                    # Extract block reason
                    if hasattr(feedback, 'block_reason'):
                        print(f"   Block reason: {feedback.block_reason}")

                    # Extract safety ratings from prompt feedback
                    if hasattr(feedback, 'safety_ratings'):
                        print(f"   Prompt-level safety ratings:")
                        for rating in feedback.safety_ratings:
                            print(f"      - {rating.category}: {rating.probability}")

                raise ValueError("Gemini API returned no candidates. The response may have been blocked by safety filters.")
            
            candidate = response.candidates[0]
            
            # Debug: Print finish_reason and other details
            finish_reason = getattr(candidate, 'finish_reason', None)
            safety_ratings = getattr(candidate, 'safety_ratings', [])
            print(f"🔍 DEBUG: Candidate finish_reason: {finish_reason}")
            print(f"🔍 DEBUG: Candidate safety_ratings: {safety_ratings}")
            
            # Check if there's content in the response
            if not candidate.content or not candidate.content.parts:
                raise ValueError("Gemini API returned empty content. No text was generated.")
            
            # Extract text from the first part
            paragraph_text = candidate.content.parts[0].text.strip()
            
            if not paragraph_text:
                raise ValueError("Gemini API returned empty text content.")
            
            # Clean up any instruction prefixes that the LLM might have included
            paragraph_text = self._clean_paragraph_text(paragraph_text, para_type)
            
            title = None
            # Check for title in intro paragraphs (both 5-stage and 7-stage)
            if para_type.index == 0:
                if "Title:" in paragraph_text:
                    parts = paragraph_text.split("\n", 1)
                    title = parts[0].replace("Title:", "").strip()
                    paragraph_text = parts[1].strip() if len(parts) > 1 else paragraph_text
            
            result = {
                'paragraph_text': paragraph_text,
                'paragraph_type': para_type.type_key,
                'paragraph_index': para_type.index
            }
            if title:
                result['title'] = title
            
            print(f"✅ Generated paragraph ({para_type.type_key}): {len(paragraph_text)} chars")
            return result
            
        except ValueError as e:
            # Handle safety filter blocks specifically
            error_msg = str(e)
            print(f"❌ Gemini safety filter or content issue: {error_msg}")
            # Try to provide a helpful fallback message
            if "safety" in error_msg.lower() or "blocked" in error_msg.lower():
                print("💡 Tip: The prompt may have triggered safety filters. Try:")
                print("   - Simplifying the prompt")
                print("   - Using more neutral language")
                print("   - Checking if the Context Engineering template is appropriate")
            raise ValueError(f"Gemini generation failed: {error_msg}")
        except Exception as e:
            print(f"❌ Gemini paragraph generation failed: {e}")
            import traceback
            traceback.print_exc()
            raise
