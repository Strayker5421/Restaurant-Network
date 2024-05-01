from flask import jsonify, request, render_template, url_for
from flask_login import current_user, login_required
from app import db
from app.models import User, Menu, Restaurant, Dish
from app.admin import bp
from sqlalchemy import or_, cast, and_
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

        dishes = Dish.query.all()
        for dish in dishes:
            if dish.image:
                full_image_path = os.path.join("app", dish.image[1:])
                if os.path.exists(full_image_path):
                    os.remove(full_image_path)
            db.session.delete(dish)

        db.session.query(Menu).delete()

        restaurants = Restaurant.query.all()
        for restaurant in restaurants:
            for image in restaurant.images:
                full_path = os.path.join("app", image[1:])
                if os.path.exists(full_path):
                    os.remove(full_path)
            db.session.delete(restaurant)

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

        if dish.image:
            full_image_path = os.path.join("app", dish.image[1:])
            if os.path.exists(full_image_path):
                os.remove(full_image_path)

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
            if dish.image:
                full_image_path = os.path.join("app", dish.image[1:])
                if os.path.exists(full_image_path):
                    os.remove(full_image_path)

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

        if new_status.lower() == "open":
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
        restaurant_id = data.get("RestaurantId")
        restaurant_to_delete = Restaurant.query.get(restaurant_id)
        if restaurant_to_delete:
            image_paths = restaurant_to_delete.images

            for path in image_paths:
                full_path = os.path.join("app", path[1:])
                if os.path.exists(full_path):
                    os.remove(full_path)

            related_menus = Menu.query.filter_by(restaurant_id=restaurant_id).all()

            for menu in related_menus:
                related_dishes = Dish.query.filter_by(menu_id=menu.id).all()
                for dish in related_dishes:
                    if dish.image:
                        full_image_path = os.path.join("app", dish.image[1:])
                        if os.path.exists(full_image_path):
                            os.remove(full_image_path)
                    db.session.delete(dish)
                db.session.delete(menu)

            db.session.delete(restaurant_to_delete)
            db.session.commit()

            return jsonify({"message": "Restaurant deleted successfully"})
        else:
            return jsonify({"error": "Restaurant not found"}), 404

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


@bp.route("/delete_all_restaurants", methods=["POST"])
def delete_all_restaurants():
    try:
        restaurants = Restaurant.query.all()

        for restaurant_delete in restaurants:
            image_paths = restaurant_delete.images

            for path in image_paths:
                full_path = os.path.join("app", path[1:])
                if os.path.exists(full_path):
                    os.remove(full_path)

            related_menus = Menu.query.filter_by(
                restaurant_id=restaurant_delete.id
            ).all()

            for menu in related_menus:
                related_dishes = Dish.query.filter_by(menu_id=menu.id).all()
                for dish in related_dishes:
                    if dish.image:
                        full_image_path = os.path.join("app", dish.image[1:])
                        if os.path.exists(full_image_path):
                            os.remove(full_image_path)
                    db.session.delete(dish)
                db.session.delete(menu)

            db.session.delete(restaurant_delete)

        db.session.commit()

        return jsonify({"message": "All restaurants deleted successfully"})

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


@bp.route("/change_restaurant_name", methods=["POST"])
def change_restaurant_name():
    try:
        data = request.json
        restaurant_id = data.get("RestaurantId")
        new_name = data.get("newRestaurantName")

        restaurant = Restaurant.query.get(restaurant_id)

        if not restaurant:
            return (
                jsonify({"error": f"Restaurant with id {restaurant_id} not found"}),
                404,
            )

        restaurant.name = new_name
        db.session.commit()

        return jsonify({"message": "Restaurant name changed successfully"})

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


@bp.route("/change_restaurant_image", methods=["POST"])
def change_restaurant_image():
    try:
        restaurant_id = request.form.get("RestaurantId")
        new_images = request.files.getlist("NewRestaurantImage")

        restaurant = Restaurant.query.get(restaurant_id)

        if not restaurant:
            return (
                jsonify({"error": f"Restaurant with id {restaurant_id} not found"}),
                404,
            )

        if new_images:
            old_image_paths = restaurant.images
            print("Old Image Paths:", old_image_paths)
            deleted_paths = []
            for old_image_path in old_image_paths:
                old_image_path = f"app{old_image_path}"
                if os.path.isfile(old_image_path):
                    try:
                        os.remove(old_image_path)
                        deleted_paths.append(old_image_path)
                    except Exception as e:
                        print(f"Error deleting file {old_image_path}: {e}")
                else:
                    print(f"File not found: {old_image_path}")
            print("Deleted Paths:", deleted_paths)

            new_images_paths = save_image(new_images, "restaurants/")
            restaurant.images = new_images_paths
            db.session.commit()

            return jsonify({"message": "Restaurant images changed successfully"}), 200
        else:
            return jsonify({"error": "No images provided"}), 400

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


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
    if isinstance(images, list):
        for image in images:
            filename = secure_filename(image.filename)
            image.save("app/static/images/" + path + filename)
            images_paths.append(url_for("static", filename="images/" + path + filename))
    else:
        filename = secure_filename(images.filename)
        images.save("app/static/images/" + path + filename)
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

        image_path = save_image(dish_image, "dishes/")[0]

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
        new_image_path = save_image(new_image, "dishes/")[0]
        old_image_path = dish.image
        old_image_path = f"app{old_image_path}"
        if os.path.isfile(old_image_path):
            os.remove(old_image_path)

        dish.image = new_image_path
        db.session.commit()

        return jsonify({"message": "Dish image modified successfully"}), 200

    return jsonify({"error": "Dish not found or new image not provided"}), 404


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


