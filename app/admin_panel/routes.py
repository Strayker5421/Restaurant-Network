from flask import jsonify, request, render_template, url_for, flash, redirect
from flask_login import current_user
from app import db
from app.models import User, Menu, Restaurant
from werkzeug.utils import secure_filename
import os
from datetime import timedelta
from flask_admin.contrib.sqla import ModelView
from app import admin
from wtforms import MultipleFileField, StringField, BooleanField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, ValidationError
from flask_wtf.file import FileAllowed
from wtforms.fields import IntegerField
from datetime import datetime
from wtforms.fields import SelectField
from markupsafe import Markup
from app.admin_panel import bp
from flask_admin import expose, BaseView
import subprocess


class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.login"))


"""class CustomView(BaseView):
    @expose("/")
    def index(self):
        data = {"name": "John", "age": 30, "email": "john@example.com"}
        return self.render("custom_view.html", data=data)
"""


class RestaurantForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    user_id = StringField("User ID")
    photo = MultipleFileField(
        "Photo",
        validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only!")],
    )

    def validate_photo(form, field):
        if len(field.data) > 3:
            raise ValidationError("You can upload a maximum of 3 photos.")


class RestaurantAdmin(ModelView):
    form = RestaurantForm

    form_columns = ["name", "user_id", "photo"]
    column_list = ["id", "name", "status", "images", "user_id"]
    column_sortable_list = ["id", "name", "status", "user_id"]
    column_searchable_list = ["id", "name", "status", "user_id"]

    def images_formatter(view, context, model, name):
        images_html = ""
        for image in model.images:
            image_style = (
                'style="max-width:100px; max-height:100px; width:auto; height:auto;"'
            )
            images_html += f'<img src="{image}" {image_style}/>'
        return Markup(images_html)

    column_formatters = {"images": images_formatter}

    def on_model_delete(self, model):
        try:
            image_paths = model.images
            for path in image_paths:
                full_path = os.path.join(
                    "app", "static", "images", "restaurants", path.split("/")[-1]
                )
                if os.path.exists(full_path):
                    os.remove(full_path)

            related_menus = Menu.query.filter_by(restaurant_id=model.id).all()
            for menu in related_menus:
                restaurant_name, menu_name = set_to_low_register(model.name, menu.name)
                subprocess.run(
                    [
                        "docker-compose",
                        "-f",
                        "docker-compose-menu.yml",
                        "--project-name",
                        f"menu-{restaurant_name}-{menu_name}",
                        "down",
                    ]
                )
                qr_code_dir_menu = os.path.join("app", "static", "images", "qr_code")
                menu_qr_filename = f"{menu.name}_qr_code.png"
                full_image_path_menu = os.path.join(qr_code_dir_menu, menu_qr_filename)
                if os.path.exists(full_image_path_menu):
                    os.remove(full_image_path_menu)
                db.session.delete(menu)

            db.session.delete(model)
            db.session.commit()

            flash(f"Restaurant {model.name} was successfully deleted!", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", "error")

        return super(RestaurantAdmin, self).on_model_delete(model)

    def on_model_change(self, form, model, is_created):
        if (
            "photo" in request.files
            and request.files.getlist("photo")[0].filename != ""
        ):
            new_photos = request.files.getlist("photo")[:3]
            new_images_paths = []

            for photo in new_photos:
                if photo.filename != "":
                    new_images_paths.append(save_image(photo, "restaurants/")[0])

            if model.images:
                for old_image_path in model.images:
                    full_old_path = os.path.join(
                        "app",
                        "static",
                        "images",
                        "restaurants",
                        old_image_path.split("/")[-1],
                    )
                    if os.path.exists(full_old_path):
                        os.remove(full_old_path)

            model.images = new_images_paths
        else:
            if not is_created:
                model.images = Restaurant.query.get(model.id).images

        if is_created:
            flash(f"Restaurant {model.name} was successfully created!", "success")
        else:
            flash(f"Restaurant {model.name} was successfully updated!", "success")

        db.session.commit()
        return super(RestaurantAdmin, self).on_model_change(form, model, is_created)

    def create_model(self, form):
        if form.user_id.data:
            user = User.query.filter_by(id=form.user_id.data).first()
            if user and user.role:
                flash(
                    "You cannot assign a user with status True to a restaurant.",
                    "error",
                )
                return False
        return super(RestaurantAdmin, self).create_model(form)

    def update_model(self, form, model):
        if form.user_id.data:
            new_user = User.query.filter_by(id=form.user_id.data).first()
            old_user = User.query.filter_by(id=model.user_id).first()
            if new_user and new_user.role:
                flash(
                    "You cannot assign a user with status True to a restaurant.",
                    "error",
                )
                return False
            if old_user and old_user.role:
                flash(
                    "You cannot assign a user with status True to a restaurant.",
                    "error",
                )
                return False
        return super(RestaurantAdmin, self).update_model(form, model)


class UserAdminForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email")
    password_hash = StringField("Password")
    role = BooleanField("Role")


class UserAdmin(ModelView):
    form = UserAdminForm
    form_columns = ["id", "username", "email", "password_hash", "role"]
    column_list = ["id", "username", "email", "password_hash", "role", "admin_token"]

    def role_formatter(view, context, model, name):
        if model.role:
            return "Administrator"
        else:
            return "User"

    column_formatters = {"role": role_formatter}

    def on_model_change(self, form, model, is_created):
        if is_created:
            if not model.role:
                model.generate_admin_token()
        if "password_hash" in form.data:
            model.set_password(form.data["password_hash"])

        return super(UserAdmin, self).on_model_change(form, model, is_created)

    def on_model_delete(self, model):
        try:
            user_restaurants = Restaurant.query.filter_by(user_id=model.id).all()
            for restaurant in user_restaurants:
                if restaurant.images:
                    for path in restaurant.images:
                        full_path = os.path.join(
                            "app",
                            "static",
                            "images",
                            "restaurants",
                            path.split("/")[-1],
                        )
                        if os.path.exists(full_path):
                            os.remove(full_path)

                related_menus = Menu.query.filter_by(restaurant_id=restaurant.id).all()
                for menu in related_menus:
                    restaurant_name, menu_name = set_to_low_register(
                        restaurant.name, menu.name
                    )
                    subprocess.run(
                        [
                            "docker-compose",
                            "-f",
                            "docker-compose-menu.yml",
                            "--project-name",
                            f"menu-{restaurant_name}-{menu_name}",
                            "down",
                        ]
                    )
                    qr_code_dir_menu = os.path.join(
                        "app", "static", "images", "qr_code"
                    )
                    menu_qr_filename = f"{menu.name}_qr_code.png"
                    full_image_path_menu = os.path.join(
                        qr_code_dir_menu, menu_qr_filename
                    )
                    if os.path.exists(full_image_path_menu):
                        os.remove(full_image_path_menu)
                    db.session.delete(menu)

                db.session.delete(restaurant)

            db.session.delete(model)
            db.session.commit()

            flash(
                f"User {model.username} and associated restaurants and menus were successfully deleted!",
                "success",
            )

        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", "error")

        return super(UserAdmin, self).on_model_delete(model)


class MenuForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    restaurant_id = IntegerField("Restaurant ID", validators=[DataRequired()])
    expiration_options = [
        ("0", "0 минут"),
        ("5", "5 минут"),
        ("15", "15 минут"),
        ("60", "1 час"),
    ]
    expiration_minutes = SelectField(
        "Expiration Time", choices=expiration_options, default="0"
    )

    def validate_restaurant_id(self, field):
        if not Restaurant.query.get(field.data):
            raise ValidationError("Invalid restaurant ID")


class MenuAdmin(ModelView):
    form = MenuForm
    column_list = ["id", "name", "status", "expiration_date", "restaurant_id"]
    column_sortable_list = ["id", "name", "status", "expiration_date", "restaurant_id"]
    column_searchable_list = ["id", "name", "status", "restaurant_id"]

    def on_model_change(self, form, model, is_created):
        if form.expiration_minutes.data != "0":
            expiration_time = int(form.expiration_minutes.data)
            expiration_date = datetime.now() + timedelta(minutes=expiration_time)
            model.expiration_date = expiration_date

        return super(MenuAdmin, self).on_model_change(form, model, is_created)

    def on_model_delete(self, model):
        try:
            qr_code_filename = f"{model.name}_qr_code.png"
            qr_code_path = os.path.join(
                "app", "static", "images", "qr_code", qr_code_filename
            )
            if os.path.exists(qr_code_path):
                os.remove(qr_code_path)

            restaurant_name, menu_name = set_to_low_register(
                model.restaurant.name, model.name
            )
            subprocess.run(
                [
                    "docker-compose",
                    "-f",
                    "docker-compose-menu.yml",
                    "--project-name",
                    f"menu-{restaurant_name}-{menu_name}",
                    "down",
                ]
            )

            db.session.delete(model)
            db.session.commit()

            flash(f"Menu {model.name} was successfully deleted!", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", "error")

        return super(MenuAdmin, self).on_model_delete(model)


admin.add_view(UserAdmin(User, db.session))
admin.add_view(RestaurantAdmin(Restaurant, db.session))
admin.add_view(MenuAdmin(Menu, db.session))
# admin.add_view(CustomView(name="Custom", endpoint="custom"))


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


def set_to_low_register(restaurant_name, menu_name):
    restaurant_name = restaurant_name.replace(" ", "-").lower()
    menu_name = menu_name.split(" ")[0].lower()
    return restaurant_name, menu_name
