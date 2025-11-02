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

from .models import Story, AudioFile
from .serializers import (
    StorySerializer,
    StoryGenerateRequestSerializer,
    AudioFileSerializer,
    TTSRequestSerializer,
    UserRegisterSerializer,
    UserLoginSerializer
)
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
        Generate a new story based on theme and child information.
        
        POST /api/stories/generate/
        Body: {
            "theme": "caring",
            "child_name": "Emma" (optional),
            "child_age": 6 (optional),
            "language": "en" (optional),
            "character": "Princess" (optional),
            "background": "Castle" (optional),
            "key_items": ["Key1", "Key2"] (optional)
        }
        
        Returns: Story object with generated content
        """
        serializer = StoryGenerateRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid request', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        # Generate story
        try:
            generator = StoryGenerator()
            story_data = generator.generate_story(
                theme=data['theme'],
                child_name=data.get('child_name'),
                child_age=data.get('child_age'),
                character=data.get('character'),
                background=data.get('background'),
                key_items=data.get('key_items')
            )
            
            # Create Story instance
            story = Story.objects.create(
                user=request.user,
                title=story_data['title'],
                body=story_data['body'],
                theme=data['theme'],
                child_name=data.get('child_name'),
                child_age=data.get('child_age'),
                model_source=story_data['model_source'],
                language=data.get('language', 'en'),
                character=data.get('character'),
                background=data.get('background'),
                key_items=data.get('key_items', [])
            )
            
            result_serializer = StorySerializer(story)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': 'Story generation failed', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
