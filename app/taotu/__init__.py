from flask import Blueprint

taotu = Blueprint('taotu', __name__)

from . import views


