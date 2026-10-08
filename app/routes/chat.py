from datetime import datetime, timezone

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.extensions import db
from app.models import (
    User,
    ChatRoom,
    ChatMember,
    ChatMessage,
    AlbumMember,
    AlbumMemory,
)
from app.utils.app_lock import app_unlocked_required
from app.utils.album_permissions import get_album_access


chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

ROOM_TYPES = {"direct", "group", "album", "chapter", "memory"}


def _room_member(room_id, user_id):
    return ChatMember.query.filter_by(
        room_id=room_id,
        user_id=user_id,
    ).first()


def _serialize_room(room, user_id):
    members = sorted(room.members, key=lambda member: member.joined_at)
    return {
        "id": room.id,
        "room_type": room.room_type,
        "name": room.name,
        "created_by": room.created_by,
        "album_id": room.album_id,
        "chapter_id": room.chapter_id,
        "memory_id": room.memory_id,
        "member_count": len(members),
        "members": [
            {
                "user_id": member.user_id,
                "username": member.user.username,
                "display_name": member.user.display_name,
                "joined_at": member.joined_at.isoformat(),
                "last_read_at": (
                    member.last_read_at.isoformat()
                    if member.last_read_at
                    else None
                ),
            }
            for member in members
        ],
        "created_at": room.created_at.isoformat(),
        "updated_at": room.updated_at.isoformat(),
    }


def _serialize_message(message):
    return {
        "id": message.id,
        "room_id": message.room_id,
        "sender_id": message.sender_id,
        "sender": {
            "username": message.sender.username,
            "display_name": message.sender.display_name,
        },
        "content": message.content,
        "created_at": message.created_at.isoformat(),
        "updated_at": message.updated_at.isoformat(),
        "deleted_at": (
            message.deleted_at.isoformat()
            if message.deleted_at
            else None
        ),
    }


def _context_access(room_type, data, user_id):
    """Return (ok, status, error) for contextual rooms."""
    if room_type == "album":
        album_id = data.get("album_id")
        if not album_id:
            return False, 400, "album_id is required for an album chat."
        album, role = get_album_access(album_id, user_id)
        if not album or role is None:
            return False, 403, "You do not have access to this album."
        return True, None, None

    if room_type == "chapter":
        chapter_id = data.get("chapter_id")
        if not chapter_id:
            return False, 400, "chapter_id is required for a chapter chat."

        from app.models import Chapter

        chapter = db.session.get(Chapter, chapter_id)
        if not chapter:
            return False, 404, "Chapter not found."

        album, role = get_album_access(chapter.album_id, user_id)
        if not album or role is None:
            return False, 403, "You do not have access to this chapter."
        return True, None, None

    if room_type == "memory":
        memory_id = data.get("memory_id")
        if not memory_id:
            return False, 400, "memory_id is required for a memory chat."

        from app.models import Memory

        memory = db.session.get(Memory, memory_id)
        if not memory or memory.deleted_at is not None:
            return False, 404, "Memory not found."

        if memory.creator_id == user_id:
            return True, None, None

        # A memory chat can also be used by collaborators when the memory
        # is inside an album they can access.
        album_member = (
            AlbumMember.query
            .join(AlbumMemory, AlbumMemory.album_id == AlbumMember.album_id)
            .filter(
                AlbumMember.user_id == user_id,
                AlbumMemory.memory_id == memory_id,
            )
            .first()
        )
        if album_member:
            return True, None, None

        return False, 403, "You do not have access to this memory."

    return True, None, None


