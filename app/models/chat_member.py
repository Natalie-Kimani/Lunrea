from datetime import datetime, timezone

from app.extensions import db


class ChatMember(db.Model):
    __tablename__ = "chat_members"
    __table_args__ = (
        db.UniqueConstraint(
            "room_id",
            "user_id",
            name="uq_chat_members_room_user",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    room_id = db.Column(
        db.Integer,
        db.ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    joined_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    last_read_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    room = db.relationship(
        "ChatRoom",
        backref=db.backref("members", cascade="all, delete-orphan"),
    )

    user = db.relationship("User", backref="chat_memberships")

    def __repr__(self):
        return f"<ChatMember room={self.room_id} user={self.user_id}>"
