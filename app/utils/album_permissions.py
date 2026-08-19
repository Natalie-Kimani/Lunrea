from app.models import Album, AlbumMember


def get_album_access(album_id, user_id):
    album = Album.query.filter_by(id=album_id).first()

    if not album:
        return None, None

    if album.owner_id == user_id:
        return album, "owner"

    membership = AlbumMember.query.filter_by(
        album_id=album_id,
        user_id=user_id
    ).first()

    if not membership:
        return album, None

    return album, membership.role


def can_view_album(role):
    return role in {"owner", "contributor", "viewer"}


def can_contribute(role):
    return role in {"owner", "contributor"}


def can_manage_album(role):
    return role == "owner"
