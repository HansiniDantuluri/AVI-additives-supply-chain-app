from flask import Blueprint, render_template, session
import mysql.connector

from .decorators import login_required
from .db import get_db_connection
from .models import Material

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    low_stock_materials = []
    unacknowledged_alerts = []
    material_objects = []
    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT m.id AS material_id,
                   m.material_name,
                   m.current_quantity,
                   m.reorder_level,
                   m.unit_of_measure,
                   s.supplier_name,
                   s.email AS supplier_email
            FROM materials AS m
            JOIN suppliers AS s ON m.supplier_id = s.id
            WHERE m.status = 'active'
              AND m.current_quantity <= m.reorder_level
            """
        )
        low_stock_materials = cursor.fetchall()

        # Instantiate Material objects from database rows to demonstrate OOP
        # Each row is converted into a Material object with encapsulated attributes
        material_objects = [
            Material(
                id=row['material_id'],
                material_name=row['material_name'],
                current_quantity=float(row['current_quantity']),
                reorder_level=float(row['reorder_level']),
                unit_of_measure=row['unit_of_measure'],
                supplier_name=row['supplier_name']
            )
            for row in low_stock_materials
        ]

        cursor.execute(
            """
            SELECT a.id AS alert_id,
                   a.message,
                   m.material_name
            FROM alerts AS a
            JOIN materials AS m ON a.material_id = m.id
            WHERE a.acknowledged = FALSE
            """
        )
        unacknowledged_alerts = cursor.fetchall()
    except mysql.connector.Error:
        low_stock_materials = []
        unacknowledged_alerts = []
        material_objects = []
    finally:
        if conn is not None:
            conn.close()

    return render_template(
        'dashboard.html',
        low_stock_materials=low_stock_materials,
        unacknowledged_alerts=unacknowledged_alerts,
        material_objects=material_objects,
        role=session.get('role'),
    )
