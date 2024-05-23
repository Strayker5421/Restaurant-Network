from app import db, login, socketio
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime


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
    expiration_date = db.Column(db.DateTime, index=True, default=datetime.now)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"))
    dishes = db.relationship(
        "Dish", backref="menu", lazy="dynamic", cascade="all, delete-orphan"
    )

    def check_subscription(self):
        new_status = datetime.now() < self.expiration_date
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
        socketio.emit(
            "subscription_update", {"menu_id": self.id, "status": self.status}
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
    section = db.Column(db.String(255), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey("menu.id"))


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
