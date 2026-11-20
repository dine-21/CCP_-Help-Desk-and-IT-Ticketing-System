"""
UML State Machine Engine: Ticket Lifecycle Validator
Enforces deterministic lifecycle transitions per CCP Deliverable D2 (SRS) and D3 (Design).
"""

VALID_TRANSITIONS = {
    'Open': ['Assigned'],
    'Assigned': ['In Progress', 'Open'],
    'In Progress': ['Pending Customer', 'Resolved'],
    'Pending Customer': ['In Progress'],
    'Resolved': ['Closed', 'In Progress'],  # In Progress via Reopen
    'Closed': []  # Terminal State
}

def can_transition(current_status: str, new_status: str) -> bool:
    """Checks if a transition from current_status to new_status is allowed."""
    allowed = VALID_TRANSITIONS.get(current_status, [])
    return new_status in allowed

def validate_transition(current_status: str, new_status: str, resolution_notes: str = None) -> tuple[bool, str]:
    """
    Validates a lifecycle transition.
    Returns (True, "Success message") or (False, "Error message").
    """
    if current_status == new_status:
        return False, f"Ticket is already in '{current_status}' status."

    if not can_transition(current_status, new_status):
        allowed_str = ", ".join(VALID_TRANSITIONS.get(current_status, ['None']))
        return False, f"Invalid transition: Cannot move from '{current_status}' to '{new_status}'. Allowed target statuses: [{allowed_str}]."

    # Guard Condition: Moving to Resolved requires mandatory resolution notes
    if new_status == 'Resolved':
        if not resolution_notes or len(resolution_notes.strip()) < 10:
            return False, "Resolution notes are mandatory and must be at least 10 characters long to resolve a ticket."

    return True, f"Valid transition from '{current_status}' to '{new_status}'."