@bp.route("/change_menu_name", methods=["POST"])
def change_menu_name():
    try:
        data = request.json
        menu_id = data.get("MenuId")
        new_name = data.get("NewMenuName")

        menu = Menu.query.get(menu_id)
        if not menu:
            return jsonify({"error": f"Menu with id {menu_id} not found"}), 404

        menu.name = new_name
        db.session.commit()

        return jsonify({"message": "Menu name changed successfully"})

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500


@bp.route("/delete_menu", methods=["POST"])
def delete_menu():
    try:
        data = request.json
        menu_id = data.get("MenuIdToDelete")

        menu = Menu.query.get(menu_id)

        if not menu:
            return jsonify({"error": "Menu not found"}), 404

        related_dishes = Dish.query.filter_by(menu_id=menu.id).all()

        for dish in related_dishes:
            if dish.image:
                full_image_path = os.path.join("app", dish.image[1:])
                if os.path.exists(full_image_path):
                    os.remove(full_image_path)
            db.session.delete(dish)

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
            related_dishes = Dish.query.filter_by(menu_id=menu.id).all()

            for dish in related_dishes:
                if dish.image:
                    full_image_path = os.path.join("app", dish.image[1:])
                    if os.path.exists(full_image_path):
                        os.remove(full_image_path)
                db.session.delete(dish)

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

        restaurant_data = [
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "image": restaurant.images,
                "status": restaurant.status,
            }
            for restaurant in restaurants
        ]

        return restaurant_data
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
    return restaurants_data


@bp.route("/fetch_menus/<int:restaurant_id>", methods=["GET"])
def fetch_menus(restaurant_id):
    try:
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return {"error": f"Ресторан с id {restaurant_id} не найден"}

        menus = restaurant.menus.all()
        menu_data = []
        for menu in menus:
            data = {"id": menu.id, "name": menu.name, "status": menu.status}
            menu_data.append(data)
        return jsonify(menu_data)
    except Exception as e:
        return {"error": str(e)}


@bp.route("/search_menus")
def search_menus():
    try:
        search_query = request.args.get("search_query", "")
        restaurant_id = request.args.get("restaurant_id", "")
        menus = search_menus_by_query(search_query, restaurant_id)
        menu_data = [
            {
                "id": menu.id,
                "name": menu.name,
                "status": menu.status,
            }
            for menu in menus
        ]

        return menu_data

    except Exception as e:
        return jsonify({"error": str(e)})


def search_dishes_by_query(search_query, menu_id=None):
    try:
        query = Dish.query

        if menu_id:
            menu = Menu.query.get(menu_id)
            if not menu:
                return []
            query = query.filter(Dish.menu_id == menu_id)

        if search_query.isdigit():
            query = query.filter(
                or_(Dish.id == int(search_query), Dish.price == float(search_query))
            )
        else:
            query = query.filter(
                or_(
                    Dish.name.ilike(f"%{search_query}%"),
                    Dish.ingredients.ilike(f"%{search_query}%"),
                )
            )

        return query.order_by(Dish.id).all()
    except Exception as e:
        return []


def search_menus_by_query(search_query, restaurant_id):
    try:
        query = Menu.query
        if restaurant_id:
            restaurant = Restaurant.query.get(restaurant_id)
            if not restaurant:
                return []

        if search_query.lower() in ("true", "false"):
            query = Menu.query.filter(Menu.status == (search_query.lower() == "true"))
        else:
            if search_query.isdigit():
                query = query.filter(Menu.id == int(search_query))
            else:
                query = Menu.query.filter(
                    Menu.name.ilike(f"%{search_query}%"),
                    Menu.restaurant_id == restaurant_id,
                ).all()

        return query

    except Exception as e:
        return []


@bp.route("/search_dishes")
def search_dishes():
    try:
        search_query = request.args.get("search_query", "")
        menu_id = request.args.get("menu_id", None)

        dishes = search_dishes_by_query(search_query, menu_id)
        dish_data = [
            {
                "id": dish.id,
                "name": dish.name,
                "price": dish.price,
                "ingredients": dish.ingredients,
                "image": dish.image,
            }
            for dish in dishes
        ]

        return dish_data

    except Exception as e:
        return jsonify({"error": str(e)})


@bp.route("/fetch_dishes/<int:menu_id>", methods=["GET"])
def fetch_dishes(menu_id):
    try:
        menu = Menu.query.get(menu_id)
        if not menu:
            return []

        dishes = menu.dishes.all()
        dish_data = [
            {
                "id": dish.id,
                "name": dish.name,
                "price": dish.price,
                "ingredients": dish.ingredients,
                "image": dish.image,
            }
            for dish in dishes
        ]
        return dish_data
    except Exception as e:
        return {"error": str(e)}
