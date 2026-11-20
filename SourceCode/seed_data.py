"""
Database Seed Script: Populates realistic test data across all roles, categories,
SLA policies, ticket states, internal notes, and knowledge base articles.
"""

from datetime import datetime, timedelta
import sqlite3
import os
from config import Config
from database import init_db
from services.auth_service import hash_password

def seed():
    # Clean slate reset to guarantee deterministic primary and foreign keys starting at 1
    if os.path.exists(Config.DATABASE):
        try:
            conn = sqlite3.connect(Config.DATABASE)
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF;")
            for table in ['audit_logs', 'comments', 'attachments', 'tickets', 'kb_articles', 'categories', 'sla_policies', 'users']:
                cursor.execute(f"DROP TABLE IF EXISTS {table};")
            try:
                cursor.execute("DELETE FROM sqlite_sequence;")
            except Exception:
                pass
            conn.commit()
            conn.close()
        except Exception:
            pass

    # Ensure tables exist
    init_db()

    conn = sqlite3.connect(Config.DATABASE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    print("Seeding database...")

    # 1. Seed SLA Policies
    cursor.execute("DELETE FROM sla_policies;")
    sla_data = [
        ('Critical', 1, 4),   # 1h response, 4h resolution
        ('High', 2, 8),       # 2h response, 8h resolution
        ('Medium', 4, 24),    # 4h response, 24h resolution
        ('Low', 8, 72)        # 8h response, 72h resolution
    ]
    cursor.executemany("""
        INSERT INTO sla_policies (priority_level, response_hours, resolution_hours)
        VALUES (?, ?, ?)
    """, sla_data)

    # 2. Seed Categories (linked to SLAs)
    cursor.execute("DELETE FROM categories;")
    cat_data = [
        ('Hardware & Peripherals', 'Physical computer, monitor, docking station, keyboard issues', 3), # Medium
        ('Software & Office Apps', 'Operating system, Office 365, browser, application crashes', 3),   # Medium
        ('Network & Remote VPN', 'Wi-Fi connectivity, Cisco/GlobalProtect VPN, Ethernet drops', 2),   # High
        ('Identity & Access Management (IAM)', 'Password resets, account lockouts, MFA tokens', 1),   # Critical
        ('General IT Inquiries', 'Purchasing inquiries, standard software access requests', 4)        # Low
    ]
    cursor.executemany("""
        INSERT INTO categories (name, description, sla_id)
        VALUES (?, ?, ?)
    """, cat_data)

    # 3. Seed Users
    cursor.execute("DELETE FROM users;")
    default_pass = hash_password("pass123")
    users_data = [
        ('Alice Vance (Admin)', 'admin@company.com', default_pass, 'Admin', 'IT Infrastructure'),
        ('Bob Miller (Technician)', 'agent1@company.com', default_pass, 'Agent', 'IT Support L1'),
        ('Charlie Chen (Senior Agent)', 'agent2@company.com', default_pass, 'Agent', 'IT Support L2'),
        ('Diana Prince (HR Lead)', 'requester1@company.com', default_pass, 'Requester', 'Human Resources'),
        ('Edward Norton (Finance)', 'requester2@company.com', default_pass, 'Requester', 'Finance & Accounting')
    ]
    cursor.executemany("""
        INSERT INTO users (name, email, password_hash, role, department)
        VALUES (?, ?, ?, ?, ?)
    """, users_data)

    # 4. Seed Knowledge Base Articles
    cursor.execute("DELETE FROM kb_articles;")
    kb_data = [
        (
            'How to Connect to Corporate GlobalProtect VPN from Home',
            '1. Launch GlobalProtect from the system tray.\n2. In the Portal address field, type "vpn.company.internal".\n3. Click Connect and authenticate with your standard corporate credentials.\n4. Complete the 2FA push notification on your Microsoft Authenticator app.\n5. Once connected, the shield icon turns blue.',
            3,
            'vpn, remote, network, connection'
        ),
        (
            'Self-Service Password Reset (SSPR) Guide',
            'If your Windows domain account is locked or password expired:\n1. Navigate to https://passwordreset.microsoftonline.com from your mobile device or browser.\n2. Enter your work email address and captcha.\n3. Verify your identity using SMS or Authenticator push.\n4. Choose a new password of at least 12 characters combining uppercase, lowercase, numbers, and symbols.',
            4,
            'password, account, lockout, iam'
        ),
        (
            'Resolving Microsoft Outlook "Disconnected" Status',
            'When Outlook displays "Disconnected" in the bottom status bar:\n1. Verify internet connectivity by opening a web browser.\n2. In Outlook, click the "Send / Receive" tab and verify "Work Offline" is NOT highlighted.\n3. Close Outlook completely, open Task Manager, end any lingering OUTLOOK.EXE processes.\n4. Re-launch Outlook in Safe Mode by holding CTRL while clicking the Outlook icon.\n5. If issues persist, submit a ticket under Software & Office Apps.',
            2,
            'outlook, email, office, disconnected'
        ),
        (
            'Setting Up Multi-Factor Authentication (MFA) on New Phone',
            '1. Visit https://mysignins.microsoft.com/security-info on your desktop computer.\n2. Select "Add sign-in method" -> "Authenticator app".\n3. Download Microsoft Authenticator on your new smartphone.\n4. Scan the QR code displayed on your desktop screen.\n5. Approve the test notification on your phone to complete registration.',
            4,
            'mfa, 2fa, phone, authenticator'
        )
    ]
    cursor.executemany("""
        INSERT INTO kb_articles (title, content, category_id, tags)
        VALUES (?, ?, ?, ?)
    """, kb_data)

    # 5. Seed Realistic Sample Tickets across all States
    cursor.execute("DELETE FROM tickets;")
    now = datetime.now()

    tickets_data = [
        # Ticket 1: Open
        ('HD-2026-0001', 4, None, 1, 'Medium', 'Open',
         'Monitor intermittently flickering on HDMI connection',
         'The secondary Dell 27-inch monitor flickers black every 5-10 minutes. Tested with different HDMI cable, same behavior.',
         (now + timedelta(hours=22)).strftime("%Y-%m-%d %H:%M:%S"), 0, None, None,
         (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"), None),

        # Ticket 2: Assigned
        ('HD-2026-0002', 5, 2, 3, 'High', 'Assigned',
         'Cannot access Finance Shared Network Drive (Z:)',
         'Receiving "Network path not found" error when attempting to access \\fileserver\finance. Urgent for month-end reconciliation.',
         (now + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"), 0, None, None,
         (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"), None),

        # Ticket 3: In Progress
        ('HD-2026-0003', 4, 3, 2, 'Medium', 'In Progress',
         'Excel 365 crashes on opening macros workbook',
         'Every time the payroll sheet with VBA macros is opened, Excel terminates abruptly without an error dialog.',
         (now + timedelta(hours=14)).strftime("%Y-%m-%d %H:%M:%S"), 0, None, None,
         (now - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S"), None),

        # Ticket 4: Pending Customer
        ('HD-2026-0004', 5, 2, 4, 'Critical', 'Pending Customer',
         'SAP ERP login throwing account locked exception',
         'Need SAP account unlocked to approve procurement batches.',
         (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"), 0, None, None,
         (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"), None),

        # Ticket 5: Resolved (Awaiting CSAT Rating / Closure)
        ('HD-2026-0005', 4, 2, 3, 'High', 'Resolved',
         'GlobalProtect VPN fails to establish tunnel from home Wi-Fi',
         'Error 512: Gateway unreachable from Comcast residential IP.',
         (now + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"), 0, None, None,
         (now - timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S"),
         (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")),

        # Ticket 6: Closed (With CSAT Rating)
        ('HD-2026-0006', 5, 3, 1, 'Low', 'Closed',
         'Request for ergonomic wireless keyboard and vertical mouse',
         'Doctor recommendation letter on file for ergonomic accessories.',
         (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"), 0, 5, 'Dispatched items same afternoon, very satisfied!',
         (now - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S"),
         (now - timedelta(hours=30)).strftime("%Y-%m-%d %H:%M:%S")),

        # Ticket 7: Breached (To demonstrate SLA auto-escalation alert)
        ('HD-2026-0007', 4, 2, 4, 'Critical', 'In Progress',
         'Core Database query timeouts affecting customer portal',
         'Database connection pool exhausted during peak morning hours.',
         (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"), 1, None, None,
         (now - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"), None)
    ]

    cursor.executemany("""
        INSERT INTO tickets (ticket_number, requester_id, assigned_agent_id, category_id, priority, status,
                             subject, description, due_date, is_breached, rating, feedback, created_at, resolved_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tickets_data)

    # 6. Seed Comments & Internal Notes
    cursor.execute("DELETE FROM comments;")
    comments_data = [
        # Ticket 3 comments
        (3, 3, "Reproduced the crash on Excel 2402. Disabling hardware graphics acceleration.", 1, (now - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")),
        (3, 3, "Hello Diana, we have identified a known bug with the legacy macro. Applying the Office 365 hotfix now.", 0, (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")),
        # Ticket 4 comments
        (4, 2, "Bob: Please provide your employee badge ID so we can verify identity before SAP reset.", 0, (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")),
        (4, 2, "Internal: Confirmed with SAP Basis team that user failed password 5 times from external IP.", 1, (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")),
        # Ticket 5 comments
        (5, 2, "Resolved: Reconfigured VPN gateway MTU size to 1350 for home ISP compatibility. Connected successfully.", 0, (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"))
    ]
    cursor.executemany("""
        INSERT INTO comments (ticket_id, author_id, message, is_internal, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, comments_data)

    # 7. Seed Initial Audit Logs
    cursor.execute("DELETE FROM audit_logs;")
    audit_data = [
        (1, 4, 'Ticket Created', 'None', 'Created HD-2026-0001 (Priority: Medium)', (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")),
        (2, 5, 'Ticket Created', 'None', 'Created HD-2026-0002 (Priority: High)', (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")),
        (2, 2, 'Agent Assignment', 'Unassigned', 'Assigned to Bob Miller (#2)', (now - timedelta(hours=1, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")),
        (2, 2, 'Status Auto-Transition', 'Open', 'Assigned', (now - timedelta(hours=1, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")),
        (3, 3, 'Status Change', 'Assigned', 'In Progress', (now - timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")),
        (4, 2, 'Status Change', 'In Progress', 'Pending Customer', (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")),
        (5, 2, 'Status Change', 'In Progress', 'Resolved', (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")),
        (6, 3, 'CSAT Rating & Closure', 'Resolved', 'Rated 5/5 Stars - Status: Closed', (now - timedelta(hours=30)).strftime("%Y-%m-%d %H:%M:%S")),
        (7, 1, 'SLA Breach Auto-Escalation', 'Within SLA', 'BREACHED', (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"))
    ]
    cursor.executemany("""
        INSERT INTO audit_logs (ticket_id, actor_id, action_type, old_value, new_value, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, audit_data)

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed()
