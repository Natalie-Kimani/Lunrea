from datetime import datetime, timezone

from app.extensions import db


class ChapterMemory(db.Model):
    __tablename__ = "chapter_memories"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    chapter_id = db.Column(
        db.Integer,
        db.ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False
    )

    memory_id = db.Column(
        db.Integer,
        db.ForeignKey("memories.id"),
        nullable=False
    )

    position = db.Column(
        db.Integer,
        nullable=False,
        default=0
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

    chapter = db.relationship(
        "Chapter",
        backref=db.backref("chapter_memories", cascade="all, delete-orphan", passive_deletes=True)
    )

    memory = db.relationship(
        "Memory",
        backref="chapter_memories"
    )

    user = db.relationship(
        "User",
        backref="chapter_memories_added"
    )

    def __repr__(self):
        return f"<ChapterMemory chapter={self.chapter_id} memory={self.memory_id}>"
