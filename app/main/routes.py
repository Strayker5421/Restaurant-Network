from flask import jsonify, request, render_template
from flask_login import current_user, login_required
from app import db
from app.models import User, Menu, Restaurant
from app.main import bp


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    restaurants = Restaurant.query.all()
    return render_template("index.html", restaurants=restaurants)


@bp.route("/menu/<int:restaurant_id>")
def menu_detail(restaurant_id):
    restaurant = Restaurant.query.get(restaurant_id)
    menus = restaurant.menus.all()
    return render_template("menu_detail.html", restaurant=restaurant, menus=menus)


@bp.route("/search", methods=["GET"])
def search():
    search_query = request.args.get("q", "")
    restaurants = Restaurant.query.filter(
        Restaurant.name.ilike(f"%{search_query}%")
    ).all()
    return render_template("index.html", restaurants=restaurants)
