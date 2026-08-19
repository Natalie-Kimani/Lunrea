from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Memory, Perspective
from app.utils.app_lock import app_unlocked_required


perspective_bp = Blueprint(
    "perspectives",
    __name__,
    url_prefix="/api/memories"
)


@perspective_bp.post("/<int:memory_id>/perspectives")
@jwt_required()
@app_unlocked_required
def create_perspective(memory_id):
    user_id = int(get_jwt_identity())

    memory = (
        Memory.query
        .filter(
            Memory.id == memory_id,
            Memory.deleted_at.is_(None)
        )
        .first()
    )

    if not memory:
        return {
            "error": "Memory not found."
        }, 404

    data = request.get_json() or {}

    content = data.get("content")

    if not content:
        return {
            "error": "content is required."
        }, 400

    perspective = Perspective(
        memory_id=memory.id,
        user_id=user_id,
        content=content
    )

    db.session.add(perspective)
    db.session.commit()

    return {
        "message": "Perspective added successfully.",
        "perspective": {
            "id": perspective.id,
            "memory_id": perspective.memory_id,
            "user_id": perspective.user_id,
            "content": perspective.content,
            "created_at": perspective.created_at.isoformat(),
            "updated_at": perspective.updated_at.isoformat(),
        }
    }, 201

@perspective_bp.get("/<int:memory_id>/perspectives")
@jwt_required()
@app_unlocked_required
def get_perspectives(memory_id):
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

    perspectives = (
        Perspective.query
        .filter_by(memory_id=memory.id)
        .order_by(Perspective.created_at.asc())
        .all()
    )

    return {
        "memory_id": memory.id,
        "perspectives": [
            {
                "id": perspective.id,
                "memory_id": perspective.memory_id,
                "user_id": perspective.user_id,
                "content": perspective.content,
                "created_at": perspective.created_at.isoformat(),
                "updated_at": perspective.updated_at.isoformat(),
            }
            for perspective in perspectives
        ]
    }, 200