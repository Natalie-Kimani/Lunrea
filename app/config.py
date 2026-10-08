import os

from dotenv import load_dotenv

load_dotenv()


def _database_url():
    url = os.getenv("DATABASE_URL")
    # Render/Heroku-style URLs start with postgres://, which SQLAlchemy 2 rejects.
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = _database_url()

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    APP_LOCK_TIMEOUT_MINUTES = 15

    # Comma-separated list of allowed frontend origins, e.g.
    # "https://lunrea.netlify.app". Defaults to "*" for local development.
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]
