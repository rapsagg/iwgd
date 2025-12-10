from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Like, FactCheckVote, UserProfile, Post, Comment, Topic, ReputationTier

# ============================================================================
# LIKE SIGNALS - Auto-update reputation
# ============================================================================

@receiver(post_save, sender=Like)
def update_reputation_on_like(sender, instance, created, **kwargs):
    """When a like is created, update author's reputation"""
    if not created:
        return  # Only on creation, not updates
    
    # Get the liker's tier multiplier
    liker_profile = instance.user.profile
    liker_tier = liker_profile.reputation_tier
    reputation_value = int(liker_tier.reputation_multiplier)
    
    # Posts are worth 1.5x comments
    if instance.content_type == 'post':
        reputation_value = int(reputation_value * 1.5)
    
    instance.reputation_value = reputation_value
    instance.save(update_fields=['reputation_value'])
    
    # Update the author's reputation
    if instance.post:
        author = instance.post.creator
        post = instance.post
        post.reputation_gained += reputation_value
        post.save(update_fields=['reputation_gained'])
    elif instance.comment:
        author = instance.comment.creator
        comment = instance.comment
        comment.reputation_gained += reputation_value
        comment.save(update_fields=['reputation_gained'])
    else:
        return
    
    # Update author profile
    author_profile = author.profile
    author_profile.reputation_points += reputation_value
    author_profile.likes_received_count += 1
    author_profile.save(update_fields=['reputation_points', 'likes_received_count'])
    
    # Update liker's count
    liker_profile.likes_given_count += 1
    liker_profile.save(update_fields=['likes_given_count'])
    
    # Check if author crossed tier threshold
    author_profile.update_reputation_tier()


@receiver(post_delete, sender=Like)
def remove_reputation_on_like_delete(sender, instance, **kwargs):
    """When a like is deleted, remove reputation"""
    reputation_value = instance.reputation_value
    
    # Update the content's reputation
    if instance.post:
        author = instance.post.creator
        post = instance.post
        post.reputation_gained = max(0, post.reputation_gained - reputation_value)
        post.save(update_fields=['reputation_gained'])
    elif instance.comment:
        author = instance.comment.creator
        comment = instance.comment
        comment.reputation_gained = max(0, comment.reputation_gained - reputation_value)
        comment.save(update_fields=['reputation_gained'])
    else:
        return
    
    # Update author profile
    author_profile = author.profile
    author_profile.reputation_points = max(0, author_profile.reputation_points - reputation_value)
    author_profile.likes_received_count = max(0, author_profile.likes_received_count - 1)
    author_profile.save(update_fields=['reputation_points', 'likes_received_count'])
    
    # Update liker's count
    liker_profile = instance.user.profile
    liker_profile.likes_given_count = max(0, liker_profile.likes_given_count - 1)
    liker_profile.save(update_fields=['likes_given_count'])
    
    # Recheck tier
    author_profile.update_reputation_tier()


# ============================================================================
# POST/COMMENT SIGNALS - Track creation counts
# ============================================================================

@receiver(post_save, sender=Post)
def update_topic_on_post_create(sender, instance, created, **kwargs):
    """When a post is created, update topic and creator stats"""
    if not created:
        return
    
    # Update topic
    topic = instance.topic
    topic.posts_count += 1
    topic.last_updated = instance.created_at
    topic.save(update_fields=['posts_count', 'last_updated'])
    
    # Update creator profile
    creator_profile = instance.creator.profile
    creator_profile.posts_count += 1
    creator_profile.save(update_fields=['posts_count'])


@receiver(post_delete, sender=Post)
def update_topic_on_post_delete(sender, instance, **kwargs):
    """When a post is deleted, update topic and creator stats"""
    topic = instance.topic
    topic.posts_count = max(0, topic.posts_count - 1)
    topic.save(update_fields=['posts_count'])
    
    creator_profile = instance.creator.profile
    creator_profile.posts_count = max(0, creator_profile.posts_count - 1)
    creator_profile.save(update_fields=['posts_count'])


