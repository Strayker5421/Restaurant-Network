from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from flask_socketio import SocketIO


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = "auth.login"
login.login_message = "Please log in to access this page."
scheduler = BackgroundScheduler(daemon=True)
socketio = SocketIO()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    socketio.init_app(app)

    from app.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    from app.admin import bp as admin_bp

    app.register_blueprint(admin_bp)

    from app.models import Menu

    def check_subscriptions():
        with app.app_context():
            menus = Menu.query.all()
            for menu in menus:
                menu.check_subscription()

    scheduler.add_job(
        func=check_subscriptions,
        trigger="interval",
        seconds=app.config["DAEMON_INTERVAL"],
    )
    scheduler.start()

    return app


from app import models
