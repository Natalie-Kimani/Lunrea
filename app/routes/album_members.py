from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Album, AlbumMember, User
from app.utils.app_lock import app_unlocked_required


album_member_bp = Blueprint(
    "album_members",
    __name__,
    url_prefix="/api/albums"
)


@album_member_bp.post("/<int:album_id>/members")
@jwt_required()
@app_unlocked_required
def add_album_member(album_id):
    user_id = int(get_jwt_identity())

    album = Album.query.filter_by(
        id=album_id,
        owner_id=user_id
    ).first()

    if not album:
        return {
            "error": "Album not found."
        }, 404

    data = request.get_json() or {}

    member_user_id = data.get("user_id")
    role = data.get("role", "viewer")

    if not member_user_id:
        return {
            "error": "user_id is required."
        }, 400

    member_user = User.query.get(member_user_id)

    if not member_user:
        return {
            "error": "User not found."
        }, 404

    existing_member = AlbumMember.query.filter_by(
        album_id=album.id,
        user_id=member_user_id
    ).first()

    if existing_member:
        return {
            "error": "User is already a member of this album."
        }, 409

    if role not in ["viewer", "contributor"]:
        return {
            "error": "Invalid role."
        }, 400

    member = AlbumMember(
        album_id=album.id,
        user_id=member_user_id,
        role=role
    )

    db.session.add(member)
    db.session.commit()

    return {
        "message": "Member added successfully.",
        "member": {
            "id": member.id,
            "album_id": member.album_id,
            "user_id": member.user_id,
            "role": member.role,
            "joined_at": member.joined_at.isoformat(),
        }
    }, 201


@album_member_bp.get("/<int:album_id>/members")
@jwt_required()
@app_unlocked_required
def get_album_members(album_id):
    user_id = int(get_jwt_identity())

    album = Album.query.filter_by(
        id=album_id,
        owner_id=user_id
    ).first()

    if not album:
        return {
            "error": "Album not found."
        }, 404

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
                "role": member.role,
                "joined_at": member.joined_at.isoformat(),
            }
            for member in members
        ]
    }, 200
