from flask import Blueprint, render_template, request, redirect, flash, session
import mysql.connector

from .db import get_db_connection, log_action
from .decorators import login_required, admin_required

materials_bp = Blueprint('materials_bp', __name__)


@materials_bp.route('/materials', methods=['GET'])
@login_required
def materials_list():
    materials = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT m.id, m.material_name, m.category, m.unit_of_measure,
                   m.current_quantity, m.reorder_level, s.supplier_name
            FROM materials AS m
            LEFT JOIN suppliers AS s ON m.supplier_id = s.id
            WHERE m.status = 'active'
            ORDER BY m.material_name ASC
            """
        )
        materials = cursor.fetchall()
    except mysql.connector.Error:
        flash('Unable to load materials. Please try again.', 'danger')
    finally:
        if conn is not None:
            conn.close()

    return render_template('materials_list.html', materials=materials)


@materials_bp.route('/materials/<int:id>', methods=['GET'])
@login_required
def material_detail(id):
    material = None
    usage_history = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT m.*, s.supplier_name, s.email AS supplier_email
            FROM materials AS m
            LEFT JOIN suppliers AS s ON m.supplier_id = s.id
            WHERE m.id = %s
            """,
            (id,),
        )
        material = cursor.fetchone()

        if material:
            cursor.execute(
                """
                SELECT b.batch_name, b.production_date, bu.quantity_used
                FROM batch_usage AS bu
                JOIN batches AS b ON bu.batch_id = b.id
                WHERE bu.material_id = %s
                ORDER BY b.production_date DESC
                """,
                (id,),
            )
            usage_history = cursor.fetchall()
        else:
            flash('Material not found.', 'warning')
            return redirect('/materials')
    except mysql.connector.Error:
        flash('Unable to load material details. Please try again.', 'danger')
        return redirect('/materials')
    finally:
        if conn is not None:
            conn.close()

    return render_template('material_detail.html', material=material, usage_history=usage_history, role=session.get('role')) 


def _load_suppliers():
    conn = None
    suppliers = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, supplier_name FROM suppliers ORDER BY supplier_name ASC")
        suppliers = cursor.fetchall()
    except mysql.connector.Error:
        flash('Unable to load suppliers. Please try again.', 'danger')
    finally:
        if conn is not None:
            conn.close()
    return suppliers


@materials_bp.route('/materials/add', methods=['GET', 'POST'])
@login_required
def add_material():
    suppliers = _load_suppliers()
    material = {
        'material_name': '',
        'category': '',
        'unit_of_measure': '',
        'current_quantity': '',
        'reorder_level': '',
        'unit_cost': '',
        'supplier_id': '',
    }

    if request.method == 'POST':
        material.update({
            'material_name': request.form.get('material_name', '').strip(),
            'category': request.form.get('category', '').strip(),
            'unit_of_measure': request.form.get('unit_of_measure', '').strip(),
            'current_quantity': request.form.get('current_quantity', '').strip(),
            'reorder_level': request.form.get('reorder_level', '').strip(),
            'unit_cost': request.form.get('unit_cost', '').strip(),
            'supplier_id': request.form.get('supplier_id', '').strip(),
        })

        errors = []
        if not material['material_name']:
            errors.append('Material name is required.')
        if not material['unit_of_measure']:
            errors.append('Unit of measure is required.')

        try:
            current_quantity = float(material['current_quantity'])
            if current_quantity < 0:
                errors.append('Current quantity must be non-negative.')
        except ValueError:
            errors.append('Current quantity must be a number.')

        try:
            reorder_level = float(material['reorder_level'])
            if reorder_level < 0:
                errors.append('Reorder level must be non-negative.')
        except ValueError:
            errors.append('Reorder level must be a number.')

        unit_cost = None
        if material['unit_cost']:
            try:
                unit_cost = float(material['unit_cost'])
            except ValueError:
                errors.append('Unit cost must be a number.')

        if errors:
            for message in errors:
                flash(message, 'warning')
            return render_template('material_form.html', material=material, suppliers=suppliers, form_action='/materials/add', title='Add Material')

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO materials
                    (material_name, category, unit_of_measure, current_quantity, reorder_level, unit_cost, supplier_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    material['material_name'],
                    material['category'],
                    material['unit_of_measure'],
                    current_quantity,
                    reorder_level,
                    unit_cost,
                    material['supplier_id'] or None,
                ),
            )
            conn.commit()
            log_action(session.get('user_id'), f"Added material: {material['material_name']}")
            flash('Material added successfully.', 'success')
            return redirect('/materials')
        except mysql.connector.Error:
            flash('Unable to add material. Please try again.', 'danger')
        finally:
            if conn is not None:
                conn.close()

    return render_template('material_form.html', material=material, suppliers=suppliers, form_action='/materials/add', title='Add Material')


