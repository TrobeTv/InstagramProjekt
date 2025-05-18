from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User # Nebo settings.AUTH_USER_MODEL
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Exists, OuterRef, Q
from django.http import JsonResponse, Http404, HttpResponseForbidden
from django.contrib.auth import logout, login
from django.views.decorators.http import require_POST

from .forms import PostForm, CommentForm, ProfileForm, RegistrationForm, MessageForm # Ujistěte se, že MessageForm je zde také
from .models import Post, Profile, Comment, Conversation, Message, SavedPost # << ZDE JE KLÍČOVÝ IMPORT


@login_required
def feed_view(request):
    current_user_profile = request.user.profile
    profiles_i_follow = current_user_profile.following.all()

    # Subquery pro zjištění, zda je příspěvek uložen přihlášeným uživatelem
    saved_subquery = SavedPost.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk
    )
    # Subquery pro zjištění, zda je příspěvek lajkován přihlášeným uživatelem (již byste měli mít)
    liked_subquery = Post.likes.through.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk
    )

    if not profiles_i_follow.exists():
        posts = Post.objects.none()
    else:
        posts_query = Post.objects.filter(author__in=profiles_i_follow)
        # Případně pokud chcete zahrnout i vlastní příspěvky:
        # posts_query = Post.objects.filter(
        # Q(author__in=profiles_i_follow) | Q(author=current_user_profile)
        # )

        posts = posts_query.annotate(
            likes_count=Count('likes'),
            comments_count=Count('comments'),
            is_liked=Exists(liked_subquery),
            is_saved=Exists(saved_subquery)  # << PŘIDÁNO
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
    profile = profile_user.profile  # Toto je Profile objekt zobrazovaného uživatele
    posts = Post.objects.filter(author=profile).order_by('-created_at')

    # Získání seznamů pro modální okna
    # .select_related('user') optimalizuje dotazy pro přístup k user.username a profile.avatar.url v šabloně
    followers_profiles = profile.followers.all().select_related('user')  # Profily, které sledují tento 'profile'
    following_profiles = profile.following.all().select_related('user')  # Profily, které tento 'profile' sleduje

    # Počty (tyto již pravděpodobně máte, ale pro úplnost)
    followers_count = followers_profiles.count()
    following_count = following_profiles.count()
    post_count = posts.count()

    # Zjistíme, zda přihlášený uživatel sleduje zobrazený profil (pokud je přihlášen a není to jeho vlastní profil)
    is_followed_by_request_user = False
    if request.user.is_authenticated and request.user != profile_user:
        is_followed_by_request_user = request.user.profile.following.filter(pk=profile.pk).exists()

    context = {
        'profile_user': profile_user,  # User objekt zobrazovaného profilu
        'profile': profile,  # Profile objekt zobrazovaného profilu
        'posts': posts,
        'post_count': post_count,
        'followers_count': followers_count,
        'following_count': following_count,
        'followers_list': followers_profiles,  # << NOVĚ PŘIDÁNO
        'following_list': following_profiles,  # << NOVĚ PŘIDÁNO
        'is_followed_by_request_user': is_followed_by_request_user,  # Pro tlačítko Sledovat/Přestat sledovat
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
@login_required
def post_detail_view(request, pk):
    # Subquery pro zjištění, zda je příspěvek uložen přihlášeným uživatelem
    saved_subquery = SavedPost.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk
    )
    # Subquery pro zjištění, zda je příspěvek lajkován (již byste měli mít)
    liked_subquery = Post.likes.through.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk
    )

    post = get_object_or_404(
        Post.objects.annotate(
            is_saved=Exists(saved_subquery.filter(post_id=OuterRef('pk'))), # Anotace přímo pro jeden post
            likes_count_annotated=Count('likes'), # Přejmenováno, abychom se vyhnuli konfliktu s post.likes.count() níže
            is_liked_annotated=Exists(liked_subquery.filter(post_id=OuterRef('pk')))
        ).select_related('author__user'),
        pk=pk
    )

    if request.method == 'POST': # Pro přidání komentáře
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
        'is_liked': post.is_liked_annotated, # Použijeme anotovanou hodnotu
        'likes_count': post.likes_count_annotated, # Použijeme anotovanou hodnotu
        'is_saved': post.is_saved, # << PŘIDÁNO (použijeme anotovanou hodnotu)
        'comment_form': form,
    }
    return render(request, 'post_detail.html', context)

