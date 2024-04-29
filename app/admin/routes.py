from flask import jsonify, request, render_template, url_for
from flask_login import current_user, login_required
from app import db
from app.models import User, Menu, Restaurant, Dish
from app.admin import bp
from sqlalchemy import or_, cast
from sqlalchemy.types import String
from werkzeug.utils import secure_filename
import os


@bp.route("/administrator", methods=["POST", "GET"])
def administrator():
    return render_template("administrator.html")


@bp.route("/delete_all_data", methods=["POST"])
def delete_all_data():
    try:
        db.session.query(User).delete()
        db.session.query(Menu).delete()
        db.session.query(Restaurant).delete()
        db.session.commit()
        return jsonify({"message": "All data successfully deleted from all tables"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/delete_dish", methods=["POST"])
def delete_dish():
    try:
        data = request.json
        dish_id = data.get("DishIdToDelete")

        dish = Dish.query.get(dish_id)

        if not dish:
            return jsonify({"error": "Dish not found"}), 404

        db.session.delete(dish)
        db.session.commit()

        return jsonify({"message": "Dish deleted successfully"})

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@bp.route("/delete_all_dishes", methods=["POST"])
def delete_all_dishes():
    try:
        dishes = Dish.query.all()
        for dish in dishes:
            db.session.delete(dish)
        db.session.commit()

        return jsonify({"message": "All dish deleted successfully"})
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@bp.route("/change_status_restaurant", methods=["POST"])
def change_status_restaurant():
    try:
        data = request.json
        menu_id = data.get("RestaurantId")
        new_status = data.get("newStatus")

        if new_status.lower() == "Open":
            new_status = True
        else:
            new_status = False

        change_restaurant = Restaurant.query.get(menu_id)
        if not change_restaurant:
            return jsonify({"error": f"Restaurant with id {menu_id} not found"}), 404

        change_restaurant.status = new_status
        db.session.commit()

        return jsonify({"message": "Restaurant status changed successfully"})

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


@bp.route("/delete_restaurant", methods=["POST"])
def delete_restaurant():
    try:
        data = request.json
        menu_id = data.get("RestaurantId")

        restaurant_delete = Restaurant.query.get(menu_id)
        if restaurant_delete:
            related_menu_items = Menu.query.filter_by(id=restaurant_delete.id).all()
            for related_menu_item in related_menu_items:
                db.session.delete(related_menu_item)
            db.session.delete(restaurant_delete)
            db.session.commit()

            return jsonify({"message": "Restaurant deleted successfully"})
        else:
            return jsonify({"error": "Restaurant not found"}), 404

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


@bp.route("/delete_all_restaurants", methods=["POST"])
def delete_all_restaurants():
    Restaurants = Restaurant.query.all()
    for Restaurant_delete in Restaurants:
        db.session.delete(Restaurant_delete)
    db.session.commit()
    return jsonify({"message": "All restaurants deleted successfully"})


@bp.route("/add_restaurant", methods=["POST"])
def add_restaurant():
    try:
        restaurant_name = request.form.get("RestaurantName")
        status = request.form.get("Status")
        images = request.files.getlist("RestaurantImage")

        status_bool = True if status == "Open" else False

        existing_restaurant = Restaurant.query.filter_by(name=restaurant_name).first()

        if existing_restaurant:
            return jsonify({"error": "Restaurant already exists"}), 404

        images_paths = save_image(images, "restaurants/")
        new_restaurant = Restaurant(
            name=restaurant_name, images=images_paths, status=status_bool
        )

        db.session.add(new_restaurant)
        db.session.commit()

        return jsonify(
            {
                "message": "Restaurant added successfully",
                "new_restaurant_id": new_restaurant.id,
            }
        )
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


def save_image(images, path):
    images_paths = []
    for image in images:
        filename = secure_filename(image.filename)
        image.save("app/static/images/" + path + filename)
        images_paths.append(url_for("static", filename="images/" + path + filename))
    return images_paths


@bp.route("/add_dish", methods=["POST"])
def add_dish():
    try:
        dish_name = request.form.get("DishItemName")
        dish_price = request.form.get("DishItemPrice")
        menu_id = request.form.get("DishIdForMenu")
        dish_image = request.files.get("DishItemImageURL")
        dish_ingredients = request.form.get("DishItemIngredients")

        existing_menu = Menu.query.get(menu_id)

        if not existing_menu:
            error_message = "Menu not found"

            return jsonify({"error": error_message}), 404

        image_path = save_image(dish_image, "dishes/")

        new_menu = Dish(
            name=dish_name,
            ingredients=dish_ingredients,
            image=image_path,
            price=dish_price,
            menu_id=menu_id,
        )
        db.session.add(new_menu)
        db.session.commit()

        return jsonify({"message": "Dish added successfully"})
    except Exception as e:
        error_message = f"Internal Server Error: {str(e)}"

        return jsonify({"error": error_message}), 500


@bp.route("/change_price_item", methods=["POST"])
def change_price_item():
    data = request.json
    dish_id = data.get("DishIDToModPrice")
    new_price = data.get("NewDishPrice")

    dish = Dish.query.get(dish_id)

    if dish:
        dish.price = new_price
        db.session.commit()

        return jsonify({"message": "Dish price modified successfully"}), 200

    return jsonify({"error": "Dish not found"}), 404


@bp.route("/add_user", methods=["POST"])
def add_user():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password_hash = data.get("password_hash")
    role = data.get("role")

    role_bool = True if role == "Administrator" else False
    try:
        new_user = User(username=username, email=email, role=role_bool)
        new_user.set_password(password_hash)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User added successfully"})
    except Exception as e:
        error_message = f"Error adding user: {str(e)}"
        return jsonify({"error": error_message}), 500


@bp.route("/delete_user", methods=["POST"])
def delete_user():
    try:
        data = request.json
        user_id = data.get("user_id")

        user_to_delete = User.query.get(user_id)
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
            return jsonify({"message": "User deleted successfully"})
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/change_name_item", methods=["POST"])
def change_name_item():
    data = request.json
    dish_id = data.get("DishIdToModName")
    new_name = data.get("NameToModify")

    dish = Dish.query.get(dish_id)

    if dish:
        dish.name = new_name
        db.session.commit()

        return jsonify({"message": "Dish name modified successfully"}), 200

    return jsonify({"error": "Dish not found"}), 404


@bp.route("/change_ingredients", methods=["POST"])
def change_ingredients():
    data = request.json
    dish_id = data.get("DishIDToModIngredients")
    new_ingredients = data.get("NewDishIngredients")

    dish = Dish.query.get(dish_id)

    if dish:
        dish.ingredients = new_ingredients
        db.session.commit()

        return jsonify({"message": "Ingredients modified successfully"}), 200

    return jsonify({"error": "Dish not found"}), 404


@bp.route("/change_image_item", methods=["POST"])
def change_image_item():
    dish_id = request.form.get("DishIdToModImage")
    new_image = request.files.get("DishImageChangeURL")

    dish = Dish.query.get(dish_id)

    if dish and new_image:
        new_image_path = save_image(new_image, "dishes/")
        old_image_path = dish.image  # old_image_path = "app/" + dish.image
        if os.path.isfile(old_image_path):
            os.remove(old_image_path)

        dish.image = new_image_path
        db.session.commit()

        return jsonify({"message": "Dish image modified successfully"}), 200

    return jsonify({"error": "Dish not found"}), 404


@bp.route("/add_menu", methods=["POST"])
def add_menu():
    try:
        data = request.json

        menu_name = data.get("MenuName")
        status = data.get("Status")
        restaurant_id = data.get("RestaurantIdForMenu")
        status_bool = True if status == "Active" else False

        existing_restaurant = Restaurant.query.get(restaurant_id)

        if not existing_restaurant:
            error_message = "Restaurant not found"

            return jsonify({"error": error_message}), 404

        new_menu = Menu(name=menu_name, status=status_bool, restaurant_id=restaurant_id)
        db.session.add(new_menu)
        db.session.commit()

        return jsonify({"message": "Dish added successfully"})
    except Exception as e:
        error_message = f"Internal Server Error: {str(e)}"

        return jsonify({"error": error_message}), 500


@bp.route("/delete_menu", methods=["POST"])
def delete_menu():
    try:
        data = request.json
        menu_id = data.get("MenuIdToDelete")

        menu = Menu.query.get(menu_id)

        if not menu:
            return jsonify({"error": "Menu not found"}), 404

        db.session.delete(menu)
        db.session.commit()

        return jsonify({"message": "Menu deleted successfully"})

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@bp.route("/delete_all_menu", methods=["POST"])
def delete_all_menu():
    try:
        menus = Menu.query.all()

        for menu in menus:
            db.session.delete(menu)
        db.session.commit()

        return jsonify({"message": "All menu deleted successfully"})
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@bp.route("/change_status_menu", methods=["POST"])
def change_status_menu():
    try:
        data = request.json
        menu_id = data.get("MenuId")
        new_status = data.get("newStatus")
        if new_status.lower() == "active":
            new_status = True
        else:
            new_status = False

        change_menu = Menu.query.get(menu_id)
        if not change_menu:
            return jsonify({"error": f"Menu with id {menu_id} not found"}), 404

        change_menu.status = new_status
        db.session.commit()

        return jsonify({"message": "Menu status changed successfully"})

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


@bp.route("/fetch_restaurants", methods=["GET"])
def fetch_restaurants():
    try:
        restaurants = Restaurant.query.order_by(Restaurant.id).all()

        Restaurant_data = []
        for restaurant in restaurants:
            restaurant_data = {
                "id": restaurant.id,
                "name": restaurant.name,
                "image": restaurant.images,
                "status": restaurant.status,
            }
            Restaurant_data.append(restaurant_data)

        return jsonify(Restaurant_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_restaurant_by_search_query(search_query):
    if (
        search_query == "true"
        or search_query == "false"
        or search_query == "True"
        or search_query == "False"
    ):
        query = Restaurant.query.filter(cast(Restaurant.status, String) == search_query)
    else:
        query = Restaurant.query.filter(
            or_(
                Restaurant.name.ilike(f"%{search_query}%"),
                cast(Restaurant.id, String).ilike(f"%{search_query}%"),
            )
        )

    return query.order_by(Restaurant.id).all()


@bp.route("/search_restaurants")
def search_restaurants():
    search_query = request.args.get("search_query", "")
    restaurants = get_restaurant_by_search_query(search_query)

    restaurants_data = [
        {
            "id": restaurant.id,
            "name": restaurant.name,
            "image": restaurant.images,
            "status": restaurant.status,
        }
        for restaurant in restaurants
    ]
    return jsonify(restaurants_data)
