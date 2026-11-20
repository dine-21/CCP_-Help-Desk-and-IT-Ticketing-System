# IT Help Desk and IT Ticketing System — Source Code & Setup Guide

**Course:** Software Engineering (CT-365)  
**Project:** Complex Computing Problem (CCP) — Project #11  
**Group:** Group 03  
**Technology Stack:** Python 3 (Flask) + SQLite3 + Bootstrap 5 + Jinja2  

---

## 1. Quick Start Guide

### Step 1: Open Terminal in `SourceCode/` Directory
```bash
cd "C:\Help desk system\CCP_-Help-Desk-and-IT-Ticketing-System\SourceCode"
```

### Step 2: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Seed the Database with Test Data
```bash
python seed_data.py
```
*(This initializes `helpdesk.db` with all 8 relational tables, sample users, categories, SLA policies, and 7 realistic tickets across all lifecycle states).*

### Step 4: Run the Application
```bash
python app.py
```

### Step 5: Open in Web Browser
Navigate to:
```
http://127.0.0.1:5000
```

---

## 2. Pre-Configured Test Credentials

| Role | Email | Password | Primary Capabilities |
|:---|:---|:---|:---|
| **Administrator / Supervisor** | `admin@company.com` | `pass123` | KPI Analytics dashboard, overdue auto-escalations, reassigning agents, full queue view, user directory. |
| **IT Support Agent (L1)** | `agent1@company.com` | `pass123` | Claiming tickets, updating lifecycle states (`In Progress`, `Pending Cust.`, `Resolved`), posting internal notes, viewing full queue. |
| **IT Support Agent (L2)** | `agent2@company.com` | `pass123` | High/Critical priority troubleshooting, internal notes, resolution documentation. |
| **Requester (HR Lead)** | `requester1@company.com` | `pass123` | Submitting new tickets, file attachments, replying to tickets, CSAT star ratings (1–5). |
| **Requester (Finance)** | `requester2@company.com` | `pass123` | Submitting tickets, searching self-service knowledge base, confirming closures. |

*(Note: The login page includes 1-click evaluation buttons to instantly autofill these credentials).*

---

## 3. Project Architecture & Code Organization

```
SourceCode/
├── app.py                  # Application factory, blueprint registration & error handlers
├── config.py               # Core configuration, database paths & upload constraints
├── database.py             # SQLite connection management & 3NF relational schema DDL
├── seed_data.py            # Comprehensive seed generator with sample tickets & users
├── requirements.txt        # Minimal Python dependencies
├── routes/
│   ├── auth_routes.py      # Login, registration, session management & RBAC guards
│   ├── ticket_routes.py    # Ticket CRUD, lifecycle transitions, notes & attachments
│   ├── kb_routes.py        # Knowledge base browsing & live deflection search API
│   └── admin_routes.py     # Supervisor analytics, SLA breach alerts & agent workload
├── services/
│   ├── auth_service.py     # Hashing & @login_required, @role_required decorators
│   ├── state_machine.py    # Strict deterministic lifecycle transition validator
│   ├── sla_service.py      # Due date calculation, countdown formatting & breach scanner
│   └── ticket_service.py   # Ticket numbering (HD-2026-xxxx), audit logging, file validation
├── static/
│   ├── css/style.css       # Clean enterprise styling
│   └── js/main.js          # Interactive UI alerts
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Unified master layout
│   ├── auth/               # Sign In & Registration views
│   ├── tickets/            # Queue list, ticket submission & interactive detail view
│   ├── kb/                 # Knowledge base directory & article view
│   └── admin/              # Supervisor analytics & user directory
└── uploads/                # Safe directory for uploaded attachments
```

---

## 4. Key Functional Implementations (FR-01 to FR-10)

- **FR-01: RBAC & Authentication:** Enforced via `werkzeug.security` password hashing and `@role_required` decorators.
- **FR-02: Ticket Submission:** Automatic generation of unique numbers (`HD-2026-0001`) and input sanitization.
- **FR-03: SLA Calculation:** Automatic due dates computed using priority-based resolution hours (4h, 8h, 24h, 72h).
- **FR-04: State Machine Engine:** Deterministic state progression (`Open` → `Assigned` → `In Progress` → `Pending Cust.` → `Resolved` → `Closed`). Mandatory notes required on resolution.
- **FR-05: Real-time SLA Breach Detection:** Automatic background scanning of active tickets; overdue incidents flagged and routed to Supervisor escalation queue.
- **FR-06: Internal Technician Notes:** Role-based comment visibility; notes marked `is_internal=1` are hidden from Requesters.
- **FR-07: File Attachments:** Validated uploads (max 5MB) stored securely in `uploads/`.
- **FR-08: Knowledge Base Deflection:** Real-time AJAX search dynamically suggests articles while typing ticket subject to prevent redundant tickets.
- **FR-09: Filtering & Search:** Real-time multi-facet queue filtering by Status, Priority, Category, and keyword search.
- **FR-10: Audit Trail & Operational Analytics:** Every transition, assignment, and priority change logged into immutable `audit_logs` table. Supervisor dashboard provides mean resolution time and CSAT metrics.
