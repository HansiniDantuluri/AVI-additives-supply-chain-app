from flask import Blueprint, render_template, request, session, redirect, flash
import mysql.connector

from .db import get_db_connection, log_action
from .extensions import bcrypt

auth_bp = Blueprint('auth_bp', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        conn = None
        user = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username = %s",
                (username,),
            )
            user = cursor.fetchone()
        except mysql.connector.Error:
            flash('An error occurred while logging in. Please try again.', 'danger')
        finally:
            if conn is not None:
                conn.close()

        if user and bcrypt.check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect('/dashboard')

        flash('Invalid username or password', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/login')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect('/login')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'staff')

        if not username:
            flash('Username is required.', 'warning')
            return render_template('register.html')

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash('Username already exists.', 'warning')
                return render_template('register.html')

            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, password_hash, role),
            )
            conn.commit()

            log_action(session.get('user_id'), f'Created user: {username}')
            flash('User created successfully.', 'success')
            return redirect('/register')
        except mysql.connector.Error:
            flash('An error occurred while creating the user. Please try again.', 'danger')
        finally:
            if conn is not None:
                conn.close()

    return render_template('register.html')