from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.contrib.auth import get_user_model
from .models import Post
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

User = get_user_model()

def api_posts_list(request):
    posts = Post.objects.select_related('author__user').order_by('-created_at')
    data = []
    for post in posts:
        obj = model_to_dict(post, fields=['id', 'caption', 'created_at'])
        obj['author'] = post.author.user.username
        obj['image_url'] = request.build_absolute_uri(post.image.url)
        data.append(obj)
    return JsonResponse(data, safe=False)

def api_post_detail(request, post_id):
    try:
        post = Post.objects.select_related('author__user').get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post not found'}, status=404)
    obj = model_to_dict(post, fields=['id', 'caption', 'created_at'])
    obj['author'] = post.author.user.username
    obj['image_url'] = request.build_absolute_uri(post.image.url)
    return JsonResponse(obj)


@login_required
@require_POST
def api_follow_toggle(request, username):
    # nalazení cílového uživatele a jeho profilu
    target_user = get_object_or_404(User, username=username)
    target_profile = target_user.profile

    # profil přihlášeného uživatele
    user_profile = request.user.profile

    if target_profile in user_profile.following.all():
        user_profile.following.remove(target_profile)
        action = 'unfollowed'
    else:
        user_profile.following.add(target_profile)
        action = 'followed'

    # vrátíme nový stav
    return JsonResponse({
        'action': action,
        'followers_count': target_profile.followed_by.count(),
        'following_count': user_profile.following.count(),
    })