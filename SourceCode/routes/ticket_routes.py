import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from database import get_db
from config import Config
from services.auth_service import login_required, role_required
from services.state_machine import validate_transition, VALID_TRANSITIONS
from services.sla_service import calculate_due_date, check_and_update_breaches, format_time_remaining
from services.ticket_service import generate_ticket_number, log_audit, save_attachment

ticket_bp = Blueprint('tickets', __name__)

@ticket_bp.route('/', strict_slashes=False)
@ticket_bp.route('/tickets', strict_slashes=False)
@login_required
def list_tickets():
    db = get_db()
    check_and_update_breaches(db)

    user_id = session.get('user_id')
    user_role = session.get('role')

    # Query Filters
    status_filter = request.args.get('status', '').strip()
    priority_filter = request.args.get('priority', '').strip()
    category_filter = request.args.get('category', '').strip()
    search_query = request.args.get('q', '').strip()
    view_scope = request.args.get('scope', 'all')  # 'all' or 'assigned_to_me'

    query = """
        SELECT t.*, u.name AS requester_name, a.name AS agent_name, c.name AS category_name
        FROM tickets t
        JOIN users u ON t.requester_id = u.user_id
        LEFT JOIN users a ON t.assigned_agent_id = a.user_id
        JOIN categories c ON t.category_id = c.category_id
        WHERE 1=1
    """
    params = []

    # RBAC Data Isolation: Requesters can only see their own tickets
    if user_role == 'Requester':
        query += " AND t.requester_id = ?"
        params.append(user_id)
    elif user_role == 'Agent' and view_scope == 'assigned_to_me':
        query += " AND t.assigned_agent_id = ?"
        params.append(user_id)

    # Dynamic filters
    if status_filter:
        query += " AND t.status = ?"
        params.append(status_filter)
    if priority_filter:
        query += " AND t.priority = ?"
        params.append(priority_filter)
    if category_filter:
        query += " AND t.category_id = ?"
        params.append(category_filter)
    if search_query:
        query += " AND (t.ticket_number LIKE ? OR t.subject LIKE ? OR t.description LIKE ?)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term, like_term])

    query += " ORDER BY t.created_at DESC"
    tickets_rows = db.execute(query, params).fetchall()

    # Enrich tickets with SLA remaining info
    tickets = []
    for r in tickets_rows:
        tdict = dict(r)
        tdict['sla_info'] = format_time_remaining(tdict['due_date'])
        tickets.append(tdict)

    # Load categories for filter dropdown
    categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()

    # Count badges for quick filters
    if user_role == 'Requester':
        counts = db.execute("""
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS count_open,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS count_in_prog,
                SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS count_resolved
            FROM tickets WHERE requester_id = ?
        """, (user_id,)).fetchone()
    else:
        counts = db.execute("""
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS count_open,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS count_in_prog,
                SUM(CASE WHEN is_breached = 1 AND status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS count_breached
            FROM tickets
        """).fetchone()

    return render_template('tickets/list.html',
                           tickets=tickets,
                           categories=categories,
                           counts=counts,
                           selected_status=status_filter,
                           selected_priority=priority_filter,
                           selected_category=category_filter,
                           search_query=search_query,
                           view_scope=view_scope)

