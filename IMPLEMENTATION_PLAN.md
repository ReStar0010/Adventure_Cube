# Progressive Story Generation Implementation Plan

## Overview
Transform story generation from single-shot to progressive paragraph-by-paragraph generation with immediate first-paragraph delivery, following the 5-paragraph structure from Context Engineering templates.

---

## Part 1: Context Engineering Module

### 1.1 Module Structure
Create a new module to handle context engineering templates:

```
server/stories/context_engineering/
├── __init__.py
├── templates.py          # Load and parse context engineering templates
├── prompts.py            # Build prompts from templates
└── structures.py         # Define story structure (5 paragraphs)
```

### 1.2 Template System Requirements
- Load templates from `Context_Engineering/` folder
- Support multiple templates: `5min_basic.md`, `10min_basic.md`, etc.
- Parse system prompt and user prompt sections
- Extract story structure (5 paragraphs: Intro Goal, Problem Obstacle, Effort Effort, Climax Climax, Ending Ending)

### 1.3 Template Parser Implementation
The parser should:
- Read markdown files from `Context_Engineering/` directory
- Extract `# system_prompt` section
- Extract `# user_prompt` section
- Parse story structure definitions
- Return structured template object

---

## Part 2: Database Schema Changes

### 2.1 New Model: StoryParagraph

```python
class StoryParagraph(models.Model):
    """
    Represents a single paragraph of a story with its TTS.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='paragraphs')
    paragraph_index = models.IntegerField()  # 0-4 (5 paragraphs)
    paragraph_type = models.CharField(max_length=50)  # 'intro_goal', 'problem_obstacle', etc.
    text = models.TextField()
    tts_audio_file = models.FileField(upload_to='audio/paragraphs/', null=True, blank=True)
    tts_duration_seconds = models.FloatField(null=True, blank=True)
    is_generated = models.BooleanField(default=False)  # Track generation status
    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['story', 'paragraph_index']
        unique_together = ['story', 'paragraph_index']
```

**Paragraph Types:**
- `intro_goal` (Index 0)
- `problem_obstacle` (Index 1)
- `effort_effort` (Index 2)
- `climax_climax` (Index 3)
- `ending_ending` (Index 4)

### 2.2 Update Story Model

Add new fields to existing `Story` model:

```python
class Story(models.Model):
    # ... existing fields ...
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
    context_template = models.CharField(max_length=100, default='5min_basic')  # Which template used
```

### 2.3 Migration Strategy
- Create migration for `StoryParagraph` model
- Add new fields to `Story` model
- Keep existing `body` field for backward compatibility (can be deprecated later)

---

## Part 3: Two-Phase Generation System

### 3.1 Phase 1: Generate Intro Paragraph (Immediate)

**Endpoint:** `POST /api/stories/generate-intro/`

**Workflow:**
1. Create Story with `generation_status='generating_intro'`
2. Load context template (e.g., `5min_basic.md`)
3. Generate only Intro Goal paragraph using full prompt
4. Generate TTS for intro paragraph immediately
5. Save StoryParagraph (index=0) with text + TTS
6. Update Story: `generation_status='intro_ready'`
7. Return response with intro paragraph + TTS URL

**Prompt Structure (Phase 1):**
```
[System Prompt from 5min_basic.md]

[User Prompt with story elements]

**Generate ONLY the first paragraph (Intro Goal):**
- Establish the world and introduce characters
- Set up the goal
- Keep it to 2-4 sentences
- Use simple vocabulary for children
- Follow the structure: 故事開端(短篇)
```

**Response Format:**
```json
{
  "id": "story-uuid",
  "title": "Story Title",
  "generation_status": "intro_ready",
  "paragraphs": [
    {
      "index": 0,
      "type": "intro_goal",
      "text": "Paragraph text...",
      "tts_url": "http://.../audio/paragraph_0.mp3",
      "is_ready": true
    }
  ],
  "total_paragraphs": 5,
  "paragraphs_ready": 1
}
```

