from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

# ============================================================================
# USER PROFILE & REPUTATION SYSTEM
# ============================================================================

class ReputationTier(models.Model):
    """Defines reputation tiers and their thresholds"""
    tier_number = models.IntegerField(unique=True, validators=[MinValueValidator(0)])
    min_points = models.IntegerField(validators=[MinValueValidator(0)])
    reputation_multiplier = models.FloatField(default=0)  # Points this tier's likes are worth
    description = models.CharField(max_length=100)
    
    class Meta:
        ordering = ['tier_number']
    
    def __str__(self):
        return f"Tier {self.tier_number} ({self.description})"


def get_default_reputation_tier_pk():
# Tier 0 as default, for example
    tier, _ = ReputationTier.objects.get_or_create(
        tier_number=0,
        defaults={
            "min_points": 0,
            "reputation_multiplier": 0,
            "description": "Novo utilizador",
        },
    )
    return tier.pk

class UserProfile(models.Model):
    """Extended user profile with community features"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal info
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True, 
                                      default="https://via.placeholder.com/150?text=Default")
    country = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    display_name = models.CharField(max_length=150, blank=True, null=True)
            
    # Reputation system
    reputation_points = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reputation_tier = models.ForeignKey(
        ReputationTier,
        on_delete=models.SET_NULL,
        null=True,
        default=get_default_reputation_tier_pk,
    )

    
    # Activity counts
    posts_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    comments_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    topics_created_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    likes_given_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    likes_received_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Social
    followers_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    following_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Timestamps
    account_created = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-reputation_points']
    
    def __str__(self):
        return f"{self.user.username}'s Profile (Tier {self.reputation_tier.tier_number if self.reputation_tier else 0})"

    def update_reputation_tier(self):
        """Update user's tier based on reputation points"""
        tier = ReputationTier.objects.filter(
            min_points__lte=self.reputation_points
        ).order_by('-tier_number').first()
        if tier:
            self.reputation_tier = tier
            self.save(update_fields=['reputation_tier'])


class UserFollowing(models.Model):
    """Track user-to-user following relationships"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_users')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers_users')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


# ============================================================================
# TOPICS & MODERATION
# ============================================================================

class Topic(models.Model):
    """Discussion topics created by users"""
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics_created')
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.URLField(blank=True, null=True)  # Topic icon/image
    
    # Permissions & settings
    allow_images = models.BooleanField(default=True)
    allow_videos = models.BooleanField(default=True)
    allow_gifs = models.BooleanField(default=True)
    allow_links = models.BooleanField(default=True)
    allow_posts_by_others = models.BooleanField(default=True)  # Non-creator can post
    
    # Moderation
    moderators = models.ManyToManyField(User, related_name='moderated_topics', blank=True)
    
    # Stats & reputation
    posts_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    followers_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reputation_points_earned = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-followers_count', '-created_at']
    
    def __str__(self):
        return self.name


class TopicFollowing(models.Model):
    """Track user subscriptions to topics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_topics')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='followers')
    followed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'topic')
    
    def __str__(self):
        return f"{self.user.username} follows {self.topic.name}"


class Moderation(models.Model):
    """Track moderation actions"""
    MODERATION_TYPES = [
        ('warning', 'Warning'),
        ('hidden', 'Post Hidden'),
        ('deleted', 'Post Deleted'),
        ('temp_ban', 'Temporary Ban'),
        ('perm_ban', 'Permanent Ban'),
    ]
    
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                 related_name='moderation_actions')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, 
                                   related_name='moderation_received')
    action_type = models.CharField(max_length=20, choices=MODERATION_TYPES)
    reason = models.TextField()
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    
    # For bans
    ban_duration_days = models.IntegerField(null=True, blank=True)  # None = permanent
    ban_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.action_type} on {self.target_user.username}"


