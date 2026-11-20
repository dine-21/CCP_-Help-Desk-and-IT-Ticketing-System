import os
from flask import Flask, render_template
from config import Config
from database import init_db, close_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints conditionally to support staged module integration
    try:
        from routes.auth_routes import auth_bp
        app.register_blueprint(auth_bp)
    except ImportError:
        pass

    try:
        from routes.ticket_routes import ticket_bp
        app.register_blueprint(ticket_bp)
    except ImportError:
        pass

    try:
        from routes.kb_routes import kb_bp
        app.register_blueprint(kb_bp)
    except ImportError:
        pass

    try:
        from routes.admin_routes import admin_bp
        app.register_blueprint(admin_bp)
    except ImportError:
        pass

    # Register database teardown
    app.teardown_appcontext(close_db)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html'), 404

    @app.errorhandler(403)
    def access_forbidden(e):
        return render_template('base.html'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html'), 500

    # Ensure DB exists and is properly initialized
    needs_init = False
    if not os.path.exists(Config.DATABASE) or os.path.getsize(Config.DATABASE) == 0:
        needs_init = True
    else:
        try:
            import sqlite3
            conn = sqlite3.connect(Config.DATABASE)
            tbl_count = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            conn.close()
            if tbl_count < 8:
                needs_init = True
        except Exception:
            needs_init = True

    if needs_init:
        with app.app_context():
            print("Database not found or incomplete. Initializing and seeding...")
            from seed_data import seed
            seed()

    return app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print(" IT HelpDesk System (Group 03 — SE CCP Project #11)")
    print(" Running locally at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
