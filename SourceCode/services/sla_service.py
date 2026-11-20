"""
SLA Engine: Policy Calculation, Due Date Target, and Breach Detection
"""

from datetime import datetime, timedelta
import sqlite3

# Default resolution hours fallback in case DB not yet queried
DEFAULT_SLA_HOURS = {
    'Critical': 4,
    'High': 8,
    'Medium': 24,
    'Low': 72
}

def calculate_due_date(priority: str, db=None) -> datetime:
    """Calculates due date based on SLA policy table for the given priority."""
    hours = DEFAULT_SLA_HOURS.get(priority, 24)
    if db:
        try:
            row = db.execute(
                "SELECT resolution_hours FROM sla_policies WHERE priority_level = ?",
                (priority,)
            ).fetchone()
            if row:
                hours = row['resolution_hours']
        except Exception:
            pass
    return datetime.now() + timedelta(hours=hours)

def check_and_update_breaches(db) -> int:
    """
    Scans all active (non-resolved, non-closed) tickets.
    If current UTC time > due_date and is_breached == 0, flags the breach
    and records an audit log entry.
    Returns count of newly breached tickets.
    """
    now = datetime.now()
    active_tickets = db.execute("""
        SELECT ticket_id, ticket_number, due_date, is_breached
        FROM tickets
        WHERE status NOT IN ('Resolved', 'Closed')
    """).fetchall()

    newly_breached = 0
    for t in active_tickets:
        due = t['due_date']
        if isinstance(due, str):
            try:
                due = datetime.fromisoformat(due)
            except ValueError:
                continue

        if now > due and t['is_breached'] == 0:
            db.execute("UPDATE tickets SET is_breached = 1 WHERE ticket_id = ?", (t['ticket_id'],))
            db.execute("""
                INSERT INTO audit_logs (ticket_id, actor_id, action_type, old_value, new_value)
                VALUES (?, 1, 'SLA Breach Auto-Escalation', 'Within SLA', 'BREACHED')
            """, (t['ticket_id'],))
            newly_breached += 1

    if newly_breached > 0:
        db.commit()

    return newly_breached

def format_time_remaining(due_date) -> dict:
    """Returns structured time remaining info with breach badge styling."""
    if isinstance(due_date, str):
        try:
            due_date = datetime.fromisoformat(due_date)
        except ValueError:
            return {"text": "Unknown", "class": "secondary", "breached": False}

    now = datetime.now()
    if now > due_date:
        diff = now - due_date
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        return {
            "text": f"Breached by {hours}h {minutes}m",
            "class": "danger",
            "breached": True
        }
    else:
        diff = due_date - now
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        badge_class = "warning" if hours < 2 else "info"
        return {
            "text": f"{hours}h {minutes}m left",
            "class": badge_class,
            "breached": False
        }
