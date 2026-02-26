from typing import Any, Callable, Dict, List, Optional, TypedDict

# --- Tool function signatures (stubs) ---
# NOTE: Implementations are backend-owned and MUST enforce policy/RBAC again.

def respond_to_user(conversation_id: str, text: str) -> Dict[str, Any]:
    """Send final assistant message to the user."""
    raise NotImplementedError

def ask_clarifying_question(conversation_id: str, question: str, about: Optional[str] = None) -> Dict[str, Any]:
    """Ask a single clarification question to unblock execution."""
    raise NotImplementedError

def log_state_entry(
    user_id: str,
    conversation_id: str,
    entries: List[Dict[str, Any]],
    evidence_message_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Persist structured wellness entries (mood/sleep/anxiety/etc.).
    entries item example: {"type":"mood","value":6,"scale":"0-10","ts":"...","note":"..."}
    """
    raise NotImplementedError

def extract_parameters_from_dialogue(
    conversation_id: str,
    message_window: int = 12,
) -> Dict[str, Any]:
    """Extract structured parameters and user info hints from recent dialogue."""
    raise NotImplementedError

def create_task(
    owner_user_id: str,
    conversation_id: str,
    task_type: str,
    title: str,
    schedule: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create reminders, follow-ups, shadow tasks (background extraction), etc.
    schedule example: {"kind":"daily","time":"22:30","tz":"America/Argentina/Salta"}
    """
    raise NotImplementedError

def run_analysis(
    user_id: str,
    conversation_id: str,
    analysis_type: str,
    time_range: Dict[str, str],
    metrics: List[str],
    chart: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Trigger analytics/graph pipeline.
    analysis_type example: "correlation", "trend", "summary"
    """
    raise NotImplementedError

def export_user_data(
    user_id: str,
    conversation_id: str,
    format: str,
    time_range: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Prepare user data export (CSV/PDF/JSON)."""
    raise NotImplementedError

def delete_my_data(
    user_id: str,
    conversation_id: str,
    scope: str = "all",
    confirm_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Request deletion of user's own data (may require confirmation token)."""
    raise NotImplementedError

def create_attention_flag(
    conversation_id: str,
    user_id: str,
    reason: str,
    severity: str = "low",
    related_message_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create internal attention flag for clinician/support review."""
    raise NotImplementedError