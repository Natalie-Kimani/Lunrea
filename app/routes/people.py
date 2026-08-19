from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Person
from app.utils.app_lock import app_unlocked_required


people_bp = Blueprint(
    "people",
    __name__,
    url_prefix="/api/people"
)


@people_bp.post("/")
@jwt_required()
@app_unlocked_required
def create_person():
    user_id = int(get_jwt_identity())

    data = request.get_json() or {}

    name = data.get("name")

    if not name:
        return {
            "error": "name is required."
        }, 400

    person = Person(
        name=name,
        created_by=user_id
    )

    db.session.add(person)
    db.session.commit()

    return {
        "message": "Person created successfully.",
        "person": {
            "id": person.id,
            "name": person.name,
            "created_by": person.created_by,
            "created_at": person.created_at.isoformat(),
        }
    }, 201


@people_bp.get("/")
@jwt_required()
@app_unlocked_required
def get_people():
    user_id = int(get_jwt_identity())

    people = Person.query.filter_by(
        created_by=user_id
    ).order_by(
        Person.created_at.asc()
    ).all()

    return {
        "people": [
            {
                "id": person.id,
                "name": person.name,
                "created_by": person.created_by,
                "created_at": person.created_at.isoformat(),
            }
            for person in people
        ]
    }, 200
