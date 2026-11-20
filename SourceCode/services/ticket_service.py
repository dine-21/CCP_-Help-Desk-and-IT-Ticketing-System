"""
Ticket Service: Audit Logging, Ticket Number Generator, and Helpers
"""

import os
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config

def generate_ticket_number(db) -> str:
    """Generates unique formatted ticket number, e.g. HD-2026-0001."""
    year = datetime.now().year
    cursor = db.execute("SELECT COUNT(*) AS total FROM tickets")
    count = cursor.fetchone()['total'] + 1
    return f"HD-{year}-{count:04d}"

def log_audit(ticket_id: int, actor_id: int, action_type: str, old_val: str, new_val: str, db):
    """Inserts a structured immutable audit log record."""
    db.execute("""
        INSERT INTO audit_logs (ticket_id, actor_id, action_type, old_value, new_value)
        VALUES (?, ?, ?, ?, ?)
    """, (ticket_id, actor_id, action_type, str(old_val), str(new_val)))

def allowed_file(filename: str) -> bool:
    """Checks if uploaded file extension is permitted."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

def save_attachment(file_obj, ticket_id: int, db) -> tuple[bool, str]:
    """Validates and saves ticket file attachment."""
    if not file_obj or file_obj.filename == '':
        return False, "No file selected."

    if not allowed_file(file_obj.filename):
        return False, f"Invalid file type. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}"

    orig_name = secure_filename(file_obj.filename)
    timestamp_prefix = datetime.now().strftime("%Y%m%d%H%M%S")
    stored_name = f"t{ticket_id}_{timestamp_prefix}_{orig_name}"
    save_path = os.path.join(Config.UPLOAD_FOLDER, stored_name)

    file_obj.save(save_path)
    file_size = os.path.getsize(save_path)
    mime_type = file_obj.mimetype or "application/octet-stream"

    db.execute("""
        INSERT INTO attachments (ticket_id, file_path, original_filename, file_size, mime_type)
        VALUES (?, ?, ?, ?, ?)
    """, (ticket_id, stored_name, orig_name, file_size, mime_type))
    db.commit()

    return True, orig_name
