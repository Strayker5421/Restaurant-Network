from app import create_app, db
from app.models import User, Restaurant, Menu, Dish


app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Restaurant": Restaurant,
        "Menu": Menu,
        "Dish": Dish,
    }
