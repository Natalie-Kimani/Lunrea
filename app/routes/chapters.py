from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Album, Chapter
from app.utils.app_lock import app_unlocked_required
from app.utils.album_permissions import (
    get_album_access,
    can_contribute,
)


chapter_bp = Blueprint(
    "chapters",
    __name__,
    url_prefix="/api/albums"
)


@chapter_bp.post("/<int:album_id>/chapters")
@jwt_required()
@app_unlocked_required
def create_chapter(album_id):
    user_id = int(get_jwt_identity())

    album, role = get_album_access(album_id, user_id)

    if not album:
        return {
            "error": "Album not found."
        }, 404

    if not can_contribute(role):
        return {
            "error": "You do not have permission to create chapters in this album."
        }, 403

    data = request.get_json() or {}

    title = data.get("title")

    if not title:
        return {
            "error": "title is required."
        }, 400

    description = data.get("description")

    position = data.get("position", 0)

    chapter = Chapter(
        album_id=album.id,
        created_by=user_id,
        title=title,
        description=description,
        position=position
    )

    db.session.add(chapter)
    db.session.commit()

    return {
        "message": "Chapter created successfully.",
        "chapter": {
            "id": chapter.id,
            "album_id": chapter.album_id,
            "created_by": chapter.created_by,
            "title": chapter.title,
            "description": chapter.description,
            "position": chapter.position,
            "created_at": chapter.created_at.isoformat(),
            "updated_at": chapter.updated_at.isoformat(),
        }
    }, 201


@chapter_bp.get("/<int:album_id>/chapters")
@jwt_required()
@app_unlocked_required
def get_chapters(album_id):
    user_id = int(get_jwt_identity())

    album, role = get_album_access(album_id, user_id)

    if not album:
        return {
            "error": "Album not found."
        }, 404

    if role is None:
        return {
            "error": "You do not have access to this album."
        }, 403

    chapters = Chapter.query.filter_by(
        album_id=album.id
    ).order_by(
        Chapter.position.asc(),
        Chapter.created_at.asc()
    ).all()

    return {
        "album_id": album.id,
        "chapters": [
            {
                "id": chapter.id,
                "created_by": chapter.created_by,
                "title": chapter.title,
                "description": chapter.description,
                "position": chapter.position,
                "created_at": chapter.created_at.isoformat(),
                "updated_at": chapter.updated_at.isoformat(),
            }
            for chapter in chapters
        ]
    }, 200

@chapter_bp.patch("/<int:album_id>/chapters/<int:chapter_id>")
@jwt_required()
@app_unlocked_required
def update_chapter(album_id, chapter_id):
    user_id = int(get_jwt_identity())

    album, role = get_album_access(album_id, user_id)

    if not album:
        return {
            "error": "Album not found."
        }, 404

    if not can_contribute(role):
        return {
            "error": "You do not have permission to update chapters."
        }, 403

    chapter = Chapter.query.filter_by(
        id=chapter_id,
        album_id=album.id
    ).first()

    if not chapter:
        return {
            "error": "Chapter not found."
        }, 404

    data = request.get_json() or {}

    if "title" in data:
        if not data["title"]:
            return {
                "error": "title cannot be empty."
            }, 400

        chapter.title = data["title"]

    if "description" in data:
        chapter.description = data["description"]

    if "position" in data:
        chapter.position = data["position"]

    db.session.commit()

    return {
        "message": "Chapter updated successfully.",
        "chapter": {
            "id": chapter.id,
            "album_id": chapter.album_id,
            "created_by": chapter.created_by,
            "title": chapter.title,
            "description": chapter.description,
            "position": chapter.position,
            "created_at": chapter.created_at.isoformat(),
            "updated_at": chapter.updated_at.isoformat(),
        }
    }, 200


@chapter_bp.delete("/<int:album_id>/chapters/<int:chapter_id>")
@jwt_required()
@app_unlocked_required
def delete_chapter(album_id, chapter_id):
    user_id = int(get_jwt_identity())

    album, role = get_album_access(album_id, user_id)

    if not album:
        return {
            "error": "Album not found."
        }, 404

    if not can_contribute(role):
        return {
            "error": "You do not have permission to delete chapters."
        }, 403

    chapter = Chapter.query.filter_by(
        id=chapter_id,
        album_id=album.id
    ).first()

    if not chapter:
        return {
            "error": "Chapter not found."
        }, 404

    db.session.delete(chapter)
    db.session.commit()

    return {
        "message": "Chapter deleted successfully."
    }, 200
