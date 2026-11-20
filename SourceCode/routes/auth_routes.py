from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
from services.auth_service import hash_password, verify_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('tickets.list_tickets'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return render_template('auth/login.html')

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,)).fetchone()

        if user and verify_password(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['user_id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            session['department'] = user['department']
            flash(f"Welcome back, {user['name']}! Signed in as {user['role']}.", "success")
            
            if user['role'] == 'Admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('tickets.list_tickets'))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('tickets.list_tickets'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        department = request.form.get('department', 'General Support').strip()

        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template('auth/register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('auth/register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('auth/register.html')

        db = get_db()
        existing = db.execute("SELECT user_id FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
        if existing:
            flash("An account with this email already exists.", "danger")
            return render_template('auth/register.html')

        password_hash = hash_password(password)
        db.execute("""
            INSERT INTO users (name, email, password_hash, role, department)
            VALUES (?, ?, ?, 'Requester', ?)
        """, (name, email, password_hash, department))
        db.commit()

        flash("Registration successful! You may now sign in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for('auth.login'))
