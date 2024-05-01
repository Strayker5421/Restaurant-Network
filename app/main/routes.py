from flask import jsonify, request, render_template, send_from_directory, abort
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
def show_menus(restaurant_id):
    restaurant = Restaurant.query.get(restaurant_id)
    menus = restaurant.menus.all()
    return render_template("menus.html", restaurant=restaurant, menus=menus)


@bp.route("/menu_template")
def menu_template():
    menu_name = request.args.get("menu_name", None)
    if menu_name is None:
        abort(400, description="Menu name is not provided")

    menu = Menu.query.filter_by(name=menu_name).first()
    if menu is None:
        abort(404, description="Menu not found")

    return render_template("_menu.html", menu=menu)


@bp.route("/search", methods=["GET"])
def search():
    search_query = request.args.get("q", "")
    restaurants = Restaurant.query.filter(
        Restaurant.name.ilike(f"%{search_query}%")
    ).all()
    return render_template("index.html", restaurants=restaurants)
