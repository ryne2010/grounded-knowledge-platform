from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple


# Conservative prompt injection / policy circumvention detection.
# This is intentionally strict for PUBLIC_DEMO_MODE and generally appropriate for regulated deployments.
_INJECTION_PATTERNS: List[Tuple[str, re.Pattern]] = [
    # Attempts to extract system/dev messages or hidden policies.
    ("reveal_system_prompt", re.compile(r"\b(system prompt|developer message|hidden instructions)\b", re.I)),

    # Attempts to override instructions/policies.
    ("ignore_instructions", re.compile(r"\b(ignore|disregard)\b.*\b(instruction|policy|previous)\b", re.I)),
    ("admin_mode", re.compile(r"\b(admin mode|override|bypass|disable safety)\b", re.I)),

    # Attempts to suppress grounding/citations or force ungrounded answers.
    ("no_citations", re.compile(
        r"\b("
        r"without citations|without citing|no citations|do not cite|ignore citations|"
        r"do not include citations|don't include citations|"
        r"answer without sources|no sources"
        r")\b",
        re.I,
    )),

    # Attempts to exfiltrate secrets.
    ("exfiltrate_secrets", re.compile(
        r"\b(api key|password|secret|token)\b.*\b(show|reveal|dump|exfiltrate|leak)\b", re.I
    )),

    # Attempts to dump verbatim content (copyright/PII risk; also an injection vector).
    ("verbatim_dump", re.compile(r"\b(verbatim|full contents|entire document|print the document)\b", re.I)),

    # Classic “the document says you must…” compliance attack.
    # This pattern catches instruction-following that is framed as coming from retrieved content.
    ("instruction_from_document", re.compile(
        r"\b("
        r"the document says|the doc says|according to the document|"
        r"the policy says|the instructions say|"
        r"you must comply|please comply|must answer|"
        r"follow these instructions|do exactly as written"
        r")\b",
        re.I,
    )),

    # Direct “confidential info” requests framed as compliance.
    ("confidential_compliance", re.compile(
        r"\b(confidential)\b.*\b(info|information|data)\b.*\b(comply|follow|provide)\b", re.I
    )),
]


@dataclass(frozen=True)
class InjectionCheck:
    is_injection: bool
    reasons: List[str]


def detect_prompt_injection(text: str) -> InjectionCheck:
    """
    Lightweight prompt-injection/circumvention detector.

    For public demos (and many regulated deployments), it's better to refuse than to risk leakage.
    """
    t = (text or "").strip()
    if not t:
        return InjectionCheck(False, [])

    reasons: List[str] = []
    for name, pat in _INJECTION_PATTERNS:
        if pat.search(t):
            reasons.append(name)

    return InjectionCheck(len(reasons) > 0, reasons)