@ticket_bp.route('/tickets/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    db = get_db()

    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id')
        priority = request.form.get('priority', 'Medium')
        user_id = session.get('user_id')

        # Form Validations
        if not subject or len(subject) < 5:
            flash("Subject must be at least 5 characters long.", "danger")
            categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
            return render_template('tickets/create.html', categories=categories)

        if not description or len(description) < 10:
            flash("Description must be at least 10 characters long to provide sufficient detail.", "danger")
            categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
            return render_template('tickets/create.html', categories=categories)

        if not category_id:
            flash("Please select a relevant incident category.", "danger")
            categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
            return render_template('tickets/create.html', categories=categories)

        if priority not in ['Low', 'Medium', 'High', 'Critical']:
            priority = 'Medium'

        # SLA Calculation
        due_date = calculate_due_date(priority, db)
        ticket_number = generate_ticket_number(db)

        # Insert Ticket
        cursor = db.execute("""
            INSERT INTO tickets (ticket_number, requester_id, category_id, priority, status, subject, description, due_date)
            VALUES (?, ?, ?, ?, 'Open', ?, ?, ?)
        """, (ticket_number, user_id, category_id, priority, subject, description, due_date.strftime("%Y-%m-%d %H:%M:%S")))
        ticket_id = cursor.lastrowid

        # Audit Log Record
        log_audit(ticket_id, user_id, 'Ticket Created', 'None', f"Created {ticket_number} (Priority: {priority})", db)

        # Handle Attachment
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '':
                success, msg = save_attachment(file, ticket_id, db)
                if not success:
                    flash(f"Ticket logged, but attachment warning: {msg}", "warning")
                else:
                    log_audit(ticket_id, user_id, 'Attachment Uploaded', 'None', msg, db)

        db.commit()
        flash(f"Ticket #{ticket_number} successfully submitted. Our IT team has been notified.", "success")
        return redirect(url_for('tickets.ticket_detail', ticket_id=ticket_id))

    categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    return render_template('tickets/create.html', categories=categories)

@ticket_bp.route('/tickets/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    db = get_db()
    check_and_update_breaches(db)

    user_id = session.get('user_id')
    user_role = session.get('role')

    ticket = db.execute("""
        SELECT t.*, u.name AS requester_name, u.email AS requester_email, u.department AS requester_dept,
               a.name AS agent_name, a.email AS agent_email,
               c.name AS category_name, c.description AS category_desc,
               p.response_hours, p.resolution_hours
        FROM tickets t
        JOIN users u ON t.requester_id = u.user_id
        LEFT JOIN users a ON t.assigned_agent_id = a.user_id
        JOIN categories c ON t.category_id = c.category_id
        JOIN sla_policies p ON c.sla_id = p.sla_id
        WHERE t.ticket_id = ?
    """, (ticket_id,)).fetchone()

    if not ticket:
        flash("The requested ticket does not exist.", "danger")
        return redirect(url_for('tickets.list_tickets'))

    # Security check: Requesters can only view their own tickets
    if user_role == 'Requester' and ticket['requester_id'] != user_id:
        flash("Access Denied: You are not authorized to view tickets filed by other users.", "danger")
        return redirect(url_for('tickets.list_tickets'))

    # SLA Info
    sla_info = format_time_remaining(ticket['due_date'])

    # Comments Filtering based on RBAC
    # Requesters CANNOT see internal technician notes!
    if user_role == 'Requester':
        comments = db.execute("""
            SELECT c.*, u.name AS author_name, u.role AS author_role
            FROM comments c
            JOIN users u ON c.author_id = u.user_id
            WHERE c.ticket_id = ? AND c.is_internal = 0
            ORDER BY c.created_at ASC
        """, (ticket_id,)).fetchall()
    else:
        comments = db.execute("""
            SELECT c.*, u.name AS author_name, u.role AS author_role
            FROM comments c
            JOIN users u ON c.author_id = u.user_id
            WHERE c.ticket_id = ?
            ORDER BY c.created_at ASC
        """, (ticket_id,)).fetchall()

    # Attachments
    attachments = db.execute("""
        SELECT * FROM attachments WHERE ticket_id = ? ORDER BY uploaded_at ASC
    """, (ticket_id,)).fetchall()

    # Audit Trail
    audit_trail = db.execute("""
        SELECT a.*, u.name AS actor_name, u.role AS actor_role
        FROM audit_logs a
        JOIN users u ON a.actor_id = u.user_id
        WHERE a.ticket_id = ?
        ORDER BY a.timestamp ASC
    """, (ticket_id,)).fetchall()

    # Allowed Next Statuses from State Machine
    current_status = ticket['status']
    allowed_transitions = VALID_TRANSITIONS.get(current_status, [])

    # List of Agents for Admin/Agent assignment dropdown
    agents = db.execute("SELECT user_id, name FROM users WHERE role IN ('Agent', 'Admin') ORDER BY name").fetchall()

    return render_template('tickets/detail.html',
                           ticket=dict(ticket),
                           sla_info=sla_info,
                           comments=comments,
                           attachments=attachments,
                           audit_trail=audit_trail,
                           allowed_transitions=allowed_transitions,
                           agents=agents)

@ticket_bp.route('/tickets/<int:ticket_id>/transition', methods=['POST'])
@login_required
def transition_status(ticket_id):
    db = get_db()
    user_id = session.get('user_id')
    user_role = session.get('role')

    ticket = db.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    if not ticket:
        flash("Ticket not found.", "danger")
        return redirect(url_for('tickets.list_tickets'))

    new_status = request.form.get('target_status')
    resolution_notes = request.form.get('resolution_notes', '').strip()
    current_status = ticket['status']

    # State Machine Validation
    valid, message = validate_transition(current_status, new_status, resolution_notes)
    if not valid:
        flash(message, "danger")
        return redirect(url_for('tickets.ticket_detail', ticket_id=ticket_id))

    # RBAC permissions on transitions:
    # Requesters can only:
    # - Close ticket (Resolved -> Closed)
    # - Reopen ticket (Resolved -> In Progress)
    # And MUST own the ticket!
    if user_role == 'Requester':
        if ticket['requester_id'] != user_id:
            flash("Access Denied: You cannot transition tickets filed by other users.", "danger")
            return redirect(url_for('tickets.list_tickets'))
        if new_status not in ['Closed', 'In Progress']:
            flash("Requesters can only confirm closure or reopen resolved tickets.", "danger")
            return redirect(url_for('tickets.ticket_detail', ticket_id=ticket_id))

    resolved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_status == 'Resolved' else ticket['resolved_at']

    db.execute("""
        UPDATE tickets
        SET status = ?, resolved_at = ?
        WHERE ticket_id = ?
    """, (new_status, resolved_at, ticket_id))

    # If resolution notes were provided, add as public comment
    if resolution_notes:
        db.execute("""
            INSERT INTO comments (ticket_id, author_id, message, is_internal)
            VALUES (?, ?, ?, 0)
        """, (ticket_id, user_id, f"**Resolution Details:** {resolution_notes}"))

    log_audit(ticket_id, user_id, 'Status Change', current_status, new_status, db)
    db.commit()

    flash(f"Ticket status successfully changed from '{current_status}' to '{new_status}'.", "success")
    return redirect(url_for('tickets.ticket_detail', ticket_id=ticket_id))

@ticket_bp.route('/tickets/<int:ticket_id>/assign', methods=['POST'])
@login_required
@role_required('Agent', 'Admin')
def assign_ticket(ticket_id):
    db = get_db()
    current_user_id = session.get('user_id')
    assigned_agent_id = request.form.get('agent_id')

    # If button was "Claim Ticket", assign to self
    if not assigned_agent_id:
        assigned_agent_id = current_user_id

    ticket = db.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    if not ticket:
        flash("Ticket not found.", "danger")
        return redirect(url_for('tickets.list_tickets'))

    agent = db.execute("SELECT name FROM users WHERE user_id = ?", (assigned_agent_id,)).fetchone()
    agent_name = agent['name'] if agent else "Unknown Agent"

    # Auto transition Open -> Assigned if currently Open
    new_status = 'Assigned' if ticket['status'] == 'Open' else ticket['status']

    db.execute("""
        UPDATE tickets
        SET assigned_agent_id = ?, status = ?
        WHERE ticket_id = ?
    """, (assigned_agent_id, new_status, ticket_id))

    old_agent = ticket['assigned_agent_id'] or 'Unassigned'
    log_audit(ticket_id, current_user_id, 'Agent Assignment', str(old_agent), f"Assigned to {agent_name} (#{assigned_agent_id})", db)
    if new_status != ticket['status']:
        log_audit(ticket_id, current_user_id, 'Status Auto-Transition', ticket['status'], new_status, db)

    db.commit()
    flash(f"Ticket assigned to {agent_name}.", "success")
    return redirect(url_for('tickets.ticket_detail', ticket_id=ticket_id))

@ticket_bp.route('/tickets/<int:ticket_id>/comment', methods=['POST'])
@login_required
def add_comment(ticket_id):
    db = get_db()
    user_id = session.get('user_id')
    user_role = session.get('role')

    ticket = db.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    if not ticket:
        flash("Ticket not found.", "danger")
        return redirect(url_for('tickets.list_tickets'))

    # Security check: Requesters cannot comment on other users' tickets
    if user_role == 'Requester' and ticket['requester_id'] != user_id:
        flash("Access Denied: You cannot comment on tickets filed by other users.", "danger")
        return redirect(url_for('tickets.list_tickets'))

    message = request.form.get('message', '').strip()
    is_internal = 1 if request.form.get('is_internal') == '1' else 0

    # Requesters cannot post internal notes
    if user_role == 'Requester':
        is_internal = 0

    if not message or len(message) < 2:
        flash("Comment message cannot be empty.", "danger")
        return redirect(url_for('tickets.ticket_detail', ticket_id=ticket_id))

    db.execute("""
        INSERT INTO comments (ticket_id, author_id, message, is_internal)
        VALUES (?, ?, ?, ?)
    """, (ticket_id, user_id, message, is_internal))

    note_label = "Internal Technician Note" if is_internal else "Public Comment"
    log_audit(ticket_id, user_id, 'Comment Added', 'None', f"Posted {note_label}", db)

    # If ticket was 'Pending Customer' and Requester commented, automatically return to 'In Progress'
    if ticket['status'] == 'Pending Customer' and user_role == 'Requester':
        db.execute("UPDATE tickets SET status = 'In Progress' WHERE ticket_id = ?", (ticket_id,))
        log_audit(ticket_id, user_id, 'Status Auto-Transition', 'Pending Customer', 'In Progress (Customer Replied)', db)
        flash("Thank you for your response! Ticket has returned to 'In Progress'.", "info")

    db.commit()
    flash("Comment posted successfully.", "success")
    return redirect(url_for('tickets.ticket_detail', ticket_id=ticket_id))

@ticket_bp.route('/tickets/<int:ticket_id>/rate', methods=['POST'])
@login_required
def rate_ticket(ticket_id):
    db = get_db()
    user_id = session.get('user_id')

    ticket = db.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    if not ticket or ticket['requester_id'] != user_id:
        flash("You are not authorized to rate this ticket.", "danger")
        return redirect(url_for('tickets.list_tickets'))

    rating = request.form.get('rating', type=int)
    feedback = request.form.get('feedback', '').strip()

    if not rating or rating < 1 or rating > 5:
        flash("Please provide a valid rating between 1 and 5 stars.", "danger")
        return redirect(url_for('tickets.ticket_detail', ticket_id=ticket_id))

    db.execute("""
        UPDATE tickets
        SET rating = ?, feedback = ?, status = 'Closed'
        WHERE ticket_id = ?
    """, (rating, feedback, ticket_id))

    log_audit(ticket_id, user_id, 'CSAT Rating & Closure', f"Previous Status: {ticket['status']}", f"Rated {rating}/5 Stars - Status: Closed", db)
    db.commit()

    flash(f"Thank you for rating! Ticket #{ticket['ticket_number']} is now officially Closed.", "success")
    return redirect(url_for('tickets.ticket_detail', ticket_id=ticket_id))

@ticket_bp.route('/uploads/<filename>')
@login_required
def get_attachment(filename):
    db = get_db()
    user_id = session.get('user_id')
    user_role = session.get('role')

    att = db.execute("SELECT ticket_id FROM attachments WHERE file_path = ?", (filename,)).fetchone()
    if not att:
        abort(404)

    # Requesters can only access attachments belonging to their own tickets
    if user_role == 'Requester':
        ticket = db.execute("SELECT requester_id FROM tickets WHERE ticket_id = ?", (att['ticket_id'],)).fetchone()
        if not ticket or ticket['requester_id'] != user_id:
            abort(403)

    return send_from_directory(Config.UPLOAD_FOLDER, filename)
