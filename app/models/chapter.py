from datetime import datetime, timezone

from app.extensions import db


class Chapter(db.Model):
    __tablename__ = "chapters"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    album_id = db.Column(
        db.Integer,
        db.ForeignKey("albums.id", ondelete="CASCADE"),
        nullable=False
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    position = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    album = db.relationship(
        "Album",
        backref="chapters"
    )

    creator = db.relationship(
        "User",
        backref="chapters_created"
    )

    def __repr__(self):
        return f"<Chapter {self.title}>"
