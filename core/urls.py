from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, api_views
from .forms import LoginForm
from .views import feed_view, profile_view, settings_view, create_post_view, add_comment, toggle_like, logout_view
from django.contrib.auth.views import LogoutView
from core.api import api

urlpatterns = [
path('api/', api.urls),
    path('', views.feed_view, name='feed'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html', authentication_form=LoginForm), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('settings/', views.settings_view, name='settings'),
    path('profile/<str:username>/', profile_view, name='profile'),
    path('post/new/', create_post_view, name='create_post'),
    path('post/<int:post_id>/comment/', add_comment, name='add_comment'),
    path('post/<int:post_id>/like/', toggle_like, name='toggle_like'),
    path('api/logout/', views.logout_api, name='api_logout'),
    path('api/profile/update/', views.profile_update_api, name='api_profile_update'),
    path('api/profile/toggle-dark-mode/', views.toggle_dark_mode_api, name='api_toggle_dark_mode'),
    path('api/profile/<str:username>/follow-toggle/', views.toggle_follow_api, name='api_toggle_follow'),
    path('profile/<str:username>/follow-toggle/', api_views.api_follow_toggle, name='api_follow_toggle'),
    path('post/<int:pk>/', views.post_detail_view, name='post_detail'),
    path('explore/', views.explore_view, name='explore'),
    path('explore/<int:post_pk>/', views.explore_view, name='explore_post'),
    path('explore/search/', views.explore_search_view, name='explore_search'),
    path('post/<int:pk>/delete/', views.delete_post_view, name='delete_post'),
path('messages/', views.messages_list_view, name='messages_list'),
    path('messages/<str:username>/', views.conversation_detail_view, name='conversation_detail'),
path('post/<int:post_id>/toggle-save/', views.toggle_save_post_view, name='toggle_save_post'),

]
