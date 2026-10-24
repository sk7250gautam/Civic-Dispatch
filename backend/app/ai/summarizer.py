"""
Civic Dispatch — Grievance Summarizer
Extracts key technical facts for field officers while removing citizen personal data (PII).
"""

import re
from typing import Dict, Any

def sanitize_pii(text: str) -> str:
    """Redacts potential phone numbers and email addresses."""
    # Redact email
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED_EMAIL]', text)
    # Redact phone numbers
    text = re.sub(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', '[REDACTED_PHONE]', text)
    return text

def generate_officer_summary(title: str, description: str, category: str, address: str = None) -> Dict[str, Any]:
    """
    Creates concise field-dispatch summary for mobile officers.
    """
    clean_desc = sanitize_pii(description)
    clean_title = sanitize_pii(title)

    sentences = [s.strip() for s in re.split(r'[.!?\n]', clean_desc) if len(s.strip()) > 5]
    lead = sentences[0] if sentences else clean_title

    summary_text = f"[{category.replace('_', ' ')}] {clean_title} — {lead}."
    if address:
        summary_text += f" Location: {address}."

    return {
        "summary": summary_text,
        "key_action_item": f"Inspect {category.lower().replace('_', ' ')} issue at reported site.",
        "pii_filtered": True,
        "source": "civic_rule_summarizer"
    }
