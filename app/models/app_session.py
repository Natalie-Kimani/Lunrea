from datetime import datetime, timezone

from app.extensions import db


class AppSession(db.Model):
    __tablename__ = "app_sessions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    session_token = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )

    unlocked_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    last_activity = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    locked_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    is_locked = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship(
        "User",
        back_populates="app_sessions"
    )

    def lock(self):
        self.is_locked = True
        self.locked_at = datetime.now(timezone.utc)

    def touch(self):
        self.last_activity = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<AppSession {self.id} user={self.user_id}>"
