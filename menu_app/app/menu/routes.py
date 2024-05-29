from flask import jsonify, request, render_template, url_for, redirect, flash
from app.menu.forms import LoginForm
from app import db
from app.models import Dish
from app.menu import bp
from sqlalchemy import or_
from werkzeug.utils import secure_filename
import os
from docker import DockerClient
from docker.errors import NotFound


@bp.route("/<restaurant_name>/menu/<menu_name>", methods=["GET", "POST"])
def show_menu(menu_name):
    menu_name = menu_name.replace(" ", "-").lower()
    dishes = Dish.query.all()
    return render_template("single_menu.html", menu_name=menu_name, dishes=dishes)


@bp.route("/menu/<menu_name>/admin", methods=["POST", "GET"])
def show_menu_admin(menu_name):
    return redirect(
        f"http://0.0.0.0:8081/login/admin?next=http://0.0.0.0:8082/menu/{menu_name}/admin"
    )


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


@bp.route("/add_dish", methods=["POST"])
def add_dish():
    try:
        dish_name = request.form.get("DishItemName")
        dish_price = request.form.get("DishItemPrice")
        menu_id = request.form.get("DishIdForMenu")
        dish_image = request.files.get("DishItemImageURL")
        dish_ingredients = request.form.get("DishItemIngredients")
        dishSection = request.form.get("DishSection")
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
            section=dishSection,
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


import logging


@bp.route("/change_menu_name", methods=["POST"])
def change_menu_name():
    try:
        data = request.json
        menu_id = data.get("MenuId")
        new_name = data.get("NewMenuName")

        logging.info(f"Changing menu name. Menu ID: {menu_id}, New Name: {new_name}")

        menu = Menu.query.get(menu_id)
        if not menu:
            logging.error(f"Menu with ID {menu_id} not found")
            return jsonify({"error": f"Menu with id {menu_id} not found"}), 404

        menu.name = new_name
        db.session.commit()

        logging.info("Menu name changed successfully")

        return jsonify({"message": "Menu name changed successfully"})

    except Exception as e:
        logging.exception("An unexpected error occurred")
        return jsonify({"error": "An unexpected error occurred"}), 500


@bp.route("/change_menu_image", methods=["POST"])
def change_menu_image():
    try:
        MenuIdToModify = request.form.get("MenuIdToModifyTemplate")
        NewMenuImage = request.files["NewMenuImage"]

        menu = Menu.query.get(MenuIdToModify)
        if not menu:
            error_message = f"Menu with ID {MenuIdToModify} not found"
            return jsonify({"error": error_message}), 404

        # Путь к текущему изображению меню
        current_image_path = os.path.join(
            "app", "static", "images", "menu_templates", f"{menu.name}.jpg"
        )

        # Удаляем текущее изображение, если оно существует
        if os.path.exists(current_image_path):
            os.remove(current_image_path)

        # Сохраняем новое изображение в папке menu_templates с тем же именем, что и у текущего меню
        NewMenuImage.save(current_image_path)

        return jsonify({"message": "Menu image changed successfully"})
    except Exception as e:
        error_message = f"Error changing menu image: {str(e)}"
        return jsonify({"error": error_message}), 500


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
