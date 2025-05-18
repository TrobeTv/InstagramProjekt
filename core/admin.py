from django.contrib import admin
from .models import Profile, Post, Comment, Notification

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'dark_mode')
    list_filter = ('dark_mode',)
    search_fields = ('user__username',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'caption', 'created_at')
    search_fields = ('caption', 'author__user__username')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'text', 'created_at')
    search_fields = ('text', 'user__username', 'post__caption')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'verb', 'target_display', 'action_object_display', 'read', 'timestamp')
    list_filter = ('read', 'timestamp', 'verb', 'content_type_target')
    search_fields = ('recipient__username', 'actor__username', 'verb')
    readonly_fields = ('timestamp',)

    def target_display(self, obj):
        return obj.target
    target_display.short_description = 'Target Object'

    def action_object_display(self, obj):
        return obj.action_object
    action_object_display.short_description = 'Action Object'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'recipient', 'actor', 'content_type_target', 'content_type_action_object'
        )