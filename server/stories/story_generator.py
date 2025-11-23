"""
Story generation service using Gemini API with Context Engineering templates.
"""
from django.conf import settings
from .context_engineering import ContextTemplateLoader, StoryStructure, ParagraphType


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
        prompt = self._build_intro_prompt(theme, child_name, child_age, template_data, **kwargs)
        
        # Check if Gemini is configured
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set. Please configure it in your environment variables.")
        
        if self.provider != 'gemini':
            print(f"⚠️  WARNING: LLM_PROVIDER is set to '{self.provider}', but only Gemini is supported.")
            print(f"   Setting provider to 'gemini' for this generation.")
        
        # Generate using Gemini
        print("🚀 Using Gemini for paragraph generation with Context Engineering template")
        result = self._generate_paragraph_with_gemini(prompt, template_data['system_prompt'], ParagraphType.INTRO_GOAL)
        
        return result
    
    def generate_paragraph(self, story, paragraph_index, previous_paragraphs, theme, child_name=None, child_age=None, context_template='5min_basic', **kwargs):
        """
        Generate a specific paragraph using previous paragraphs as context.
        
        Args:
            story: Story model instance
            paragraph_index: Index of paragraph to generate (1-4)
            previous_paragraphs: List of StoryParagraph instances (already generated)
            theme: Story theme
            child_name: Optional child's name
            child_age: Optional child's age
            context_template: Template name
            **kwargs: Additional story elements
        
        Returns:
            dict: {
                'paragraph_text': str,
                'paragraph_type': str,
                'paragraph_index': int
            }
        """
        if paragraph_index < 1 or paragraph_index > 4:
            raise ValueError("paragraph_index must be between 1 and 4")
        
        para_type = ParagraphType.get_by_index(paragraph_index)
        if not para_type:
            raise ValueError(f"Invalid paragraph_index: {paragraph_index}")
        
        # Load context template
        try:
            template_data = self.template_loader.load_template(context_template)
        except Exception as e:
            print(f"Failed to load template {context_template}: {e}")
            raise
        
        # Build prompt for this paragraph
        prompt = self._build_paragraph_prompt(
            para_type, previous_paragraphs, theme, child_name, child_age, template_data, **kwargs
        )
        
        # Check if Gemini is configured
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set. Please configure it in your environment variables.")
        
        # Generate using Gemini
        result = self._generate_paragraph_with_gemini(prompt, template_data['system_prompt'], para_type)
        
        return result
    
    def _build_intro_prompt(self, theme, child_name, child_age, template_data, **kwargs):
        """Build prompt for intro paragraph generation."""
            name = child_name or "Your Hero"
            age = child_age or 5
            age = max(3, min(age, 10))
            
            character = kwargs.get('character', 'an adventurer')
            background = kwargs.get('background', 'a magical place')
            key_items = kwargs.get('key_items', [])
            
            # Get character personalities
            personalities = self._get_character_personalities(character)
            items_text = ", ".join(key_items) if key_items else "no special items"
            
            personality_text = ""
            if personalities:
                personality_list = "、".join(personalities)
                personality_text = f"\n角色性格特質：{personality_list}"
            
        # Get structure instruction for intro
        structure_instruction = template_data['structure'].get('intro_goal', '故事的開端(短篇)')
        
        # Build user prompt - replace placeholders manually since template uses [請在此填入...] format
        user_prompt = template_data['user_prompt_template']
        user_prompt = user_prompt.replace('[請在此填入故事希望傳達的中心思想，例如：互相合作、勇敢面對恐懼、分享的快樂]', theme)
        user_prompt = user_prompt.replace('[請在此填入主角1的中文名字，例如：小老鼠「吱吱」]', character)
        user_prompt = user_prompt.replace('[請在此填入主角2的中文名字，例如：小松鼠「果果」]', name)
        user_prompt = user_prompt.replace('[請在此填入一個充滿童趣的中文地點名稱，例如：「棉花糖雲朵」的柔軟森林]', background)
        user_prompt = user_prompt.replace('[請在此填入主角們要去達成的具體目標]', 
                                       f"探索{background}並找到{items_text}" if key_items else f"在{background}中冒險")
        # Replace [主角1] and [主角2] references in the structure section
        user_prompt = user_prompt.replace('[主角1]', character)
        user_prompt = user_prompt.replace('[主角2]', name)
        
        # Add specific instruction for intro paragraph
        prompt = f"""{user_prompt}

**現在請生成第一段（Intro Goal）：**
- {structure_instruction}
- 建立世界並介紹角色
- 確立目標
- 保持2-4個句子的長度
- 使用適合兒童的簡單詞彙
- 嚴格使用繁體中文"""
        
        return prompt
    
    def _build_paragraph_prompt(self, para_type, previous_paragraphs, theme, child_name, child_age, template_data, **kwargs):
        """Build prompt for generating a specific paragraph."""
            name = child_name or "Your Hero"
            age = child_age or 5
            age = max(3, min(age, 10))
            
            character = kwargs.get('character', 'an adventurer')
            background = kwargs.get('background', 'a magical place')
            key_items = kwargs.get('key_items', [])
            
            personalities = self._get_character_personalities(character)
            items_text = ", ".join(key_items) if key_items else "no special items"
            
            personality_text = ""
            if personalities:
                personality_list = "、".join(personalities)
                personality_text = f"\n角色性格特質：{personality_list}"
            
        # Build original user prompt - replace placeholders manually
        user_prompt = template_data['user_prompt_template']
        user_prompt = user_prompt.replace('[請在此填入故事希望傳達的中心思想，例如：互相合作、勇敢面對恐懼、分享的快樂]', theme)
        user_prompt = user_prompt.replace('[請在此填入主角1的中文名字，例如：小老鼠「吱吱」]', character)
        user_prompt = user_prompt.replace('[請在此填入主角2的中文名字，例如：小松鼠「果果」]', name)
        user_prompt = user_prompt.replace('[請在此填入一個充滿童趣的中文地點名稱，例如：「棉花糖雲朵」的柔軟森林]', background)
        user_prompt = user_prompt.replace('[請在此填入主角們要去達成的具體目標]', 
                                       f"探索{background}並找到{items_text}" if key_items else f"在{background}中冒險")
        # Replace [主角1] and [主角2] references in the structure section
        user_prompt = user_prompt.replace('[主角1]', character)
        user_prompt = user_prompt.replace('[主角2]', name)
        
        # Build previous paragraphs context
        previous_text = "\n\n".join([
            f"段落 {p.paragraph_index} ({p.paragraph_type}):\n{p.text}"
            for p in sorted(previous_paragraphs, key=lambda x: x.paragraph_index)
        ])
        
        # Get structure instruction for this paragraph
        structure_key = para_type.type_key
        structure_instruction = template_data['structure'].get(structure_key, para_type.chinese_name)
        
        # Build paragraph-specific instruction
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
                    'gemini-2.5-flash',
                    system_instruction=system_prompt,
                    safety_settings=safety_settings
                )
            else:
                model = genai.GenerativeModel(
                    'gemini-2.5-flash',
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
                if hasattr(response, 'prompt_feedback'):
                    print(f"   Prompt feedback: {response.prompt_feedback}")
                # Try to get prompt feedback for more info
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    print(f"   Prompt feedback block_reason: {getattr(response.prompt_feedback, 'block_reason', 'N/A')}")
                raise ValueError("Gemini API returned no candidates. The response may have been blocked by safety filters.")
            
            candidate = response.candidates[0]
            
            # Debug: Print finish_reason and other details
            finish_reason = getattr(candidate, 'finish_reason', None)
            safety_ratings = getattr(candidate, 'safety_ratings', [])
            print(f"🔍 DEBUG: Candidate finish_reason: {finish_reason}")
            print(f"🔍 DEBUG: Candidate safety_ratings: {safety_ratings}")
            
            # Check finish_reason - 2 means SAFETY (blocked by safety filters)
            # Even with BLOCK_NONE, Gemini may still block at system level
            if finish_reason == 2:
                # Get more details about what was blocked
                blocked_categories = []
                for rating in safety_ratings:
                    if hasattr(rating, 'category') and hasattr(rating, 'probability'):
                        if rating.probability >= 2:  # MEDIUM or HIGH
                            blocked_categories.append(f"{rating.category} (probability: {rating.probability})")
                
                # Check if there's any partial content we can use
                partial_content = None
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                partial_content = part.text
                                break
                
                error_details = "Content was blocked by Gemini's safety filters (even with BLOCK_NONE - system-level block)."
                if blocked_categories:
                    error_details += f" Blocked categories: {', '.join(blocked_categories)}"
                else:
                    error_details += " No specific category details available."
                
                print(f"❌ DEBUG: Safety filter triggered (system-level block)!")
                print(f"   Finish reason: {finish_reason} (2 = SAFETY)")
                print(f"   Blocked categories: {blocked_categories}")
                print(f"   Safety ratings: {safety_ratings}")
                print(f"   Partial content available: {bool(partial_content)}")
                
                # If we have partial content, try to use it
                if partial_content and len(partial_content.strip()) > 50:
                    print(f"⚠️  Using partial content (first {len(partial_content)} chars)")
                    paragraph_text = partial_content.strip()
                else:
                    # No usable content - the prompt itself might be problematic
                    print(f"💡 Suggestion: The Context Engineering template or prompt may contain words/phrases that trigger Gemini's hardcoded safety filters.")
                    print(f"   Consider simplifying the prompt or checking the template for potentially problematic content.")
                    raise ValueError(
                        error_details + " "
                        "The prompt itself may be triggering Gemini's system-level safety filters. "
                        "Try simplifying the Context Engineering template or using different wording."
                    )
            
            # Check if there's content in the response
            if not candidate.content or not candidate.content.parts:
                raise ValueError("Gemini API returned empty content. No text was generated.")
            
            # Extract text from the first part
            paragraph_text = candidate.content.parts[0].text.strip()
            
            if not paragraph_text:
                raise ValueError("Gemini API returned empty text content.")
            
            title = None
            if para_type == ParagraphType.INTRO_GOAL:
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
