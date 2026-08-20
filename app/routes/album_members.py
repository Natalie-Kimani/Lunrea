from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import AlbumMember, User
from app.utils.app_lock import app_unlocked_required
from app.utils.album_permissions import (
    get_album_access,
    can_manage_album,
)


album_member_bp = Blueprint(
    "album_members",
    __name__,
    url_prefix="/api/albums"
)


@album_member_bp.post("/<int:album_id>/members")
@jwt_required()
@app_unlocked_required
def add_member(album_id):
    user_id = int(get_jwt_identity())

    album, role = get_album_access(album_id, user_id)

    if not album:
        return {"error": "Album not found."}, 404

    if not can_manage_album(role):
        return {
            "error": "Only the album owner can manage members."
        }, 403

    data = request.get_json() or {}

    member_user_id = data.get("user_id")
    member_role = data.get("role", "viewer")

    if not member_user_id:
        return {"error": "user_id is required."}, 400

    if member_role not in {"viewer", "contributor"}:
        return {
            "error": "role must be viewer or contributor."
        }, 400

    member = User.query.filter_by(id=member_user_id).first()

    if not member:
        return {"error": "User not found."}, 404

    if member.id == album.owner_id:
        return {
            "error": "The album owner is already a member."
        }, 400

    existing = AlbumMember.query.filter_by(
        album_id=album.id,
        user_id=member.id
    ).first()

    if existing:
        return {
            "error": "User is already a member of this album."
        }, 409

    album_member = AlbumMember(
        album_id=album.id,
        user_id=member.id,
        role=member_role
    )

    db.session.add(album_member)
    db.session.commit()

    return {
        "message": "Member added successfully.",
        "member": {
            "id": album_member.id,
            "album_id": album_member.album_id,
            "user_id": album_member.user_id,
            "role": album_member.role,
            "joined_at": album_member.joined_at.isoformat(),
        }
    }, 201


@album_member_bp.get("/<int:album_id>/members")
@jwt_required()
@app_unlocked_required
def get_members(album_id):
    user_id = int(get_jwt_identity())

    album, role = get_album_access(album_id, user_id)

    if not album:
        return {"error": "Album not found."}, 404

    if role is None:
        return {
            "error": "You do not have access to this album."
        }, 403

    members = AlbumMember.query.filter_by(
        album_id=album.id
    ).order_by(
        AlbumMember.joined_at.asc()
    ).all()

    return {
        "album_id": album.id,
        "members": [
            {
                "id": member.id,
                "user_id": member.user_id,
                "username": member.user.username,
                "display_name": member.user.display_name,
                "role": member.role,
                "joined_at": member.joined_at.isoformat(),
            }
            for member in members
        ]
    }, 200
