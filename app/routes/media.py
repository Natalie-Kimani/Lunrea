import os
import uuid

from flask import Blueprint, Response, current_app, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Memory, Media
from app.utils.app_lock import app_unlocked_required
from app.services import storage

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp",
    "mp4",
    "mov",
    "webm",
    "mp3",
    "wav",
    "m4a",
}

MEDIA_TYPES = {
    "jpg": "image",
    "jpeg": "image",
    "png": "image",
    "gif": "image",
    "webp": "image",
    "mp4": "video",
    "mov": "video",
    "webm": "video",
    "mp3": "audio",
    "wav": "audio",
    "m4a": "audio",
}

MAX_FILE_SIZE = 50 * 1024 * 1024

def get_extension(filename):
    return (
        filename.rsplit(".", 1)[1].lower()
        if "." in filename
        else ""
    )

media_bp = Blueprint(
    "media",
    __name__,
)

@media_bp.post("/api/memories/<int:memory_id>/upload")
@jwt_required()
@app_unlocked_required
def upload_media(memory_id):
    user_id = int(get_jwt_identity())

    memory = (
        Memory.query
        .filter(
            Memory.id == memory_id,
            Memory.creator_id == user_id,
            Memory.deleted_at.is_(None)
        )
        .first()
    )

    if not memory:
        return {
            "error": "Memory not found."
        }, 404

    if "file" not in request.files:
        return {
            "error": "No file provided."
        }, 400

    file = request.files["file"]

    if not file.filename:
        return {
            "error": "Filename is required."
        }, 400

    extension = get_extension(file.filename)

    if extension not in ALLOWED_EXTENSIONS:
        return {
            "error": "Unsupported file type."
        }, 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return {
            "error": "File exceeds the 50 MB limit."
        }, 400

    media_type = MEDIA_TYPES[extension]

    safe_filename = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    try:
        relative_path = storage.save_upload(
            file,
            safe_filename,
            file.mimetype,
        )
    except Exception:
        current_app.logger.exception("Upload storage failed")
        return {
            "error": "Could not store the file."
        }, 500

    media = Media(
        memory_id=memory.id,
        uploaded_by=user_id,
        media_type=media_type,
        file_path=relative_path,
        file_name=file.filename,
        mime_type=file.mimetype,
        file_size=file_size,
    )

    try:
        db.session.add(media)
        db.session.commit()

    except Exception:
        db.session.rollback()

        storage.delete_file(relative_path)

        return {
            "error": "Could not save media."
        }, 500

    return {
        "message": "File uploaded successfully.",
        "media": {
            "id": media.id,
            "memory_id": media.memory_id,
            "uploaded_by": media.uploaded_by,
            "media_type": media.media_type,
            "file_path": media.file_path,
            "file_name": media.file_name,
            "mime_type": media.mime_type,
            "file_size": media.file_size,
            "created_at": media.created_at.isoformat(),
        }
    }, 201

@media_bp.post("/api/memories/<int:memory_id>/media")
@jwt_required()
@app_unlocked_required
def add_media(memory_id):
    user_id = int(get_jwt_identity())

    memory = (
        Memory.query
        .filter(
            Memory.id == memory_id,
            Memory.creator_id == user_id,
            Memory.deleted_at.is_(None)
        )
        .first()
    )

    if not memory:
        return {
            "error": "Memory not found."
        }, 404

    data = request.get_json() or {}

    required_fields = [
        "media_type",
        "file_path",
        "file_name",
    ]

    for field in required_fields:
        if not data.get(field):
            return {
                "error": f"{field} is required."
            }, 400

    # Clients may not point at files in our own storage: uploads go through
    # /upload, which is the only thing that creates stored paths.
    stored = str(data["file_path"])
    if ".." in stored or stored.startswith(("r2:", "/", "uploads")):
        return {
            "error": "Invalid file_path."
        }, 400

    media = Media(
        memory_id=memory.id,
        uploaded_by=user_id,
        media_type=data["media_type"],
        file_path=data["file_path"],
        file_name=data["file_name"],
        mime_type=data.get("mime_type"),
        file_size=data.get("file_size"),
    )

    db.session.add(media)
    db.session.commit()

    return {
        "message": "Media attached successfully.",
        "media": {
            "id": media.id,
            "memory_id": media.memory_id,
            "uploaded_by": media.uploaded_by,
            "media_type": media.media_type,
            "file_path": media.file_path,
            "file_name": media.file_name,
            "mime_type": media.mime_type,
            "file_size": media.file_size,
            "created_at": media.created_at.isoformat(),
        }
    }, 201

@media_bp.get("/api/memories/<int:memory_id>/media")
@jwt_required()
@app_unlocked_required
def get_memory_media(memory_id):
    user_id = int(get_jwt_identity())

    memory = (
        Memory.query
        .filter(
            Memory.id == memory_id,
            Memory.creator_id == user_id,
            Memory.deleted_at.is_(None)
        )
        .first()
    )

    if not memory:
        return {
            "error": "Memory not found."
        }, 404

    media_items = Media.query.filter_by(
        memory_id=memory.id
    ).order_by(
        Media.created_at.asc()
    ).all()

    return {
        "memory_id": memory.id,
        "media": [
            {
                "id": media.id,
                "memory_id": media.memory_id,
                "uploaded_by": media.uploaded_by,
                "media_type": media.media_type,
                "file_path": media.file_path,
                "file_name": media.file_name,
                "mime_type": media.mime_type,
                "file_size": media.file_size,
                "created_at": media.created_at.isoformat(),
            }
            for media in media_items
        ]
    }, 200

@media_bp.get("/api/media/<int:media_id>")
@jwt_required()
@app_unlocked_required
def get_media_file(media_id):
    user_id = int(get_jwt_identity())

    media = (
        Media.query
        .join(Memory, Media.memory_id == Memory.id)
        .filter(
            Media.id == media_id,
            Memory.creator_id == user_id,
            Memory.deleted_at.is_(None)
        )
        .first()
    )

    if not media:
        return {
            "error": "Media not found."
        }, 404

    if storage.is_remote(media.file_path):
        try:
            remote = storage.open_remote(media.file_path)
        except Exception:
            return {
                "error": "Media file not found."
            }, 404

        headers = {
            "Content-Disposition": f'inline; filename="{media.file_name}"',
            "Cache-Control": "private, max-age=3600",
        }
        if remote.get("ContentLength") is not None:
            headers["Content-Length"] = str(remote["ContentLength"])

        return Response(
            remote["Body"].iter_chunks(chunk_size=64 * 1024),
            mimetype=media.mime_type or "application/octet-stream",
            headers=headers,
        )

    file_path = storage.local_path(media.file_path)

    if not file_path or not os.path.isfile(file_path):
        return {
            "error": "Media file not found."
        }, 404

    return send_file(
        file_path,
        mimetype=media.mime_type,
        download_name=media.file_name
    )
