import docker.errors
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
from docker import DockerClient
from sqlalchemy import create_engine, text
import os, time
import subprocess, pytz
from jinja2 import Environment, FileSystemLoader
from docker import DockerClient
import qrcode
from flask import url_for


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.Boolean, default=False)
    restaurants = db.relationship(
        "Restaurant", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    images = db.Column(ARRAY(db.String()))
    status = db.Column(db.Boolean, default=False)
    menus = db.relationship(
        "Menu", backref="restaurant", lazy="dynamic", cascade="all, delete-orphan"
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Boolean, default=False)
    expiration_date = db.Column(
        db.DateTime,
        index=True,
        default=datetime.now,
    )
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"))
    PORT = 8000

    def check_subscription(self):
        new_status = datetime.now() < self.expiration_date
        if new_status != self.status:
            self.status = new_status
            db.session.commit()
            restaurant = self.restaurant
            active_menus = Menu.query.filter_by(
                restaurant_id=restaurant.id, status=True
            ).count()
            if active_menus == 0:
                restaurant.status = False
            else:
                restaurant.status = True
            db.session.commit()

            if self.status:
                Menu.PORT += 1
                self.start_container(
                    self.name.replace(" ", "-").lower(),
                    self.restaurant.name.split(" ")[0].lower(),
                    self.PORT,
                )
            else:
                self.stop_container(
                    self.name.replace(" ", "-").lower(),
                    self.restaurant.name.split(" ")[0].lower(),
                )

    def generate_and_save_qr_code(self, container_ip, port):
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            qr.add_data(f"http://45.93.201.166:{port}/menu")
            save_path = os.path.join("app", "static", "images", "qr_code")

            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="black", back_color="white")

            if not os.path.exists(save_path):
                os.makedirs(save_path)

            filename = f"{self.name}_qr_code.png"
            qr_image.save(os.path.join(save_path, filename))

            qr_image_path = url_for("static", filename=f"images/qr_code/{filename}")

            return qr_image_path
        except Exception as e:
            return None

    def start_container(self, menu_name, restaurant_name, port=PORT):
        os.environ["APP_PORT"] = str(port)
        subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker-compose-menu.yml",
                "--project-name",
                f"menu-{restaurant_name}-{menu_name}",
                "up",
                "-d",
            ]
        )
        time.sleep(5)
        self.change_nginx_conf(menu_name, restaurant_name, port)

    def change_nginx_conf(self, menu_name, restaurant_name, port):
        client = DockerClient.from_env()
        containers = client.containers.list(
            filters={"name": f"menu-{restaurant_name}-{menu_name}"}
        )
        container_ip = containers[0].attrs["NetworkSettings"]["Networks"]["frontnet"][
            "IPAddress"
        ]
        self.generate_and_save_qr_code(container_ip, port)
        new_location_block = f"""
    location /menu/{self.id} {{
        proxy_pass http://{container_ip}:80/menu;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    location /menu/{self.id}/admin/cat {{
        proxy_pass http://{container_ip}:80/menu/admin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        """
        nginx_conf_path = os.path.join(os.getcwd(), "nginx.conf")
        with open(nginx_conf_path, "r") as f:
            lines = f.readlines()

        if f"    location /menu/{self.id} {{\n" not in lines:
            insert_index = (
                lines.index("    #error_page  404              /404.html;\n") - 1
            )
            lines.insert(insert_index, new_location_block)

        with open(nginx_conf_path, "w") as f:
            f.writelines(lines)

        subprocess.run(
            [
                "docker",
                "cp",
                nginx_conf_path,
                f"root-nginx-1:/etc/nginx/conf.d/default.conf",
            ]
        )

        subprocess.run(
            [
                "docker",
                "restart",
                "root-nginx-1",
            ]
        )

    @staticmethod
    def stop_container(menu_name, restaurant_name):
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

    @staticmethod
    def get_menu(menu_name):
        menu = Menu.query.filter_by(name=menu_name).first()
        return menu


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
