from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Exists, OuterRef, Q
from django.http import JsonResponse, Http404, HttpResponseForbidden
from django.contrib.auth import logout, login
from django.views.decorators.http import require_POST

from .forms import PostForm, CommentForm, ProfileForm, RegistrationForm, MessageForm
from .models import Post, Profile, Comment, Conversation, Message, SavedPost, Notification

@login_required
def feed_view(request):
    current_user_profile = request.user.profile
    profiles_i_follow = current_user_profile.following.all()
    saved_subquery = SavedPost.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk
    )
    liked_subquery = Post.likes.through.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk
    )
    if not profiles_i_follow.exists():
        posts = Post.objects.none()
    else:
        posts_query = Post.objects.filter(author__in=profiles_i_follow)
        posts = posts_query.annotate(
            likes_count=Count('likes'),
            comments_count=Count('comments'),
            is_liked=Exists(liked_subquery),
            is_saved=Exists(saved_subquery)
        ).select_related('author__user').prefetch_related('comments__user').order_by('-created_at')

    comment_form = CommentForm()
    return render(request, 'feed.html', {
        'posts': posts,
        'comment_form': comment_form,
        'feed_type': 'following',
    })


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('feed')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def settings_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('settings')
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, 'settings.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('feed')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile = profile_user.profile
    posts = Post.objects.filter(author=profile).order_by('-created_at')
    followers_profiles = profile.followers.all().select_related('user')
    following_profiles = profile.following.all().select_related('user')
    followers_count = followers_profiles.count()
    following_count = following_profiles.count()
    post_count = posts.count()
    is_followed_by_request_user = False
    if request.user.is_authenticated and request.user != profile_user:
        is_followed_by_request_user = request.user.profile.following.filter(pk=profile.pk).exists()

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'posts': posts,
        'post_count': post_count,
        'followers_count': followers_count,
        'following_count': following_count,
        'followers_list': followers_profiles,
        'following_list': following_profiles,
        'is_followed_by_request_user': is_followed_by_request_user,
    }
    return render(request, 'profile.html', context)


@login_required
def settings_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('settings')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'settings.html', {'form': form})

@login_required
def create_post_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user.profile
            post.save()
            return redirect('feed')
    else:
        form = PostForm()

    return render(request, 'create_post.html', {'form': form})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.save()
    return redirect('feed')

@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    if user in post.likes.all():
        post.likes.remove(user)
        liked = False
    else:
        post.likes.add(user)
        liked = True
    return JsonResponse({
        'likes_count': post.likes.count(),
        'liked': liked,
    })

@login_required
def logout_api(request):
    logout(request)
    return JsonResponse({'ok': True})

@login_required
def settings_view(request):
    return render(request, 'settings.html', {
      'profile': request.user.profile
    })

@login_required
def profile_update_api(request):
    form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
    if form.is_valid():
        form.save()
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'errors': form.errors}, status=400)

@login_required
def toggle_dark_mode_api(request):
    p = request.user.profile
    p.dark_mode = not p.dark_mode
    p.save()
    return JsonResponse({'dark_mode': p.dark_mode})

def toggle_follow_api(request, username):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        target_profile = Profile.objects.get(user__username=username)
    except Profile.DoesNotExist:
        raise Http404
    me = request.user.profile
    if target_profile == me:
        return JsonResponse({'error': "Can't follow yourself"}, status=400)
    if me.following.filter(pk=target_profile.pk).exists():
        me.following.remove(target_profile)
        action = 'unfollowed'
    else:
        me.following.add(target_profile)
        action = 'followed'
    data = {
        'action': action,
        'followers_count': target_profile.followers.count(),
        'following_count': me.following.count(),
    }
    return JsonResponse(data)

def logout_view(request):
    logout(request)
    return render(request, 'logged_out.html')

@login_required
@login_required
def post_detail_view(request, pk):
    saved_subquery = SavedPost.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk
    )
    liked_subquery = Post.likes.through.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk
    )

    post = get_object_or_404(
        Post.objects.annotate(
            is_saved=Exists(saved_subquery.filter(post_id=OuterRef('pk'))),
            likes_count_annotated=Count('likes'),
            is_liked_annotated=Exists(liked_subquery.filter(post_id=OuterRef('pk')))
        ).select_related('author__user'),
        pk=pk
    )
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()
    context = {
        'post': post,
        'comments': post.comments.select_related('user').all(),
        'is_liked': post.is_liked_annotated,
        'likes_count': post.likes_count_annotated,
        'is_saved': post.is_saved,
        'comment_form': form,
    }
    return render(request, 'post_detail.html', context)

