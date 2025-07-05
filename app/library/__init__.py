from flask import Blueprint
from markupsafe import Markup, escape

bp = Blueprint('library', __name__)

# Register nl2br filter for this blueprint
def nl2br(value):
    return Markup('<br>'.join(escape(value).split('\n')))

@bp.app_template_filter('nl2br')
def nl2br_filter(value):
    return nl2br(value)

from app.library import routes
