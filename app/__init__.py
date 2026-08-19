from flask import Flask

from app.config import Config
from app.extensions import db, migrate, jwt, ma


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    from app.models import (
        User,
        Person,
        Memory,
        Perspective,
        Reflection,
        Media,
        Album,
        Chapter,
        AlbumMember,
        AlbumMemory,
        ChapterMemory,
        MemoryPerson,
    )

    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
   
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.memories import memory_bp
    app.register_blueprint(memory_bp)

    from app.routes.media import media_bp
    app.register_blueprint(media_bp)

    from app.routes.perspectives import perspective_bp
    app.register_blueprint(perspective_bp)

    from app.routes.reflections import reflection_bp
    app.register_blueprint(reflection_bp)

    from app.routes.people import people_bp
    app.register_blueprint(people_bp)

    from app.routes.memory_people import memory_people_bp
    app.register_blueprint(memory_people_bp)

    from app.routes.albums import album_bp
    app.register_blueprint(album_bp)

    from app.routes.album_memories import album_memory_bp
    app.register_blueprint(album_memory_bp)

    from app.routes.album_members import album_member_bp
    app.register_blueprint(album_member_bp)

    from app.routes.chapters import chapter_bp
    app.register_blueprint(chapter_bp)

    from app.routes.chapter_memories import chapter_memory_bp
    app.register_blueprint(chapter_memory_bp)

    return app
