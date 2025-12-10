from rest_framework import serializers
from django.contrib.auth.models import User
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

# ============================================================================
# USER & AUTHENTICATION SERIALIZERS
# ============================================================================

class ReputationTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReputationTier
        fields = ['id', 'tier_number', 'min_points', 'reputation_multiplier', 'description']


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile with reputation info"""
    reputation_tier = ReputationTierSerializer(read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user_id', 'username', 'email',
            'bio', 'profile_picture', 'country', 'location', 'display_name',
            'reputation_points', 'reputation_tier',
            'posts_count', 'comments_count', 'topics_created_count',
            'likes_given_count', 'likes_received_count',
            'followers_count', 'following_count',
            'account_created', 'last_activity'
        ]

class UserSerializer(serializers.ModelSerializer):
    """Basic user info"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """For user registration"""
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)  # Auto-create profile
        return user


class UserFollowingSerializer(serializers.ModelSerializer):
    follower = UserProfileSerializer(read_only=True)
    following = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = UserFollowing
        fields = ['id', 'follower', 'following', 'created_at']


# ============================================================================
# TOPIC SERIALIZERS
# ============================================================================

class TopicSerializer(serializers.ModelSerializer):
    creator = UserProfileSerializer(read_only=True)
    moderators = UserProfileSerializer(many=True, read_only=True)
    
    class Meta:
        model = Topic
        fields = [
            'id', 'creator', 'name', 'description', 'icon',
            'allow_images', 'allow_videos', 'allow_gifs', 'allow_links',
            'allow_posts_by_others',
            'moderators',
            'posts_count', 'followers_count', 'reputation_points_earned',
            'created_at', 'last_updated'
        ]
        read_only_fields = [
            'posts_count', 'followers_count', 'reputation_points_earned',
            'created_at', 'last_updated'
        ]


class TopicFollowingSerializer(serializers.ModelSerializer):
    topic = TopicSerializer(read_only=True)
    
    class Meta:
        model = TopicFollowing
        fields = ['id', 'topic', 'followed_at']


# ============================================================================
# POST & COMMENT SERIALIZERS
# ============================================================================

class PostSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField()
    topic = TopicSerializer(read_only=True)
    topic_id = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        source='topic',
        write_only=True
    )
    is_liked = serializers.SerializerMethodField()
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    
    def get_creator(self, obj):
        try:
            profile = obj.creator.profile
            return UserProfileSerializer(profile).data
        except:
            return None
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        print(f"Request in context: {request}")
        print(f"User authenticated: {request.user.is_authenticated if request else 'No request'}")
        if request and request.user.is_authenticated:
            return Like.objects.filter(
                user=request.user,
                post=obj
            ).exists()
        return False
    
    class Meta:
        model = Post
        fields = [
            'id', 'creator', 'topic', 'topic_id', 'title', 'content',
            'images', 'videos', 'gifs', 'links',
            'likes_count', 'comments_count',
            'is_liked',  # Add this
            'reputation_gained',
            'is_hidden',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'likes_count', 'comments_count', 'reputation_gained',
            'created_at', 'updated_at'
        ]


class CommentSerializer(serializers.ModelSerializer):
    creator = UserProfileSerializer(read_only=True)
    post = PostSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'creator', 'post', 'parent_comment',
            'content',
            'images', 'videos', 'gifs', 'links',
            'likes_count', 'reactions_count',
            'reputation_gained',
            'is_hidden',
            'is_edited', 'edit_history',
            'replies',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'likes_count', 'reactions_count', 'reputation_gained',
            'created_at', 'updated_at'
        ]
    
    def get_replies(self, obj):
        """Get nested replies"""
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True).data


# ============================================================================
# LIKE & REACTION SERIALIZERS
# ============================================================================

class LikeSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Like
        fields = [
            'id', 'user', 'content_type', 'post', 'comment',
            'reputation_value', 'created_at'
        ]
        read_only_fields = ['reputation_value', 'created_at']


class ReactionSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Reaction
        fields = [
            'id', 'user', 'content_type', 'post', 'comment',
            'emoji', 'created_at'
        ]
        read_only_fields = ['created_at']


# ============================================================================
# POLL SERIALIZERS
# ============================================================================

class PollOptionSerializer(serializers.ModelSerializer):
    vote_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PollOption
        fields = ['id', 'text', 'order', 'vote_count']
    
    def get_vote_count(self, obj):
        return obj.votes.count()


class PollSerializer(serializers.ModelSerializer):
    creator = UserProfileSerializer(read_only=True)
    options = PollOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Poll
        fields = [
            'id', 'creator', 'question',
            'allow_vote_change', 'show_results_before_voting',
            'duration_hours', 'can_end_manually',
            'options',
            'is_active',
            'created_at', 'ended_at'
        ]
        read_only_fields = [
            'is_active', 'created_at', 'ended_at'
        ]


class PollVoteSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = PollVote
        fields = ['id', 'user', 'poll', 'option', 'created_at']
        read_only_fields = ['created_at']


# ============================================================================
# FACT-CHECK & MODERATION SERIALIZERS
# ============================================================================

class FactCheckNoteSerializer(serializers.ModelSerializer):
    creator = UserProfileSerializer(read_only=True)
    helpful_ratio = serializers.SerializerMethodField()
    
    class Meta:
        model = FactCheckNote
        fields = [
            'id', 'creator', 'content_type', 'post', 'comment',
            'title', 'explanation', 'sources',
            'helpful_count', 'unhelpful_count', 'helpful_ratio',
            'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'helpful_count', 'unhelpful_count',
            'created_at', 'updated_at'
        ]
    
    def get_helpful_ratio(self, obj):
        """Calculate helpful ratio"""
        total = obj.helpful_count + obj.unhelpful_count
        if total == 0:
            return 0
        return round((obj.helpful_count / total) * 100, 2)


class FactCheckVoteSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = FactCheckVote
        fields = [
            'id', 'user', 'note', 'vote_type',
            'vote_weight', 'created_at'
        ]
        read_only_fields = ['created_at']


class FlagSerializer(serializers.ModelSerializer):
    identified_flagger = UserProfileSerializer(read_only=True)
    reviewed_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Flag
        fields = [
            'id', 'identified_flagger',
            'content_type', 'post', 'comment', 'flagged_user',
            'reason', 'description', 'is_anonymous',
            'status', 'reviewed_by', 'review_notes',
            'created_at', 'reviewed_at'
        ]
        read_only_fields = [
            'status', 'reviewed_by', 'review_notes',
            'created_at', 'reviewed_at'
        ]


class ModerationSerializer(serializers.ModelSerializer):
    moderator = UserProfileSerializer(read_only=True)
    target_user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Moderation
        fields = [
            'id', 'moderator', 'target_user', 'action_type',
            'reason', 'topic', 'ban_duration_days', 'ban_until',
            'created_at'
        ]
        read_only_fields = ['created_at']


class BanAppealSerializer(serializers.ModelSerializer):
    banned_user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = BanAppeal
        fields = [
            'id', 'banned_user', 'moderation', 'reason',
            'status', 'response',
            'created_at', 'resolved_at'
        ]
        read_only_fields = ['created_at', 'resolved_at']
        