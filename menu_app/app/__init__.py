from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_admin import Admin


db = SQLAlchemy()
admin = Admin(name="My Admin", template_mode="bootstrap3", url="/menu/admin/cat")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    admin.init_app(app)

    from app.admin_panel import bp as admin_bp

    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    return app


from app import models