### 3.2 Phase 2: Generate Remaining Paragraphs (Background)

**Endpoint:** `POST /api/stories/generate-remaining/{story_id}/`

**Workflow:**
1. Fetch Story and first paragraph
2. Update `generation_status='generating_remaining'`
3. For each remaining paragraph (index 1-4):
   - Generate paragraph using:
     - Original prompt
     - Previously generated paragraphs as context
     - Specific paragraph type instruction
   - Generate TTS for paragraph
   - Save StoryParagraph
   - Update Story status
4. Update Story: `generation_status='completed'`

**Prompt Structure (Phase 2 - Example for Paragraph 2):**
```
[System Prompt from 5min_basic.md]

[Original User Prompt with story elements]

**Previously Generated Paragraphs:**
[Paragraph 0: Intro Goal text]

**Now Generate Paragraph 2 (Problem Obstacle):**
- Build on the intro paragraph
- Introduce a specific obstacle
- Keep it to 2-4 sentences
- Follow the structure: 出現了阻礙(短篇)
- The obstacle should directly challenge the goal established in intro
```

**Paragraph Generation Order:**
1. Paragraph 1 (Problem Obstacle) - uses Paragraph 0 as context
2. Paragraph 2 (Effort Effort) - uses Paragraphs 0-1 as context
3. Paragraph 3 (Climax Climax) - uses Paragraphs 0-2 as context
4. Paragraph 4 (Ending Ending) - uses Paragraphs 0-3 as context

---

## Part 4: Backend API Endpoints

### 4.1 New Endpoints in StoryViewSet

```python
# views.py

@action(detail=False, methods=['post'])
def generate_intro(self, request):
    """
    Generate only the first paragraph (Intro Goal) immediately.
    
    POST /api/stories/generate-intro/
    Body: {
        "theme": "caring",
        "child_name": "Emma",
        "child_age": 6,
        "character": "Princess",
        "background": "Castle",
        "key_items": ["Magic Key"],
        "language": "zh-TW",
        "context_template": "5min_basic"  # optional, defaults to 5min_basic
    }
    
    Returns: Story object with first paragraph + TTS ready
    """
    pass

@action(detail=True, methods=['post'])
def generate_remaining(self, request, pk=None):
    """
    Generate remaining paragraphs (2-5) in background.
    Can be called after intro is ready.
    
    POST /api/stories/{id}/generate-remaining/
    
    Returns: { "message": "Generation started", "story_id": "..." }
    """
    pass

@action(detail=True, methods=['get'])
def get_paragraph(self, request, pk=None):
    """
    Get a specific paragraph by index.
    
    GET /api/stories/{id}/get_paragraph/?index=0
    
    Returns: StoryParagraph object with text and TTS
    """
    pass

@action(detail=True, methods=['get'])
def get_status(self, request, pk=None):
    """
    Get story generation status.
    
    GET /api/stories/{id}/get_status/
    
    Returns: {
        "status": "intro_ready",
        "paragraphs_ready": [0, 1],
        "total_paragraphs": 5,
        "paragraphs": [
            {"index": 0, "type": "intro_goal", "is_ready": true},
            {"index": 1, "type": "problem_obstacle", "is_ready": true},
            ...
        ]
    }
    """
    pass
```

### 4.2 Background Task for Remaining Paragraphs

Consider using:
- Django background tasks (django-background-tasks)
- Celery (for production)
- Or simple async task in views.py

---

## Part 5: Story Generator Changes

### 5.1 New Methods in StoryGenerator

