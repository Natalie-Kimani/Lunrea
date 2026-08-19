from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from flask import current_app

from app.extensions import db
from app.models import AppSession


def create_unlock_session(user_id):
    now = datetime.now(timezone.utc)

    # Lock any previously active sessions for this user.
    active_sessions = AppSession.query.filter_by(
        user_id=user_id,
        is_locked=False,
    ).all()

    for session in active_sessions:
        session.lock()

    # Create the new active session.
    session = AppSession(
        user_id=user_id,
        session_token=token_urlsafe(32),
        unlocked_at=now,
        last_activity=now,
        is_locked=False,
    )

    db.session.add(session)
    db.session.commit()

    return session


def get_valid_unlock_session(user_id, session_token):
    session = AppSession.query.filter_by(
        user_id=user_id,
        session_token=session_token,
        is_locked=False,
    ).first()

    if not session:
        return None

    now = datetime.now(timezone.utc)

    timeout_minutes = current_app.config[
        "APP_LOCK_TIMEOUT_MINUTES"
    ]

    timeout = timedelta(minutes=timeout_minutes)

    if now - session.last_activity >= timeout:
        session.lock()
        db.session.commit()
        return None

    session.touch()
    db.session.commit()

    return session


def lock_session(session):
    session.lock()
    db.session.commit()
