from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db
from services.auth_service import login_required, role_required
from services.sla_service import check_and_update_breaches, format_time_remaining

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard', strict_slashes=False)
@login_required
@role_required('Admin')
def dashboard():
    db = get_db()
    check_and_update_breaches(db)

    # 1. High Level KPI Metrics
    total_tickets = db.execute("SELECT COUNT(*) AS total FROM tickets").fetchone()['total']
    open_tickets = db.execute("SELECT COUNT(*) AS total FROM tickets WHERE status = 'Open'").fetchone()['total']
    in_progress = db.execute("SELECT COUNT(*) AS total FROM tickets WHERE status = 'In Progress'").fetchone()['total']
    resolved_tickets = db.execute("SELECT COUNT(*) AS total FROM tickets WHERE status = 'Resolved'").fetchone()['total']
    closed_tickets = db.execute("SELECT COUNT(*) AS total FROM tickets WHERE status = 'Closed'").fetchone()['total']
    breached_tickets = db.execute("SELECT COUNT(*) AS total FROM tickets WHERE is_breached = 1").fetchone()['total']

    # 2. Average Resolution Time (in hours)
    avg_res_row = db.execute("""
        SELECT AVG((julianday(resolved_at) - julianday(created_at)) * 24) AS avg_hours
        FROM tickets
        WHERE resolved_at IS NOT NULL
    """).fetchone()
    avg_resolution_hours = round(avg_res_row['avg_hours'], 1) if avg_res_row and avg_res_row['avg_hours'] else 0.0

    # 3. Customer Satisfaction (CSAT) Breakdown
    csat_row = db.execute("""
        SELECT AVG(rating) AS avg_csat, COUNT(rating) AS total_rated
        FROM tickets
        WHERE rating IS NOT NULL
    """).fetchone()
    avg_csat = round(csat_row['avg_csat'], 2) if csat_row and csat_row['avg_csat'] else 0.0
    total_rated = csat_row['total_rated'] if csat_row else 0

    # 4. Tickets by Category
    category_stats = db.execute("""
        SELECT c.name, COUNT(t.ticket_id) AS count
        FROM categories c
        LEFT JOIN tickets t ON c.category_id = t.category_id
        GROUP BY c.category_id, c.name
        ORDER BY count DESC
    """).fetchall()

    # 5. Overdue / At Risk Tickets Requiring Supervisor Escalation
    overdue_rows = db.execute("""
        SELECT t.*, u.name AS requester_name, a.name AS agent_name, c.name AS category_name
        FROM tickets t
        JOIN users u ON t.requester_id = u.user_id
        LEFT JOIN users a ON t.assigned_agent_id = a.user_id
        JOIN categories c ON t.category_id = c.category_id
        WHERE (t.is_breached = 1 OR datetime(t.due_date) < datetime('now'))
          AND t.status NOT IN ('Resolved', 'Closed')
        ORDER BY t.due_date ASC
    """).fetchall()

    overdue_tickets = []
    for r in overdue_rows:
        td = dict(r)
        td['sla_info'] = format_time_remaining(td['due_date'])
        overdue_tickets.append(td)

    # 6. Team Workload (Tickets per Agent)
    agent_workload = db.execute("""
        SELECT u.user_id, u.name,
               COUNT(t.ticket_id) AS total_assigned,
               SUM(CASE WHEN t.status IN ('Assigned', 'In Progress') THEN 1 ELSE 0 END) AS active_load
        FROM users u
        LEFT JOIN tickets t ON u.user_id = t.assigned_agent_id
        WHERE u.role IN ('Agent', 'Admin')
        GROUP BY u.user_id, u.name
        ORDER BY active_load DESC
    """).fetchall()

    return render_template('admin/dashboard.html',
                           kpis={
                               'total': total_tickets,
                               'open': open_tickets,
                               'in_progress': in_progress,
                               'resolved': resolved_tickets,
                               'closed': closed_tickets,
                               'breached': breached_tickets,
                               'avg_res_hours': avg_resolution_hours,
                               'avg_csat': avg_csat,
                               'total_rated': total_rated
                           },
                           category_stats=category_stats,
                           overdue_tickets=overdue_tickets,
                           agent_workload=agent_workload)

@admin_bp.route('/admin/users', strict_slashes=False)
@login_required
@role_required('Admin')
def user_management():
    db = get_db()
    users = db.execute("SELECT * FROM users ORDER BY role, name").fetchall()
    return render_template('admin/users.html', users=users)
