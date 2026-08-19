from functools import wraps

from flask import request

from flask_jwt_extended import get_jwt_identity

from app.services.app_lock import get_valid_unlock_session


def app_unlocked_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()

        session_token = request.headers.get("X-App-Session")

        if not session_token:
            return {
                "error": "Lunrea is locked.",
                "code": "APP_LOCKED"
            }, 423

        session = get_valid_unlock_session(
            int(user_id),
            session_token
        )

        if not session:
            return {
                "error": "Lunrea is locked.",
                "code": "APP_LOCKED"
            }, 423

        return function(*args, **kwargs)

    return decorated_function