@chat_bp.post("/rooms")
@jwt_required()
@app_unlocked_required
def create_room():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    room_type = data.get("room_type", "group")
    if room_type not in ROOM_TYPES:
        return {"error": "Invalid room_type."}, 400

    if room_type == "direct":
        other_user_id = data.get("user_id")
        if not other_user_id or int(other_user_id) == user_id:
            return {"error": "A different user_id is required for a direct chat."}, 400

        other_user = db.session.get(User, int(other_user_id))
        if not other_user:
            return {"error": "User not found."}, 404

        existing = (
            ChatRoom.query
            .join(ChatMember, ChatMember.room_id == ChatRoom.id)
            .filter(ChatRoom.room_type == "direct")
            .filter(ChatMember.user_id == user_id)
            .all()
        )
        for room in existing:
            ids = {member.user_id for member in room.members}
            if ids == {user_id, other_user.id}:
                return {
                    "message": "Direct chat already exists.",
                    "room": _serialize_room(room, user_id),
                }, 200

        room = ChatRoom(room_type="direct", created_by=user_id)
        member_ids = [user_id, other_user.id]

    else:
        ok, status, error = _context_access(room_type, data, user_id)
        if not ok:
            return {"error": error}, status

        room = ChatRoom(
            room_type=room_type,
            name=data.get("name"),
            created_by=user_id,
            album_id=data.get("album_id"),
            chapter_id=data.get("chapter_id"),
            memory_id=data.get("memory_id"),
        )
        member_ids = [user_id]

        requested_member_ids = data.get("member_ids", [])
        if not isinstance(requested_member_ids, list):
            return {"error": "member_ids must be a list."}, 400
        member_ids.extend(requested_member_ids)

        # Album chats automatically include the current album members.
        if room_type == "album":
            album_members = AlbumMember.query.filter_by(
                album_id=room.album_id
            ).all()
            member_ids.extend(member.user_id for member in album_members)

    unique_member_ids = list(dict.fromkeys(int(value) for value in member_ids))
    users = User.query.filter(User.id.in_(unique_member_ids)).all()
    found_ids = {user.id for user in users}
    missing_ids = [value for value in unique_member_ids if value not in found_ids]
    if missing_ids:
        return {"error": f"User(s) not found: {missing_ids}."}, 404

    db.session.add(room)
    db.session.flush()

    for member_id in unique_member_ids:
        db.session.add(ChatMember(room_id=room.id, user_id=member_id))

    db.session.commit()

    return {
        "message": "Chat room created successfully.",
        "room": _serialize_room(room, user_id),
    }, 201


@chat_bp.get("/rooms")
@jwt_required()
@app_unlocked_required
def list_rooms():
    user_id = int(get_jwt_identity())

    rooms = (
        ChatRoom.query
        .join(ChatMember, ChatMember.room_id == ChatRoom.id)
        .filter(ChatMember.user_id == user_id)
        .order_by(ChatRoom.updated_at.desc())
        .all()
    )

    return {
        "rooms": [_serialize_room(room, user_id) for room in rooms]
    }, 200


@chat_bp.get("/rooms/<int:room_id>")
@jwt_required()
@app_unlocked_required
def get_room(room_id):
    user_id = int(get_jwt_identity())
    room = db.session.get(ChatRoom, room_id)

    if not room:
        return {"error": "Chat room not found."}, 404

    if not _room_member(room.id, user_id):
        return {"error": "You are not a member of this chat."}, 403

    return {"room": _serialize_room(room, user_id)}, 200


@chat_bp.post("/rooms/<int:room_id>/members")
@jwt_required()
@app_unlocked_required
def add_room_member(room_id):
    user_id = int(get_jwt_identity())
    room = db.session.get(ChatRoom, room_id)

    if not room:
        return {"error": "Chat room not found."}, 404

    if not _room_member(room.id, user_id):
        return {"error": "You are not a member of this chat."}, 403

    if room.room_type == "direct":
        return {"error": "Direct chats cannot have additional members."}, 400

    if room.created_by != user_id:
        return {"error": "Only the room creator can add members."}, 403

    data = request.get_json() or {}
    member_user_id = data.get("user_id")
    if not member_user_id:
        return {"error": "user_id is required."}, 400

    member_user = db.session.get(User, int(member_user_id))
    if not member_user:
        return {"error": "User not found."}, 404

    if _room_member(room.id, member_user.id):
        return {"error": "User is already a member."}, 409

    db.session.add(ChatMember(room_id=room.id, user_id=member_user.id))
    db.session.commit()

    return {"message": "Chat member added successfully."}, 201


