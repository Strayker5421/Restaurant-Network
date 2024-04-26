from flask import jsonify, request, render_template
from flask_login import current_user, login_required
from app import db
from app.models import User, Menu, Restaurant
from app.main import bp
import logging


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    return "Hello, World!"


@bp.route("/administrator", methods=["POST", "GET"])
def administrator():
    return render_template("administrator.html")


@bp.route("/delete_all_data", methods=["POST"])
def delete_all_data():
    try:
        # Удаление данных из каждой таблицы
        db.session.query(User).delete()
        db.session.query(Menu).delete()
        db.session.query(Restaurant).delete()
        db.session.commit()
        return jsonify({"message": "All data successfully deleted from all tables"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/delete_menu_item", methods=["POST"])
def delete_menu_item():
    try:
        data = request.json
        menu_item_id = data.get("MenuItemId")

        menu_item = Menu.query.get(menu_item_id)

        db.session.delete(menu_item)
        db.session.commit()

        logging.info(f"Menu item {menu_item} deleted successfully.")
        return jsonify({"message": "Menu item deleted successfully"})

    except Exception as e:
        # Логируем ошибку
        logging.error(f"Error deleting menu item: {str(e)}")
        # Возвращаем более информативный JSON-ответ
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@bp.route("/delete_all_menu_item", methods=["POST"])
def delete_all_menu_item():
    try:
        menu_item = Menu.query.all()

        db.session.delete(menu_item)
        db.session.commit()

        logging.info("All menu item deleted successfully.")
        return jsonify({"message": "All menu item deleted successfully"})
    except Exception as e:
        # Логируем ошибку
        logging.error(f"Error deleting all menu item: {str(e)}")
        # Возвращаем более информативный JSON-ответ
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@bp.route("/change_status_restaurant", methods=["POST"])
def change_status_restaurant():
    try:
        data = request.json

        Restaurant_id = data["RestaurantId"]
        new_status = data["newStatus"]

        Restaurant = Restaurant.query.get(Restaurant_id)
        if not Restaurant:
            return (
                jsonify({"error": f"Restaurant with id {Restaurant_id} not found"}),
                404,
            )

        Restaurant.status = new_status
        db.session.commit()

        return jsonify({"message": "Restaurant status changed successfully"})
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@bp.route("/delete_restaurant", methods=["POST"])
def delete_restaurant():
    data = request.json
    Restaurant_id = data.get("RestaurantId")

    Restaurant = Restaurant.query.get(Restaurant_id)
    if Restaurant:
        # Удаляем связные меню
        related_menu_items = Menu.query.filter_by(Menu_id=Restaurant.id).all()
        for related_menu_item in related_menu_items:
            db.session.delete(related_menu_item)
        db.session.delete(Restaurant)
        db.session.commit()
        return jsonify({"message": "Restaurant deleted successfully"})
    else:
        return jsonify({"error": "Restaurant not found"}), 404


@bp.route("/delete_all_restaurants", methods=["POST"])
def delete_all_restaurants():
    Restaurants = Restaurant.query.all()
    for Restaurant in Restaurants:
        db.session.delete(Restaurant)
    db.session.commit()
    return jsonify({"message": "All restaurants deleted successfully"})


@bp.route("/add_restaurant", methods=["POST"])
def add_restaurant():
    try:
        data = request.json

        # Извлекаем данные из запроса
        Restaurant_name = data.get("Restaurant_name")
        Image = data.get("Image")
        Status = data.get("Status")

        existing_reastaurant = Restaurant.query.filter_by(name=Restaurant_name).first()

        if existing_reastaurant:
            # Если запись существует, используем её product_id
            reastaurant_id = existing_reastaurant.id
        else:
            # Если записи нет, создаем новую
            new_Restaurant = Restaurant(
                name=Restaurant_name, image=Image, Status=Status
            )
            db.session.add(new_Restaurant)
            db.session.commit()
            # Получаем product_id после вставки новой записи
            reastaurant_id = new_Restaurant.id

        return jsonify(
            {
                "message": "Restaurant added successfully",
                "new_Restaurant_id": reastaurant_id,
            }
        )
    except Exception as e:
        # Логируем ошибку
        logging.error(f"Error adding Restaurant: {str(e)}")
        # Возвращаем более информативный JSON-ответ
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@bp.route("/add_menu_item", methods=["POST"])
def add_menu_item():
    try:
        data = request.json

        # Извлекаем данные из запроса
        MenuItemName = data.get("MenuItemName")
        MenuItemPrice = data.get("MenuItemPrice")
        MenuIdForRestaurant = data.get("MenuIdForRestaurant")
        backImageModelURL = data.get("backImageModelURL")
        Status = data.get("Status")

        existing_Restaurant = Restaurant.query.get(MenuIdForRestaurant)

        if not existing_Restaurant:
            return jsonify({"error": "Restaurant not found"}), 404

        # Создаем новую запись в Menu
        new_menu = Menu(
            id=MenuIdForRestaurant,
            name=MenuItemName,
            image=backImageModelURL,
            price=MenuItemPrice,
            status=Status,
        )
        db.session.add(new_menu)
        db.session.commit()

        return jsonify({"message": "Menu added successfully"})
    except Exception as e:
        # Логируем ошибку
        logging.error(f"Error adding menu: {str(e)}")
        # Возвращаем более информативный JSON-ответ
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@bp.route("/change_price_item", methods=["POST"])
def change_price_item():
    MenuIdForRestaurant = request.json.get("MenuIdForRestaurant")
    MenuItemIdToModify = request.json.get("MenuItemIdToModify")
    MenuItemPrice = request.json.get("MenuItemPrice")

    Restaurant = Restaurant.query.get(MenuIdForRestaurant)

    if Restaurant:
        Menu_item = Menu.query.get(MenuItemIdToModify)

        if Menu_item:
            Menu.price = MenuItemPrice
            db.session.commit()

            return jsonify({"message": "Menu price modified successfully"}), 200

        return jsonify({"error": "Menu item not found"}), 404

    return jsonify({"error": "Restaurant not found"}), 404
