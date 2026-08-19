from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Memory, Person, MemoryPerson
from app.utils.app_lock import app_unlocked_required


memory_people_bp = Blueprint(
    "memory_people",
    __name__,
    url_prefix="/api/memories"
)


@memory_people_bp.post("/<int:memory_id>/people")
@jwt_required()
@app_unlocked_required
def attach_person_to_memory(memory_id):
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

    person_id = data.get("person_id")

    if not person_id:
        return {
            "error": "person_id is required."
        }, 400

    person = (
        Person.query
        .filter(
            Person.id == person_id,
            Person.created_by == user_id
        )
        .first()
    )

    if not person:
        return {
            "error": "Person not found."
        }, 404

    existing = MemoryPerson.query.filter_by(
        memory_id=memory.id,
        person_id=person.id
    ).first()

    if existing:
        return {
            "error": "Person is already attached to this memory."
        }, 409

    memory_person = MemoryPerson(
        memory_id=memory.id,
        person_id=person.id
    )

    db.session.add(memory_person)
    db.session.commit()

    return {
        "message": "Person attached to memory successfully.",
        "memory_person": {
            "id": memory_person.id,
            "memory_id": memory_person.memory_id,
            "person_id": memory_person.person_id,
            "person": {
                "id": person.id,
                "name": person.name
            }
        }
    }, 201


@memory_people_bp.get("/<int:memory_id>/people")
@jwt_required()
@app_unlocked_required
def get_memory_people(memory_id):
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

    memory_people = (
        MemoryPerson.query
        .join(Person)
        .filter(
            MemoryPerson.memory_id == memory.id,
            Person.created_by == user_id
        )
        .all()
    )

    return {
        "memory_id": memory.id,
        "people": [
            {
                "id": mp.person.id,
                "name": mp.person.name,
                "relationship_id": mp.id
            }
            for mp in memory_people
        ]
    }, 200
