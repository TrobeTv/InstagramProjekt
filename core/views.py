from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Exists, OuterRef
from django.http import JsonResponse, Http404, HttpResponseForbidden
from django.contrib.auth import logout, login
from .forms import PostForm, CommentForm, ProfileForm, RegistrationForm
from .models import Post, Profile


def feed_view(request):
    posts = Post.objects \
        .annotate(
          likes_count=Count('likes'),
          comments_count=Count('comments'),
          is_liked=Exists(
            Post.likes.through.objects.filter(
              post_id=OuterRef('pk'),
              user_id=request.user.pk
            )
          )
        ) \
        .prefetch_related('comments__user') \
        .order_by('-created_at')

    comment_form = CommentForm()
    return render(request, 'feed.html', {
        'posts': posts,
        'comment_form': comment_form,
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
    followers_count = profile.followers.count()
    following_count = profile.following.count()
    post_count = posts.count()

    return render(request, 'profile.html', {
        'profile_user': profile_user,
        'profile': profile,
        'posts': posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'post_count': post_count,
    })


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
        # už sleduji -> unfollow
        me.following.remove(target_profile)
        action = 'unfollowed'
    else:
        # začít sledovat
        me.following.add(target_profile)
        action = 'followed'

    # nové počty
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
def post_detail_view(request, pk):
    post = get_object_or_404(Post.objects.select_related('author__user'), pk=pk)
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
        'is_liked': post.likes.filter(pk=request.user.pk).exists(),
        'likes_count': post.likes.count(),
        'comment_form': form,
    }
    return render(request, 'post_detail.html', context)

def explore_view(request, post_pk=None):
    posts = Post.objects.all().order_by('-created_at')
    selected_post = None
    comment_form = None
    if post_pk is not None:
        selected_post = get_object_or_404(Post, pk=post_pk)
        comment_form = CommentForm()

    return render(request, 'explore.html', {
        'posts': posts,
        'selected_post': selected_post,
        'comment_form': comment_form,
    })

def explore_search_view(request):
    q = request.GET.get('q', '').strip()
    users = []
    if q:
        users = User.objects.filter(username__icontains=q)[:50] # limit 50 příspěvků
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
    # GET -> potvrzovací stránka vykreslení
    return render(request, 'post_confirm_delete.html', {
        'post': post,
    })