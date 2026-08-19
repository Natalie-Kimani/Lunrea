from flask import Blueprint

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def home():
    return {
        "application": "Lunrea",
        "message": "Where every moment can have more than one story."
    }
