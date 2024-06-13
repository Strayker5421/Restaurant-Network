import docker.errors
import app
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
import os, time
import subprocess
from jinja2 import Environment, FileSystemLoader
from docker import DockerClient
import qrcode
from flask import url_for, current_app
import jwt


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.Boolean, default=False)
    restaurants = db.relationship(
        "Restaurant", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    admin_token = db.Column(db.String(256))

    def generate_admin_token(self):
        payload = {"user_id": self.id, "timestamp": datetime.utcnow().timestamp()}
        self.admin_token = jwt.encode(
            payload, current_app.config["SECRET_KEY"], algorithm="HS256"
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

    def generate_and_save_qr_code(self, name):
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            qr.add_data(f"http://{name}.3069535-ab61855.twc1.net")
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
        volume_name = "static"
        project_name = f"menu-{restaurant_name}-{menu_name}"
        menu_container_name = f"menu-{restaurant_name}-{menu_name}-app"
        menu_db_container_name = f"menu-{restaurant_name}-{menu_name}-db"

        os.environ["APP_PORT"] = str(port)

        env = Environment(loader=FileSystemLoader(current_app.config["TEMPLATE_DIR"]))

        compose_template = env.get_template("docker-compose-menu-template.j2")

        with open("docker-compose-menu.yml", "w") as f:
            f.write(
                compose_template.render(
                    menu_container_name=menu_container_name,
                    menu_db_container_name=menu_db_container_name,
                    volume_name=volume_name,
                    admin_token=self.restaurant.user.admin_token,
                )
            )

        subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker-compose-menu.yml",
                "--project-name",
                project_name,
                "up",
                "-d",
            ]
        )
        time.sleep(5)
        self.change_config(menu_name, restaurant_name, menu_container_name)

    def change_config(self, menu_name, restaurant_name, menu_container_name):
        client = DockerClient.from_env()
        containers = client.containers.list(filters={"name": menu_container_name})
        container_ip = containers[0].attrs["NetworkSettings"]["Networks"]["menu_net"][
            "IPAddress"
        ]

        menu_config = {
            "name": f"{restaurant_name}-{menu_name}",
            "container_address": f"{container_ip}:80",
            "static_volume": f"menu-{restaurant_name}-{menu_name}_static",
        }

        self.generate_and_save_qr_code(menu_config["name"])

        env = Environment(loader=FileSystemLoader(current_app.config["TEMPLATE_DIR"]))

        nginx_template = env.get_template("nginx-template.j2")

        new_config = nginx_template.render(
            menu_name=menu_config["name"],
            container_address=menu_config["container_address"],
        )

        with open("nginx.conf", "r") as f:
            lines = f.readlines()

        if new_config not in "".join(lines):
            lines.append(new_config + "\n")
            with open("nginx.conf", "w") as f:
                f.writelines(lines)

        nginx_conf_path = os.path.join(os.getcwd(), "nginx.conf")

        subprocess.run(
            [
                "docker",
                "cp",
                nginx_conf_path,
                f"nginx:/etc/nginx/conf.d/default.conf",
            ]
        )
        subprocess.run(["docker", "exec", "nginx", "nginx", "-s", "reload"])

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
