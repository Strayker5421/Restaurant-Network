from flask import jsonify, request, render_template
from flask_login import current_user, login_required
from app import db
from app.models import User, Menu, Restaurant
from app.main import bp
import logging
from werkzeug.security import generate_password_hash
from sqlalchemy import  or_ , cast,VARCHAR


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    return render_template("index.html")


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
        menu_item_id = data.get("MenuItemIdToDelete")
        print(menu_item_id)
        menu_item = Menu.query.get(menu_item_id)

        if not menu_item:
            return jsonify({"error": "Menu item not found"}), 404

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
        menu_id = data.get("RestaurantId")
        new_status = data.get("newStatus")

        if not menu_id or new_status is None:
            return jsonify({"error": "Invalid request data"}), 400

        # Преобразование строкового значения 'active' в булево значение True
        if new_status.lower() == 'active':
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
        logging.exception("An unexpected error occurred")
        return jsonify({"error": "An unexpected error occurred"}), 500


@bp.route("/delete_restaurant", methods=["POST"])
def delete_restaurant():
    try:
        data = request.json
        menu_id = data.get("RestaurantId")

        restaurant_delete = Restaurant.query.get(menu_id)
        if restaurant_delete:
            # Удаляем связные меню
            related_menu_items = Menu.query.filter_by(id=restaurant_delete.id).all()
            for related_menu_item in related_menu_items:
                db.session.delete(related_menu_item)
            db.session.delete(restaurant_delete)
            db.session.commit()

            logging.info(f"Restaurant {menu_id} deleted successfully")
            return jsonify({"message": "Restaurant deleted successfully"})
        else:
            logging.warning(f"Restaurant with ID {menu_id} not found")
            return jsonify({"error": "Restaurant not found"}), 404

    except Exception as e:
        logging.exception("An unexpected error occurred")
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
        data = request.json

        # Извлекаем данные из запроса
        Restaurant_name = data.get("RestaurantName")
        Image = data.get("Image")
        Status = data.get("Status")
        # Преобразуем строку "Status" в булево значение
        status_bool = True if Status == "Active" else False

        existing_restaurant = Restaurant.query.filter_by(name=Restaurant_name).first()

        if existing_restaurant:
            # Если запись существует, используем ее id
            menu_id = existing_restaurant.id
        else:
            # Если записи нет, создаем новую
            new_restaurant = Restaurant(
                name=Restaurant_name, image_path=Image, status=status_bool
            )
            db.session.add(new_restaurant)
            db.session.commit()
            # Получаем id после вставки новой записи
            menu_id = new_restaurant.id

        return jsonify(
            {
                "message": "Restaurant added successfully",
                "new_menu_id": menu_id,
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
        MenuItemImageURL = data.get("MenuItemImageURL")
        Status = data.get("Status")

        existing_Restaurant = Restaurant.query.get(MenuIdForRestaurant)

        if not existing_Restaurant:
            return jsonify({"error": "Restaurant not found"}), 404

        # Создаем новую запись в Menu
        new_menu = Menu(
            name=MenuItemName,
            image_path=MenuItemImageURL,
            price=MenuItemPrice,
            status=True if Status == "Active" else False,
            menu_id=MenuIdForRestaurant
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
    data = request.json
    menu_id = data.get("menu_id")
    menu_id = data.get("menu_id")
    new_price = data.get("new_price")

    restaurant = Restaurant.query.get(menu_id)

    if restaurant:
        Menu_item = Menu.query.get(menu_id)

        if Menu_item:
            Menu_item.price = new_price
            db.session.commit()

            return jsonify({"message": "Menu price modified successfully"}), 200

        return jsonify({"error": "Menu item not found"}), 404

    return jsonify({"error": "Restaurant not found"}), 404

@bp.route('/hash_password', methods=['POST'])
def hash_password():
    data = request.json
    password = data.get('password')

    if not password:
        return jsonify({'error': 'No password provided'}), 400

    hashed_password = generate_password_hash(password)

    return jsonify({'hashedPassword': hashed_password}), 200
  
@bp.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password_hash = data.get('password_hash')
    role = data.get('role')
    print(username)
    print(password_hash)
    role_bool = True if role == "Administrator" else False
    try:
        new_user = User(username=username, email=email, password_hash=password_hash, role=role_bool)
        db.session.add(new_user)
        db.session.commit()
        logging.info(f"User added: {new_user}")
        return jsonify({'message': 'User added successfully'})
    except Exception as e:
        error_message = f"Error adding user: {str(e)}"
        logging.error(error_message)
        return jsonify({'error': error_message}), 500
    
@bp.route('/delete_user', methods=['POST'])
def delete_user():
    try:
        data = request.json
        user_id = data.get('user_id')
        
        user_to_delete = User.query.get(user_id)
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
            return jsonify({'message': 'User deleted successfully'})
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@bp.route("/change_name_item", methods=["POST"])
def change_name_item():
    data = request.json
    menu_id = data.get("menu_id")
    menu_id = data.get("menu_id")
    new_name = data.get("new_name")

    restaurant = Restaurant.query.get(menu_id)

    if restaurant:
        Menu_item = Menu.query.get(menu_id)

        if Menu_item:
            Menu_item.name = new_name
            db.session.commit()

            return jsonify({"message": "Menu price modified successfully"}), 200

        return jsonify({"error": "Menu item not found"}), 404

    return jsonify({"error": "Restaurant not found"}), 404


@bp.route("/change_image_item", methods=["POST"])
def change_imege_item():
    data = request.json
    menu_id = data.get("menu_id")
    menu_id = data.get("menu_id")
    new_image = data.get("new_image")

    restaurant = Restaurant.query.get(menu_id)

    if restaurant:
        Menu_item = Menu.query.get(menu_id)

        if Menu_item:
            Menu_item.image_path = new_image
            db.session.commit()

            return jsonify({"message": "Menu price modified successfully"}), 200

        return jsonify({"error": "Menu item not found"}), 404

    return jsonify({"error": "Restaurant not found"}), 404

@bp.route("/change_status_item", methods=["POST"])
def change_status_item():
    try:
        data = request.json
        menu_id = data.get("MenuId")
        new_status = data.get("newStatus")
        print(new_status)

        if not menu_id or new_status is None:
            return jsonify({"error": "Invalid request data"}), 400

        # Преобразование строкового значения 'active' в булево значение True
        if new_status.lower() == 'active':
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
        logging.exception("An unexpected error occurred")
        return jsonify({"error": "An unexpected error occurred"}), 500
    

@bp.route('/fetch_restaurants', methods=['GET'])
def fetch_restaurants():
    try:
        restaurants = Restaurant.query.order_by(Restaurant.id).all()

        # Преобразование объектов заказов в словари для сериализации в JSON
        Restaurant_data = []
        for restaurant in restaurants:
            restaurant_data = {
                'id': restaurant.id,
                'name': restaurant.name,
                'image': restaurant.image_path,
                'status': restaurant.status
            }
            Restaurant_data.append(restaurant_data)

        return jsonify(Restaurant_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

def get_restaurant_by_search_query(search_query):
    query = Restaurant.query.filter(
        or_(
            Restaurant.name.ilike(f'%{search_query}%'),
            cast(Restaurant.id, VARCHAR).ilike(f'%{search_query}%'),
            Restaurant.status.ilike(f'%{search_query}%')
        )
    )
    return query.order_by(Restaurant.id).all()

@bp.route('/search_restaurants')
def search_restaurants():
    search_query = request.args.get('search_query', '')
    restaurants = get_restaurant_by_search_query(search_query)
    # Преобразование результатов в формат JSON и возврат
    restaurants_data = [{'id': restaurant.id, 'name': restaurant.name, 'image': restaurant.image_path,  'status': restaurant.status} for restaurant in restaurants]
    return jsonify(restaurants_data)