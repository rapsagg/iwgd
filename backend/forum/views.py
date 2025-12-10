from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import GenericAPIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, AnonymousUser, User
from typing import TYPE_CHECKING

from .models import (
    ReputationTier, UserProfile, UserFollowing,
    Topic, TopicFollowing,
    Moderation, BanAppeal,
    Post, Comment,
    Like, Reaction,
    Poll, PollOption, PollVote,
    FactCheckNote, FactCheckVote,
    Flag,
)
from .serializers import (
    ReputationTierSerializer, UserProfileSerializer, UserRegistrationSerializer,
    UserFollowingSerializer,
    TopicSerializer, TopicFollowingSerializer,
    PostSerializer, CommentSerializer,
    LikeSerializer, ReactionSerializer,
    PollSerializer, PollOptionSerializer, PollVoteSerializer,
    FactCheckNoteSerializer, FactCheckVoteSerializer,
    FlagSerializer, ModerationSerializer, BanAppealSerializer,
)

AbstractUser.profile: UserProfile     # type: ignore[attr-defined]
AnonymousUser.profile: UserProfile    # type: ignore[attr-defined]
User.profile: UserProfile             # type: ignore[attr-defined]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_like(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        
        # Check if already liked
        existing_like = Like.objects.filter(user=request.user, post=post).first()
        
        if existing_like:
            # Unlike
            existing_like.delete()
            liked = False
        else:
            # Like
            Like.objects.create(
                user=request.user,
                post=post,
                content_type='post'
            )
            liked = True
        
        # Manually count likes instead of relying on signals
        post.refresh_from_db()
        likes_count = Like.objects.filter(post=post).count()
        
        return Response({
            'liked': liked, 
            'likes_count': likes_count
        })
            
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ============================================================================
# PAGINATION
# ============================================================================

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ============================================================================
# USER & AUTHENTICATION VIEWSETS
# ============================================================================

