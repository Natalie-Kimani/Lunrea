from datetime import datetime, timezone

from app.extensions import db


class Reflection(db.Model):
    __tablename__ = "reflections"

    id = db.Column(db.Integer, primary_key=True)

    memory_id = db.Column(
        db.Integer,
        db.ForeignKey("memories.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
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

    memory = db.relationship(
        "Memory",
        back_populates="reflections"
    )

    user = db.relationship(
        "User",
        back_populates="reflections"
    )

    def __repr__(self):
        return f"<Reflection {self.id}>"