@chat_bp.delete("/rooms/<int:room_id>/members/<int:member_user_id>")
@jwt_required()
@app_unlocked_required
def remove_room_member(room_id, member_user_id):
    user_id = int(get_jwt_identity())
    room = db.session.get(ChatRoom, room_id)

    if not room:
        return {"error": "Chat room not found."}, 404

    if room.created_by != user_id:
        return {"error": "Only the room creator can remove members."}, 403

    if member_user_id == room.created_by:
        return {"error": "The room creator cannot be removed."}, 400

    member = _room_member(room.id, member_user_id)
    if not member:
        return {"error": "Chat member not found."}, 404

    db.session.delete(member)
    db.session.commit()

    return {"message": "Chat member removed successfully."}, 200


@chat_bp.get("/rooms/<int:room_id>/messages")
@jwt_required()
@app_unlocked_required
def get_messages(room_id):
    user_id = int(get_jwt_identity())
    room = db.session.get(ChatRoom, room_id)

    if not room:
        return {"error": "Chat room not found."}, 404

    if not _room_member(room.id, user_id):
        return {"error": "You are not a member of this chat."}, 403

    try:
        limit = min(max(int(request.args.get("limit", 50)), 1), 100)
        before_id = request.args.get("before_id", type=int)
    except (TypeError, ValueError):
        return {"error": "limit and before_id must be valid integers."}, 400

    query = ChatMessage.query.filter_by(room_id=room.id)
    if before_id:
        query = query.filter(ChatMessage.id < before_id)

    messages = (
        query.order_by(ChatMessage.id.desc())
        .limit(limit)
        .all()
    )
    messages.reverse()

    member = _room_member(room.id, user_id)
    member.last_read_at = datetime.now(timezone.utc)
    db.session.commit()

    return {
        "room_id": room.id,
        "messages": [_serialize_message(message) for message in messages],
        "has_more": len(messages) == limit,
    }, 200


@chat_bp.post("/rooms/<int:room_id>/messages")
@jwt_required()
@app_unlocked_required
def send_message(room_id):
    user_id = int(get_jwt_identity())
    room = db.session.get(ChatRoom, room_id)

    if not room:
        return {"error": "Chat room not found."}, 404

    if not _room_member(room.id, user_id):
        return {"error": "You are not a member of this chat."}, 403

    data = request.get_json() or {}
    content = (data.get("content") or "").strip()

    if not content:
        return {"error": "Message content is required."}, 400

    if len(content) > 5000:
        return {"error": "Message cannot exceed 5000 characters."}, 400

    message = ChatMessage(
        room_id=room.id,
        sender_id=user_id,
        content=content,
    )
    db.session.add(message)
    room.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return {
        "message": "Message sent successfully.",
        "chat_message": _serialize_message(message),
    }, 201


@chat_bp.patch("/messages/<int:message_id>")
@jwt_required()
@app_unlocked_required
def edit_message(message_id):
    user_id = int(get_jwt_identity())
    message = db.session.get(ChatMessage, message_id)

    if not message or message.deleted_at is not None:
        return {"error": "Message not found."}, 404

    if message.sender_id != user_id:
        return {"error": "You can only edit your own messages."}, 403

    if not _room_member(message.room_id, user_id):
        return {"error": "You are not a member of this chat."}, 403

    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if not content:
        return {"error": "Message content is required."}, 400
    if len(content) > 5000:
        return {"error": "Message cannot exceed 5000 characters."}, 400

    message.content = content
    message.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return {"message": "Message updated successfully.", "chat_message": _serialize_message(message)}, 200


@chat_bp.delete("/messages/<int:message_id>")
@jwt_required()
@app_unlocked_required
def delete_message(message_id):
    user_id = int(get_jwt_identity())
    message = db.session.get(ChatMessage, message_id)

    if not message or message.deleted_at is not None:
        return {"error": "Message not found."}, 404

    if message.sender_id != user_id:
        return {"error": "You can only delete your own messages."}, 403

    if not _room_member(message.room_id, user_id):
        return {"error": "You are not a member of this chat."}, 403

    message.deleted_at = datetime.now(timezone.utc)
    message.content = "Message deleted"
    db.session.commit()

    return {"message": "Message deleted successfully."}, 200