```python
class StoryGenerator:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.context_loader = ContextTemplateLoader()
    
    def generate_intro_paragraph(self, theme, child_name, child_age, 
                                  character, background, key_items, 
                                  language='zh-TW', context_template='5min_basic'):
        """
        Generate ONLY the first paragraph (Intro Goal).
        Uses full prompt but only generates intro.
        
        Returns: {
            'title': str,
            'paragraph_text': str,
            'model_source': 'online' or 'offline'
        }
        """
        pass
    
    def generate_paragraph(self, paragraph_index, paragraph_type, 
                          theme, character, background, key_items,
                          previous_paragraphs, language='zh-TW', 
                          context_template='5min_basic'):
        """
        Generate a specific paragraph using previous paragraphs as context.
        
        Args:
            paragraph_index: 1-4 (0 is intro, already generated)
            paragraph_type: 'problem_obstacle', 'effort_effort', etc.
            previous_paragraphs: List of generated paragraph texts
            language: Language code
            context_template: Template name (5min_basic, 10min_basic, etc.)
        
        Returns: {
            'paragraph_text': str,
            'model_source': 'online' or 'offline'
        }
        """
        pass
    
    def _load_context_template(self, template_name='5min_basic'):
        """
        Load context engineering template from file.
        
        Returns: {
            'system_prompt': str,
            'user_prompt_template': str,
            'structure': {
                'intro_goal': str,
                'problem_obstacle': str,
                'effort_effort': str,
                'climax_climax': str,
                'ending_ending': str
            }
        }
        """
        pass
    
    def _build_intro_prompt(self, context_template, story_elements, language='zh-TW'):
        """
        Build prompt for intro paragraph generation.
        
        Args:
            context_template: Loaded template object
            story_elements: Dict with theme, character, background, etc.
            language: Language code
        
        Returns: Complete prompt string
        """
        pass
    
    def _build_paragraph_prompt(self, context_template, story_elements, 
                                paragraph_type, previous_paragraphs, language='zh-TW'):
        """
        Build prompt for subsequent paragraph generation.
        
        Args:
            context_template: Loaded template object
            story_elements: Dict with theme, character, background, etc.
            paragraph_type: Type of paragraph to generate
            previous_paragraphs: List of previously generated paragraph texts
            language: Language code
        
        Returns: Complete prompt string
        """
        pass
```

### 5.2 Prompt Building Logic

**Intro Prompt Structure:**
```
[System Prompt from template]

[User Prompt Template filled with story elements]

**重要：請只生成第一段（Intro Goal）**
根據以下要求創作故事的開端：
- 快速建立一個充滿奇特細節的世界
- 透過簡短有趣的行為介紹主角的獨特個性
- 清晰地確立他們要去達成的目標
- 保持2-4個句子的長度
- 使用學齡前兒童能理解的簡單詞彙
```

**Remaining Paragraph Prompt Structure:**
```
[System Prompt from template]

[Original User Prompt with story elements]

**已生成的前面段落：**
[Paragraph 0: Intro Goal text]
[Paragraph 1: Problem Obstacle text]  # if generating paragraph 3+

**現在請生成第{paragraph_index}段（{paragraph_type}）：**
[Specific instructions for this paragraph type from template]
- 必須與前面段落連貫
- 保持2-4個句子的長度
- 使用簡單詞彙
```

---

## Part 6: TTS Service Updates

### 6.1 Per-Paragraph TTS Generation

Update `tts_service.py` to work with paragraphs:

```python
def generate_paragraph_audio(self, paragraph_text, story_id, paragraph_index, language='zh-TW'):
    """
    Generate TTS audio for a single paragraph.
    
    Returns: Audio file content
    """
    pass
```

### 6.2 Audio File Naming
- Format: `story_{story_id}_paragraph_{index}.mp3`
- Storage: `media/audio/paragraphs/`

---

## Part 7: Frontend Implementation

### 7.1 Update StoryService

```typescript
// services/story.service.ts

export class StoryService {
    /**
     * Generate intro paragraph only (fast)
     */
    static async generateIntro(
        storyTitle: string,
        theme: StoryAsset,
        character: StoryAsset,
        background: StoryAsset,
        keyItems?: StoryAsset[],
        childName?: string,
        childAge?: number,
        language: string = 'zh-TW',
        contextTemplate: string = '5min_basic'
    ): Promise<{ story: Story; introParagraph: StoryParagraph }> {
        // Call POST /api/stories/generate-intro/
    }
    
    /**
     * Start generating remaining paragraphs (background)
     */
    static async generateRemaining(storyId: string): Promise<void> {
        // Call POST /api/stories/{id}/generate-remaining/
    }
    
    /**
     * Get story generation status
     */
    static async getStoryStatus(storyId: string): Promise<StoryStatus> {
        // Call GET /api/stories/{id}/get_status/
    }
    
    /**
     * Get specific paragraph
     */
    static async getParagraph(storyId: string, index: number): Promise<StoryParagraph> {
        // Call GET /api/stories/{id}/get_paragraph/?index={index}
    }
}
```