def explore_view(request, post_pk=None):
    # Subquery pro zjištění, zda je příspěvek uložen přihlášeným uživatelem
    saved_subquery = SavedPost.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk if request.user.is_authenticated else None # Ochrana pro anonymní uživatele
    )
    # Subquery pro lajky (již byste měli mít)
    liked_subquery = Post.likes.through.objects.filter(
        post_id=OuterRef('pk'),
        user_id=request.user.pk if request.user.is_authenticated else None
    )

    posts_query = Post.objects.all().annotate(
        is_saved=Exists(saved_subquery), # << PŘIDÁNO pro mřížku
        is_liked=Exists(liked_subquery), # << PŘIDÁNO pro mřížku (pro konzistenci, pokud byste to tam potřebovali)
        likes_count=Count('likes')       # << PŘIDÁNO pro mřížku
    ).order_by('-created_at')

    selected_post_obj = None
    comment_form = None

    if post_pk is not None:
        selected_post_obj = get_object_or_404(
            Post.objects.annotate(
                is_saved=Exists(saved_subquery.filter(post_id=OuterRef('pk'))), # << PŘIDÁNO pro detail
                is_liked=Exists(liked_subquery.filter(post_id=OuterRef('pk'))), # << PŘIDÁNO pro detail
                likes_count=Count('likes') # << PŘIDÁNO pro detail
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


@login_required
def messages_list_view(request):
    user_profile = request.user.profile
    following_profiles = user_profile.following.all()
    users_i_follow = User.objects.filter(profile__in=following_profiles)

    search_query = request.GET.get('q', None)
    search_results = None  # Inicializujeme jako None

    if search_query and search_query.strip():  # Pokud je dotaz a není to jen mezera
        # Vyhledáváme v uživatelských jménech a bio profilech
        # Chceme vrátit objekty Profile, aby bylo snadné přistupovat k avataru
        # Vyloučíme sebe sama z výsledků vyhledávání
        search_results = Profile.objects.filter(
            Q(user__username__icontains=search_query) |
            Q(bio__icontains=search_query)  # Volitelně můžete vyhledávat i v bio
        ).exclude(user=request.user).select_related('user')

    # Pokud je aktivní vyhledávání, `search_results` bude obsahovat QuerySet nebo prázdný QuerySet.
    # Pokud není aktivní vyhledávání (search_query je None nebo prázdný), `search_results` zůstane None.

    context = {
        'chat_contacts': users_i_follow,
        'search_query': search_query,
        'search_results': search_results,  # Bude None, pokud se nehledalo
    }
    return render(request, 'messages_list.html', context)


@login_required
def conversation_detail_view(request, username):
    other_user = get_object_or_404(User, username=username)
    current_user = request.user

    if other_user == current_user:
        # Uživatel nemůže chatovat sám se sebou (můžeme přesměrovat nebo zobrazit chybu)
        return redirect('messages_list')

    # Pokusíme se najít existující konverzaci mezi těmito dvěma uživateli
    # Použijeme Q objekty pro nalezení konverzace, kde jsou oba uživatelé účastníky
    # Je důležité, aby pořadí v ManyToMany poli nehrálo roli, ale jednodušší je často:
    # 1. Získat konverzace current_user
    # 2. Z nich vyfiltrovat ty, kde je i other_user

    conversation = Conversation.objects.filter(
        participants=current_user
    ).filter(
        participants=other_user
    ).first()  # .distinct() by mohl být potřeba, pokud by mohly vzniknout duplicity

    if not conversation:
        # Pokud konverzace neexistuje, vytvoříme novou
        conversation = Conversation.objects.create()
        conversation.participants.add(current_user, other_user)
        # Není třeba conversation.save() po add, pokud je to nový objekt a save() je volán jinde nebo implicitně
        # Ale pro jistotu:
        # conversation.save() # Django >3.2 by to měl zvládnout automaticky s add() na novém objektu

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message_text = form.cleaned_data['text']
            Message.objects.create(
                conversation=conversation,
                sender=current_user,
                text=message_text
            )
            # Po odeslání zprávy přesměrujeme na tu samou stránku (reload)
            return redirect('conversation_detail', username=other_user.username)
    else:
        form = MessageForm()

    # Načteme zprávy pro tuto konverzaci
    messages = conversation.messages.all().order_by('created_at')

    # Označit zprávy od other_user jako přečtené (jednoduchá implementace)
    # messages.filter(sender=other_user, is_read=False).update(is_read=True)
    # Pokročilejší by bylo označovat jen ty, které jsou viditelné na stránce atd.
    # Prozatím to necháme bez automatického označování jako přečtené při načtení.

    context = {
        'other_user': other_user,
        'conversation': conversation,
        'messages': messages,
        'form': form,
    }
    return render(request, 'conversation_detail.html', context)


@login_required
def saved_posts_view(request):
    # Získáme všechny záznamy SavedPost pro aktuálně přihlášeného uživatele.
    # Použijeme select_related pro optimalizaci dotazů na související objekty Post a jejich autory.
    # Chceme načíst samotné příspěvky, ne jen záznamy o uložení.

    user_saved_entries = SavedPost.objects.filter(user=request.user).order_by('-saved_at')

    # Získáme seznam ID uložených příspěvků
    saved_post_ids = user_saved_entries.values_list('post_id', flat=True)

    # Načteme samotné Post objekty, které jsou uložené, a přidáme k nim potřebné anotace
    # jako pro feed, abychom mohli v šabloně použít stejné komponenty/logiku
    if request.user.is_authenticated:
        saved_subquery_for_saved_posts = SavedPost.objects.filter(
            post_id=OuterRef('pk'),
            user_id=request.user.pk
        )
        liked_subquery_for_saved_posts = Post.likes.through.objects.filter(
            post_id=OuterRef('pk'),
            user_id=request.user.pk
        )
    else:  # Pro případ, že by view nebylo @login_required, i když zde je
        saved_subquery_for_saved_posts = SavedPost.objects.none()
        liked_subquery_for_saved_posts = Post.likes.through.objects.none()

    saved_posts_list = Post.objects.filter(pk__in=saved_post_ids).annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments'),
        is_liked=Exists(liked_subquery_for_saved_posts),
        is_saved=Exists(saved_subquery_for_saved_posts)  # Zde by is_saved mělo být vždy True, ale pro konzistenci
    ).select_related('author__user').prefetch_related('comments__user')

    # Seřadíme podle toho, jak byly uloženy (od nejnovějšího)
    # To je trochu složitější, protože původní řazení bylo na SavedPost.
    # Můžeme je seřadit v Pythonu po načtení, nebo načíst `SavedPost` objekty a iterovat přes ně v šabloně.
    # Pro jednoduchost zatím necháme řazení podle `Post.created_at` nebo `pk`, nebo můžeme iterovat `user_saved_entries`
    # a přistupovat k `entry.post`.
    # Použijeme druhou, jednodušší variantu pro zachování pořadí uložení:

    # Nahrazujeme `saved_posts_list` tímto, abychom zachovali pořadí uložení
    # a stále měli anotované post objekty.
    # Toto je komplexnější, zjednodušme to prozatím a vraťme se k tomu v případě potřeby.
    # Prozatím zobrazíme `saved_posts_list` seřazené podle data vytvoření příspěvku.
    # Chceme-li řadit podle data uložení, musíme iterovat `user_saved_entries` v šabloně
    # a pro každý `entry` přistupovat k `entry.post` (a anotace by se musely řešit jinak nebo pro každý post zvlášť).

    # Zjednodušená verze (řadí podle data vytvoření příspěvku, ne data uložení):
    saved_posts_list = saved_posts_list.order_by('-created_at')  # Nebo jiné řazení pro Post

    # Alternativa: Předat user_saved_entries do šablony a v šabloně iterovat a přistupovat k entry.post.
    # Pak by se anotace musely přidávat individuálně nebo by se nepoužívaly.
    # Pro zobrazení jako v explore (mřížka obrázků), nepotřebujeme hned všechny anotace.

    context = {
        # 'saved_entries': user_saved_entries, # Možnost 1: iterovat toto a brát entry.post
        'saved_posts': saved_posts_list,  # Možnost 2: iterovat toto (již anotované Post objekty)
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
        # Příspěvek již byl uložen, takže ho odstraníme (zrušíme uložení)
        saved_post_entry.delete()
        is_saved = False
    else:
        # Příspěvek nebyl uložen (get_or_create ho právě vytvořil), takže je nyní uložen
        is_saved = True

    return JsonResponse({'is_saved': is_saved, 'post_id': post.id})