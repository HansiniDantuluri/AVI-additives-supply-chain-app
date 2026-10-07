from flask import Blueprint, render_template, request, redirect, flash, session, url_for, current_app
import mysql.connector

from .db import get_db_connection, log_action
from .decorators import login_required
from .email_utils import send_order_email, is_valid_email

orders_bp = Blueprint('orders_bp', __name__)


@orders_bp.route('/orders', methods=['GET'])
@login_required
def orders_list():
    orders = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            '''
            SELECT po.id, po.order_date, po.expected_delivery, po.status,
                   s.supplier_name
            FROM purchase_orders AS po
            JOIN suppliers AS s ON po.supplier_id = s.id
            ORDER BY po.order_date DESC
            '''
        )
        orders = cursor.fetchall()
    except mysql.connector.Error:
        flash('Unable to load orders. Please try again.', 'danger')
    finally:
        if conn is not None:
            conn.close()

    return render_template('orders_list.html', orders=orders)


@orders_bp.route('/orders/<int:id>', methods=['GET'])
@login_required
def order_detail(id):
    order = None
    items = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            '''
            SELECT po.id, po.order_date, po.expected_delivery, po.status,
                   s.supplier_name, s.email AS supplier_email
            FROM purchase_orders AS po
            JOIN suppliers AS s ON po.supplier_id = s.id
            WHERE po.id = %s
            ''',
            (id,),
        )
        order = cursor.fetchone()

        if not order:
            flash('Order not found.', 'warning')
            return redirect('/orders')

        cursor.execute(
            '''
            SELECT oi.quantity, m.material_name
            FROM order_items AS oi
            JOIN materials AS m ON oi.material_id = m.id
            WHERE oi.po_id = %s
            ORDER BY m.material_name ASC
            ''',
            (id,),
        )
        items = cursor.fetchall()
    except mysql.connector.Error:
        flash('Unable to load order details. Please try again.', 'danger')
        return redirect('/orders')
    finally:
        if conn is not None:
            conn.close()

    return render_template('order_detail.html', order=order, items=items)


