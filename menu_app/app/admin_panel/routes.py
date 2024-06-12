from flask import jsonify, request, render_template, url_for, flash, redirect
from flask_login import current_user, login_required
from app import db
from app.models import Menu, Dish
from app.admin_panel import bp
from sqlalchemy import or_, cast, and_
from sqlalchemy.types import String
from werkzeug.utils import secure_filename
import os, qrcode, pytz
from datetime import datetime, timedelta
from flask_admin.contrib.sqla import ModelView
from app import admin
from wtforms import FileField, StringField, BooleanField, DateTimeField, FloatField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, ValidationError
from flask_wtf.file import FileAllowed
from wtforms.fields import IntegerField
from datetime import datetime
from wtforms.fields import SelectField
from markupsafe import Markup


@bp.route("/", methods=["GET", "POST"])
def index():
    dishes = Dish.query.all()
    return render_template("single_menu.html", dishes=dishes)


class DishForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    ingredients = StringField("Ingredients")
    price = FloatField("Price", validators=[DataRequired()])
    section = SelectField(
        "Section",
        choices=[
            ("Hot Dishes", "Hot Dishes"),
            ("Cold Dishes", "Cold Dishes"),
            ("Desserts", "Desserts"),
            ("Drinks", "Drinks"),
            ("Appetizers", "Appetizers"),
            ("Salad", "Salad"),
        ],
        validators=[DataRequired()],
    )
    photo = FileField(
        "Photo",
        validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only!")],
    )


# Обновленный класс представления администрирования ресторанов
class DishAdmin(ModelView):
    form = DishForm  # Используем новую форму

    # Включаем поле для фотографии в форму
    form_columns = ["name", "ingredients", "price", "section", "image"]
    column_list = ["id", "name", "ingredients", "price", "section", "image"]
    column_sortable_list = ["id", "name", "price", "section"]
    column_searchable_list = ["id", "name", "ingredients", "section", "price"]

    def images_formatter(view, context, model, name):
        images_html = ""
        for image in model.image:
            image_style = (
                'style="max-width:100px; max-height:100px; width:auto; height:auto;"'
            )
            images_html += f'<img src="{image}" {image_style}/>'
        return Markup(images_html)

    column_formatters = {"images": images_formatter}

    def on_model_delete(self, model):
        try:
            image_path = model.image
            full_path = os.path.join(
                "app", "static", "images", "dishes", image_path.split("/")[-1]
            )
            if os.path.exists(full_path):
                os.remove(full_path)
            db.session.delete(model)
            db.session.commit()

            flash(f"Dish {model.name} was successfully deleted!", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", "error")

        return super(DishAdmin, self).on_model_delete(model)

    def on_model_change(self, form, model, is_created):
        if "photo" in request.files:
            if model.image:
                old_image_path = model.image
                full_old_path = os.path.join(
                    "app", "static", "images", "dishes", old_image_path.split("/")[-1]
                )
                if os.path.exists(full_old_path):
                    os.remove(full_old_path)

            photo = request.files.get("photo")
            images_paths_raw = []
            if photo.filename != "":
                images_paths_raw.append(save_image(photo, "dishes/"))

            images_paths = []
            images_paths.append(images_paths_raw[0][0])

            model.image = images_paths[0]

        # Продолжаем выполнение остальной части метода
        if is_created:
            flash(f"Dish {model.name} was successfully created!", "success")
        else:
            flash(f"Dish {model.name} was successfully updated!", "success")

        db.session.commit()
        return super(DishAdmin, self).on_model_change(form, model, is_created)


class MenuForm(FlaskForm):
    template = FileField(
        "template",
        validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only!")],
    )


# Класс представления для администрирования меню
class MenuAdminView(ModelView):
    # Определяем форму для редактирования меню
    form = MenuForm

    # Определяем колонки для отображения в списке
    column_list = ["template"]

    # Определяем форматтер для отображения изображений
    def template_formatter(self, context, model, name):
        template_folder = "app/static/images/menu_templates"
        files = os.listdir(template_folder)
        if files:
            template_filename = files[0]
            template_path = f"/static/images/menu_templates/{template_filename}"
            image_html = f'<img src="{template_path}" style="max-width:100px; max-height:100px; width:auto; height:auto;"/>'
            return Markup(image_html)
        else:
            return "No template image available"

    # Подключаем форматтер к колонке
    column_formatters = {"template": template_formatter}

    # Метод для изменения модели меню
    def on_model_change(self, form, model, is_created):
        if "template" in request.files:
            template_folder = os.path.join("app", "static", "images", "menu_templates")

            # Удаляем все файлы из папки template_folder
            for filename in os.listdir(template_folder):
                file_path = os.path.join(template_folder, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

            # Обработка нового загруженного файла
            file = request.files["template"]
            filename = secure_filename(file.filename)
            file.save(os.path.join(template_folder, filename))

            # Продолжаем выполнение остальной части метода
            if is_created:
                flash(f"Menu_template was successfully created!", "success")
            else:
                flash(f"Menu_template was successfully updated!", "success")

        return super(MenuAdminView, self).on_model_change(form, model, is_created)

    # Метод для удаления модели меню
    def on_model_delete(self, model):
        try:
            # Путь к папке с шаблонами
            template_folder = os.path.join("app", "static", "images", "menu_templates")

            # Удаление всех файлов в папке
            for filename in os.listdir(template_folder):
                file_path = os.path.join(template_folder, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

            # Удаляем саму модель
            db.session.delete(model)
            db.session.commit()
            flash(f"Template  was successfully deleted!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", "error")

        return super(MenuAdminView, self).on_model_delete(model)


# Добавляем представления в админ-панель
admin.add_view(DishAdmin(Dish, db.session))
admin.add_view(MenuAdminView(Menu, db.session))


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