### 7.2 New Types

```typescript
// types/Story.ts

export interface StoryParagraph {
    index: number;
    type: 'intro_goal' | 'problem_obstacle' | 'effort_effort' | 'climax_climax' | 'ending_ending';
    text: string;
    tts_url?: string;
    tts_duration_seconds?: number;
    is_ready: boolean;
    generated_at?: string;
}

export interface StoryStatus {
    status: 'pending' | 'generating_intro' | 'intro_ready' | 'generating_remaining' | 'completed';
    paragraphs_ready: number[];
    total_paragraphs: number;
    paragraphs: StoryParagraph[];
}
```

### 7.3 Story Viewer Component

```typescript
// app/(tabs)/story.tsx or new component

const StoryViewer = () => {
    const [currentParagraphIndex, setCurrentParagraphIndex] = useState(0);
    const [paragraphs, setParagraphs] = useState<StoryParagraph[]>([]);
    const [storyStatus, setStoryStatus] = useState<StoryStatus | null>(null);
    const [storyId, setStoryId] = useState<string | null>(null);
    
    // Generate intro on mount
    useEffect(() => {
        generateIntro();
    }, []);
    
    // Poll for new paragraphs
    useEffect(() => {
        if (storyId && storyStatus?.status !== 'completed') {
            const interval = setInterval(() => {
                pollForNewParagraphs();
            }, 2000); // Poll every 2 seconds
            
            return () => clearInterval(interval);
        }
    }, [storyId, storyStatus]);
    
    const generateIntro = async () => {
        const result = await StoryService.generateIntro(...);
        setParagraphs([result.introParagraph]);
        setStoryId(result.story.id);
        
        // Start generating remaining
        StoryService.generateRemaining(result.story.id);
    };
    
    const pollForNewParagraphs = async () => {
        const status = await StoryService.getStoryStatus(storyId!);
        setStoryStatus(status);
        setParagraphs(status.paragraphs.filter(p => p.is_ready));
    };
    
    const handleNext = () => {
        if (currentParagraphIndex < paragraphs.length - 1) {
            setCurrentParagraphIndex(currentParagraphIndex + 1);
        }
    };
    
    return (
        <View>
            {/* Current paragraph display */}
            {paragraphs[currentParagraphIndex] && (
                <>
                    <Text>{paragraphs[currentParagraphIndex].text}</Text>
                    {/* TTS player */}
                    <AudioPlayer src={paragraphs[currentParagraphIndex].tts_url} />
                </>
            )}
            
            {/* Next button */}
            {currentParagraphIndex < paragraphs.length - 1 && (
                <Button onPress={handleNext}>下一段</Button>
            )}
            
            {/* Loading indicator for remaining paragraphs */}
            {storyStatus?.status === 'generating_remaining' && (
                <Text>正在生成後續段落...</Text>
            )}
        </View>
    );
};
```

---

## Part 8: Implementation Checklist

### Backend Tasks

- [ ] Create `server/stories/context_engineering/` module directory
- [ ] Implement `templates.py` - Template loader and parser
- [ ] Implement `prompts.py` - Prompt builder
- [ ] Implement `structures.py` - Story structure definitions
- [ ] Create `StoryParagraph` model in `models.py`
- [ ] Update `Story` model with `generation_status` and `context_template`
- [ ] Create database migration for new models
- [ ] Update `StoryGenerator` class with new methods:
  - [ ] `generate_intro_paragraph()`
  - [ ] `generate_paragraph()`
  - [ ] `_load_context_template()`
  - [ ] `_build_intro_prompt()`
  - [ ] `_build_paragraph_prompt()`
