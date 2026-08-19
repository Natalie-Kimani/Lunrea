from datetime import datetime, timezone

from app.extensions import db


class Album(db.Model):
    __tablename__ = "albums"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    owner_id = db.Column(
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

    cover_media_id = db.Column(
        db.Integer,
        db.ForeignKey("media.id"),
        nullable=True
    )

    theme = db.Column(
        db.String(50),
        nullable=True
    )

    start_date = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    end_date = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    privacy = db.Column(
        db.String(30),
        nullable=False,
        default="private"
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

    owner = db.relationship(
        "User",
        backref="albums_owned"
    )

    cover_media = db.relationship(
        "Media",
        foreign_keys=[cover_media_id]
    )

    def __repr__(self):
        return f"<Album {self.title}>"
