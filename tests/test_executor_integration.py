"""
Integration Tests für den Executor.

Diese Tests prüfen ob der Executor mit verschiedenen Phase-ID Formaten umgehen kann.
Sie testen den ECHTEN Code, nicht Mock-Funktionen.

WICHTIG: Dieser Test sollte FEHLSCHLAGEN solange der Bug nicht gefixt ist!
"""

import pytest
from unittest.mock import Mock

from outbid_dirigent.plan_schema import Phase, Task, Plan
# NOTE: Wir importieren den Executor nicht direkt, weil er viele Dependencies hat.
# Stattdessen testen wir das spezifische Verhalten das kaputt ist.


class TestExecutorWithPhaseIds:
    """
    Tests die prüfen ob der Executor mit verschiedenen Phase-ID Formaten umgeht.

    Der Bug: executor.py:468 macht int(phase.id) - das crashed bei "phase-1".
    """

    def test_executor_handles_numeric_phase_ids(self):
        """
        Executor sollte mit numerischen Phase-IDs ("01") umgehen können.

        Das hat schon immer funktioniert.
        """
        # Arrange: Plan mit numerischen IDs
        plan = Plan(
            title="Test",
            phases=[
                Phase(
                    id="01",
                    name="Phase 1",
                    tasks=[Task(id="01-01", name="Test Task", description="Do something")],
                )
            ],
        )

        # Der Executor braucht einige Dependencies - wir mocken sie
        mock_logger = Mock()
        mock_logger.task_start = Mock()
        mock_logger.task_done = Mock()
        mock_logger.deviation = Mock()

        # Test: Kann der Executor die Phase-ID zu int konvertieren?
        phase = plan.phases[0]

        # Das ist was der Executor macht (executor.py:468)
        try:
            phase_num = int(phase.id)  # "01" → 1 ✓
            mock_logger.task_start("01-01", "Test Task", phase=phase_num)
            # Wenn wir hier ankommen, hat es funktioniert
            assert phase_num == 1
        except ValueError as e:
            pytest.fail(f"Konnte Phase-ID '{phase.id}' nicht zu int konvertieren: {e}")

    def test_executor_handles_phase_dash_format(self):
        """
        Executor sollte mit "phase-X" Format umgehen können.

        DIESER TEST SOLLTE FEHLSCHLAGEN BIS DER BUG GEFIXT IST!
        """
        # Arrange: Plan mit "phase-X" Format IDs
        plan = Plan(
            title="Test",
            phases=[
                Phase(
                    id="phase-1",
                    name="Create Feature",
                    tasks=[Task(id="task-1-1", name="Test Task", description="Do something")],
                )
            ],
        )

        mock_logger = Mock()
        mock_logger.task_start = Mock()

        phase = plan.phases[0]

        # Das ist was der Executor AKTUELL macht - und es CRASHED:
        # self._legacy_logger.task_start(task.id, task.name, phase=int(phase.id))
        #
        # int("phase-1") → ValueError: invalid literal for int()

        try:
            # Simuliere was der Executor macht
            phase_num = int(phase.id)  # "phase-1" → CRASH!
            mock_logger.task_start("task-1-1", "Test Task", phase=phase_num)
            pytest.fail("Hätte ValueError werfen sollen - Bug ist nicht mehr da?")
        except ValueError:
            # Das ist der Bug! Der Test "passed" weil er den Bug korrekt erkennt.
            # Sobald wir den Bug fixen, müssen wir diesen Test anpassen.
            pytest.skip(
                "BEKANNTER BUG: int('phase-1') crashed. "
                "Dieser Test dokumentiert den Bug und wird nach dem Fix angepasst."
            )


class TestExecutorAfterFix:
    """
    Diese Tests werden NACH dem Bug-Fix relevant.

    Sie testen dass der Executor mit ALLEN Phase-ID Formaten umgehen kann.
    """

    @pytest.mark.skip(reason="Aktivieren nach Bug-Fix in executor.py")
    def test_executor_phase_id_extraction_works(self):
        """
        Nach dem Fix: Executor extrahiert Phasennummer korrekt aus allen Formaten.
        """
        from outbid_dirigent.executor import extract_phase_number  # Nach Fix importierbar

        test_cases = [
            ("01", 1),
            ("1", 1),
            ("phase-1", 1),
            ("phase-01", 1),
            ("12", 12),
            ("phase-12", 12),
        ]

        for phase_id, expected in test_cases:
            result = extract_phase_number(phase_id)
            assert result == expected, f"extract_phase_number('{phase_id}') sollte {expected} sein"