- [ ] Create new API endpoints in `views.py`:
  - [ ] `generate_intro()`
  - [ ] `generate_remaining()`
  - [ ] `get_paragraph()`
  - [ ] `get_status()`
- [ ] Update `serializers.py` with `StoryParagraphSerializer`
- [ ] Update `tts_service.py` for per-paragraph TTS
- [ ] Update `urls.py` with new routes
- [ ] Test paragraph generation with all LLM providers (OpenAI, Gemini, Anthropic)
- [ ] Test template loading from Context_Engineering folder

### Frontend Tasks

- [ ] Update `api.types.ts` with new types:
  - [ ] `StoryParagraph` interface
  - [ ] `StoryStatus` interface
- [ ] Update `story.service.ts` with new methods:
  - [ ] `generateIntro()`
  - [ ] `generateRemaining()`
  - [ ] `getStoryStatus()`
  - [ ] `getParagraph()`
- [ ] Update `use-story-generation.ts` hook for new flow
- [ ] Create or update story viewer component:
  - [ ] Paragraph-by-paragraph display
  - [ ] Next button navigation
  - [ ] TTS playback per paragraph
  - [ ] Loading states
  - [ ] Polling mechanism
- [ ] Update `story.tsx` to use new paragraph-based system
- [ ] Test progressive loading and display
- [ ] Test TTS playback for each paragraph

### Testing Tasks

- [ ] Test intro generation speed (< 3 seconds)
- [ ] Test remaining paragraph generation
- [ ] Test paragraph context continuity
- [ ] Test TTS generation for each paragraph
- [ ] Test frontend polling and display
- [ ] Test navigation between paragraphs
- [ ] Test error handling (generation failures)
- [ ] Test with different templates (5min_basic, 10min_basic)

---

## Part 9: Migration Strategy

### 9.1 Backward Compatibility
- Keep existing `Story.body` field for now
- Old stories can still be displayed using `body` field
- New stories use `paragraphs` relationship
- Add migration to convert old stories (optional)

### 9.2 Deployment Steps
1. Deploy backend changes first
2. Run database migrations
3. Test API endpoints
4. Deploy frontend changes
5. Monitor generation performance
6. Collect user feedback

---

## Part 10: Performance Considerations

### 10.1 Generation Speed Targets
- Intro paragraph: < 3 seconds
- Each remaining paragraph: 5-10 seconds
- Total story generation: 20-40 seconds (background)

### 10.2 Optimization Strategies
- Cache context templates in memory
- Use async/background tasks for remaining paragraphs
- Optimize TTS generation (consider caching)
- Frontend polling interval: 2 seconds (adjustable)

### 10.3 Error Handling
- If intro generation fails: Show error, allow retry
- If remaining paragraph fails: Continue with available paragraphs, show error
- If TTS generation fails: Show text only, allow retry TTS later

---

## Part 11: Future Enhancements

### 11.1 Potential Improvements
- Support for different story lengths (5min, 10min templates)
- Allow user to regenerate specific paragraphs
- Add paragraph editing capability
- Support for multiple languages in prompts
- Progressive TTS generation (streaming audio)

### 11.2 Analytics
- Track generation times per paragraph
- Monitor user engagement (which paragraphs are viewed most)
- Track TTS playback completion rates

---

## Summary

This implementation transforms the story generation system from a single-shot approach to a progressive, paragraph-by-paragraph system that:

1. **Immediately delivers** the first paragraph (< 3 seconds)
2. **Generates remaining paragraphs** in the background
3. **Stores each paragraph separately** with its own TTS
4. **Displays stories page-by-page** with navigation
5. **Uses Context Engineering templates** for structured generation
6. **Maintains story continuity** by using previous paragraphs as context

The system is designed to provide a better user experience with faster initial feedback while maintaining high-quality, coherent story generation.

