from app.extensions import db


class MemoryPerson(db.Model):
    __tablename__ = "memory_people"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    memory_id = db.Column(
        db.Integer,
        db.ForeignKey("memories.id"),
        nullable=False
    )

    person_id = db.Column(
        db.Integer,
        db.ForeignKey("people.id"),
        nullable=False
    )

    memory = db.relationship(
        "Memory",
        backref="memory_people"
    )

    person = db.relationship(
        "Person",
        backref="memory_people"
    )

    def __repr__(self):
        return f"<MemoryPerson memory={self.memory_id} person={self.person_id}>"
