from flask_login import current_user, login_required
from app import db
from app.models import User
from app.main import bp


@bp.route('/', methods=["GET", "POST"])
@bp.route('/index', methods=["GET", "POST"])
@login_required
def index():
    return "Hello, World!"
