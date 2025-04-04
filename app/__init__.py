from flask import Flask, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from flask_admin import Admin
from flask_login import current_user
from flask_admin import AdminIndexView, expose


class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not current_user.is_authenticated or not current_user.role:
            flash("You need to log in to access the admin page.", "danger")
            return redirect(url_for("auth.login"))
        return super(MyAdminIndexView, self).index()


db = SQLAlchemy()
admin = Admin(
    name="My Admin", template_mode="bootstrap3", index_view=MyAdminIndexView()
)
migrate = Migrate()
login = LoginManager()
login.login_view = "auth.login"
login.login_message = "Please log in to access this page."
scheduler = BackgroundScheduler(daemon=True)


def create_app(config_class=Config):
    app = Flask(__name__, static_url_path="/static")
    app.config.from_object(config_class)

    db.init_app(app)
    admin.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    from app.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    from app.admin_panel import bp as admin_bp

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
