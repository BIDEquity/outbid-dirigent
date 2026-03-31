"""
Utility functions for outbid-dirigent.
"""

import re
from typing import Union


def extract_phase_number(phase_id: Union[str, int]) -> int:
    """
    Extrahiert die Phasennummer aus einer Phase-ID.

    Unterstützte Formate:
    - 1 (int) → 1
    - "1" → 1
    - "01" → 1
    - "phase-1" → 1
    - "phase-01" → 1

    Args:
        phase_id: Die Phase-ID als String oder Integer

    Returns:
        Die extrahierte Phasennummer als Integer

    Raises:
        ValueError: Wenn keine Nummer extrahiert werden kann

    Examples:
        >>> extract_phase_number("01")
        1
        >>> extract_phase_number("phase-1")
        1
        >>> extract_phase_number(5)
        5
    """
    # Wenn bereits ein Integer, direkt zurückgeben
    if isinstance(phase_id, int):
        return phase_id

    # Zu String konvertieren falls nötig
    phase_id = str(phase_id)

    # Versuche direkte Konvertierung (z.B. "01", "1", "12")
    if phase_id.isdigit():
        return int(phase_id)

    # Versuche "phase-X" oder "step-X" Format
    if "-" in phase_id:
        parts = phase_id.split("-")
        for part in reversed(parts):  # Von hinten, weil Nummer meist am Ende
            if part.isdigit():
                return int(part)

    # Versuche Zahlen am Ende zu finden (z.B. "phase01", "step2")
    match = re.search(r'(\d+)$', phase_id)
    if match:
        return int(match.group(1))

    # Versuche Zahlen irgendwo zu finden
    match = re.search(r'(\d+)', phase_id)
    if match:
        return int(match.group(1))

    raise ValueError(f"Cannot extract phase number from '{phase_id}'")
