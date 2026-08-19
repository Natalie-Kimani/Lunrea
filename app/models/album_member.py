from datetime import datetime, timezone

from app.extensions import db


class AlbumMember(db.Model):
    __tablename__ = "album_members"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    album_id = db.Column(
        db.Integer,
        db.ForeignKey("albums.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    role = db.Column(
        db.String(30),
        nullable=False,
        default="viewer"
    )

    joined_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    album = db.relationship(
        "Album",
        backref="members"
    )

    user = db.relationship(
        "User",
        backref="album_memberships"
    )

    def __repr__(self):
        return f"<AlbumMember album={self.album_id} user={self.user_id}>"