@orders_bp.route('/orders/create', methods=['GET', 'POST'])
@login_required
def create_order():
    if request.method == 'GET':
        materials = []
        suppliers = []
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                '''
                SELECT id, material_name, current_quantity, reorder_level,
                       unit_of_measure
                FROM materials
                WHERE status = 'active'
                ORDER BY material_name ASC
                ''',
            )
            materials = cursor.fetchall()

            cursor.execute(
                '''
                SELECT id, supplier_name
                FROM suppliers
                ORDER BY supplier_name ASC
                ''',
            )
            suppliers = cursor.fetchall()
        except mysql.connector.Error:
            flash('Unable to load order form data. Please try again.', 'danger')
            return redirect('/orders')
        finally:
            if conn is not None:
                conn.close()

        return render_template('order_form.html', suppliers=suppliers, materials=materials)

    supplier_id = request.form.get('supplier_id')
    expected_delivery = request.form.get('expected_delivery', '').strip()
    selected_material_ids = request.form.getlist('material_ids')
    all_material_ids = request.form.getlist('all_material_ids')
    quantities = request.form.getlist('quantities')

    errors = []
    if not supplier_id:
        errors.append('Supplier selection is required.')

    if not selected_material_ids:
        errors.append('At least one material must be selected for the order.')

    if len(all_material_ids) != len(quantities):
        errors.append('Unable to read material quantities. Please try again.')

    selected_items = []
    if not errors:
        for material_id in selected_material_ids:
            try:
                index = all_material_ids.index(material_id)
            except ValueError:
                errors.append('Invalid material selection.')
                continue

            quantity_value = quantities[index].strip() if index < len(quantities) else ''
            try:
                quantity = float(quantity_value)
                if quantity <= 0:
                    raise ValueError()
            except ValueError:
                errors.append('Each selected material must have a positive quantity.')
                continue

            selected_items.append({'material_id': material_id, 'quantity': quantity})

    if errors:
        for message in errors:
            flash(message, 'warning')
        return redirect('/orders/create')

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            '''
            SELECT supplier_name, email
            FROM suppliers
            WHERE id = %s
            ''',
            (supplier_id,),
        )
        supplier = cursor.fetchone()
        if not supplier:
            flash('Selected supplier was not found.', 'danger')
            return redirect('/orders/create')

        cursor.execute(
            '''
            INSERT INTO purchase_orders (supplier_id, order_date, expected_delivery)
            VALUES (%s, CURDATE(), %s)
            ''',
            (supplier_id, expected_delivery or None),
        )
        po_id = cursor.lastrowid

        for item in selected_items:
            cursor.execute(
                '''
                INSERT INTO order_items (po_id, material_id, quantity)
                VALUES (%s, %s, %s)
                ''',
                (po_id, item['material_id'], item['quantity']),
            )

        conn.commit()

        material_ids = [item['material_id'] for item in selected_items]
        placeholders = ','.join(['%s'] * len(material_ids))
        cursor.execute(
            f'''
            SELECT id, material_name
            FROM materials
            WHERE id IN ({placeholders})
            ''',
            tuple(material_ids),
        )
        material_rows = cursor.fetchall()
        material_map = {str(row['id']): row['material_name'] for row in material_rows}

        email_items = [
            {'material_name': material_map.get(str(item['material_id']), 'Unknown'), 'quantity': item['quantity']}
            for item in selected_items
        ]

        try:
            if not is_valid_email(supplier['email']):
                raise ValueError('Invalid supplier email address.')

            send_order_email(
                mail=current_app.extensions.get('mail'),
                supplier_email=supplier['email'],
                supplier_name=supplier['supplier_name'],
                items=email_items,
            )
        except Exception as e:
            import traceback
            with open('email_error.txt', 'w') as f:
                f.write(f"Email failed: {type(e).__name__}: {e}\n")
                traceback.print_exc(file=f)
            flash('Order saved but email notification failed.', 'warning')

        log_action(session.get('user_id'), f"Created purchase order for {supplier['supplier_name']}")
        flash('Purchase order created successfully.', 'success')
        return redirect(url_for('orders_bp.order_detail', id=po_id))
    except mysql.connector.Error as e:
        import traceback
        with open('email_error.txt', 'a') as f:
            f.write(f"DB error: {type(e).__name__}: {e}\n")
            traceback.print_exc(file=f)
        if conn is not None:
            conn.rollback()
        flash('Unable to create purchase order. Please try again.', 'danger')
        return redirect('/orders/create')
    finally:
        if conn is not None:
            conn.close()


@orders_bp.route('/orders/<int:id>/update-status', methods=['POST'])
@login_required
def update_order_status(id):
    new_status = request.form.get('new_status')
    if not new_status:
        flash('Status selection is required.', 'warning')
        return redirect(url_for('orders_bp.order_detail', id=id))

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            '''
            SELECT status
            FROM purchase_orders
            WHERE id = %s
            ''',
            (id,),
        )
        order = cursor.fetchone()
        if not order:
            flash('Order not found.', 'warning')
            return redirect('/orders')

        current_status = order['status']
        valid_transitions = {
            'Pending': 'Confirmed',
            'Confirmed': 'Delivered',
        }

        if valid_transitions.get(current_status) != new_status:
            flash('Invalid status transition.', 'danger')
            return redirect(url_for('orders_bp.order_detail', id=id))

        cursor.execute(
            '''
            UPDATE purchase_orders
            SET status = %s
            WHERE id = %s
            ''',
            (new_status, id),
        )
        conn.commit()

        log_action(session.get('user_id'), f"Updated order {id} status to {new_status}")
        flash('Order status updated successfully.', 'success')
    except mysql.connector.Error:
        flash('Unable to update order status. Please try again.', 'danger')
    finally:
        if conn is not None:
            conn.close()

    return redirect(url_for('orders_bp.order_detail', id=id))