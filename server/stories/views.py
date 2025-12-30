"""
API Views for Story generation, TTS, and image serving.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import FileResponse, JsonResponse
from django.conf import settings
from pathlib import Path
import os

from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from .models import Story, AudioFile, StoryParagraph
from .serializers import (
    StorySerializer,
    StoryParagraphSerializer,
    StoryGenerateRequestSerializer,
    AudioFileSerializer,
    TTSRequestSerializer,
    UserRegisterSerializer,
    UserLoginSerializer
)
from .context_engineering import StoryStructure, get_paragraph_type_by_index
from django.utils import timezone
from .story_generator import StoryGenerator
from .tts_service import TTSService


class StoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Story CRUD operations.
    
    Endpoints:
    - GET /api/stories/ - List all stories (user's own)
    - POST /api/stories/ - Create/save a story
    - GET /api/stories/{id}/ - Retrieve a story
    - PUT/PATCH /api/stories/{id}/ - Update a story
    - DELETE /api/stories/{id}/ - Delete a story
    - POST /api/stories/generate/ - Generate a new story
    """
    
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only stories belonging to the current user."""
        return Story.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Automatically set the user when creating a story."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        DEPRECATED: This endpoint is deprecated. Use generate_intro instead.
        
        This endpoint is kept for backward compatibility but will return an error.
        Please use POST /api/stories/generate_intro/ for the new two-stage generation.
        """
        return Response(
            {
                'error': 'This endpoint is deprecated',
                'message': 'Please use /api/stories/generate_intro/ for story generation',
                'details': 'The old generate endpoint has been replaced with a two-stage generation system using Context Engineering templates.'
            },
            status=status.HTTP_410_GONE  # 410 Gone indicates the resource is no longer available
        )
    
    @action(detail=False, methods=['post'])
    def generate_intro(self, request):
        """
        Generate only the first paragraph (Intro Goal) immediately.
        
        POST /api/stories/generate-intro/
        Body: {
            "theme": "caring",
            "child_name": "Emma" (optional),
            "child_age": 6 (optional),
            "language": "en" (optional),
            "character": "Princess" (optional),
            "background": "Castle" (optional),
            "key_items": ["Key1", "Key2"] (optional),
            "context_template": "5min_basic" (optional)
        }
        
        Returns: Story with first paragraph and TTS
        """
        serializer = StoryGenerateRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid request', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        context_template = request.data.get('context_template', '5min_basic')
        
        try:
            generator = StoryGenerator()
            tts_service = TTSService()
            
            # Generate intro paragraph
            intro_data = generator.generate_intro_paragraph(
                theme=data['theme'],
                child_name=data.get('child_name'),
                child_age=data.get('child_age'),
                context_template=context_template,
                character=data.get('character'),
                background=data.get('background'),
                key_items=data.get('key_items')
            )
            
            # Create Story instance
            # Use user-provided title if available, otherwise fall back to LLM-generated title
            user_title = data.get('title', '').strip()
            story_title = user_title if user_title else intro_data.get('title', 'Untitled Story')
            
            story = Story.objects.create(
                user=request.user,
                title=story_title,
                body='',  # Will be built from paragraphs
                theme=data['theme'],
                child_name=data.get('child_name'),
                child_age=data.get('child_age'),
                model_source='online',
                language=data.get('language', 'zh-TW'),
                character=data.get('character'),
                background=data.get('background'),
                key_items=data.get('key_items', []),
                generation_status='generating_intro',
                context_template=context_template
            )
            
            # Generate TTS for intro paragraph
            audio_content = tts_service.generate_audio(
                text=intro_data['paragraph_text'],
                language=data.get('language', 'zh-TW')
            )
            
            # Get intro paragraph type based on template
            intro_para_type = StoryStructure.get_intro_paragraph_type(story.context_template)
            
            # Create StoryParagraph
            paragraph = StoryParagraph.objects.create(
                story=story,
                paragraph_index=0,
                paragraph_type=intro_para_type.type_key,
                text=intro_data['paragraph_text'],
                is_generated=True,
                generated_at=timezone.now()
            )
            
            if audio_content:
                paragraph.tts_audio_file.save(
                    f'story_{story.id}_para_0.mp3',
                    audio_content
                )
                # Get duration if available
                try:
                    import mutagen
                    audio_file = mutagen.File(paragraph.tts_audio_file.path)
                    if audio_file:
                        paragraph.tts_duration_seconds = audio_file.info.length
                        paragraph.save()
                except:
                    pass
            
            # Update story status
            story.generation_status = 'intro_ready'
            story.save()
            
            # Serialize response
            result_serializer = StorySerializer(story, context={'request': request})
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Error in generate_intro: {str(e)}")
            print(f"Traceback:\n{error_trace}")
            return Response(
                {
                    'error': 'Intro generation failed',
                    'details': str(e),
                    'message': f'Failed to generate intro paragraph: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def generate_remaining(self, request, pk=None):
        """
        Generate remaining paragraphs (1-4) in the background.
        
        POST /api/stories/{id}/generate-remaining/
        
        Returns: Story with all paragraphs
        """
        try:
            story = self.get_object()
            
            # Verify ownership
            if story.user != request.user:
                return Response(
                    {'error': 'You do not have permission to generate paragraphs for this story'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if intro is ready
            if story.generation_status != 'intro_ready':
                return Response(
                    {'error': 'Intro paragraph must be generated first'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update status
            story.generation_status = 'generating_remaining'
            story.save()
            
            generator = StoryGenerator()
            tts_service = TTSService()
            
            # Get existing paragraphs
            existing_paragraphs = list(story.paragraphs.all().order_by('paragraph_index'))
            
            # Get total paragraph count for this template
            total_paragraphs = StoryStructure.get_paragraph_count(story.context_template)
            
            # Generate remaining paragraphs (1 to total-1)
            for para_index in range(1, total_paragraphs):
                try:
                    # Generate paragraph
                    para_data = generator.generate_paragraph(
                        paragraph_index=para_index,
                        previous_paragraphs=existing_paragraphs,
                        theme=story.theme,
                        child_name=story.child_name,
                        child_age=story.child_age,
                        context_template=story.context_template,
                        story=story,  # Pass story for backward compatibility (though not used)
                        character=story.character,
                        background=story.background,
                        key_items=story.key_items or []
                    )
                    
                    # Generate TTS
                    audio_content = tts_service.generate_audio(
                        text=para_data['paragraph_text'],
                        language=story.language
                    )
                    
                    # Create paragraph
                    paragraph = StoryParagraph.objects.create(
                        story=story,
                        paragraph_index=para_index,
                        paragraph_type=para_data['paragraph_type'],
                        text=para_data['paragraph_text'],
                        is_generated=True,
                        generated_at=timezone.now()
                    )
                    
                    if audio_content:
                        paragraph.tts_audio_file.save(
                            f'story_{story.id}_para_{para_index}.mp3',
                            audio_content
                        )
                        # Get duration
                        try:
                            import mutagen
                            audio_file = mutagen.File(paragraph.tts_audio_file.path)
                            if audio_file:
                                paragraph.tts_duration_seconds = audio_file.info.length
                                paragraph.save()
                        except:
                            pass
                    
                    # Add to existing paragraphs for next iteration
                    existing_paragraphs.append(paragraph)
                    
                except Exception as e:
                    print(f"Failed to generate paragraph {para_index}: {e}")
                    # Continue with next paragraph even if one fails
            
            # Update story status and build full body
            story.generation_status = 'completed'
            # Build body from all paragraphs
            all_paragraphs = story.paragraphs.all().order_by('paragraph_index')
            story.body = '\n\n'.join([p.text for p in all_paragraphs])
            story.save()
            
            # Serialize response
            result_serializer = StorySerializer(story, context={'request': request})
            return Response(result_serializer.data, status=status.HTTP_200_OK)
            
        except Story.DoesNotExist:
            return Response(
                {'error': 'Story not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': 'Remaining paragraphs generation failed', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def get_status(self, request, pk=None):
        """
        Get story generation status and available paragraphs.
        
        GET /api/stories/{id}/get-status/
        
        Returns: Story status and paragraphs
        """
        try:
            story = self.get_object()
            
            # Verify ownership
            if story.user != request.user:
                return Response(
                    {'error': 'You do not have permission to view this story'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            result_serializer = StorySerializer(story, context={'request': request})
            return Response(result_serializer.data, status=status.HTTP_200_OK)
            
        except Story.DoesNotExist:
            return Response(
                {'error': 'Story not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'], url_path='paragraphs/(?P<paragraph_index>[0-9]+)')
    def get_paragraph(self, request, pk=None, paragraph_index=None):
        """
        Get a specific paragraph by index.
        
        GET /api/stories/{id}/paragraphs/{index}/
        
        Returns: Paragraph data
        """
        try:
            story = self.get_object()
            
            # Verify ownership
            if story.user != request.user:
                return Response(
                    {'error': 'You do not have permission to view this story'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            para_index = int(paragraph_index)
            paragraph = story.paragraphs.filter(paragraph_index=para_index).first()
            
            if not paragraph:
                return Response(
                    {'error': 'Paragraph not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            para_serializer = StoryParagraphSerializer(paragraph, context={'request': request})
            return Response(para_serializer.data, status=status.HTTP_200_OK)
            
        except Story.DoesNotExist:
            return Response(
                {'error': 'Story not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Invalid paragraph index'},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_audio(request):
    """
    Generate audio (TTS) for a story.
    
    POST /api/tts/generate/
    Body: {
        "story_id": "uuid",
        "language": "en" (optional),
        "voice": "nova" (optional)
    }
    
    Returns: AudioFile object with audio URL
    """
    serializer = TTSRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    data = serializer.validated_data
    
    try:
        # Get the story
        story = Story.objects.get(id=data['story_id'])
        
        # Verify ownership
        if story.user != request.user:
            return Response(
                {'error': 'You do not have permission to generate audio for this story'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if audio already exists for this language
        existing_audio = AudioFile.objects.filter(
            story=story,
            language=data.get('language', 'en')
        ).first()
        
        if existing_audio:
            audio_serializer = AudioFileSerializer(existing_audio, context={'request': request})
            return Response(audio_serializer.data)
        
        # Generate audio
        tts_service = TTSService()
        audio_content = tts_service.generate_audio(
            text=f"{story.title}. {story.body}",
            language=data.get('language', 'en'),
            voice=data.get('voice')
        )
        
        if not audio_content:
            return Response(
                {'error': 'Audio generation failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Save audio file
        audio_file = AudioFile.objects.create(
            story=story,
            language=data.get('language', 'en')
        )
        audio_file.audio_file.save(f'story_{story.id}.mp3', audio_content)
        
        audio_serializer = AudioFileSerializer(audio_file, context={'request': request})
        return Response(audio_serializer.data, status=status.HTTP_201_CREATED)
        
    except Story.DoesNotExist:
        return Response(
            {'error': 'Story not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Audio generation failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def list_images(request):
    """
    List available images for stories.
    
    GET /api/images/
    Query params:
        - category: 'characters', 'backgrounds', 'themes', 'key-items' (optional)
    
    Returns: {
        "characters": [...],
        "backgrounds": [...],
        "themes": [...],
        "key_items": [...]
    }
    """
    # Path to assets in the frontend
    assets_path = Path(settings.BASE_DIR).parent / 'adventure-cube' / 'assets' / 'images'
    
    category = request.GET.get('category')
    
    result = {}
    
    categories = {
        'characters': 'Characters',
        'backgrounds': 'Background',
        'themes': 'Theme',
        'key_items': 'Key Items'
    }
    
    try:
        for key, folder_name in categories.items():
            if category and category != key:
                continue
            
            folder_path = assets_path / folder_name
            
            if folder_path.exists() and folder_path.is_dir():
                images = []
                for file in folder_path.iterdir():
                    if file.is_file() and file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                        images.append({
                            'name': file.stem,
                            'filename': file.name,
                            'path': f'/images/{folder_name}/{file.name}',
                            'category': key
                        })
                result[key] = sorted(images, key=lambda x: x['name'])
            else:
                result[key] = []
        
        return Response(result)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to list images', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_themes(request):
    """
    Get available story themes.
    
    GET /api/themes/
    
    Returns: List of available themes
    """
    from .story_generator import STORY_TEMPLATES
    
    themes = [
        {
            'id': theme,
            'name': theme.capitalize(),
            'description': f'Stories about {theme}',
            'story_count': len(templates)
        }
        for theme, templates in STORY_TEMPLATES.items()
    ]
    
    return Response({'themes': themes})


# Authentication endpoints

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user.
    
    POST /api/auth/register/
    Body: {
        "username": "user",
        "password": "pass123",
        "password2": "pass123",
        "email": "user@example.com" (optional)
    }
    
    Returns: User object and authentication token
    """
    serializer = UserRegisterSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid registration data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = serializer.save()
        # Create authentication token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'token': token.key
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': 'Registration failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login a user.
    
    POST /api/auth/login/
    Body: {
        "username": "user",
        "password": "pass123"
    }
    
    Returns: User object and authentication token
    """
    serializer = UserLoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid login data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get or create token
    token, created = Token.objects.get_or_create(user=user)
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'token': token.key
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout a user by deleting their token.
    
    POST /api/auth/logout/
    
    Requires: Authorization header with token
    """
    try:
        # Delete the user's token
        request.user.auth_token.delete()
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': 'Logout failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
