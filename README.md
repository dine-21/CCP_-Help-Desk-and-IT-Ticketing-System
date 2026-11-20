# Help Desk and IT Ticketing System (Project #11)

**Course:** Software Engineering (CT-365) — 5th Semester BS Computer Science  
**Group:** Group XX  
**Project:** Complex Computing Problem (CCP) — Project #11  
**Technology Stack:** Python 3 (Flask) + SQLite3 (3NF) + Bootstrap 5 + Jinja2 + Werkzeug  
**Repository Link:** [https://github.com/CCP_-Help-Desk-and-IT-Ticketing-System](https://github.com/CCP_-Help-Desk-and-IT-Ticketing-System)  

---

## 1. Project Overview

The **Help Desk and IT Ticketing System** is a production-grade 3-tier client-server web application engineered to centralize, streamline, and govern technical incident management in institutional and corporate environments. 

### Key Architectural Highlights:
- **Deterministic State Progression:** Strict UML state machine lifecycle (`Open` → `Assigned` → `In Progress` → `Pending Cust.` → `Resolved` → `Closed`) preventing illegal jumps and premature closures.
- **Dynamic SLA Calculation & Breach Auto-Escalation:** Automatic due-date targets computed from incident priorities (Critical: 4h, High: 8h, Medium: 24h, Low: 72h). Active overdue incidents are automatically flagged and routed to the Supervisor Priority Escalation Queue.
- **Confidential Internal Collaboration:** Role-separated commenting distinguishes between public customer replies and internal technician notes (`is_internal = 1`) hidden from requesters.
- **Self-Service Knowledge Base Deflection:** Asynchronous AJAX live search suggests verified troubleshooting guides while users type their incident summary to deflect repetitive tickets.
- **Robust Security & IDOR Hardening:** Cryptographically salted one-way password hashing (PBKDF2-SHA256), session integrity guards, and object-level ownership checks preventing cross-user tampering.

---

## 2. Repository Structure & Deliverables Index

```
CCP_Group03_HelpDesk/
├── README.md                                  # Repository overview, setup, and navigation guide
├── Proposal/                                  # Deliverable D1: Proposal & Feasibility
│   └── SE_CCP_Group XX_Proposal.docx           # (Also includes approved PDF & Markdown formats)
├── SRS/                                       # Deliverable D2: Software Requirements Specification
│   └── SE_CCP_Group XX_SRS.docx                # (10 FRs, 5 NFRs, MoSCoW matrix, RTM, Acceptance criteria)
├── Design/                                    # Deliverable D3: System Analysis & Design Document
│   ├── SE_CCP_Group XX_DesignDocument.docx     # (Complete architecture, 8 UML diagrams, 2 wireframes)
│   ├── UML_Diagrams/                          # High-resolution standalone diagram assets (.png)
│   └── Wireframes/                            # UI Mockups for Requester Portal & Technician Queue
├── SourceCode/                                # Deliverable D4: Working Prototype & Implementation
│   ├── app.py                                 # Application factory & blueprint registration
│   ├── database.py                            # SQLite3 connection manager & 3NF schema DDL
│   ├── seed_data.py                           # Pre-seeded test data (Users, SLAs, Categories, Tickets)
│   ├── requirements.txt                       # Minimal dependency manifest (Flask, Werkzeug, etc.)
│   ├── README.md                              # Detailed local setup and execution instructions
│   ├── SE_CCP_Group XX_ImplementationReport.docx # Deliverable D4 Sprint Tracking & Code Report
│   ├── routes/                                # HTTP route blueprints (auth, tickets, kb, admin)
│   ├── services/                              # Domain business services (state machine, sla, auth)
│   ├── templates/                             # Jinja2 responsive HTML templates (Bootstrap 5)
│   ├── static/                                # Custom enterprise styles and JavaScript helpers
│   └── uploads/                               # Secure directory for validated attachments
├── Tests/                                     # Automated Test Suites & Regression Code
│   ├── test_unit_suite.py                     # 12 automated unit tests (State machine & SLA logic)
│   ├── test_system_integration.py             # 10 integration & IDOR security test suites
│   └── SE_CCP_Group XX_TestReport.docx         # Mirrored copy of formal test report
├── TestReports/                               # Deliverable D5: Software Testing & SQA Report
│   └── SE_CCP_Group XX_TestReport.docx         # (Master test plan, 26 TCs, Defect log, DRE & SQA metrics)
├── FinalReport/                               # Deliverable D6: Consolidated Final Project Report
│   └── SE_CCP_Group XX_FinalReport.docx        # Master consolidated documentation with embedded diagrams
└── Presentation/                              # Final Viva & Evaluation Presentation Deck
    └── SE_CCP_Group XX_Presentation.pptx       # 12-slide modern widescreen presentation deck
```

---

## 3. Quick Start & Execution Guide

### Prerequisites
- Python 3.10+ installed on your system.

### Step 1: Open Terminal in `SourceCode/` Directory
```bash
cd "C:\Help desk system\CCP_-Help-Desk-and-IT-Ticketing-System\SourceCode"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Initialize & Seed Database
```bash
python seed_data.py
```
*(Initializes `helpdesk.db` with 8 relational tables, sample users, categories, SLA policies, and 7 realistic tickets across all lifecycle states).*

### Step 4: Run the Application
```bash
python app.py
```

### Step 5: Access the Web Portal
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 4. Pre-Configured Test Credentials for Evaluation

The login page includes **1-click quick evaluation buttons** to instantly fill these credentials:

| Role | Email Address | Password | Key Evaluation Capabilities |
|:---|:---|:---|:---|
| **Administrator** | `admin@company.com` | `pass123` | Supervisor KPI dashboard, SLA breach escalations, agent reassignment, user list. |
| **IT Support Agent (L1)** | `agent1@company.com` | `pass123` | Claiming tickets, state changes (`In Progress`, `Pending Cust.`, `Resolved`), internal notes. |
| **IT Support Agent (L2)** | `agent2@company.com` | `pass123` | Senior technician queue, complex incident diagnosis, resolution documentation. |
| **Requester (HR Lead)** | `requester1@company.com` | `pass123` | Ticket submission, file attachments, customer replies, 5-star CSAT ratings. |
| **Requester (Finance)** | `requester2@company.com` | `pass123` | Self-service Knowledge Base search, ticket tracking, reopen workflows. |

---

## 5. Running the Automated Test Suite

From the project root:
```bash
# Run isolated Unit Tests (State Machine, SLA Engine, Hashing)
python Tests/test_unit_suite.py

# Run End-to-End System Integration & IDOR Security Tests
python Tests/test_system_integration.py
```
*Current test metrics: **22 automated tests, 100% pass rate in 0.7s**.*

---

## 6. Balanced 4-Member Work Distribution (25% Each)

| Member | Specialized Role | Primary Deliverables & Code Ownership | Effort Share |
|:---|:---|:---|:---:|
| **Dinesh** | Project Coordinator & Backend/Auth Lead | D1 Proposal Lead, DB Architecture, Auth Routes, Session Guards | **25%** |
| **Abdullah** | Workflow & State Machine Lead | D2 SRS Lead, State Machine Engine, Ticket CRUD Routes | **25%** |
| **Bheesham** | SLA, Notes & Knowledge Base Lead | D3 Design Lead, SLA Policy Engine, Live Deflection API, Internal Notes | **25%** |
| **Pooran** | SQA, Requirements & Analytics Lead | D4 Tracking, D5 SQA Report Lead, D6 Final Report, Automated Test Suites | **25%** |
