from flask import Blueprint, flash, redirect, session
import mysql.connector

from .db import get_db_connection, log_action
from .decorators import login_required

alerts_bp = Blueprint('alerts_bp', __name__)


@alerts_bp.route('/alerts/acknowledge/<int:alert_id>', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE alerts SET acknowledged = TRUE WHERE id = %s",
            (alert_id,),
        )
        conn.commit()
        log_action(session.get('user_id'), f'Acknowledged alert id {alert_id}')
        flash('Alert acknowledged successfully.', 'success')
    except mysql.connector.Error:
        flash('Unable to acknowledge the alert. Please try again.', 'danger')
    finally:
        if conn is not None:
            conn.close()

    return redirect('/dashboard')