def explore_view(request, post_pk=None):
    saved_subquery = SavedPost.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk if request.user.is_authenticated else None
    )
    liked_subquery = Post.likes.through.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk if request.user.is_authenticated else None
    )
    posts_query = Post.objects.all().annotate(
        is_saved=Exists(saved_subquery),
        is_liked=Exists(liked_subquery),
        likes_count=Count('likes')
    ).order_by('-created_at')

    selected_post_obj = None
    comment_form = None

    if post_pk is not None:
        selected_post_obj = get_object_or_404(
            Post.objects.annotate(
                is_saved=Exists(saved_subquery.filter(post_id=OuterRef('pk'))),
                is_liked=Exists(liked_subquery.filter(post_id=OuterRef('pk'))),
                likes_count=Count('likes')
            ).select_related('author__user').prefetch_related('comments__user'),
            pk=post_pk
        )
        if request.user.is_authenticated:
            comment_form = CommentForm()

    return render(request, 'explore.html', {
        'posts': posts_query,
        'selected_post': selected_post_obj,
        'comment_form': comment_form,
    })

def explore_search_view(request):
    q = request.GET.get('q', '').strip()
    users = []
    if q:
        users = User.objects.filter(username__icontains=q)[:50]
    return render(request, 'explore_search.html', {
        'query': q,
        'users': users,
    })

@login_required
def delete_post_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author.user != request.user:
        return HttpResponseForbidden()
    if request.method == 'POST':
        post.delete()
        return redirect('profile', username=request.user.username)
    return render(request, 'post_confirm_delete.html', {
        'post': post,
    })

@login_required
def messages_list_view(request):
    user_profile = request.user.profile
    following_profiles = user_profile.following.all()
    users_i_follow = User.objects.filter(profile__in=following_profiles)
    search_query = request.GET.get('q', None)
    search_results = None
    if search_query and search_query.strip():
        search_results = Profile.objects.filter(
            Q(user__username__icontains=search_query) |
            Q(bio__icontains=search_query)
        ).exclude(user=request.user).select_related('user')
    context = {
        'chat_contacts': users_i_follow,
        'search_query': search_query,
        'search_results': search_results,
    }
    return render(request, 'messages_list.html', context)


@login_required
def conversation_detail_view(request, username):
    other_user = get_object_or_404(User, username=username)
    current_user = request.user
    if other_user == current_user:
        return redirect('messages_list')
    conversation = Conversation.objects.filter(
        participants=current_user
    ).filter(
        participants=other_user
    ).first()
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(current_user, other_user)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message_text = form.cleaned_data['text']
            Message.objects.create(
                conversation=conversation,
                sender=current_user,
                text=message_text
            )
            return redirect('conversation_detail', username=other_user.username)
    else:
        form = MessageForm()
    messages = conversation.messages.all().order_by('created_at')
    context = {
        'other_user': other_user,
        'conversation': conversation,
        'messages': messages,
        'form': form,
    }
    return render(request, 'conversation_detail.html', context)


@login_required
def saved_posts_view(request):
    user_saved_entries = SavedPost.objects.filter(user=request.user).order_by('-saved_at')
    saved_post_ids = user_saved_entries.values_list('post_id', flat=True)
    if request.user.is_authenticated:
        saved_subquery_for_saved_posts = SavedPost.objects.filter(
            post_id=OuterRef('pk'),
            user_id=request.user.pk
        )
        liked_subquery_for_saved_posts = Post.likes.through.objects.filter(
            post_id=OuterRef('pk'),
            user_id=request.user.pk
        )
    else:
        saved_subquery_for_saved_posts = SavedPost.objects.none()
        liked_subquery_for_saved_posts = Post.likes.through.objects.none()

    saved_posts_list = Post.objects.filter(pk__in=saved_post_ids).annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments'),
        is_liked=Exists(liked_subquery_for_saved_posts),
        is_saved=Exists(saved_subquery_for_saved_posts)
    ).select_related('author__user').prefetch_related('comments__user')
    saved_posts_list = saved_posts_list.order_by('-created_at')
    context = {
        'saved_posts': saved_posts_list,
        'page_title': 'Uložené příspěvky'
    }
    return render(request, 'saved_posts.html', context)

@login_required
@require_POST
def toggle_save_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    saved_post_entry, created = SavedPost.objects.get_or_create(user=user, post=post)
    if not created:
        saved_post_entry.delete()
        is_saved = False
    else:
        is_saved = True
    return JsonResponse({'is_saved': is_saved, 'post_id': post.id})

@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(recipient=request.user).select_related(
        'actor',
        'actor__profile',
    ).prefetch_related(
        'target',
        'action_object'
    )
    unread_notifications_query = notifications.filter(read=False)
    unread_notification_ids = list(unread_notifications_query.values_list('id', flat=True))
    if unread_notification_ids:
        Notification.objects.filter(id__in=unread_notification_ids).update(read=True)
        for notification in notifications:
            if notification.id in unread_notification_ids:
                notification.read = True
    context = {
        'notifications': notifications,
        'page_title': 'Vaše oznámení'
    }
    return render(request, 'notifications.html', context)