@receiver(post_save, sender=Comment)
def update_post_on_comment_create(sender, instance, created, **kwargs):
    """When a comment is created, update post and creator stats"""
    if not created:
        return
    
    # Update post
    post = instance.post
    post.comments_count += 1
    post.save(update_fields=['comments_count'])
    
    # Update creator profile
    creator_profile = instance.creator.profile
    creator_profile.comments_count += 1
    creator_profile.save(update_fields=['comments_count'])


@receiver(post_delete, sender=Comment)
def update_post_on_comment_delete(sender, instance, **kwargs):
    """When a comment is deleted, update post and creator stats"""
    post = instance.post
    post.comments_count = max(0, post.comments_count - 1)
    post.save(update_fields=['comments_count'])
    
    creator_profile = instance.creator.profile
    creator_profile.comments_count = max(0, creator_profile.comments_count - 1)
    creator_profile.save(update_fields=['comments_count'])


@receiver(post_save, sender=Topic)
def update_creator_on_topic_create(sender, instance, created, **kwargs):
    """When a topic is created, update creator stats"""
    if not created:
        return
    
    creator_profile = instance.creator.profile
    creator_profile.topics_created_count += 1
    creator_profile.save(update_fields=['topics_created_count'])


@receiver(post_delete, sender=Topic)
def update_creator_on_topic_delete(sender, instance, **kwargs):
    """When a topic is deleted, update creator stats"""
    creator_profile = instance.creator.profile
    creator_profile.topics_created_count = max(0, creator_profile.topics_created_count - 1)
    creator_profile.save(update_fields=['topics_created_count'])


# ============================================================================
# TOPIC REPUTATION - Creator gains rep from topic popularity
# ============================================================================

@receiver(post_save, sender=Topic)
def update_topic_reputation_on_followers(sender, instance, **kwargs):
    """Track when topics gain followers (for future notifications)"""
    # This is a placeholder for topic-based reputation
    # Topics gain reputation from: post count, follower count
    # This can be calculated periodically or on demand
    pass


# ============================================================================
# FACT-CHECK VOTE SIGNALS - Track helpful votes
# ============================================================================

@receiver(post_save, sender=FactCheckVote)
def update_note_usefulness(sender, instance, created, **kwargs):
    """When a fact-check vote is created, update note's helpful/unhelpful counts"""
    if not created:
        return
    
    note = instance.note
    if instance.vote_type == 'helpful':
        note.helpful_count += int(instance.vote_weight)
    else:
        note.unhelpful_count += int(instance.vote_weight)
    
    note.save(update_fields=['helpful_count', 'unhelpful_count'])


@receiver(post_delete, sender=FactCheckVote)
def remove_note_vote(sender, instance, **kwargs):
    """When a fact-check vote is deleted, update note counts"""
    note = instance.note
    if instance.vote_type == 'helpful':
        note.helpful_count = max(0, note.helpful_count - int(instance.vote_weight))
    else:
        note.unhelpful_count = max(0, note.unhelpful_count - int(instance.vote_weight))
    
    note.save(update_fields=['helpful_count', 'unhelpful_count'])


# ============================================================================
# REACTION SIGNALS - Track reaction counts
# ============================================================================

from .models import Reaction

@receiver(post_save, sender=Reaction)
def update_reaction_count_on_create(sender, instance, created, **kwargs):
    """When a reaction is created, update the content's reaction count"""
    if not created:
        return
    
    if instance.post:
        post = instance.post
        post.reactions_count = post.reactions.count()
        post.save(update_fields=['reactions_count'])
    elif instance.comment:
        comment = instance.comment
        comment.reactions_count = comment.reactions.count()
        comment.save(update_fields=['reactions_count'])


@receiver(post_delete, sender=Reaction)
def update_reaction_count_on_delete(sender, instance, **kwargs):
    """When a reaction is deleted, update the content's reaction count"""
    if instance.post:
        post = instance.post
        post.reactions_count = post.reactions.count()
        post.save(update_fields=['reactions_count'])
    elif instance.comment:
        comment = instance.comment
        comment.reactions_count = comment.reactions.count()
        comment.save(update_fields=['reactions_count'])


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        tier0 = ReputationTier.objects.filter(tier_number=0).first()
        UserProfile.objects.create(user=instance, reputation_tier=tier0)
        