from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

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
    # předpokládám, že lajky máš jako M2M:
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_posts', blank=True)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']