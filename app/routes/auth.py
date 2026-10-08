from flask import Blueprint, request

from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.models import User, AppSession

from app.services.app_lock import (
    create_unlock_session,
    get_valid_unlock_session,
    lock_session,
)

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    display_name = data.get("display_name")

    if not username or not email or not password or not display_name:
        return {
            "error": "username, email, password and display_name are required."
        }, 400

    existing_user = User.query.filter(
        (User.username == username) |
        (User.email == email)
    ).first()

    if existing_user:
        return {
            "error": "Username or email already exists."
        }, 409

    try:
        user = User(
            username=username,
            email=email,
            display_name=display_name
        )

        user.password = password

    except ValueError as error:
        return {
            "error": str(error)
        }, 400

    db.session.add(user)
    db.session.commit()

    return {
        "message": "Lunrea account created.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name
        }
    }, 201


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {
            "error": "username and password are required."
        }, 400

    user = User.query.filter_by(
        username=username
    ).first()

    if not user or not user.check_password(password):
        return {
            "error": "Invalid username or password."
        }, 401

    access_token = create_access_token(
        identity=str(user.id)
    )

    return {
        "message": "Login successful.",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name
        }
    }, 200

@auth_bp.get("/pin-status")
@jwt_required()
def pin_status():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return {"error": "User not found."}, 404
    return {"pin_set": bool(user.app_pin_hash)}, 200


@auth_bp.post("/pin")
@jwt_required()
def set_pin():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return {"error": "User not found."}, 404

    data = request.get_json() or {}
    pin = str(data.get("pin") or "").strip()
    try:
        user.set_app_pin(pin)
    except ValueError as error:
        return {"error": str(error)}, 400

    db.session.commit()
    return {"message": "App PIN saved."}, 200


@auth_bp.post("/unlock")
@jwt_required()
def unlock():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    pin = str(data.get("pin") or "").strip()

    user = db.session.get(User, int(user_id))
    if not user:
        return {"error": "User not found."}, 404

    if not user.app_pin_hash:
        return {"error": "Set your Lunrea PIN before unlocking."}, 409

    if not user.check_app_pin(pin):
        return {"error": "Incorrect PIN."}, 401

    session = create_unlock_session(user.id)

    return {
        "message": "Lunrea unlocked.",
        "session_token": session.session_token,
        "expires_after_minutes": 15,
    }, 200

@auth_bp.post("/lock")
@jwt_required()
def lock():
    user_id = get_jwt_identity()

    data = request.get_json() or {}
    session_token = data.get("session_token")

    if not session_token:
        return {
            "error": "Session token is required."
        }, 400

    session = AppSession.query.filter_by(
        user_id=int(user_id),
        session_token=session_token,
        is_locked=False,
    ).first()

    if not session:
        return {
            "error": "Active unlock session not found."
        }, 404

    lock_session(session)

    return {
        "message": "Lunrea locked."
    }, 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()

    user = db.session.get(
        User,
        int(user_id)
    )

    if not user:
        return {
            "error": "User not found."
        }, 404

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name
    }, 200


@auth_bp.post("/logout")
@jwt_required()
def logout():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    session_token = data.get("session_token") or request.headers.get("X-App-Session")

    if session_token:
        session = AppSession.query.filter_by(
            user_id=user_id,
            session_token=session_token,
            is_locked=False,
        ).first()
        if session:
            lock_session(session)

    return {
        "message": "Logged out successfully."
    }, 200


@auth_bp.get("/users")
@jwt_required()
def users():
    current_user_id = int(get_jwt_identity())
    query = (request.args.get("q") or "").strip()

    if len(query) < 2:
        return {"users": []}, 200

    users = (
        User.query
        .filter(User.id != current_user_id)
        .filter(
            (User.username.ilike(f"%{query}%")) |
            (User.display_name.ilike(f"%{query}%"))
        )
        .order_by(User.username.asc())
        .limit(20)
        .all()
    )

    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
            }
            for user in users
        ]
    }, 200
