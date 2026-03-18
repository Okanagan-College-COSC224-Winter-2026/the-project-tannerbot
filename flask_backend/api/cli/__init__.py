from .database import init_app as _init_db
from .user_commands import init_app as _init_user_commands


def init_app(app):
    _init_db(app)
    _init_user_commands(app)

