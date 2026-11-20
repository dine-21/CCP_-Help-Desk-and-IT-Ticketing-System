"""
Unit Test Suite: Software Quality Assurance (QA) Unit Test Matrix
Tests isolated helper functions, algorithms, and business logic.
"""

import sys
import os
import unittest
from datetime import datetime, timedelta

# Add SourceCode to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'SourceCode')))

from services.state_machine import can_transition, validate_transition, VALID_TRANSITIONS
from services.sla_service import calculate_due_date, format_time_remaining, DEFAULT_SLA_HOURS
from services.auth_service import hash_password, verify_password
from services.ticket_service import allowed_file

class TestStateMachineEngine(unittest.TestCase):
    """Unit tests for deterministic state machine validator (FR-04)."""

    def test_valid_forward_transitions(self):
        self.assertTrue(can_transition('Open', 'Assigned'))
        self.assertTrue(can_transition('Assigned', 'In Progress'))
        self.assertTrue(can_transition('In Progress', 'Pending Customer'))
        self.assertTrue(can_transition('Pending Customer', 'In Progress'))
        self.assertTrue(can_transition('In Progress', 'Resolved'))
        self.assertTrue(can_transition('Resolved', 'Closed'))

    def test_valid_reopen_transition(self):
        # Dissatisfied customer can reopen within 48h
        self.assertTrue(can_transition('Resolved', 'In Progress'))

    def test_illegal_state_jumps_rejected(self):
        # Cannot jump straight from Open to Resolved or Closed
        self.assertFalse(can_transition('Open', 'Resolved'))
        self.assertFalse(can_transition('Open', 'Closed'))
        self.assertFalse(can_transition('Assigned', 'Closed'))

    def test_terminal_closed_state_immutable(self):
        # Closed state is strictly terminal: no outgoing transitions allowed
        self.assertEqual(VALID_TRANSITIONS['Closed'], [])
        self.assertFalse(can_transition('Closed', 'Open'))
        self.assertFalse(can_transition('Closed', 'In Progress'))
        self.assertFalse(can_transition('Closed', 'Resolved'))

    def test_resolution_notes_guard_condition(self):
        # Moving to Resolved without notes must fail
        ok, msg = validate_transition('In Progress', 'Resolved', None)
        self.assertFalse(ok)
        self.assertIn("at least 10 characters", msg)

        # Short notes (<10 chars) must fail
        ok, msg = validate_transition('In Progress', 'Resolved', 'Done')
        self.assertFalse(ok)

        # Valid notes (>= 10 chars) must succeed
        ok, msg = validate_transition('In Progress', 'Resolved', 'Reinstalled the corrupted display drivers.')
        self.assertTrue(ok)
        self.assertIn("Valid transition", msg)

    def test_identical_status_transition_rejected(self):
        ok, msg = validate_transition('In Progress', 'In Progress')
        self.assertFalse(ok)
        self.assertIn("already in 'In Progress'", msg)


class TestSLAEngine(unittest.TestCase):
    """Unit tests for SLA policy targets and breach formatting (FR-03 & FR-05)."""

    def test_sla_resolution_windows(self):
        self.assertEqual(DEFAULT_SLA_HOURS['Critical'], 4)
        self.assertEqual(DEFAULT_SLA_HOURS['High'], 8)
        self.assertEqual(DEFAULT_SLA_HOURS['Medium'], 24)
        self.assertEqual(DEFAULT_SLA_HOURS['Low'], 72)

    def test_sla_due_date_calculation_ordering(self):
        now = datetime.now()
        crit_due = calculate_due_date('Critical')
        high_due = calculate_due_date('High')
        med_due = calculate_due_date('Medium')
        low_due = calculate_due_date('Low')

        self.assertTrue(now < crit_due < high_due < med_due < low_due)

    def test_sla_countdown_active(self):
        future_date = datetime.now() + timedelta(hours=5, minutes=30)
        info = format_time_remaining(future_date)
        self.assertFalse(info['breached'])
        self.assertIn("5h", info['text'])
        self.assertEqual(info['class'], 'info')

    def test_sla_countdown_breached(self):
        past_date = datetime.now() - timedelta(hours=2, minutes=15)
        info = format_time_remaining(past_date)
        self.assertTrue(info['breached'])
        self.assertIn("Breached by 2h", info['text'])
        self.assertEqual(info['class'], 'danger')


class TestSecurityAndValidation(unittest.TestCase):
    """Unit tests for cryptographic password hashing and file extension validation (FR-01 & FR-07)."""

    def test_password_hashing_and_verification(self):
        password = "SecurePassword123!"
        hashed = hash_password(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(hashed, password))
        self.assertFalse(verify_password(hashed, "WrongPassword"))

    def test_allowed_file_extensions(self):
        self.assertTrue(allowed_file("screenshot.png"))
        self.assertTrue(allowed_file("error_log.txt"))
        self.assertTrue(allowed_file("diagnostic.pdf"))
        self.assertTrue(allowed_file("report.docx"))
        self.assertTrue(allowed_file("system.log"))

        # Dangerous or unsupported extensions rejected
        self.assertFalse(allowed_file("malware.exe"))
        self.assertFalse(allowed_file("script.sh"))
        self.assertFalse(allowed_file("exploit.py"))
        self.assertFalse(allowed_file("archive.zip"))
        self.assertFalse(allowed_file("no_extension"))

if __name__ == '__main__':
    unittest.main(verbosity=2)
