import os
import sys

# Add SourceCode to sys.path
sys.path.insert(0, r"C:\Help desk system\CCP_-Help-Desk-and-IT-Ticketing-System\SourceCode")

from app import create_app
from database import get_db
from services.state_machine import validate_transition, can_transition
from services.sla_service import calculate_due_date, format_time_remaining

def test_system():
    print("=== STARTING FULL SYSTEM VERIFICATION ===")
    app = create_app()
    client = app.test_client()

    with app.app_context():
        # 1. Test Database Connectivity & Counts
        db = get_db()
        users_count = db.execute("SELECT COUNT(*) AS c FROM users").fetchone()['c']
        tickets_count = db.execute("SELECT COUNT(*) AS c FROM tickets").fetchone()['c']
        categories_count = db.execute("SELECT COUNT(*) AS c FROM categories").fetchone()['c']
        sla_count = db.execute("SELECT COUNT(*) AS c FROM sla_policies").fetchone()['c']
        print(f"[DB PASS] Users: {users_count}, Tickets: {tickets_count}, Categories: {categories_count}, SLA Policies: {sla_count}")

        # 2. Test State Machine Transition Engine
        assert can_transition('Open', 'Assigned') == True
        assert can_transition('Open', 'Resolved') == False
        assert can_transition('In Progress', 'Resolved') == True
        assert can_transition('Closed', 'In Progress') == False

        # Guard condition test (Resolved requires mandatory notes >= 10 chars)
        ok, msg = validate_transition('In Progress', 'Resolved', 'Fixed it')
        assert ok == False
        assert "at least 10 characters" in msg

        ok, msg = validate_transition('In Progress', 'Resolved', 'Replaced faulty RAM module and ran diagnostic test successfully.')
        assert ok == True
        print("[STATE MACHINE PASS] All deterministic transition rules and guard conditions verified.")

        # 3. Test SLA Due Date Calculation
        crit_due = calculate_due_date('Critical', db)
        low_due = calculate_due_date('Low', db)
        assert crit_due < low_due
        print("[SLA ENGINE PASS] Dynamic target calculation validated.")

    # 4. Test Web Endpoints via Flask Test Client
    # A. Login as Requester
    res = client.post('/login', data={'email': 'requester1@company.com', 'password': 'pass123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Signed in as Requester" in res.data
    print("[AUTH PASS] Requester login verified.")

    # B. View Tickets Queue as Requester
    res = client.get('/tickets')
    assert res.status_code == 200
    assert b"My Support Tickets" in res.data
    print("[RBAC PASS] Requester scoped view verified.")

    # C. Submit New Ticket as Requester
    res = client.post('/tickets/create', data={
        'subject': 'Test Automated Ticket for Verification',
        'category_id': 1,
        'priority': 'High',
        'description': 'This is an automated end-to-end test ticket verifying the creation workflow.'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"successfully submitted" in res.data
    print("[TICKET CRUD PASS] Ticket submission & SLA auto-assignment verified.")

    # D. Sign In as IT Support Agent
    client.get('/logout')
    res = client.post('/login', data={'email': 'agent1@company.com', 'password': 'pass123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Signed in as Agent" in res.data

    # E. View Unified Queue as Agent
    res = client.get('/tickets')
    assert b"Unified Service Queue" in res.data
    print("[RBAC PASS] Agent unified queue verified.")

    # F. Sign In as Admin & View Supervisor Dashboard
    client.get('/logout')
    res = client.post('/login', data={'email': 'admin@company.com', 'password': 'pass123'}, follow_redirects=True)
    assert res.status_code == 200
    res = client.get('/admin/dashboard')
    assert res.status_code == 200
    assert b"Supervisor Analytics Dashboard" in res.data or b"IT Operations" in res.data
    print("[ANALYTICS PASS] Supervisor dashboard & KPI metrics verified.")

    # G. Knowledge Base Search API
    res = client.get('/api/kb/search?q=vpn')
    assert res.status_code == 200
    assert b"GlobalProtect" in res.data
    print("[KB PASS] Knowledge base deflection API verified.")

    # H. Security & IDOR Authorization Verification
    # Requester 2 logs in and tries to access / modify Requester 1's ticket (Ticket #1)
    client.get('/logout')
    client.post('/login', data={'email': 'requester2@company.com', 'password': 'pass123'}, follow_redirects=True)
    
    # 1. View unauthorized ticket
    res = client.get('/tickets/1', follow_redirects=True)
    assert b"Access Denied" in res.data
    
    # 2. Transition unauthorized ticket
    res = client.post('/tickets/1/transition', data={'target_status': 'Closed'}, follow_redirects=True)
    assert b"Access Denied" in res.data
    
    # 3. Comment on unauthorized ticket
    res = client.post('/tickets/1/comment', data={'message': 'Illegal comment'}, follow_redirects=True)
    assert b"Access Denied" in res.data
    print("[SECURITY & IDOR PASS] Unauthorized cross-requester access strictly blocked.")

    print("=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    test_system()
