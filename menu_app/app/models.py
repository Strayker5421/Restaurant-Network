from app import db


class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    ingredients = db.Column(db.String(500), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    section = db.Column(db.String(255), nullable=False)
