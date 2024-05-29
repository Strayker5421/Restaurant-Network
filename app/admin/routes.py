from flask import jsonify, request, render_template, url_for
from flask_login import current_user, login_required
from app import db
from app.models import User, Menu, Restaurant
from app.admin import bp
from sqlalchemy import or_, cast, and_
from sqlalchemy.types import String
from werkzeug.utils import secure_filename
import os, qrcode, pytz
from datetime import datetime, timedelta


@bp.route("/administrator", methods=["POST", "GET"])
def administrator():
    return render_template("administrator.html")


@bp.route("/delete_all_data", methods=["POST"])
def delete_all_data():
    try:
        db.session.query(User).delete()

        menus = Menu.query.all()
        for menu in menus:
            qr_code_dir_menu = os.path.join(
                "app", "static", "images", "qr_code", "menus"
            )
            menu_qr_filename = f"{menu.name}_qr_code.png"
            full_image_path_menu = os.path.join(qr_code_dir_menu, menu_qr_filename)
            if os.path.exists(full_image_path_menu):
                os.remove(full_image_path_menu)
            db.session.delete(menu)

        restaurants = Restaurant.query.all()
        for restaurant in restaurants:
            qr_code_dir_restaurant = os.path.join(
                "app", "static", "images", "qr_code", "restaurants"
            )
            for filename in os.listdir(qr_code_dir_restaurant):
                if filename.startswith(restaurant.name):
                    full_image_path = os.path.join(qr_code_dir_restaurant, filename)
                    if os.path.exists(full_image_path):
                        os.remove(full_image_path)

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

            qr_code_dir_restaurant = os.path.join(
                "app", "static", "images", "qr_code", "restaurants"
            )
            for filename in os.listdir(qr_code_dir_restaurant):
                if filename.startswith(restaurant_to_delete.name):
                    full_image_path = os.path.join(qr_code_dir_restaurant, filename)
                    if os.path.exists(full_image_path):
                        os.remove(full_image_path)

            related_menus = Menu.query.filter_by(restaurant_id=restaurant_id).all()
            for menu in related_menus:
                qr_code_dir_menu = os.path.join(
                    "app", "static", "images", "qr_code", "menus"
                )
                menu_qr_filename = f"{menu.name}_qr_code.png"
                full_image_path_menu = os.path.join(qr_code_dir_menu, menu_qr_filename)
                if os.path.exists(full_image_path_menu):
                    os.remove(full_image_path_menu)

                db.session.delete(menu)

            db.session.delete(restaurant_to_delete)
            db.session.commit()

            return jsonify({"message": "Restaurant deleted successfully"})
        else:
            return jsonify({"error": "Restaurant not found"}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


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

            qr_code_dir_restaurant = os.path.join(
                "app", "static", "images", "qr_code", "restaurants"
            )
            for filename in os.listdir(qr_code_dir_restaurant):
                if filename.startswith(restaurant_delete.name):
                    full_image_path = os.path.join(qr_code_dir_restaurant, filename)
                    if os.path.exists(full_image_path):
                        os.remove(full_image_path)

            related_menus = Menu.query.filter_by(
                restaurant_id=restaurant_delete.id
            ).all()
            for menu in related_menus:
                qr_code_dir_menu = os.path.join(
                    "app", "static", "images", "qr_code", "menus"
                )
                menu_qr_filename = f"{menu.name}_qr_code.png"
                full_image_path_menu = os.path.join(qr_code_dir_menu, menu_qr_filename)
                if os.path.exists(full_image_path_menu):
                    os.remove(full_image_path_menu)

                db.session.delete(menu)

            db.session.delete(restaurant_delete)

        db.session.commit()

        return jsonify({"message": "All restaurants deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@bp.route("/delete_all_restaurants_user/<int:user_id>", methods=["POST"])
def delete_all_restaurants_user(user_id):
    try:
        restaurants = Restaurant.query.filter_by(user_id=user_id).all()

        for restaurant_delete in restaurants:
            image_paths = restaurant_delete.images
            for path in image_paths:
                full_path = os.path.join("app", path[1:])
                if os.path.exists(full_path):
                    os.remove(full_path)

            qr_code_dir_restaurant = os.path.join(
                "app", "static", "images", "qr_code", "restaurants"
            )
            for filename in os.listdir(qr_code_dir_restaurant):
                if filename.startswith(restaurant_delete.name):
                    full_image_path = os.path.join(qr_code_dir_restaurant, filename)
                    if os.path.exists(full_image_path):
                        os.remove(full_image_path)

            related_menus = Menu.query.filter_by(
                restaurant_id=restaurant_delete.id
            ).all()
            for menu in related_menus:
                qr_code_dir_menu = os.path.join(
                    "app", "static", "images", "qr_code", "menus"
                )
                menu_qr_filename = f"{menu.name}_qr_code.png"
                full_image_path_menu = os.path.join(qr_code_dir_menu, menu_qr_filename)
                if os.path.exists(full_image_path_menu):
                    os.remove(full_image_path_menu)

                db.session.delete(menu)

            db.session.delete(restaurant_delete)

        db.session.commit()

        return jsonify(
            {"message": f"All restaurants for user {user_id} deleted successfully"}
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


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


def generate_and_save_qr_code(id, name, source, restaurant_name=None):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        if source == "menu":
            qr.add_data(f"http://{restaurant_name}.{name}.172.20.10.8.xip.io")
            save_path = os.path.join("app", "static", "images", "qr_code", "menus")
        elif source == "restaurant":
            qr.add_data(f"http://{name}.172.20.10.8.xip.io")
            save_path = os.path.join(
                "app", "static", "images", "qr_code", "restaurants"
            )
        else:
            raise ValueError("Invalid source specified")

        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")

        if not os.path.exists(save_path):
            os.makedirs(save_path)

        filename = f"{name}_qr_code.png"
        qr_image.save(os.path.join(save_path, filename))

        qr_image_path = url_for(
            "static", filename=f"images/qr_code/{source}s/{filename}"
        )

        return qr_image_path
    except Exception as e:
        return None


@bp.route("/add_restaurant", methods=["POST"])
def add_restaurant():
    try:
        restaurant_name = request.form.get("RestaurantName")
        status = request.form.get("Status")
        user_id = request.form.get("UserID")
        images = request.files.getlist("RestaurantImage")

        status_bool = True if status == "Open" else False

        existing_restaurant = Restaurant.query.filter_by(name=restaurant_name).first()

        if existing_restaurant:
            return jsonify({"error": "Restaurant already exists"}), 404

        existing_user = User.query.filter_by(id=user_id).first()

        if not existing_user:
            return jsonify({"error": "User doesn't exist"}), 404

        images_paths = save_image(images, "restaurants/")
        new_restaurant = Restaurant(
            name=restaurant_name,
            images=images_paths,
            status=status_bool,
            user_id=user_id,
        )
        db.session.add(new_restaurant)
        db.session.commit()

        qr_image_path = generate_and_save_qr_code(
            new_restaurant.id, new_restaurant.name, "restaurant"
        )

        if qr_image_path:
            return jsonify(
                {
                    "message": "Restaurant added successfully",
                    "new_restaurant_id": new_restaurant.id,
                    "qr_code_path": qr_image_path,
                }
            )
        else:
            return jsonify({"error": "Failed to generate QR code"}), 500
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
            for restaurant in user_to_delete.restaurants:
                qr_code_dir_restaurant = os.path.join(
                    "app", "static", "images", "qr_code", "restaurants"
                )
                for filename in os.listdir(qr_code_dir_restaurant):
                    if filename.startswith(restaurant.name):
                        full_image_path = os.path.join(qr_code_dir_restaurant, filename)
                        if os.path.exists(full_image_path):
                            os.remove(full_image_path)

                for image in restaurant.images:
                    full_path = os.path.join("app", image[1:])
                    if os.path.exists(full_path):
                        os.remove(full_path)

                for menu in restaurant.menus:
                    qr_code_dir_menu = os.path.join(
                        "app", "static", "images", "qr_code", "menus"
                    )
                    menu_qr_filename = f"{menu.name}_qr_code.png"
                    full_image_path_menu = os.path.join(
                        qr_code_dir_menu, menu_qr_filename
                    )
                    if os.path.exists(full_image_path_menu):
                        os.remove(full_image_path_menu)

                    for dish in menu.dishes:
                        if dish.image:
                            full_image_path_dish = os.path.join("app", dish.image[1:])
                            if os.path.exists(full_image_path_dish):
                                os.remove(full_image_path_dish)
                        db.session.delete(dish)
                    db.session.delete(menu)
                db.session.delete(restaurant)

            db.session.delete(user_to_delete)
            db.session.commit()
            return jsonify(
                {"message": "User and all related data deleted successfully"}
            )
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/add_menu", methods=["POST"])
def add_menu():
    try:
        data = (
            request.form
        )  # Изменено на request.form для обработки multipart/form-data

        menu_name = data.get("MenuName")
        subscription_length = data.get("SubscriptionLength")
        restaurant_id = data.get("RestaurantIdForMenu")

        if "menuTemplateImage" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["menuTemplateImage"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        existing_restaurant = Restaurant.query.get(restaurant_id)
        if not existing_restaurant:
            return jsonify({"error": "Restaurant not found"}), 404

        expiration_date = None
        if subscription_length and subscription_length != "None":
            moscow_tz = pytz.timezone("Europe/Moscow")
            current_time_moscow = datetime.now(moscow_tz)
            expiration_date = current_time_moscow + {
                "5 minutes": timedelta(minutes=5),
                "1 hour": timedelta(hours=1),
                "1 day": timedelta(days=1),
            }.get(subscription_length, timedelta(0))

        new_menu = Menu(
            name=menu_name,
            status=expiration_date is not None,
            expiration_date=expiration_date,
            restaurant_id=restaurant_id,
        )
        db.session.add(new_menu)
        db.session.commit()

        qr_image_path = generate_and_save_qr_code(
            new_menu.id, new_menu.name, "menu", existing_restaurant.name
        )

        try:
            file_path = os.path.join(
                "app", "static", "images", "menu_templates", f"{new_menu.name}.png"
            )
            file.save(file_path)
        except Exception as file_save_error:
            return jsonify({"error": "Failed to save file"}), 500

        if qr_image_path:
            return jsonify(
                {
                    "message": "Menu added successfully",
                    "new_menu_id": new_menu.id,
                    "qr_code_path": qr_image_path,
                }
            )
        else:
            return jsonify({"error": "Failed to generate QR code"}), 500
    except Exception as e:
        db.session.rollback()
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

        qr_code_dir_menu = os.path.join("app", "static", "images", "qr_code", "menus")
        menu_qr_filename = f"{menu.name}_qr_code.png"
        full_image_path_menu = os.path.join(qr_code_dir_menu, menu_qr_filename)
        if os.path.exists(full_image_path_menu):
            os.remove(full_image_path_menu)

        db.session.delete(menu)
        db.session.commit()

        return jsonify({"message": "Menu deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@bp.route("/delete_all_menu", methods=["POST"])
def delete_all_menu():
    try:
        menus = Menu.query.all()

        for menu in menus:
            qr_code_dir_menu = os.path.join(
                "app", "static", "images", "qr_code", "menus"
            )
            menu_qr_filename = f"{menu.name}_qr_code.png"
            full_image_path_menu = os.path.join(qr_code_dir_menu, menu_qr_filename)
            if os.path.exists(full_image_path_menu):
                os.remove(full_image_path_menu)

            db.session.delete(menu)

        db.session.commit()

        return jsonify({"message": "All menu deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@bp.route("/delete_all_menu_for_restaurant", methods=["POST"])
def delete_all_menu_for_restaurant():
    try:
        data = request.json
        restaurant_id = data.get("restaurant_id")

        menus = Menu.query.filter_by(restaurant_id=restaurant_id).all()

        for menu in menus:
            qr_code_dir_menu = os.path.join(
                "app", "static", "images", "qr_code", "menus"
            )
            menu_qr_filename = f"{menu.name}_qr_code.png"
            full_image_path_menu = os.path.join(qr_code_dir_menu, menu_qr_filename)
            if os.path.exists(full_image_path_menu):
                os.remove(full_image_path_menu)

            db.session.delete(menu)

        db.session.commit()

        return jsonify({"message": "All menus for the restaurant deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@bp.route("/delete_all_menu_for_user", methods=["POST"])
def delete_all_menu_for_user():
    try:
        data = request.json
        user_id = data.get("user_id")

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        restaurants = user.restaurants

        for restaurant in restaurants:
            menus = Menu.query.filter_by(restaurant_id=restaurant.id).all()
            for menu in menus:
                qr_code_dir_menu = os.path.join(
                    "app", "static", "images", "qr_code", "menus"
                )
                menu_qr_filename = f"{menu.name}_qr_code.png"
                full_image_path_menu = os.path.join(qr_code_dir_menu, menu_qr_filename)
                if os.path.exists(full_image_path_menu):
                    os.remove(full_image_path_menu)

                db.session.delete(menu)

        db.session.commit()

        return jsonify({"message": "All menus for the user deleted successfully"})
    except Exception as e:
        db.session.rollback()
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


@bp.route("/fetch_restaurants/<int:user_id>", methods=["GET"])
def fetch_restaurants(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        restaurants = user.restaurants.order_by(Restaurant.id).all()

        restaurant_data = [
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "image": restaurant.images,
                "status": restaurant.status,
            }
            for restaurant in restaurants
        ]

        return jsonify(restaurant_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_restaurant_by_search_query(search_query, user_id):
    user = User.query.get(user_id)
    if not user:
        return []

    if (
        search_query == "true"
        or search_query == "false"
        or search_query == "True"
        or search_query == "False"
    ):
        query = user.restaurants.filter(cast(Restaurant.status, String) == search_query)
    else:
        query = user.restaurants.filter(
            or_(
                Restaurant.name.ilike(f"%{search_query}%"),
                cast(Restaurant.id, String).ilike(f"%{search_query}%"),
            )
        )

    return query.order_by(Restaurant.id).all()


@bp.route("/search_restaurants")
def search_restaurants():
    search_query = request.args.get("search_query", "")
    user_id = request.args.get("user_id", "")
    restaurants = get_restaurant_by_search_query(search_query, user_id)

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


@bp.route("/fetch_menus/<int:restaurant_id>", methods=["GET"])
def fetch_menus(restaurant_id):
    try:
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return []

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
