from datetime import datetime, timezone

from app.extensions import db


class ChatRoom(db.Model):
    __tablename__ = "chat_rooms"

    id = db.Column(db.Integer, primary_key=True)

    room_type = db.Column(db.String(20), nullable=False, default="group")
    name = db.Column(db.String(200), nullable=True)

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    album_id = db.Column(
        db.Integer,
        db.ForeignKey("albums.id", ondelete="CASCADE"),
        nullable=True,
    )

    chapter_id = db.Column(
        db.Integer,
        db.ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=True,
    )

    memory_id = db.Column(
        db.Integer,
        db.ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    creator = db.relationship("User", backref="chat_rooms_created")
    album = db.relationship("Album", backref="chat_rooms")
    chapter = db.relationship("Chapter", backref="chat_rooms")
    memory = db.relationship("Memory", backref="chat_rooms")

    def __repr__(self):
        return f"<ChatRoom {self.id} {self.room_type}>"
