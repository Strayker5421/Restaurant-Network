from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import ARRAY


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.Boolean, default=False)

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


class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Boolean, default=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"))
    dishes = db.relationship(
        "Dish", backref="menu", lazy="dynamic", cascade="all, delete-orphan"
    )

    @staticmethod
    def get_menu(menu_name):
        menu = Menu.query.filter_by(name=menu_name).first()
        return menu


class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    ingredients = db.Column(db.String(500), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    menu_id = db.Column(db.Integer, db.ForeignKey("menu.id"))


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
