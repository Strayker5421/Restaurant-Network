import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    SECRET_KEY = "you-will-never-guess"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
