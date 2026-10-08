from datetime import datetime, timezone

import bcrypt

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    app_pin_hash = db.Column(
        db.String(255),
        nullable=True
    )

    display_name = db.Column(
        db.String(100),
        nullable=False
    )

    profile_image = db.Column(
        db.String(500),
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

    memories = db.relationship(
        "Memory",
        back_populates="creator",
        cascade="all, delete-orphan"
    )

    perspectives = db.relationship(
        "Perspective",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    reflections = db.relationship(
        "Reflection",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    app_sessions = db.relationship(
        "AppSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    @property
    def password(self):
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, plain_password):
        if not plain_password:
            raise ValueError("Password cannot be empty.")

        if len(plain_password) < 8:
            raise ValueError(
                "Password must be at least 8 characters long."
            )

        hashed_password = bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt()
        )

        self.password_hash = hashed_password.decode("utf-8")

    def check_password(self, plain_password):
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )

    def set_app_pin(self, pin):
        pin = str(pin or "").strip()
        if not pin.isdigit() or len(pin) not in (4, 5, 6):
            raise ValueError("PIN must be 4 to 6 digits.")
        self.app_pin_hash = bcrypt.hashpw(
            pin.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

    def check_app_pin(self, pin):
        if not self.app_pin_hash:
            return False
        return bcrypt.checkpw(
            str(pin).encode("utf-8"),
            self.app_pin_hash.encode("utf-8")
        )

    def __repr__(self):
        return f"<User {self.username}>"
