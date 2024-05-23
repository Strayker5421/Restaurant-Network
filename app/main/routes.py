from flask import (
    jsonify,
    request,
    render_template,
    send_from_directory,
    abort,
    url_for,
    session,
    redirect,
    flash,
)
from flask_login import current_user, login_required
from app import db
from app.models import User, Menu, Restaurant
from app.main import bp
from datetime import timedelta, datetime


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    restaurants = current_user.restaurants
    return render_template("index.html", restaurants=restaurants)


@bp.route("/menus/<int:restaurant_id>")
@login_required
def menus_list(restaurant_id):
    restaurant = Restaurant.query.get(restaurant_id)
    menus = restaurant.menus.all()
    return render_template("menus.html", restaurant=restaurant, menus=menus)


@bp.route("/qr_code/<qr_code_type>/<name>")
@login_required
def show_qr_code(qr_code_type, name):
    filename = f"{name}_qr_code.png"
    if qr_code_type == "restaurant":
        qr_code_path = url_for(
            "static", filename=f"images/qr_code/restaurants/{filename}"
        )
    elif qr_code_type == "menu":
        qr_code_path = url_for("static", filename=f"images/qr_code/menus/{filename}")
    else:
        abort(400, description="Invalid type provided")
    return render_template("_show_qr_code.html", qr_code_path=qr_code_path)


@bp.route("/restaurant")
def show_menus():
    restaurant_name = request.args.get("restaurant_name", None)
    if restaurant_name is None:
        abort(400, description="Menu name is not provided")
    restaurant = Restaurant.query.filter_by(name=restaurant_name).first()
    if restaurant is None:
        abort(404, description="Menu not found")
    return render_template("show_menus.html", restaurant=restaurant)


@bp.route("/menu/<int:menu_id>")
def show_menu(menu_id):
    menu = Menu.query.get(menu_id)
    dishes = menu.dishes.all()
    return render_template("_menu_test.html", menu=menu, dishes=dishes)


@bp.route("/menu_template")
def menu_template():
    menu_id = request.args.get("menu_id", None)
    if menu_id is None:
        abort(400, description="Menu name is not provided")

    menu = Menu.query.get(menu_id)
    if menu is None:
        abort(404, description="Menu not found")

    return render_template("_menu.html", menu=menu)


@bp.route("/search", methods=["GET"])
@login_required
def search():
    search_query = request.args.get("q", "")
    restaurants = Restaurant.query.filter(
        Restaurant.name.ilike(f"%{search_query}%")
    ).all()
    return render_template("index.html", restaurants=restaurants)


@bp.route(
    "/extend/<int:restaurant_id>/<int:menu_id>/<int:duration>", methods=["GET", "POST"]
)
@login_required
def extend(restaurant_id, menu_id, duration):
    restaurant = Restaurant.query.get(restaurant_id)
    menu = Menu.query.get(menu_id)
    menu.expiration_date += timedelta(minutes=duration)
    db.session.commit()
    flash("Your subscription extended!")
    return redirect(url_for("main.menus_list", restaurant_id=restaurant.id))


@bp.route(
    "/renew/<int:restaurant_id>/<int:menu_id>/<int:duration>", methods=["GET", "POST"]
)
@login_required
def renew(restaurant_id, menu_id, duration):
    restaurant = Restaurant.query.get(restaurant_id)
    menu = Menu.query.get(menu_id)
    menu.expiration_date = datetime.now() + timedelta(minutes=duration)
    db.session.commit()
    flash("Your subscription renewed!")
    return redirect(url_for("main.menus_list", restaurant_id=restaurant.id))
