from datetime import datetime, timezone

from app.extensions import db


class Person(db.Model):
    __tablename__ = "people"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    creator = db.relationship(
        "User",
        backref="people_created"
    )

    def __repr__(self):
        return f"<Person {self.name}>"

