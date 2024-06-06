from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config


db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from app.menu import bp as menu_bp

    app.register_blueprint(menu_bp)

    with app.app_context():
        db.create_all()

    return app


from app import models
