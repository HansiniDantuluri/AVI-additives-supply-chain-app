import os
import mysql.connector
from datetime import date, timedelta, datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Blueprint, render_template, request

from .db import get_db_connection
from .decorators import login_required, admin_required

reports_bp = Blueprint('reports_bp', __name__)


def _parse_date_param(value, default_date):
    try:
        if value:
            return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        pass
    return default_date


@reports_bp.route('/reports/stock-levels', methods=['GET'])
@login_required
@admin_required
def stock_levels_report():
    materials = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            '''
            SELECT material_name, current_quantity, reorder_level
            FROM materials
            WHERE status = 'active'
            ORDER BY material_name
            '''
        )
        materials = cursor.fetchall()
    except mysql.connector.Error:
        return render_template('reports_stock_levels.html', message='Unable to load stock level data.')
    finally:
        if conn is not None:
            conn.close()

    if not materials:
        return render_template('reports_stock_levels.html', message='No materials found')

    names = [row['material_name'] for row in materials]
    current_values = [float(row['current_quantity']) for row in materials]
    reorder_values = [float(row['reorder_level']) for row in materials]
    colors = ['red' if current_values[i] <= reorder_values[i] else 'green' for i in range(len(materials))]

    fig, ax = plt.subplots(figsize=(max(8, len(names) * 0.5), 5))
    x = range(len(names))
    width = 0.35

    ax.bar([xi - width / 2 for xi in x], current_values, width, label='Current Quantity', color=colors)
    ax.bar([xi + width / 2 for xi in x], reorder_values, width, label='Reorder Level', color='grey')
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, rotation=45, ha='right')
    ax.set_ylabel('Quantity')
    ax.set_title('Stock Levels vs Reorder Levels')
    ax.legend()
    fig.tight_layout()

    chart_path = os.path.join('static', 'charts', 'stock_levels.png')
    fig.savefig(chart_path)
    plt.close(fig)

    return render_template('reports_stock_levels.html', message=None)


@reports_bp.route('/reports/consumption', methods=['GET'])
@login_required
@admin_required
def consumption_report():
    today = date.today()
    default_start = today - timedelta(days=30)
    start_date = _parse_date_param(request.args.get('start_date'), default_start)
    end_date = _parse_date_param(request.args.get('end_date'), today)

    rows = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Group by material name and sum quantity_used to calculate total consumption per material in the date range.
        cursor.execute(
            '''
            SELECT materials.material_name,
                   SUM(batch_usage.quantity_used) as total_used
            FROM batch_usage
            JOIN materials ON batch_usage.material_id = materials.id
            JOIN batches ON batch_usage.batch_id = batches.id
            WHERE batches.production_date BETWEEN %s AND %s
            GROUP BY materials.material_name
            HAVING total_used > 0
            ORDER BY total_used DESC
            ''',
            (start_date, end_date),
        )
        rows = cursor.fetchall()
    except mysql.connector.Error:
        return render_template('reports_consumption.html', start_date=start_date, end_date=end_date, message='Unable to load consumption data.')
    finally:
        if conn is not None:
            conn.close()

    if not rows:
        return render_template('reports_consumption.html', start_date=start_date, end_date=end_date, message='No consumption data for this date range')

    names = [row['material_name'] for row in rows]
    totals = [float(row['total_used']) for row in rows]

    fig, ax = plt.subplots(figsize=(max(10, len(names) * 0.6), 5))
    ax.bar(range(len(names)), totals, color='steelblue')
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha='right')
    ax.set_ylabel('Total Used')
    ax.set_title(f'Consumption from {start_date} to {end_date}')
    fig.tight_layout()

    chart_path = os.path.join('static', 'charts', 'consumption.png')
    fig.savefig(chart_path)
    plt.close(fig)

    return render_template('reports_consumption.html', start_date=start_date, end_date=end_date, message=None)


@reports_bp.route('/reports/usage-trends', methods=['GET'])
@login_required
@admin_required
def usage_trends_report():
    today = date.today()
    default_start = today - timedelta(days=30)
    start_date = _parse_date_param(request.args.get('start_date'), default_start)
    end_date = _parse_date_param(request.args.get('end_date'), today)

    rows = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Group by material name and batch production date to calculate total usage per material per date.
        cursor.execute(
            '''
            SELECT materials.material_name, batches.production_date,
                   SUM(batch_usage.quantity_used) as total_used
            FROM batch_usage
            JOIN materials ON batch_usage.material_id = materials.id
            JOIN batches ON batch_usage.batch_id = batches.id
            WHERE batches.production_date BETWEEN %s AND %s
            GROUP BY materials.material_name, batches.production_date
            ORDER BY batches.production_date
            ''',
            (start_date, end_date),
        )
        rows = cursor.fetchall()
    except mysql.connector.Error:
        return render_template('reports_usage_trends.html', start_date=start_date, end_date=end_date, message='Unable to load usage trends data.')
    finally:
        if conn is not None:
            conn.close()

    if not rows:
        return render_template('reports_usage_trends.html', start_date=start_date, end_date=end_date, message='No usage data for this date range')

    trends = {}
    for row in rows:
        material_name = row['material_name']
        production_date = row['production_date']
        total_used = float(row['total_used'])
        trends.setdefault(material_name, []).append((production_date, total_used))

    fig, ax = plt.subplots(figsize=(max(10, len(set(row['production_date'] for row in rows)) * 0.6), 6))
    for material_name, points in trends.items():
        points.sort(key=lambda x: x[0])
        dates = [point[0] for point in points]
        values = [point[1] for point in points]
        ax.plot(dates, values, marker='o', label=material_name)

    ax.set_xlabel('Production Date')
    ax.set_ylabel('Quantity Used')
    ax.set_title(f'Usage Trends from {start_date} to {end_date}')
    ax.legend()
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()

    chart_path = os.path.join('static', 'charts', 'usage_trends.png')
    fig.savefig(chart_path)
    plt.close(fig)

    return render_template('reports_usage_trends.html', start_date=start_date, end_date=end_date, message=None)