@materials_bp.route('/materials/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_material(id):
    suppliers = _load_suppliers()
    material = None
    conn = None

    if request.method == 'POST':
        material = {
            'id': id,
            'material_name': request.form.get('material_name', '').strip(),
            'category': request.form.get('category', '').strip(),
            'unit_of_measure': request.form.get('unit_of_measure', '').strip(),
            'current_quantity': request.form.get('current_quantity', '').strip(),
            'reorder_level': request.form.get('reorder_level', '').strip(),
            'unit_cost': request.form.get('unit_cost', '').strip(),
            'supplier_id': request.form.get('supplier_id', '').strip(),
        }

        errors = []
        if not material['material_name']:
            errors.append('Material name is required.')
        if not material['unit_of_measure']:
            errors.append('Unit of measure is required.')

        try:
            current_quantity = float(material['current_quantity'])
            if current_quantity < 0:
                errors.append('Current quantity must be non-negative.')
        except ValueError:
            errors.append('Current quantity must be a number.')

        try:
            reorder_level = float(material['reorder_level'])
            if reorder_level < 0:
                errors.append('Reorder level must be non-negative.')
        except ValueError:
            errors.append('Reorder level must be a number.')

        unit_cost = None
        if material['unit_cost']:
            try:
                unit_cost = float(material['unit_cost'])
            except ValueError:
                errors.append('Unit cost must be a number.')

        if errors:
            for message in errors:
                flash(message, 'warning')
            return render_template('material_form.html', material=material, suppliers=suppliers, form_action=f'/materials/edit/{id}', title='Edit Material')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE materials
                SET material_name = %s,
                    category = %s,
                    unit_of_measure = %s,
                    current_quantity = %s,
                    reorder_level = %s,
                    unit_cost = %s,
                    supplier_id = %s
                WHERE id = %s
                """,
                (
                    material['material_name'],
                    material['category'],
                    material['unit_of_measure'],
                    current_quantity,
                    reorder_level,
                    unit_cost,
                    material['supplier_id'] or None,
                    id,
                ),
            )
            conn.commit()
            log_action(session.get('user_id'), f"Updated material: {material['material_name']}")
            flash('Material updated successfully.', 'success')
            return redirect(f'/materials/{id}')
        except mysql.connector.Error:
            flash('Unable to update material. Please try again.', 'danger')
        finally:
            if conn is not None:
                conn.close()
    else:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, material_name, category, unit_of_measure, current_quantity,
                       reorder_level, unit_cost, supplier_id
                FROM materials
                WHERE id = %s
                """,
                (id,),
            )
            material = cursor.fetchone()
            if not material:
                flash('Material not found.', 'warning')
                return redirect('/materials')
        except mysql.connector.Error:
            flash('Unable to load material for editing. Please try again.', 'danger')
            return redirect('/materials')
        finally:
            if conn is not None:
                conn.close()

    return render_template('material_form.html', material=material, suppliers=suppliers, form_action=f'/materials/edit/{id}', title='Edit Material')


@materials_bp.route('/materials/deactivate/<int:id>', methods=['POST'])
@login_required
@admin_required
def deactivate_material(id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT material_name FROM materials WHERE id = %s", (id,))
        row = cursor.fetchone()
        if not row:
            flash('Material not found.', 'warning')
            return redirect('/materials')

        material_name = row[0]
        cursor.execute("UPDATE materials SET status = 'inactive' WHERE id = %s", (id,))
        conn.commit()
        log_action(session.get('user_id'), f"Deactivated material: {material_name}")
        flash('Material deactivated successfully.', 'success')
    except mysql.connector.Error:
        flash('Unable to deactivate material. Please try again.', 'danger')
    finally:
        if conn is not None:
            conn.close()

    return redirect('/materials')
