"""
Smoke Tests für den Dirigent.

Diese Tests stellen sicher, dass der Dirigent grundsätzlich funktioniert
und keine offensichtlichen Bugs hat, die zum Crash führen.

Läuft bei jedem Push in GitHub Actions.
"""

from pathlib import Path
from unittest.mock import Mock, patch

from outbid_dirigent.plan_schema import Plan, Phase, Task
from outbid_dirigent.utils import extract_phase_number
from outbid_dirigent.logger import DirigentLogger


class TestSmokeBasics:
    """Grundlegende Smoke Tests - stellt sicher dass nichts crasht."""

    def test_can_import_all_modules(self):
        """Alle wichtigen Module können importiert werden."""
        # Diese Imports sollten nicht crashen
        from outbid_dirigent.plan_schema import Plan
        from outbid_dirigent.utils import extract_phase_number

        assert Plan is not None
        assert extract_phase_number is not None

    def test_can_create_plan_with_various_phase_ids(self):
        """Plans mit verschiedenen Phase-ID Formaten können erstellt werden."""
        # Alle diese Formate sollten funktionieren
        test_cases = [
            "01",
            "1",
            "phase-1",
            "phase-01",
            "step-1",
        ]

        for phase_id in test_cases:
            plan = Plan(
                title="Test",
                phases=[
                    Phase(
                        id=phase_id,
                        name=f"Phase {phase_id}",
                        tasks=[Task(id=f"{phase_id}-01", name="Test Task")],
                    )
                ],
            )

            # Sollte nicht crashen
            phase_num = extract_phase_number(plan.phases[0].id)
            assert isinstance(phase_num, int), f"Phase ID '{phase_id}' sollte zu int werden"

    def test_logger_handles_all_phase_id_formats(self):
        """Der Logger crashed nicht bei verschiedenen Phase-ID Formaten."""
        logger = DirigentLogger(repo_path="/tmp/test", verbose=False)

        # Diese Aufrufe sollten nicht crashen
        test_phase_ids = ["01", "1", "phase-1", "phase-01"]

        for phase_id in test_phase_ids:
            phase_num = extract_phase_number(phase_id)

            # Simuliere was der Executor macht
            logger.task_start("task-1", "Test Task", phase=phase_num)
            logger.task_done("task-1", commit_hash="abc1234", phase=phase_num)


class TestSmokePlanExecution:
    """Smoke Tests die einen Plan-Durchlauf simulieren."""

    def test_plan_execution_simulation(self):
        """
        Simuliert einen kompletten Plan-Durchlauf.

        Das ist der kritische Pfad der heute gebrochen war.
        """
        # Plan mit "phase-X" Format (das hat den Bug verursacht)
        plan = Plan(
            title="Integration Test Feature",
            phases=[
                Phase(
                    id="phase-1",
                    name="Create Feature",
                    tasks=[
                        Task(id="task-1-1", name="Create file"),
                        Task(id="task-1-2", name="Add content"),
                    ],
                ),
                Phase(
                    id="phase-2",
                    name="Ship",
                    tasks=[
                        Task(id="task-2-1", name="Create PR"),
                    ],
                ),
            ],
        )

        # Mock Logger
        logger = DirigentLogger(repo_path="/tmp/test", verbose=False)

        # Simuliere Execution Loop (wie in executor.py)
        for phase in plan.phases:
            phase_num = extract_phase_number(phase.id)

            # Phase Start
            logger.phase_start(phase.id, phase.name, len(phase.tasks))

            for task in phase.tasks:
                # Task Start - DAS HAT VORHER GECRASHT
                logger.task_start(task.id, task.name, phase=phase_num)

                # Simuliere Task-Completion
                logger.task_done(task.id, commit_hash="abc1234", phase=phase_num)

            # Phase Complete
            logger.phase_complete(
                phase.id,
                phase.name,
                len(phase.tasks),
                commit_count=len(phase.tasks),
                deviation_count=0,
            )

        # Wenn wir hier ankommen, hat nichts gecrasht
        assert True


class TestSmokePortalReporter:
    """Smoke Tests für Portal-Integration."""

    def test_portal_reporter_event_format(self):
        """
        Portal Reporter erzeugt Events im korrekten Format.

        Dieser Test würde in einer echten Integration gegen das Portal laufen,
        aber hier mocken wir den HTTP Call.
        """
        from outbid_dirigent.portal_reporter import PortalReporter

        # Mock requests.post
        with patch("outbid_dirigent.portal_reporter.requests.post") as mock_post:
            mock_post.return_value = Mock(status_code=200, json=lambda: {"success": True})

            reporter = PortalReporter(
                portal_url="https://test.portal.com",
                execution_id="test-123",
                reporter_token="test-token",
            )

            # Diese Calls sollten nicht crashen und valide Events senden
            reporter.phase_start("phase-1", "Create Feature", task_count=2)
            reporter.task_start("task-1-1", "Create file")
            reporter.task_complete("task-1-1", commit_hash="abc1234")

            # Verify: Events wurden gesendet
            assert mock_post.called


class TestSmokeFixtures:
    """Tests mit Fixture-Dateien."""

    def test_can_load_simple_spec(self):
        """Die Test-Spec Datei kann geladen werden."""
        spec_path = Path(__file__).parent / "fixtures" / "simple-spec.md"

        assert spec_path.exists(), f"Fixture {spec_path} sollte existieren"

        content = spec_path.read_text()
        assert "Test Feature" in content
        assert "hello.txt" in content
