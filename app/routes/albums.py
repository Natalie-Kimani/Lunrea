from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Album
from app.utils.app_lock import app_unlocked_required


album_bp = Blueprint(
    "albums",
    __name__,
    url_prefix="/api/albums"
)


@album_bp.post("/")
@jwt_required()
@app_unlocked_required
def create_album():
    user_id = int(get_jwt_identity())

    data = request.get_json() or {}

    title = data.get("title")

    if not title:
        return {
            "error": "title is required."
        }, 400

    start_date = None
    end_date = None

    if data.get("start_date"):
        try:
            start_date = datetime.fromisoformat(
                data["start_date"]
            )
        except ValueError:
            return {
                "error": "start_date must be a valid ISO 8601 date."
            }, 400

    if data.get("end_date"):
        try:
            end_date = datetime.fromisoformat(
                data["end_date"]
            )
        except ValueError:
            return {
                "error": "end_date must be a valid ISO 8601 date."
            }, 400

    album = Album(
        owner_id=user_id,
        title=title,
        description=data.get("description"),
        cover_media_id=data.get("cover_media_id"),
        theme=data.get("theme"),
        start_date=start_date,
        end_date=end_date,
        privacy=data.get("privacy", "private"),
    )

    db.session.add(album)
    db.session.commit()

    return {
        "message": "Album created successfully.",
        "album": {
            "id": album.id,
            "owner_id": album.owner_id,
            "title": album.title,
            "description": album.description,
            "cover_media_id": album.cover_media_id,
            "theme": album.theme,
            "start_date": (
                album.start_date.isoformat()
                if album.start_date
                else None
            ),
            "end_date": (
                album.end_date.isoformat()
                if album.end_date
                else None
            ),
            "privacy": album.privacy,
            "created_at": album.created_at.isoformat(),
            "updated_at": album.updated_at.isoformat(),
        }
    }, 201


@album_bp.get("/")
@jwt_required()
@app_unlocked_required
def get_albums():
    user_id = int(get_jwt_identity())

    albums = Album.query.filter_by(
        owner_id=user_id
    ).order_by(
        Album.created_at.asc()
    ).all()

    return {
        "albums": [
            {
                "id": album.id,
                "owner_id": album.owner_id,
                "title": album.title,
                "description": album.description,
                "cover_media_id": album.cover_media_id,
                "theme": album.theme,
                "start_date": (
                    album.start_date.isoformat()
                    if album.start_date
                    else None
                ),
                "end_date": (
                    album.end_date.isoformat()
                    if album.end_date
                    else None
                ),
                "privacy": album.privacy,
                "created_at": album.created_at.isoformat(),
                "updated_at": album.updated_at.isoformat(),
            }
            for album in albums
        ]
    }, 200
