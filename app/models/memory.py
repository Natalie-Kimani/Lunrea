from datetime import datetime, timezone

from app.extensions import db


class Memory(db.Model):
    __tablename__ = "memories"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    creator_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    caption = db.Column(
        db.Text,
        nullable=True
    )

    memory_date = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    location = db.Column(
        db.String(255),
        nullable=True
    )

    why_it_matters = db.Column(
        db.Text,
        nullable=True
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

    deleted_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    creator = db.relationship(
        "User",
        back_populates="memories"
    )

    perspectives = db.relationship(
        "Perspective",
        back_populates="memory",
        cascade="all, delete-orphan"
    )

    reflections = db.relationship(
        "Reflection",
        back_populates="memory",
        cascade="all, delete-orphan"
    )

    media = db.relationship(
        "Media",
        back_populates="memory",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Memory {self.id}>"
