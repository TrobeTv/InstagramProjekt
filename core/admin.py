from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'dark_mode')
    list_filter = ('dark_mode',)
    search_fields = ('user__username',)
