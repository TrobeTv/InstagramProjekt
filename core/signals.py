from django.contrib.auth.models import User
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Post, Comment, Profile, Notification

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()

@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        comment = instance
        post_owner = comment.post.author.user
        commenter = comment.user
        if post_owner != commenter:
            Notification.objects.create(
                recipient=post_owner,
                actor=commenter,
                verb='okomentoval(a) váš příspěvek',
                target=comment.post,
                action_object=comment
            )

@receiver(m2m_changed, sender=Post.likes.through)
def create_like_notification(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        post_instance = instance
        post_owner = post_instance.author.user
        for user_pk in pk_set:
            liker = User.objects.get(pk=user_pk)
            if post_owner != liker:
                Notification.objects.create(
                    recipient=post_owner,
                    actor=liker,
                    verb='se líbí váš příspěvek',
                    target=post_instance
                )

@receiver(m2m_changed, sender=Profile.following.through)
def create_follow_notification(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        actor_profile = instance
        for followed_profile_pk in pk_set:
            if actor_profile.pk == followed_profile_pk:
                continue
            recipient_profile = Profile.objects.get(pk=followed_profile_pk)
            Notification.objects.create(
                recipient=recipient_profile.user,
                actor=actor_profile.user,
                verb='vás začal(a) sledovat',
                target=actor_profile
            )