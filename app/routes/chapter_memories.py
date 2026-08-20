from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Chapter, Memory, ChapterMemory
from app.utils.app_lock import app_unlocked_required
from app.utils.album_permissions import (
    get_album_access,
    can_contribute,
)


chapter_memory_bp = Blueprint(
    "chapter_memories",
    __name__,
    url_prefix="/api/chapters"
)


@chapter_memory_bp.post("/<int:chapter_id>/memories")
@jwt_required()
@app_unlocked_required
def add_memory_to_chapter(chapter_id):
    user_id = int(get_jwt_identity())

    chapter = Chapter.query.filter_by(
        id=chapter_id
    ).first()

    if not chapter:
        return {
            "error": "Chapter not found."
        }, 404

    album, role = get_album_access(
        chapter.album_id,
        user_id
    )

    if not album:
        return {
            "error": "Album not found."
        }, 404

    if not can_contribute(role):
        return {
            "error": "You do not have permission to add memories to this chapter."
        }, 403

    data = request.get_json() or {}

    memory_id = data.get("memory_id")

    if not memory_id:
        return {
            "error": "memory_id is required."
        }, 400

    memory = Memory.query.filter_by(
        id=memory_id,
        creator_id=user_id
    ).first()

    if not memory:
        return {
            "error": "Memory not found."
        }, 404

    existing = ChapterMemory.query.filter_by(
        chapter_id=chapter.id,
        memory_id=memory.id
    ).first()

    if existing:
        return {
            "error": "Memory is already in this chapter."
        }, 409

    position = data.get("position", 0)

    chapter_memory = ChapterMemory(
        chapter_id=chapter.id,
        memory_id=memory.id,
        position=position,
        added_by=user_id
    )

    db.session.add(chapter_memory)
    db.session.commit()

    return {
        "message": "Memory added to chapter successfully.",
        "chapter_memory": {
            "id": chapter_memory.id,
            "chapter_id": chapter_memory.chapter_id,
            "memory_id": chapter_memory.memory_id,
            "position": chapter_memory.position,
            "added_by": chapter_memory.added_by,
            "added_at": chapter_memory.added_at.isoformat(),
        }
    }, 201


@chapter_memory_bp.get("/<int:chapter_id>/memories")
@jwt_required()
@app_unlocked_required
def get_chapter_memories(chapter_id):
    user_id = int(get_jwt_identity())

    chapter = Chapter.query.filter_by(
        id=chapter_id
    ).first()

    if not chapter:
        return {
            "error": "Chapter not found."
        }, 404

    album, role = get_album_access(
        chapter.album_id,
        user_id
    )

    if not album:
        return {
            "error": "Album not found."
        }, 404

    if role is None:
        return {
            "error": "You do not have access to this album."
        }, 403

    chapter_memories = ChapterMemory.query.filter_by(
        chapter_id=chapter.id
    ).order_by(
        ChapterMemory.position.asc(),
        ChapterMemory.added_at.asc()
    ).all()

    return {
        "chapter_id": chapter.id,
        "memories": [
            {
                "id": cm.memory.id,
                "title": cm.memory.title,
                "caption": cm.memory.caption,
                "description": cm.memory.description,
                "location": cm.memory.location,
                "memory_date": (
                    cm.memory.memory_date.isoformat()
                    if cm.memory.memory_date
                    else None
                ),
                "why_it_matters": cm.memory.why_it_matters,
                "position": cm.position,
                "added_by": cm.added_by,
                "added_at": cm.added_at.isoformat(),
            }
            for cm in chapter_memories
        ]
    }, 200
