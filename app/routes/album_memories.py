from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Album, AlbumMemory, Memory
from app.utils.app_lock import app_unlocked_required


album_memory_bp = Blueprint(
    "album_memories",
    __name__,
    url_prefix="/api/albums"
)


@album_memory_bp.post("/<int:album_id>/memories")
@jwt_required()
@app_unlocked_required
def add_memory_to_album(album_id):
    user_id = int(get_jwt_identity())

    album = Album.query.filter(
        Album.id == album_id,
        Album.owner_id == user_id
    ).first()

    if not album:
        return {
            "error": "Album not found."
        }, 404

    data = request.get_json() or {}

    memory_id = data.get("memory_id")

    if not memory_id:
        return {
            "error": "memory_id is required."
        }, 400

    memory = Memory.query.filter(
        Memory.id == memory_id,
        Memory.creator_id == user_id,
        Memory.deleted_at.is_(None)
    ).first()

    if not memory:
        return {
            "error": "Memory not found."
        }, 404

    existing = AlbumMemory.query.filter_by(
        album_id=album.id,
        memory_id=memory.id
    ).first()

    if existing:
        return {
            "error": "Memory is already in this album."
        }, 409

    album_memory = AlbumMemory(
        album_id=album.id,
        memory_id=memory.id,
        added_by=user_id
    )

    db.session.add(album_memory)
    db.session.commit()

    return {
        "message": "Memory added to album successfully.",
        "album_memory": {
            "id": album_memory.id,
            "album_id": album_memory.album_id,
            "memory_id": album_memory.memory_id,
            "added_by": album_memory.added_by,
            "added_at": album_memory.added_at.isoformat(),
        }
    }, 201


@album_memory_bp.get("/<int:album_id>/memories")
@jwt_required()
@app_unlocked_required
def get_album_memories(album_id):
    user_id = int(get_jwt_identity())

    album = Album.query.filter(
        Album.id == album_id,
        Album.owner_id == user_id
    ).first()

    if not album:
        return {
            "error": "Album not found."
        }, 404

    album_memories = AlbumMemory.query.filter_by(
        album_id=album.id
    ).order_by(
        AlbumMemory.added_at.asc()
    ).all()

    return {
        "album_id": album.id,
        "memories": [
            {
                "id": item.memory.id,
                "title": item.memory.title,
                "caption": item.memory.caption,
                "description": item.memory.description,
                "location": item.memory.location,
                "memory_date": (
                    item.memory.memory_date.isoformat()
                    if item.memory.memory_date
                    else None
                ),
                "added_by": item.added_by,
                "added_at": item.added_at.isoformat(),
            }
            for item in album_memories
        ]
    }, 200
