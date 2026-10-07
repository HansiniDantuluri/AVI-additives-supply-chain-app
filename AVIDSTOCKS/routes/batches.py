from flask import Blueprint, render_template, request, redirect, flash, session, url_for
import mysql.connector

from .db import get_db_connection, log_action
from .decorators import login_required

batches_bp = Blueprint('batches_bp', __name__)


@batches_bp.route('/batches', methods=['GET'])
@login_required
def batches_list():
    batches = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            '''
            SELECT id, batch_name, product_type, production_date
            FROM batches
            ORDER BY production_date DESC
            '''
        )
        batches = cursor.fetchall()
    except mysql.connector.Error:
        flash('Unable to load batches. Please try again.', 'danger')
    finally:
        if conn is not None:
            conn.close()

    return render_template('batches_list.html', batches=batches)


@batches_bp.route('/batches/add', methods=['GET', 'POST'])
@login_required
def add_batch():
    batch = {
        'batch_name': '',
        'product_type': '',
        'production_date': '',
    }

    if request.method == 'POST':
        batch['batch_name'] = request.form.get('batch_name', '').strip()
        batch['product_type'] = request.form.get('product_type', '').strip()
        batch['production_date'] = request.form.get('production_date', '').strip()

        errors = []
        if not batch['batch_name']:
            errors.append('Batch name is required.')
        if not batch['production_date']:
            errors.append('Production date is required.')

        if errors:
            for message in errors:
                flash(message, 'warning')
            return render_template('batch_form.html', batch=batch, form_action='/batches/add', title='Add Batch')

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO batches (batch_name, product_type, production_date)
                VALUES (%s, %s, %s)
                ''',
                (
                    batch['batch_name'],
                    batch['product_type'] or None,
                    batch['production_date'],
                ),
            )
            conn.commit()
            new_id = cursor.lastrowid
            log_action(session.get('user_id'), f"Added batch: {batch['batch_name']}")
            flash('Batch added successfully.', 'success')
            return redirect(url_for('batches_bp.batch_detail', id=new_id))
        except mysql.connector.Error:
            flash('Unable to add batch. Please try again.', 'danger')
        finally:
            if conn is not None:
                conn.close()

    return render_template('batch_form.html', batch=batch, form_action='/batches/add', title='Add Batch')


@batches_bp.route('/batches/<int:id>', methods=['GET'])
@login_required
def batch_detail(id):
    batch = None
    usage = []
    active_materials = []
    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            '''
            SELECT id, batch_name, product_type, production_date
            FROM batches
            WHERE id = %s
            ''',
            (id,),
        )
        batch = cursor.fetchone()

        if not batch:
            flash('Batch not found.', 'warning')
            return redirect('/batches')

        cursor.execute(
            '''
            SELECT m.material_name, m.unit_of_measure, bu.quantity_used
            FROM batch_usage AS bu
            JOIN materials AS m ON bu.material_id = m.id
            WHERE bu.batch_id = %s
            ORDER BY bu.id ASC
            ''',
            (id,),
        )
        usage = cursor.fetchall()

        cursor.execute(
            '''
            SELECT id, material_name, unit_of_measure, current_quantity
            FROM materials
            WHERE status = 'active'
            ORDER BY material_name ASC
            ''',
        )
        active_materials = cursor.fetchall()
    except mysql.connector.Error:
        flash('Unable to load batch details. Please try again.', 'danger')
        return redirect('/batches')
    finally:
        if conn is not None:
            conn.close()

    return render_template('batch_detail.html', batch=batch, usage=usage, active_materials=active_materials)


@batches_bp.route('/batches/<int:id>/link-material', methods=['POST'])
@login_required
def link_material(id):
    material_id = request.form.get('material_id')
    quantity_used = request.form.get('quantity_used', '').strip()
    errors = []

    if not material_id:
        errors.append('Material selection is required.')

    try:
        quantity_used_value = float(quantity_used)
        if quantity_used_value <= 0:
            errors.append('Quantity used must be a positive number.')
    except ValueError:
        errors.append('Quantity used must be a valid number.')
        quantity_used_value = None

    if errors:
        for message in errors:
            flash(message, 'warning')
        return redirect(url_for('batches_bp.batch_detail', id=id))

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            '''
            SELECT batch_name
            FROM batches
            WHERE id = %s
            ''',
            (id,),
        )
        batch_row = cursor.fetchone()
        if not batch_row:
            flash('Batch not found.', 'warning')
            return redirect('/batches')

        batch_name = batch_row['batch_name']

        # Wrap all stock reduction and alert creation in one transaction so that
        # batch usage recording, inventory decrement, and alert generation are
        # atomic and cannot partially succeed.
        # autocommit=False ensures all statements below are part of
        # one atomic transaction - commit() or rollback() at the end

        cursor.execute(
            '''
            INSERT INTO batch_usage (batch_id, material_id, quantity_used)
            VALUES (%s, %s, %s)
            ''',
            (id, material_id, quantity_used_value),
        )

        cursor.execute(
            '''
            UPDATE materials
            SET current_quantity = current_quantity - %s
            WHERE id = %s
            ''',
            (quantity_used_value, material_id),
        )

        cursor.execute(
            '''
            SELECT material_name, unit_of_measure, current_quantity, reorder_level
            FROM materials
            WHERE id = %s
            ''',
            (material_id,),
        )
        material = cursor.fetchone()

        if not material:
            raise ValueError('Material not found after update.')

        if material['current_quantity'] <= material['reorder_level']:
            cursor.execute(
                '''
                SELECT id
                FROM alerts
                WHERE material_id = %s AND acknowledged = FALSE
                ''',
                (material_id,),
            )
            existing_alert = cursor.fetchone()
            if not existing_alert:
                alert_message = (
                    f"{material['material_name']} is at or below reorder level "
                    f"({material['current_quantity']} {material['unit_of_measure']}, "
                    f"reorder at {material['reorder_level']} {material['unit_of_measure']})"
                )
                cursor.execute(
                    '''
                    INSERT INTO alerts (material_id, message, acknowledged, created_at)
                    VALUES (%s, %s, FALSE, NOW())
                    ''',
                    (material_id, alert_message),
                )

        conn.commit()
        log_action(
            session.get('user_id'),
            f"Linked {quantity_used_value} {material['unit_of_measure']} of {material['material_name']} to batch {batch_name}"
        )
        flash('Material linked to batch successfully.', 'success')
    except Exception as e:
        if conn is not None:
            conn.rollback()
            print(f"Transaction failed: {e}")
            flash('Unable to link material usage. Please try again.', 'danger')
    finally:
        if conn is not None:
            conn.close()

    return redirect(url_for('batches_bp.batch_detail', id=id))
