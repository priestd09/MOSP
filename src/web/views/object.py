import json
from flask import Blueprint, render_template, redirect, url_for, flash, \
                  request, abort, Response
from flask_login import login_required, current_user

from bootstrap import db, application
from web.views.decorators import check_object_view_permission, check_object_edit_permission
from web.models import Schema, JsonObject
from web.forms import AddObjectForm

object_bp = Blueprint('object_bp', __name__, url_prefix='/object')
objects_bp = Blueprint('objects_bp', __name__, url_prefix='/objects')


@object_bp.route('/get/<int:object_id>', methods=['GET'])
@check_object_view_permission
def get_json_object(object_id):
    """
    Export the JSON part of a JsonObject as a clean JSON file.
    """
    json_object = JsonObject.query.filter(JsonObject.id == object_id).first()
    result = json.dumps(json_object.json_object,
                        sort_keys=True, indent=4, separators=(',', ': '))
    return Response(result,
                    mimetype='application/json',
                    headers={
                        'Content-Disposition':'attachment;filename={}.json'. \
                            format(json_object.name.replace(' ', '_'))
                            }
                    )


@object_bp.route('/view/<int:object_id>', methods=['GET'])
@check_object_view_permission
def view(object_id=None):
    """
    Display the JSON part of a JsonObject object.
    """
    json_object = JsonObject.query.filter(JsonObject.id == object_id).first()
    result = json.dumps(json_object.json_object,
                        sort_keys=True, indent=4, separators=(',', ': '))
    return render_template('view_json.html',
                            json_object=result)


@object_bp.route('/delete/<int:object_id>', methods=['GET'])
@login_required
@check_object_edit_permission
def delete(object_id=None):
    """
    Delete the requested JsonObject.
    """
    json_object = JsonObject.query.filter(JsonObject.id == object_id).first()
    schema_id = json_object.schema_id
    db.session.delete(json_object)
    db.session.commit()
    return redirect(url_for('schema_bp.get', schema_id=schema_id))


@object_bp.route('/jsoneditor/<int:object_id>', methods=['GET'])
@login_required
@check_object_view_permission
def edit_json(object_id=None):
    """
    Edit a JSON object with JSON editor.
    """
    action = "Edit an object"
    head_titles = [action]

    json_object = JsonObject.query.filter(JsonObject.id == object_id).first()
    schema = json_object.schema

    return render_template('edit_json.html', action=action,
                            head_titles=head_titles,
                            schema=schema,
                            json_object=json_object)


@object_bp.route('/create', methods=['GET'])
@object_bp.route('/edit/<int:object_id>', methods=['GET'])
@login_required
def form(schema_id=None, object_id=None):
    action = "Create an object"
    head_titles = [action]

    form = AddObjectForm()
    form.org_id.choices = [(0, '')]
    form.org_id.choices.extend([(org.id, org.name) for org in
                                                    current_user.organizations])

    if object_id is None:
        schema_id = request.args.get('schema_id', None)
        form.schema_id.data = schema_id
        schema = Schema.query.filter(Schema.id == schema_id).first()
        return render_template('edit_object.html', action=action,
                               head_titles=head_titles, form=form,
                               schema=schema)

    json_object = JsonObject.query.filter(JsonObject.id == object_id).first()
    schema = json_object.schema
    form = AddObjectForm(obj=json_object)
    form.schema_id.data = schema.id
    form.org_id.choices = [(0, '')]
    form.org_id.choices.extend([(org.id, org.name) for org in
                                                    current_user.organizations])
    action = "Edit an object"
    head_titles = [action]
    head_titles.append(json_object.name)
    return render_template('edit_object.html', action=action,
                           head_titles=head_titles,
                           form=form, schema=schema)


@object_bp.route('/create', methods=['POST'])
@object_bp.route('/edit/<int:object_id>', methods=['POST'])
@login_required
def process_form(object_id=None):
    form = AddObjectForm()
    form.org_id.choices = [(0, '')]
    form.org_id.choices.extend([(org.id, org.name) for org in
                                                    current_user.organizations])

    if not form.validate():
        return render_template('edit_object.html', form=form)

    # Edit an existing JsonObject
    if object_id is not None:
        json_object = JsonObject.query.filter(JsonObject.id == object_id).first()
        form.schema_id.data = json_object.schema_id
        form.populate_obj(json_object)
        try:
            db.session.commit()
            flash("'{object_name}' successfully updated.".
                  format(object_name=form.name.data), 'success')
        except Exception as e:
            form.name.errors.append('Name already exists.')
        return redirect(url_for('object_bp.form', object_id=json_object.id))

    # Create a new JsonObject
    new_object = JsonObject(name=form.name.data,
                            description=form.description.data,
                            schema_id=form.schema_id.data,
                            org_id=form.org_id.data)
    db.session.add(new_object)
    try:
        db.session.commit()
    except Exception as e:
        # TODO: display the error
        return redirect(url_for('object_bp.form', object_id=new_object.id))
    return redirect(url_for('object_bp.form', object_id=new_object.id))
