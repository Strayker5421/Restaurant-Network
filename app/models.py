import docker.errors
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
from docker import DockerClient
from sqlalchemy import create_engine, text
import os
import subprocess, pytz


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.Boolean, default=False)
    restaurants = db.relationship(
        "Restaurant", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    images = db.Column(ARRAY(db.String()))
    status = db.Column(db.Boolean, default=False)
    menus = db.relationship(
        "Menu", backref="restaurant", lazy="dynamic", cascade="all, delete-orphan"
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Boolean, default=False)
    expiration_date = db.Column(
        db.DateTime(timezone=True),
        index=True,
        default=datetime.now(pytz.timezone("Europe/Moscow")),
    )
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"))
    PORT = 8000

    def check_subscription(self):
        new_status = datetime.now(pytz.timezone("Europe/Moscow")) < self.expiration_date
        if new_status != self.status:
            self.status = new_status
            db.session.commit()
            restaurant = self.restaurant
            active_menus = Menu.query.filter_by(
                restaurant_id=restaurant.id, status=True
            ).count()
            if active_menus == 0:
                restaurant.status = False
            else:
                restaurant.status = True
            db.session.commit()

            if self.status:
                Menu.PORT += 1
                self.start_container(
                    self.name.replace(" ", "-").lower(),
                    self.restaurant.name.split(" ")[0].lower(),
                    self.PORT,
                )
            else:
                self.stop_container(
                    self.name.replace(" ", "-").lower(),
                    self.restaurant.name.split(" ")[0].lower(),
                )

    @staticmethod
    def start_container(menu_name, restaurant_name, port=PORT):
        os.environ["APP_PORT"] = str(port)
        subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker-compose-menu.yml",
                "--project-name",
                f"menu-{restaurant_name}-{menu_name}",
                "up",
                "-d",
            ]
        )

    @staticmethod
    def stop_container(menu_name, restaurant_name):
        subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker-compose-menu.yml",
                "--project-name",
                f"menu-{restaurant_name}-{menu_name}",
                "down",
            ]
        )

    @staticmethod
    def get_menu(menu_name):
        menu = Menu.query.filter_by(name=menu_name).first()
        return menu


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
