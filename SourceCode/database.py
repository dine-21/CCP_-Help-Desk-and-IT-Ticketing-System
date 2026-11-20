import sqlite3
import os
from flask import g
from config import Config

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            Config.DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    db = sqlite3.connect(Config.DATABASE)
    db.execute("PRAGMA foreign_keys = ON;")
    cursor = db.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(120) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL CHECK (role IN ('Requester', 'Agent', 'Admin')),
        department VARCHAR(80) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. SLA Policies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sla_policies (
        sla_id INTEGER PRIMARY KEY AUTOINCREMENT,
        priority_level VARCHAR(20) NOT NULL UNIQUE CHECK (priority_level IN ('Low', 'Medium', 'High', 'Critical')),
        response_hours INTEGER NOT NULL,
        resolution_hours INTEGER NOT NULL
    );
    """)

    # 3. Categories Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(50) NOT NULL UNIQUE,
        description TEXT,
        sla_id INTEGER NOT NULL,
        FOREIGN KEY (sla_id) REFERENCES sla_policies(sla_id) ON DELETE RESTRICT
    );
    """)

    # 4. Tickets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_number VARCHAR(20) NOT NULL UNIQUE,
        requester_id INTEGER NOT NULL,
        assigned_agent_id INTEGER,
        category_id INTEGER NOT NULL,
        priority VARCHAR(20) NOT NULL CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
        status VARCHAR(20) NOT NULL DEFAULT 'Open' CHECK (status IN ('Open', 'Assigned', 'In Progress', 'Pending Customer', 'Resolved', 'Closed')),
        subject VARCHAR(150) NOT NULL,
        description TEXT NOT NULL,
        due_date TIMESTAMP NOT NULL,
        is_breached INTEGER DEFAULT 0,
        rating INTEGER CHECK (rating BETWEEN 1 AND 5),
        feedback TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (requester_id) REFERENCES users(user_id) ON DELETE RESTRICT,
        FOREIGN KEY (assigned_agent_id) REFERENCES users(user_id) ON DELETE SET NULL,
        FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE RESTRICT
    );
    """)

    # 5. Comments & Notes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        is_internal INTEGER DEFAULT 0 CHECK (is_internal IN (0, 1)),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES users(user_id) ON DELETE RESTRICT
    );
    """)

    # 6. Attachments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attachments (
        attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        file_path VARCHAR(255) NOT NULL,
        original_filename VARCHAR(150) NOT NULL,
        file_size INTEGER NOT NULL,
        mime_type VARCHAR(100),
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
    );
    """)

    # 7. Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        actor_id INTEGER NOT NULL,
        action_type VARCHAR(50) NOT NULL,
        old_value VARCHAR(255),
        new_value VARCHAR(255),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
        FOREIGN KEY (actor_id) REFERENCES users(user_id) ON DELETE RESTRICT
    );
    """)

    # 8. Knowledge Base Articles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kb_articles (
        article_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(150) NOT NULL,
        content TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        tags VARCHAR(150),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
    );
    """)

    db.commit()
    db.close()
    print("Database tables initialized successfully.")
