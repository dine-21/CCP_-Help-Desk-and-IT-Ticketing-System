"""
Authentication Service & Session Decorators (RBAC)
"""

from functools import wraps
from flask import session, redirect, url_for, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(hashed_password: str, password: str) -> bool:
    return check_password_hash(hashed_password, password)

def login_required(view_func):
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        return view_func(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for('auth.login'))
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash(f"Access Denied: The '{user_role}' role is unauthorized to view this resource.", "danger")
                return redirect(url_for('tickets.list_tickets'))
            return view_func(*args, **kwargs)
        return decorated_function
    return decorator
