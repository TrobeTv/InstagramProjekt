# core/api.py
from ninja import NinjaAPI
from .models import Post, Comment, Profile
from .schemas import PostSchema, CommentSchema, ProfileSchema  # viz další krok

api = NinjaAPI()

@api.get("/posts", response=list[PostSchema])
def list_posts(request):
    return Post.objects.all()

@api.get("/posts/{post_id}", response=PostSchema)
def get_post(request, post_id: int):
    return Post.objects.get(id=post_id)

# --- případně další endpointy ---
