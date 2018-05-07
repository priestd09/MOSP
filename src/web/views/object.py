from flask import Blueprint, render_template, redirect, url_for, flash, \
                  request, abort
from flask_login import login_required, current_user

from bootstrap import db, application
from web.models import Schema, JsonObject

object_bp = Blueprint('object_bp', __name__, url_prefix='/object')
objects_bp = Blueprint('objects_bp', __name__, url_prefix='/objects')


@object_bp.route('/create', methods=['GET'])
@object_bp.route('/edit/<int:object_id>', methods=['GET'])
@login_required
def form(schema_id=None, object_id=None):
    action = "Create an object"
    head_titles = [action]

    schema_id = request.args.get('schema_id', None)
    schema = Schema.query.filter(Schema.id == schema_id).first()

    json_object = None

    return render_template('edit_object.html', action=action,
                            head_titles=head_titles,
                            schema=schema,
                            json_object=json_object)