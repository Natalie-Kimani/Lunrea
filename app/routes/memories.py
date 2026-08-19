from datetime import datetime, timezone

from flask import Blueprint, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.models import Memory
from app.utils.app_lock import app_unlocked_required


memory_bp = Blueprint(
    "memories",
    __name__,
    url_prefix="/api/memories"
)


@memory_bp.post("/")
@jwt_required()
@app_unlocked_required
def create_memory():
    user_id = int(get_jwt_identity())

    data = request.get_json() or {}

    memory_date = None

    if data.get("memory_date"):
        try:
            memory_date = datetime.fromisoformat(
                data["memory_date"]
            )
        except ValueError:
            return {
                "error": "memory_date must be a valid ISO 8601 date."
            }, 400

    memory = Memory(
        creator_id=user_id,
        title=data.get("title"),
        description=data.get("description"),
        caption=data.get("caption"),
        memory_date=memory_date,
        location=data.get("location"),
        why_it_matters=data.get("why_it_matters"),
    )

    db.session.add(memory)
    db.session.commit()

    return {
        "message": "Memory created successfully.",
        "memory": {
            "id": memory.id,
            "creator_id": memory.creator_id,
            "title": memory.title,
            "description": memory.description,
            "caption": memory.caption,
            "memory_date": (
                memory.memory_date.isoformat()
                if memory.memory_date
                else None
            ),
            "location": memory.location,
            "why_it_matters": memory.why_it_matters,
        }
    }, 201

@memory_bp.get("/")
@jwt_required()
@app_unlocked_required
def get_memories():
    user_id = int(get_jwt_identity())

    memories = (
        Memory.query
        .filter(
            Memory.creator_id == user_id,
            Memory.deleted_at.is_(None)
        )
        .order_by(Memory.memory_date.desc())
        .all()
    )

    return {
        "memories": [
            {
                "id": memory.id,
                "creator_id": memory.creator_id,
                "title": memory.title,
                "description": memory.description,
                "caption": memory.caption,
                "memory_date": (
                    memory.memory_date.isoformat()
                    if memory.memory_date
                    else None
                ),
                "location": memory.location,
                "why_it_matters": memory.why_it_matters,
                "created_at": memory.created_at.isoformat(),
                "updated_at": memory.updated_at.isoformat(),
            }
            for memory in memories
        ]
    }, 200

@memory_bp.get("/<int:memory_id>")
@jwt_required()
@app_unlocked_required
def get_memory(memory_id):
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

    return {
        "memory": {
            "id": memory.id,
            "creator_id": memory.creator_id,
            "title": memory.title,
            "description": memory.description,
            "caption": memory.caption,
            "memory_date": (
                memory.memory_date.isoformat()
                if memory.memory_date
                else None
            ),
            "location": memory.location,
            "why_it_matters": memory.why_it_matters,
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
        }
    }, 200

@memory_bp.patch("/<int:memory_id>")
@jwt_required()
@app_unlocked_required
def update_memory(memory_id):
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

    if "title" in data:
        memory.title = data["title"]

    if "description" in data:
        memory.description = data["description"]

    if "caption" in data:
        memory.caption = data["caption"]

    if "memory_date" in data:
        if data["memory_date"] is None:
            memory.memory_date = None
        else:
            try:
                memory.memory_date = datetime.fromisoformat(
                    data["memory_date"]
                )
            except ValueError:
                return {
                    "error": "memory_date must be a valid ISO 8601 date."
                }, 400

    if "location" in data:
        memory.location = data["location"]

    if "why_it_matters" in data:
        memory.why_it_matters = data["why_it_matters"]

    db.session.commit()

    return {
        "message": "Memory updated successfully.",
        "memory": {
            "id": memory.id,
            "creator_id": memory.creator_id,
            "title": memory.title,
            "description": memory.description,
            "caption": memory.caption,
            "memory_date": (
                memory.memory_date.isoformat()
                if memory.memory_date
                else None
            ),
            "location": memory.location,
            "why_it_matters": memory.why_it_matters,
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
        }
    }, 200

@memory_bp.delete("/<int:memory_id>")
@jwt_required()
@app_unlocked_required
def delete_memory(memory_id):
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

    memory.deleted_at = datetime.now(timezone.utc)

    db.session.commit()

    return {
        "message": "Memory deleted successfully."
    }, 200
