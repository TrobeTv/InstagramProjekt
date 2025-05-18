from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.api_index, name='api-index'),
    path('posts/', api_views.api_posts_list, name='api-posts-list'),
    path('posts/<int:post_id>/', api_views.api_post_detail, name='api-post-detail'),
]