class UserProfileViewSet(viewsets.ModelViewSet):
    """User profiles with reputation"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'display_name', 'country']
    ordering_fields = ['reputation_points', 'account_created']
    ordering = ['-reputation_points']
    
    def get_object(self) -> UserProfile:    # type: ignore
        """Allow fetching profile by username"""
        from rest_framework.exceptions import NotFound
        username = self.kwargs.get('pk')
        try:
            if username and username.isdigit():
                return UserProfile.objects.get(pk=username)
            return UserProfile.objects.get(user__username=username)
        except UserProfile.DoesNotExist:
            raise NotFound("Profile not found")
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user's profile"""
        profile = request.user.profile
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """Follow a user"""
        user_to_follow = self.get_object()
        follower_profile = request.user.profile
        
        if user_to_follow.user == request.user:
            return Response(
                {'detail': 'Cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        following, created = UserFollowing.objects.get_or_create(
            follower=request.user,
            following=user_to_follow.user
        )
        
        if created:
            user_to_follow.followers_count += 1
            user_to_follow.save(update_fields=['followers_count'])
            follower_profile.following_count += 1
            follower_profile.save(update_fields=['following_count'])
            return Response({'detail': 'Followed'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'Already following'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        """Unfollow a user"""
        user_to_unfollow = self.get_object()
        follower_profile = request.user.profile
        
        try:
            following = UserFollowing.objects.get(
                follower=request.user,
                following=user_to_unfollow.user
            )
            following.delete()
            user_to_unfollow.followers_count = max(0, user_to_unfollow.followers_count - 1)
            user_to_unfollow.save(update_fields=['followers_count'])
            follower_profile.following_count = max(0, follower_profile.following_count - 1)
            follower_profile.save(update_fields=['following_count'])
            return Response({'detail': 'Unfollowed'})
        except UserFollowing.DoesNotExist:
            return Response({'detail': 'Not following'}, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationViewSet(viewsets.ModelViewSet):
    """Register new users"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Register a new user"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReputationTierViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only reputation tier info"""
    queryset = ReputationTier.objects.all()
    serializer_class = ReputationTierSerializer
    permission_classes = [AllowAny]
    ordering = ['tier_number']


# ============================================================================
# TOPIC VIEWSETS
# ============================================================================

class TopicViewSet(viewsets.ModelViewSet):
    """Topics for discussion"""
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['followers_count', 'posts_count', 'created_at']
    ordering = ['-followers_count']
    
    def perform_create(self, serializer):
        """Set creator when creating topic"""
        serializer.save(creator=self.request.user)
    
    def perform_destroy(self, instance):
        """Only creator can delete"""
        from rest_framework.exceptions import PermissionDenied
        if instance.creator != self.request.user:
            raise PermissionDenied('Cannot delete topic you did not create')
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """Follow a topic"""
        topic = self.get_object()
        following, created = TopicFollowing.objects.get_or_create(
            user=request.user,
            topic=topic
        )
        
        if created:
            topic.followers_count += 1
            topic.save(update_fields=['followers_count'])
            return Response({'detail': 'Following topic'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'Already following'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        """Unfollow a topic"""
        topic = self.get_object()
        try:
            following = TopicFollowing.objects.get(user=request.user, topic=topic)
            following.delete()
            topic.followers_count = max(0, topic.followers_count - 1)
            topic.save(update_fields=['followers_count'])
            return Response({'detail': 'Unfollowed topic'})
        except TopicFollowing.DoesNotExist:
            return Response({'detail': 'Not following'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_topics(self, request):
        """Get topics user is following"""
        topics = Topic.objects.filter(
            topicfollowing__user=request.user
        ).distinct()
        page = self.paginate_queryset(topics)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(topics, many=True)
        return Response(serializer.data)


# ============================================================================
# POST VIEWSETS
# ============================================================================

class PostViewSet(viewsets.ModelViewSet):
    """Posts in topics"""
    queryset = Post.objects.filter(is_hidden=False)
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'likes_count', 'comments_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter by topic if provided"""
        queryset = super().get_queryset()
        topic_id = self.request.query_params.get('topic_id')
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        return queryset
    
    def perform_create(self, serializer):
        """Set creator when creating post"""
        serializer.save(creator=self.request.user)
    
    def perform_destroy(self, instance):
        """Only creator can delete"""
        from rest_framework.exceptions import PermissionDenied
        if instance.creator != self.request.user:
            raise PermissionDenied('Cannot delete topic you did not create')
        instance.delete()
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# ============================================================================
# COMMENT VIEWSETS
# ============================================================================

class CommentViewSet(viewsets.ModelViewSet):
    """Comments on posts"""
    queryset = Comment.objects.filter(is_hidden=False)
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Filter by post if provided"""
        queryset = super().get_queryset()
        post_id = self.request.query_params.get('post_id')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset
    
    def perform_create(self, serializer):
        """Set creator when creating comment"""
        serializer.save(creator=self.request.user)
    
    def perform_update(self, serializer):
        """Track edit history"""
        from rest_framework.exceptions import PermissionDenied
        instance = self.get_object()
        if instance.creator != self.request.user:
            raise PermissionDenied('Cannot edit comment you did not create')
        
        # Track edit
        if 'content' in serializer.validated_data and serializer.validated_data['content'] != instance.content:
            edit_history = instance.edit_history or []
            edit_history.append({
                'content': instance.content,
                'edited_at': timezone.now().isoformat()
            })
            serializer.save(is_edited=True, edit_history=edit_history)
        else:
            serializer.save()
    
    def perform_destroy(self, instance):
        """Only creator can delete"""
        from rest_framework.exceptions import PermissionDenied
        if instance.creator != self.request.user:
            raise PermissionDenied('Cannot delete topic you did not create')
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a comment"""
        comment = self.get_object()
        like, created = Like.objects.get_or_create(
            user=request.user,
            content_type='comment',
            comment=comment
        )
        
        if created:
            comment.likes_count += 1
            comment.save(update_fields=['likes_count'])
            return Response({'detail': 'Liked'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'Already liked'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Unlike a comment"""
        comment = self.get_object()
        try:
            like = Like.objects.get(user=request.user, content_type='comment', comment=comment)
            like.delete()
            comment.likes_count = max(0, comment.likes_count - 1)
            comment.save(update_fields=['likes_count'])
            return Response({'detail': 'Unliked'})
        except Like.DoesNotExist:
            return Response({'detail': 'Not liked'}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# REACTION VIEWSETS
# ============================================================================

class ReactionViewSet(viewsets.ModelViewSet):
    """Emoji reactions on posts/comments"""
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Set user when creating reaction"""
        serializer.save(user=self.request.user)
    
    def perform_destroy(self, instance):
        """Only creator can delete"""
        from rest_framework.exceptions import PermissionDenied
        if instance.creator != self.request.user:
            raise PermissionDenied('Cannot delete topic you did not create')
        instance.delete()


# ============================================================================
# POLL VIEWSETS
# ============================================================================

class PollViewSet(viewsets.ModelViewSet):
    """Polls on posts"""
    queryset = Poll.objects.all()
    serializer_class = PollSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """Vote on a poll"""
        poll = self.get_object()
        option_id = request.data.get('option_id')
        
        if not option_id:
            return Response({'detail': 'option_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        option = get_object_or_404(PollOption, id=option_id, poll=poll)
        
        # Check if user already voted
        existing_vote = PollVote.objects.filter(user=request.user, poll=poll).first()
        
        if existing_vote and not poll.allow_vote_change:
            return Response(
                {'detail': 'Cannot change vote on this poll'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if existing_vote:
            existing_vote.option = option
            existing_vote.save()
            return Response({'detail': 'Vote updated'})
        
        vote = PollVote.objects.create(user=request.user, poll=poll, option=option)
        serializer = PollVoteSerializer(vote)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End a poll (creator only)"""
        poll = self.get_object()
        if poll.creator.user != request.user:
            return Response(
                {'detail': 'Only creator can end poll'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not poll.can_end_manually:
            return Response(
                {'detail': 'This poll cannot be ended manually'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        poll.ended_at = timezone.now()
        poll.save(update_fields=['ended_at'])
        return Response({'detail': 'Poll ended'})


# ============================================================================
# FACT-CHECK VIEWSETS
# ============================================================================

class FactCheckNoteViewSet(viewsets.ModelViewSet):
    """Community fact-checking notes"""
    queryset = FactCheckNote.objects.filter(is_active=True)
    serializer_class = FactCheckNoteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Filter by post/comment"""
        queryset = super().get_queryset()
        post_id = self.request.query_params.get('post_id')
        comment_id = self.request.query_params.get('comment_id')
        
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        if comment_id:
            queryset = queryset.filter(comment_id=comment_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Check tier before creating"""
        from rest_framework.exceptions import PermissionDenied
        user_tier = self.request.user.profile.reputation_tier.tier_number   # type: ignore[attr-defined]
        if user_tier < 3:  # Only Tier 3+ can create
            raise PermissionDenied(f'Need Tier 3+ to add fact-check notes (you are Tier {user_tier})')
        serializer.save(creator=self.request.user)
    
    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """Vote on note usefulness"""
        note = self.get_object()
        vote_type = request.data.get('vote_type')  # 'helpful' or 'unhelpful'
        
        if vote_type not in ['helpful', 'unhelpful']:
            return Response({'detail': 'Invalid vote_type'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get vote weight based on user tier
        user_tier = request.user.profile.reputation_tier
        vote_weight = float(user_tier.reputation_multiplier)
        
        vote, created = FactCheckVote.objects.get_or_create(
            user=request.user,
            note=note,
            defaults={'vote_type': vote_type, 'vote_weight': vote_weight}
        )
        
        if not created:
            vote.vote_type = vote_type
            vote.vote_weight = vote_weight
            vote.save()
        
        serializer = FactCheckVoteSerializer(vote)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


# ============================================================================
# FLAG VIEWSETS
# ============================================================================

class FlagViewSet(viewsets.ModelViewSet):
    """Report content for moderation"""
    queryset = Flag.objects.all()
    serializer_class = FlagSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_queryset(self) -> "QuerySet[Flag]":     # type: ignore[override]
        """Users can only see their own flags unless they're moderators"""
        from django.db.models import QuerySet
        user = self.request.user
        if user.is_staff:
            return Flag.objects.all()
        return Flag.objects.filter(Q(identified_flagger=user) | Q(flagger=user))

    def perform_create(self, serializer):
        """Create a flag, optionally identifying the flagger"""
        is_anonymous = serializer.validated_data.get('is_anonymous', True)
        if is_anonymous:
            serializer.save(flagger=None)
        else:
            serializer.save(flagger=self.request.user, identified_flagger=self.request.user)
