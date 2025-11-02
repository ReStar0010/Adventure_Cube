"""
URL configuration for stories API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'stories', views.StoryViewSet, basename='story')

urlpatterns = [
    path('', include(router.urls)),
    path('tts/generate/', views.generate_audio, name='generate-audio'),
    path('images/', views.list_images, name='list-images'),
    path('themes/', views.get_themes, name='get-themes'),
    
    # Authentication endpoints
    path('auth/register/', views.register_user, name='register'),
    path('auth/login/', views.login_user, name='login'),
    path('auth/logout/', views.logout_user, name='logout'),
]
