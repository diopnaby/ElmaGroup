from flask import Blueprint

bp = Blueprint('testimonials', __name__)

from app.testimonials import routes
