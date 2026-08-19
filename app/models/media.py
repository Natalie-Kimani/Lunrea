from datetime import datetime, timezone

from app.extensions import db


class Media(db.Model):
    __tablename__ = "media"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    memory_id = db.Column(
        db.Integer,
        db.ForeignKey("memories.id"),
        nullable=False
    )

    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    media_type = db.Column(
        db.String(20),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    file_name = db.Column(
        db.String(255),
        nullable=False
    )

    mime_type = db.Column(
        db.String(100),
        nullable=True
    )

    file_size = db.Column(
        db.BigInteger,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    memory = db.relationship(
        "Memory",
        back_populates="media"
    )

    uploader = db.relationship(
        "User",
        backref="media_uploaded"
    )

    def __repr__(self):
        return f"<Media {self.id} {self.media_type}>"
