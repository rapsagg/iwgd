from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet, UserRegistrationViewSet, ReputationTierViewSet,
    TopicViewSet,
    PostViewSet,
    CommentViewSet,
    ReactionViewSet,
    PollViewSet,
    FactCheckNoteViewSet,
    FlagViewSet,
    toggle_like,
)

# Create a router and register all viewsets
router = DefaultRouter()

# User & Auth
router.register(r'users', UserProfileViewSet, basename='userprofile')
router.register(r'auth/register', UserRegistrationViewSet, basename='register')
router.register(r'reputation-tiers', ReputationTierViewSet, basename='reputation-tier')

# Topics
router.register(r'topics', TopicViewSet, basename='topic')

# Posts & Comments
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')

# Reactions
router.register(r'reactions', ReactionViewSet, basename='reaction')

# Polls
router.register(r'polls', PollViewSet, basename='poll')

# Fact-checking
router.register(r'fact-check-notes', FactCheckNoteViewSet, basename='fact-check-note')

# Flags & Moderation
router.register(r'flags', FlagViewSet, basename='flag')

app_name = 'forum'

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', obtain_auth_token, name='api_token_auth'),
    path('posts/<int:post_id>/like/', toggle_like, name='toggle_like'),
]