class BanAppeal(models.Model):
    """Allow banned users to appeal their ban"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    banned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ban_appeals')
    moderation = models.ForeignKey(Moderation, on_delete=models.CASCADE, related_name='appeals')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Appeal from {self.banned_user.username} - {self.status}"


# ============================================================================
# POSTS & COMMENTS
# ============================================================================

class Post(models.Model):
    """Posts made under a topic"""
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts')
    
    title = models.CharField(max_length=300)
    content = models.TextField()
    
    # Media & links
    images = models.JSONField(default=list, blank=True)  # List of image URLs
    videos = models.JSONField(default=list, blank=True)  # List of video URLs
    gifs = models.JSONField(default=list, blank=True)    # List of GIF URLs
    links = models.JSONField(default=list, blank=True)   # List of external links
    
    # Stats
    likes_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    comments_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Reputation
    reputation_gained = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Moderation
    is_hidden = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.creator.username}"


class Comment(models.Model):
    """Comments on posts"""
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, 
                                       related_name='replies', null=True, blank=True)
    
    content = models.TextField()
    
    # Media & links
    images = models.JSONField(default=list, blank=True)
    videos = models.JSONField(default=list, blank=True)
    gifs = models.JSONField(default=list, blank=True)
    links = models.JSONField(default=list, blank=True)
    
    # Stats
    likes_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reactions_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Reputation
    reputation_gained = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Moderation
    is_hidden = models.BooleanField(default=False)
    
    # Edit tracking
    is_edited = models.BooleanField(default=False)
    edit_history = models.JSONField(default=list, blank=True)  # [{content, edited_at}, ...]
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.creator.username} on post {self.post.pk}"

# ============================================================================
# LIKES & REACTIONS
# ============================================================================

class Like(models.Model):
    """Likes on posts and comments - affects reputation"""
    CONTENT_TYPES = [
        ('post', 'Post'),
        ('comment', 'Comment'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_given')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes', 
                            null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes', 
                               null=True, blank=True)
    
    # Reputation impact
    reputation_value = models.IntegerField(default=0)  # Points awarded based on liker's tier
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'content_type', 'post', 'comment')
    
    def __str__(self):
        content = self.post if self.post else self.comment
        return f"{self.user.username} liked {content}"


class Reaction(models.Model):
    """Emoji reactions on posts and comments - doesn't affect reputation"""
    CONTENT_TYPES = [
        ('post', 'Post'),
        ('comment', 'Comment'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions_given')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions', 
                            null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions', 
                               null=True, blank=True)
    
    emoji = models.CharField(max_length=10)  # Emoji character
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'content_type', 'post', 'comment', 'emoji')
    
    def __str__(self):
        content = self.post if self.post else self.comment
        return f"{self.user.username} reacted {self.emoji} to {content}"


# ============================================================================
# POLLS & VOTING
# ============================================================================

class Poll(models.Model):
    """Polls attached to posts"""
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='poll')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='polls_created')
    
    question = models.CharField(max_length=300)
    
    # Poll settings
    allow_vote_change = models.BooleanField(default=False)
    show_results_before_voting = models.BooleanField(default=False)
    duration_hours = models.IntegerField(default=24, validators=[MinValueValidator(1)])
    can_end_manually = models.BooleanField(default=True)
    
    # Duration management
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    @property
    def is_active(self):
        if self.ended_at:
            return False
        expiry = self.created_at + timezone.timedelta(hours=self.duration_hours)
        return timezone.now() < expiry
    
    def __str__(self):
        return self.question


class PollOption(models.Model):
    """Options in a poll"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=200)
    order = models.IntegerField()
    
    class Meta:
        unique_together = ('poll', 'order')
        ordering = ['order']
    
    def __str__(self):
        return self.text


class PollVote(models.Model):
    """User votes in polls"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes')
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'poll')
    
    def __str__(self):
        return f"{self.user.username} voted for {self.option.text}"


# ============================================================================
# FACT-CHECKING & COMMUNITY NOTES
# ============================================================================

class FactCheckNote(models.Model):
    """Community fact-checking notes (Twitter-style)"""
    CONTENT_TYPES = [
        ('post', 'Post'),
        ('comment', 'Comment'),
    ]
    
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fact_check_notes')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='fact_check_notes', 
                            null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='fact_check_notes', 
                               null=True, blank=True)
    
    title = models.CharField(max_length=200)
    explanation = models.TextField()
    sources = models.JSONField(default=list, blank=True)  # List of source URLs
    
    # Community voting on note usefulness
    helpful_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    unhelpful_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Moderation
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-helpful_count', '-created_at']
    
    def __str__(self):
        content = self.post if self.post else self.comment
        return f"Note on {content} by {self.creator.username}"


class FactCheckVote(models.Model):
    """Users voting on fact-check notes"""
    VOTE_CHOICES = [
        ('helpful', 'Helpful'),
        ('unhelpful', 'Unhelpful'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fact_check_votes')
    note = models.ForeignKey(FactCheckNote, on_delete=models.CASCADE, related_name='votes')
    vote_type = models.CharField(max_length=20, choices=VOTE_CHOICES)
    
    # Vote weight based on user tier
    vote_weight = models.FloatField(default=1.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'note')
    
    def __str__(self):
        return f"{self.user.username} voted {self.vote_type} on note {self.note.pk}"


class Flag(models.Model):
    """User reports for moderation"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    FLAG_REASONS = [
        ('fake_news', 'Fake News'),
        ('hate_speech', 'Hate Speech'),
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('misinformation', 'Misinformation'),
        ('other', 'Other'),
    ]
    
    CONTENT_TYPES = [
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('user', 'User'),
    ]
    
    flagger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flags_created',
                               null=True, blank=True)  # Anonymous if null
    identified_flagger = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='identified_flags')  # If flagger chose to identify
    
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='flags', 
                            null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='flags', 
                               null=True, blank=True)
    flagged_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_flags',
                                    null=True, blank=True)
    
    reason = models.CharField(max_length=50, choices=FLAG_REASONS)
    description = models.TextField()
    is_anonymous = models.BooleanField(default=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='flags_reviewed')
    review_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        content = self.post or self.comment or self.flagged_user
        return f"Flag on {content} - {self.reason}"
