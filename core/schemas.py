# core/schemas.py
from ninja import Schema

class ProfileSchema(Schema):
    id: int
    user_id: int
    bio: str | None

class PostSchema(Schema):
    id: int
    author_id: int
    text: str
    created_at: str

class CommentSchema(Schema):
    id: int
    post_id: int
    user_id: int
    text: str
    created_at: str
