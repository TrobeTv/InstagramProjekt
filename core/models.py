from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Profile(models.Model):
    user     = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(
        upload_to='avatars/',
        default='avatars/default.jpg',
        blank=True
    )
    bio      = models.TextField(blank=True)
    dark_mode = models.BooleanField(default=False)

    following = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='followers',
        blank=True,
        help_text="Kdo tento profil sleduje (větve reverse vztahu)."
    )

    def __str__(self):
        return self.user.username

class Post(models.Model):
    author = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='posts')
    image = models.ImageField(upload_to='posts/')
    caption = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_posts', blank=True)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']



class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        usernames = ", ".join([user.username for user in self.participants.all()])
        return f"Conversation between {usernames}"

    class Meta:
        ordering = ['-updated_at']


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} in conversation {self.conversation.id} at {self.created_at:%Y-%m-%d %H:%M}"

    class Meta:
        ordering = ['created_at']


class SavedPost(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_posts_entries')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saved_by_users_entries')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} saved '{self.post.caption[:20]}...'"



class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='triggered_notifications')
    verb = models.CharField(max_length=255)
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    content_type_target = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True, related_name='notification_target')
    object_id_target = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('content_type_target', 'object_id_target')
    content_type_action_object = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True, related_name='notification_action_object')
    object_id_action_object = models.PositiveIntegerField(null=True, blank=True)
    action_object = GenericForeignKey('content_type_action_object', 'object_id_action_object')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        if self.target:
            return f'{self.actor} {self.verb} your {self.target._meta.model_name if self.target else "something"}'
        return f'{self.actor} {self.verb}'

    def mark_as_read(self):
        if not self.read:
            self.read = True
            self.save()

    def mark_as_unread(self):
        if self.read:
            self.read = False
            self.save()
