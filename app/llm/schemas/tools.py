from typing import Dict, Any

from app.llm.tools import respond_to_user, ask_clarifying_question, log_state_entry, extract_parameters_from_dialogue, \
    create_task, run_analysis, export_user_data, delete_my_data, create_attention_flag

TOOLS_CATALOG: Dict[str, Dict[str, Any]] = {
    "RESPOND_TO_USER": {
        "description": "Send a final user-visible reply for this turn.",
        "handler": respond_to_user,
        "inputs": {
            "conversation_id": "str",
            "text": "str"
        }
    },
    "ASK_CLARIFYING_QUESTION": {
        "description": "Ask one concise question when execution is blocked by missing info.",
        "handler": ask_clarifying_question,
        "inputs": {
            "conversation_id": "str",
            "question": "str",
            "about": "str | null"
        }
    },
    "LOG_STATE_ENTRY": {
        "description": "Write structured wellness entries (mood/sleep/anxiety/etc.) extracted from the chat.",
        "handler": log_state_entry,
        "inputs": {
            "user_id": "str",
            "conversation_id": "str",
            "entries": "list[dict]",
            "evidence_message_ids": "list[str] | null"
        }
    },
    "EXTRACT_PARAMETERS_FROM_DIALOGUE": {
        "description": "Extract structured parameters and user-info hints from the recent dialogue window.",
        "handler": extract_parameters_from_dialogue,
        "inputs": {
            "conversation_id": "str",
            "message_window": "int (default 12)"
        }
    },
    "CREATE_TASK": {
        "description": "Create reminders, follow-ups, or shadow tasks (e.g., delayed extraction if user stops replying).",
        "handler": create_task,
        "inputs": {
            "owner_user_id": "str",
            "conversation_id": "str",
            "task_type": "str (reminder|follow_up|shadow_extraction|notify|other)",
            "title": "str",
            "schedule": "dict | null",
            "payload": "dict | null"
        }
    },
    "RUN_ANALYSIS": {
        "description": "Run analytics/graph pipeline for a user and return computed results for response.",
        "handler": run_analysis,
        "inputs": {
            "user_id": "str",
            "conversation_id": "str",
            "analysis_type": "str",
            "time_range": "dict{from:str,to:str}",
            "metrics": "list[str]",
            "chart": "dict | null"
        }
    },
    "EXPORT_USER_DATA": {
        "description": "Export the user's own data (CSV/PDF/JSON).",
        "handler": export_user_data,
        "inputs": {
            "user_id": "str",
            "conversation_id": "str",
            "format": "str (csv|pdf|json)",
            "time_range": "dict{from:str,to:str} | null"
        }
    },
    "DELETE_MY_DATA": {
        "description": "Request deletion of the user's own data (may require confirmation).",
        "handler": delete_my_data,
        "inputs": {
            "user_id": "str",
            "conversation_id": "str",
            "scope": "str (all|time_range|category)",
            "confirm_token": "str | null"
        }
    },
    "CREATE_ATTENTION_FLAG": {
        "description": "Create an internal flag for clinician/support review (non-user-visible).",
        "handler": create_attention_flag,
        "inputs": {
            "conversation_id": "str",
            "user_id": "str",
            "reason": "str",
            "severity": "str (low|medium|high)",
            "related_message_ids": "list[str] | null"
        }
    },
}