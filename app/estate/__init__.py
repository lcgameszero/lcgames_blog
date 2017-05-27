from flask import Blueprint

estate = Blueprint('estate', __name__)

from . import views


