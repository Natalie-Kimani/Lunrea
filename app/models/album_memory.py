from datetime import datetime, timezone

from app.extensions import db


class AlbumMemory(db.Model):
    __tablename__ = "album_memories"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    album_id = db.Column(
        db.Integer,
        db.ForeignKey("albums.id", ondelete="CASCADE"),
        nullable=False
    )

    memory_id = db.Column(
        db.Integer,
        db.ForeignKey("memories.id"),
        nullable=False
    )

    added_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    added_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    album = db.relationship(
        "Album",
        backref=db.backref("album_memories", cascade="all, delete-orphan", passive_deletes=True)
    )

    memory = db.relationship(
        "Memory",
        backref="album_memories"
    )

    user = db.relationship(
        "User",
        backref="album_memories_added"
    )

    def __repr__(self):
        return f"<AlbumMemory album={self.album_id} memory={self.memory_id}>"
