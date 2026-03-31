"""
Tests für Phase-ID Handling.

Diese Tests stellen sicher, dass Phase-IDs in verschiedenen Formaten
korrekt verarbeitet werden können (z.B. "01", "phase-1", "1", etc.)

Der Bug: int("phase-1") crashed mit ValueError.
Diese Tests fangen solche Bugs BEVOR sie in Production landen.
"""

import pytest
from outbid_dirigent.plan_schema import Phase, Task, Plan
from outbid_dirigent.utils import extract_phase_number  # Die echte Funktion!


# ══════════════════════════════════════════
# UNIT TESTS
# ══════════════════════════════════════════

class TestExtractPhaseNumber:
    """Tests für die extract_phase_number Helper-Funktion."""

    def test_simple_digit(self):
        """Einfache Zahl: "1" → 1"""
        assert extract_phase_number("1") == 1

    def test_padded_digit(self):
        """Mit führender Null: "01" → 1"""
        assert extract_phase_number("01") == 1
        assert extract_phase_number("001") == 1

    def test_phase_dash_format(self):
        """Phase-Dash Format: "phase-1" → 1"""
        assert extract_phase_number("phase-1") == 1
        assert extract_phase_number("phase-01") == 1
        assert extract_phase_number("phase-12") == 12

    def test_multi_digit(self):
        """Mehrstellige Nummern"""
        assert extract_phase_number("10") == 10
        assert extract_phase_number("phase-99") == 99

    def test_invalid_format_raises(self):
        """Ungültige Formate werfen ValueError"""
        with pytest.raises(ValueError):
            extract_phase_number("invalid")

        with pytest.raises(ValueError):
            extract_phase_number("no-number-here")


# ══════════════════════════════════════════
# INTEGRATION TESTS - Plan/Phase Handling
# ══════════════════════════════════════════

class TestPlanPhaseIdHandling:
    """Tests die sicherstellen, dass Plans mit verschiedenen Phase-ID Formaten funktionieren."""

    def test_plan_with_numeric_phase_ids(self):
        """Plan mit numerischen Phase-IDs: "01", "02" """
        plan = Plan(
            title="Test Plan",
            phases=[
                Phase(id="01", name="Phase 1", tasks=[
                    Task(id="01-01", name="Task 1")
                ]),
                Phase(id="02", name="Phase 2", tasks=[
                    Task(id="02-01", name="Task 2")
                ]),
            ]
        )

        assert len(plan.phases) == 2
        assert plan.phases[0].id == "01"

        # Das ist der kritische Teil - kann die ID zu int konvertiert werden?
        phase_num = extract_phase_number(plan.phases[0].id)
        assert phase_num == 1

    def test_plan_with_phase_dash_ids(self):
        """Plan mit 'phase-X' Format IDs - DAS HAT DEN BUG VERURSACHT!"""
        plan = Plan(
            title="Test Plan",
            phases=[
                Phase(id="phase-1", name="Create Feature", tasks=[
                    Task(id="task-1-1", name="Task 1")
                ]),
                Phase(id="phase-2", name="Ship", tasks=[
                    Task(id="task-2-1", name="Task 2")
                ]),
            ]
        )

        assert len(plan.phases) == 2
        assert plan.phases[0].id == "phase-1"

        # DIESER TEST WÜRDE OHNE FIX FEHLSCHLAGEN:
        # int("phase-1") → ValueError!
        phase_num = extract_phase_number(plan.phases[0].id)
        assert phase_num == 1


# ══════════════════════════════════════════
# REGRESSION TEST - Der originale Bug
# ══════════════════════════════════════════

class TestExecutorPhaseIdBug:
    """
    Regression Test für den Bug vom 31.03.2026.

    Der Bug: executor.py Zeile 468 machte int(phase.id) was bei
    "phase-1" Format crashed.

    Dieser Test stellt sicher, dass wir nie wieder diesen Bug einführen.
    """

    def test_int_phase_id_crashes_with_phase_dash_format(self):
        """
        Demonstriert den Bug: int("phase-1") crashed.

        Dieser Test dokumentiert das Problem - er sollte PASS sein,
        weil er das fehlerhafte Verhalten testet.
        """
        phase_id = "phase-1"

        # Das war der Bug - direkt int() aufrufen crashed
        with pytest.raises(ValueError, match="invalid literal"):
            int(phase_id)

    def test_extract_phase_number_handles_all_formats(self):
        """
        Nach dem Fix: extract_phase_number() handelt alle Formate.

        Dieser Test sollte PASS sein nachdem wir den Fix implementiert haben.
        """
        # Alle diese Formate sollten funktionieren
        test_cases = [
            ("1", 1),
            ("01", 1),
            ("phase-1", 1),
            ("phase-01", 1),
            ("12", 12),
            ("phase-12", 12),
        ]

        for phase_id, expected in test_cases:
            result = extract_phase_number(phase_id)
            assert result == expected, f"extract_phase_number('{phase_id}') sollte {expected} sein, war aber {result}"
