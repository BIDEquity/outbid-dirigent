#!/usr/bin/env python3
"""
Outbid Dirigent – Headless autonomous coding agent controller

Der Dirigent ist ein Python Control Plane das eine SPEC.md liest, das Ziel-Repo
analysiert, den richtigen Ausführungspfad wählt und dann autonom durcharbeitet.

Usage:
    python3 dirigent.py --spec .planning/SPEC.md --repo /path/to/repo

Kein Mensch in der Loop. Kein interaktives Terminal. Kein Warten auf Input.
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# Eigene Module
from outbid_dirigent.logger import init_logger, get_logger
from outbid_dirigent.analyzer import Analyzer, load_analysis
from outbid_dirigent.router import Router, Route, RouteType, StepType, load_route, load_state, mark_step_complete
from outbid_dirigent.executor import Executor, create_executor
from outbid_dirigent.questioner import create_questioner, create_dummy_questioner
from outbid_dirigent.portal_reporter import PortalReporter, create_portal_reporter

# Global questioner instance (set in main)
_questioner = None
# Global execution mode (autonomous, plan_first, interactive)
_execution_mode = "autonomous"
# Global portal reporter instance
_portal_reporter = None

def get_questioner():
    """Gibt die globale Questioner-Instanz zurück."""
    global _questioner
    return _questioner

def set_questioner(questioner):
    """Setzt die globale Questioner-Instanz."""
    global _questioner
    _questioner = questioner

def get_execution_mode():
    """Gibt den aktuellen Execution Mode zurück."""
    global _execution_mode
    return _execution_mode

def set_execution_mode(mode: str):
    """Setzt den Execution Mode."""
    global _execution_mode
    _execution_mode = mode

def get_portal_reporter():
    """Gibt die globale PortalReporter-Instanz zurück."""
    global _portal_reporter
    return _portal_reporter

def set_portal_reporter(reporter):
    """Setzt die globale PortalReporter-Instanz."""
    global _portal_reporter
    _portal_reporter = reporter


def validate_inputs(spec_path: Path, repo_path: Path) -> bool:
    """Validiert die Eingabepfade."""
    errors = []

    if not spec_path.exists():
        errors.append(f"SPEC nicht gefunden: {spec_path}")

    if not repo_path.exists():
        errors.append(f"Repo nicht gefunden: {repo_path}")
    elif not repo_path.is_dir():
        errors.append(f"Repo ist kein Verzeichnis: {repo_path}")

    # Prüfe ob Git-Repo
    if repo_path.exists() and not (repo_path / ".git").exists():
        errors.append(f"Repo ist kein Git-Repository: {repo_path}")

    if errors:
        for error in errors:
            print(f"❌ {error}", file=sys.stderr)
        return False

    return True


def run_analysis(repo_path: Path, spec_path: Path, force: bool = False):
    """Führt die Analyse durch."""
    logger = get_logger()
    reporter = get_portal_reporter()

    # Prüfe ob Analyse bereits existiert
    if not force:
        existing = load_analysis(str(repo_path))
        if existing:
            logger.info(f"Existierende Analyse gefunden (Route: {existing['route']})")
            # Send analysis result even for cached analysis
            if reporter:
                reporter.analysis_result(
                    language=existing.get("primary_language", "Unknown"),
                    framework=existing.get("framework_detected") or "None",
                    commit_count=existing.get("commit_count", 0),
                    file_count=existing.get("file_count", 0),
                    route=existing.get("route", "hybrid"),
                    confidence=existing.get("confidence", "medium"),
                )
            return existing

    # Send stage start event
    if reporter:
        reporter.stage_start("analysis", "Analysiere Repository-Struktur und Spec")

    # Neue Analyse durchführen
    analyzer = Analyzer(str(repo_path), str(spec_path))
    result = analyzer.analyze()

    # Send analysis result event
    if reporter:
        reporter.analysis_result(
            language=result.repo.primary_language,
            framework=result.repo.framework_detected or "None",
            commit_count=result.repo.commit_count,
            file_count=result.repo.file_count,
            route=result.route,
            confidence=result.confidence,
        )
        reporter.stage_complete(
            "analysis",
            result=f"Route: {result.route} ({result.confidence} confidence)",
            details={
                "language": result.repo.primary_language,
                "framework": result.repo.framework_detected,
                "route": result.route,
            },
        )

    return result


def run_routing(repo_path: Path, analysis) -> Route:
    """Bestimmt und speichert die Route."""
    reporter = get_portal_reporter()

    # Send stage start event
    if reporter:
        reporter.stage_start("routing", "Bestimme optimalen Ausführungspfad")

    router = Router(str(repo_path))
    route = router.determine_route(analysis)
    router.save_route(route)

    # Send route determined event
    if reporter:
        reporter.route_determined(
            route_type=route.route_type.value,
            reason=route.reason,
            steps=[step.name for step in route.steps],
            estimated_tasks=route.estimated_tasks,
        )
        reporter.stage_complete(
            "routing",
            result=f"{route.route_type.value} Route mit {len(route.steps)} Schritten",
            details={
                "routeType": route.route_type.value,
                "steps": [step.step_type.value for step in route.steps],
            },
        )

    return route


def run_execution(
    repo_path: Path,
    spec_path: Path,
    route: Route,
    dry_run: bool = False,
    use_proteus: bool = False,
    execution_mode: str = "autonomous",
    model: str = "",
    effort: str = "",
    portal_url: str = "",
    execution_id: str = "",
    reporter_token: str = "",
) -> bool:
    """Führt alle Schritte basierend auf der Route aus."""
    import json
    logger = get_logger()
    reporter = get_portal_reporter()
    executor = create_executor(
        str(repo_path), str(spec_path), dry_run, use_proteus, model, effort,
        portal_url=portal_url, execution_id=execution_id, reporter_token=reporter_token,
    )
    questioner = get_questioner()

    state = load_state(str(repo_path)) or {"completed_steps": []}
    completed_steps = state.get("completed_steps", [])

    for step in route.steps:
        step_name = step.step_type.value

        # Überspringe bereits abgeschlossene Schritte
        if step_name in completed_steps:
            logger.skip(step_name, "bereits abgeschlossen")
            continue

        success = False

        if step.step_type == StepType.INIT:
            if reporter:
                reporter.stage_start("init", "Bootstrap dev environment and configure e2e credentials")
            success = executor.run_init()
            if reporter:
                reporter.stage_complete("init", "Init phase complete" if success else "Init phase failed")

        elif step.step_type == StepType.BUSINESS_RULE_EXTRACTION:
            if reporter:
                reporter.stage_start("business_rules", "Extrahiere Business Rules aus der Codebase")
            success = executor.extract_business_rules()
            if reporter:
                reporter.stage_complete("business_rules", "Business Rules extrahiert" if success else "Fehler bei Extraktion")

        elif step.step_type == StepType.QUICK_SCAN:
            if reporter:
                reporter.stage_start("quick_scan", "Scanne relevante Dateien für das Feature")
            success = executor.quick_scan()
            if reporter:
                reporter.stage_complete("quick_scan", "Quick Scan abgeschlossen" if success else "Fehler bei Quick Scan")

        elif step.step_type == StepType.PLANNING:
            # Skip planning if PLAN.json already exists (e.g. from --plan-only)
            plan_file = repo_path / ".dirigent" / "PLAN.json"
            if plan_file.exists():
                logger.info("Existierender Plan gefunden, überspringe Planung")
                success = True
            else:
                if reporter:
                    reporter.stage_start("planning", "Erstelle Ausführungsplan mit Claude Code")
                success = executor.create_plan()

            # plan_first: Nach Plan-Erstellung auf Genehmigung warten
            if success and execution_mode == "plan_first" and questioner and questioner.is_enabled():
                plan_file = repo_path / ".dirigent" / "PLAN.json"
                if plan_file.exists():
                    try:
                        with open(plan_file, encoding="utf-8") as f:
                            plan_content = json.load(f)

                        logger.info("Warte auf Plan-Genehmigung...")
                        result = questioner.submit_plan_for_approval(plan_content)

                        if result["status"] == "rejected":
                            logger.stop(f"Plan abgelehnt: {result.get('message', 'Keine Begründung')}")
                            return False

                        elif result["status"] == "timeout":
                            logger.stop("Plan-Genehmigung Timeout - breche ab")
                            return False

                        elif result["status"] == "error":
                            logger.error(f"Plan-Approval Fehler: {result.get('message')}")
                            return False

                        elif result["status"] == "edited":
                            # Editierten Plan speichern
                            edited_plan = result["plan"]
                            with open(plan_file, "w", encoding="utf-8") as f:
                                json.dump(edited_plan, f, indent=2, ensure_ascii=False)
                            logger.info("Editierter Plan gespeichert")

                        # approved oder edited -> weiter

                    except Exception as e:
                        logger.error(f"Fehler beim Plan-Approval: {e}")
                        return False

        elif step.step_type == StepType.EXECUTION:
            if reporter:
                reporter.stage_start("execution", "Führe Tasks mit Claude Code aus")
            success = executor.execute_plan()
            if reporter:
                reporter.stage_complete("execution", "Ausführung abgeschlossen" if success else "Ausführung fehlgeschlagen")

        elif step.step_type == StepType.TEST:
            if reporter:
                reporter.stage_start("testing", "Führe Test-Suite aus")
            success = executor.run_tests()
            if reporter:
                reporter.stage_complete("testing", "Tests bestanden" if success else "Tests fehlgeschlagen")

        elif step.step_type == StepType.SHIP:
            if reporter:
                reporter.stage_start("shipping", "Erstelle Branch und PR")
            success = executor.ship()
            if reporter:
                reporter.stage_complete("shipping", "PR erstellt" if success else "Shipping fehlgeschlagen")

        if success:
            mark_step_complete(str(repo_path), step_name)
        elif not step.required:
            logger.warn(f"Optionaler Schritt '{step.name}' fehlgeschlagen, fahre fort")
            mark_step_complete(str(repo_path), step_name)
        else:
            logger.stop(f"Schritt '{step.name}' fehlgeschlagen")
            return False

    return True


def resume_execution(repo_path: Path, spec_path: Path, dry_run: bool = False, use_proteus: bool = False, model: str = "", effort: str = "") -> bool:
    """Setzt eine unterbrochene Ausführung fort."""
    logger = get_logger()

    # Lade existierende Route
    route_data = load_route(str(repo_path))
    if not route_data:
        logger.error("Keine existierende Route gefunden. Starte mit --phase all")
        return False

    # Route rekonstruieren
    route_type = RouteType(route_data["route"])
    router = Router(str(repo_path))

    # Dummy-Analyse für Route-Bestimmung (wir haben ja schon die Route)
    from outbid_dirigent.analyzer import AnalysisResult, RepoAnalysis, SpecAnalysis
    analysis = load_analysis(str(repo_path))

    if not analysis:
        logger.error("Keine Analyse gefunden. Starte mit --phase all")
        return False

    # Route basierend auf gespeichertem Typ
    if route_type == RouteType.GREENFIELD:
        route = Route(
            route_type=route_type,
            reason=route_data["reason"],
            steps=router.GREENFIELD_STEPS.copy(),
            estimated_tasks=route_data["estimated_tasks"],
            oracle_needed=route_data["oracle_needed"],
            repo_context_needed=route_data["repo_context_needed"],
        )
    elif route_type == RouteType.LEGACY:
        route = Route(
            route_type=route_type,
            reason=route_data["reason"],
            steps=router.LEGACY_STEPS.copy(),
            estimated_tasks=route_data["estimated_tasks"],
            oracle_needed=route_data["oracle_needed"],
            repo_context_needed=route_data["repo_context_needed"],
        )
    else:
        route = Route(
            route_type=route_type,
            reason=route_data["reason"],
            steps=router.HYBRID_STEPS.copy(),
            estimated_tasks=route_data["estimated_tasks"],
            oracle_needed=route_data["oracle_needed"],
            repo_context_needed=route_data["repo_context_needed"],
        )

    state = load_state(str(repo_path))
    if state and state.get("completed_tasks"):
        last_task = state["completed_tasks"][-1]
        logger.resume(last_task)

    return run_execution(repo_path, spec_path, route, dry_run, use_proteus, model=model, effort=effort)


def main():
    parser = argparse.ArgumentParser(
        description="Outbid Dirigent – Headless autonomous coding agent controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Kompletter Durchlauf
  python3 dirigent.py --spec .planning/SPEC.md --repo /path/to/repo

  # Nur Analyse
  python3 dirigent.py --spec SPEC.md --repo /path/to/repo --phase analyze

  # Fortsetzen nach Unterbrechung
  python3 dirigent.py --spec SPEC.md --repo /path/to/repo --resume

  # Dry-Run (keine Änderungen)
  python3 dirigent.py --spec SPEC.md --repo /path/to/repo --dry-run
        """,
    )

    parser.add_argument(
        "--spec",
        required=True,
        help="Pfad zur SPEC.md Datei (oder '-' / '.' fuer stdin)",
    )

    parser.add_argument(
        "--repo",
        required=True,
        help="Pfad zum Ziel-Repository",
    )

    parser.add_argument(
        "--phase",
        choices=["analyze", "execute", "ship", "all"],
        default="all",
        help="Welche Phase ausführen (default: all)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur analysieren, keine Änderungen durchführen",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Unterbrochene Ausführung fortsetzen",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Analyse neu durchführen (Cache ignorieren)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Ausführliche Ausgabe (default: True)",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimale Ausgabe",
    )

    parser.add_argument(
        "--use-proteus",
        action="store_true",
        help="Nutze Proteus für tiefgehende Domain-Extraktion (empfohlen für Legacy-Migrationen)",
    )

    parser.add_argument(
        "--output",
        choices=["json"],
        default=None,
        help="Zusätzlich JSON Lines (@@JSON@@-prefixed) nach stdout ausgeben",
    )

    parser.add_argument(
        "--execution-mode",
        choices=["autonomous", "plan_first", "interactive"],
        default="autonomous",
        help="Execution Mode: autonomous (keine Fragen), plan_first (Plan bestätigen), interactive (Rückfragen)",
    )

    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Analyse + Routing + Plan erstellen, dann stoppen. Plan liegt in .dirigent/PLAN.json",
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="[DEPRECATED] Nutze --execution-mode interactive",
    )

    parser.add_argument(
        "--question-timeout",
        type=int,
        default=30,
        help="Timeout in Minuten für interaktive Fragen (default: 30)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="Claude Model für Task-Ausführung (z.B. haiku, sonnet, opus). Leer = Claude Code Default.",
    )

    parser.add_argument(
        "--effort",
        choices=["low", "medium", "high", "max"],
        default="",
        help="Thinking Effort Level (low, medium, high, max). Leer = Default.",
    )

    parser.add_argument(
        "--portal-url",
        type=str,
        default=os.environ.get("PORTAL_URL", "https://outbid-portal.vercel.app"),
        help="URL des Outbid Portals für API-Calls",
    )

    parser.add_argument(
        "--execution-id",
        type=str,
        default=os.environ.get("EXECUTION_ID"),
        help="Execution-ID für Portal-Integration (env: EXECUTION_ID)",
    )

    parser.add_argument(
        "--reporter-token",
        type=str,
        default=os.environ.get("REPORTER_TOKEN"),
        help="Reporter-Token für Portal-Integration (env: REPORTER_TOKEN)",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Demo-Modus: Sendet simulierte Events ohne echte Ausführung (für UI-Tests und Demos)",
    )

    parser.add_argument(
        "--demo-speed",
        type=float,
        default=1.0,
        help="Geschwindigkeit des Demo-Modus (1.0 = normal, 2.0 = doppelt so schnell)",
    )

    args = parser.parse_args()

    # Pfade auflösen
    repo_path = Path(args.repo).resolve()

    # Spec von stdin lesen wenn "-" oder "." als Argument
    if args.spec in ("-", "."):
        import tempfile
        stdin_content = sys.stdin.read()
        if not stdin_content.strip():
            print("❌ Keine Spec-Daten auf stdin empfangen", file=sys.stderr)
            sys.exit(1)
        (repo_path / ".dirigent").mkdir(parents=True, exist_ok=True)
        spec_tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", prefix="spec-", dir=repo_path / ".dirigent",
            delete=False, encoding="utf-8",
        )
        spec_tmp.write(stdin_content)
        spec_tmp.close()
        spec_path = Path(spec_tmp.name)
    else:
        spec_path = Path(args.spec).resolve()

    # Validierung
    if not validate_inputs(spec_path, repo_path):
        sys.exit(1)

    # Logger initialisieren
    verbose = not args.quiet
    output_json = args.output == "json"
    logger = init_logger(str(repo_path), verbose, output_json)
    logger.start()

    # Portal Reporter initialisieren (für Events an Portal)
    has_credentials = args.portal_url and args.execution_id and args.reporter_token

    if has_credentials:
        reporter = create_portal_reporter(
            portal_url=args.portal_url,
            execution_id=args.execution_id,
            reporter_token=args.reporter_token,
        )
        set_portal_reporter(reporter)
        logger.info(f"Portal-Reporter aktiviert: {args.portal_url}")
    else:
        set_portal_reporter(None)
        logger.debug("Portal-Reporter deaktiviert (keine Credentials)")

    # Demo-Modus: Simulierte Events senden und beenden
    if args.demo:
        if not has_credentials:
            logger.error("Demo-Modus benötigt Portal-Credentials (--portal-url, --execution-id, --reporter-token)")
            sys.exit(1)

        logger.info("🎭 Demo-Modus aktiviert - sende simulierte Events")
        from outbid_dirigent.demo_runner import run_demo
        try:
            run_demo(
                portal_url=args.portal_url,
                execution_id=args.execution_id,
                reporter_token=args.reporter_token,
                speed=args.demo_speed,
            )
            logger.info("🎭 Demo-Modus abgeschlossen")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Demo-Modus fehlgeschlagen: {e}")
            sys.exit(1)

    # Questioner initialisieren (für interaktive Fragen und plan_first)
    needs_questioner = args.interactive or args.execution_mode in ["interactive", "plan_first"]

    if needs_questioner and has_credentials:
        questioner = create_questioner(
            portal_url=args.portal_url,
            reporter_token=args.reporter_token,
            execution_id=args.execution_id,
            timeout_minutes=args.question_timeout,
        )
        questioner.set_logger(logger)
        set_questioner(questioner)
        logger.info(f"Questioner aktiviert (Timeout: {args.question_timeout}min)")
    else:
        set_questioner(create_dummy_questioner())
        if needs_questioner:
            logger.warn(f"Execution Mode '{args.execution_mode}' benötigt Portal-Credentials (fehlen)")

    try:
        # Resume-Modus
        if args.resume:
            success = resume_execution(repo_path, spec_path, args.dry_run, args.use_proteus, args.model, args.effort)
            sys.exit(0 if success else 1)

        # Normale Ausführung
        if args.phase in ["analyze", "all"]:
            analysis = run_analysis(repo_path, spec_path, args.force)

            if args.phase == "analyze":
                logger.info("Analyse abgeschlossen. Beende.")
                sys.exit(0)

        # Route bestimmen
        analysis = run_analysis(repo_path, spec_path, force=False)
        route = run_routing(repo_path, analysis)

        # Determine execution mode (--execution-mode takes precedence over --interactive)
        execution_mode = args.execution_mode
        if execution_mode == "autonomous" and args.interactive:
            execution_mode = "interactive"  # Backwards compatibility

        # Set global execution mode for other modules to access
        set_execution_mode(execution_mode)
        logger.info(f"Execution Mode: {execution_mode}")

        # Plan-Only: Nur bis Plan erstellen, dann stoppen
        if args.plan_only:
            executor = create_executor(str(repo_path), str(spec_path), dry_run=False, use_proteus=args.use_proteus, model=args.model, effort=args.effort)
            success = executor.create_plan()
            if success:
                plan_file = repo_path / ".dirigent" / "PLAN.json"
                logger.info(f"Plan erstellt: {plan_file}")
                logger.info("Prüfe den Plan und starte dann mit: --phase execute")
            else:
                logger.error("Plan-Erstellung fehlgeschlagen")
            sys.exit(0 if success else 1)

        # Execution
        if args.phase in ["execute", "all"]:
            if args.dry_run:
                logger.info("[DRY-RUN] Würde Ausführung starten")
                logger.info(f"Route: {route.route_type.value}")
                logger.info(f"Schritte: {[s.name for s in route.steps]}")
                logger.info(f"Geschätzte Tasks: {route.estimated_tasks}")
            else:
                success = run_execution(
                    repo_path, spec_path, route, args.dry_run, args.use_proteus, execution_mode, args.model, args.effort,
                    portal_url=args.portal_url or "",
                    execution_id=args.execution_id or "",
                    reporter_token=args.reporter_token or "",
                )
                if not success:
                    sys.exit(1)

                # Log final progress
                from outbid_dirigent.progress import print_progress
                logger.info("\n" + print_progress(str(repo_path), "console"))

                # Summary generieren nach erfolgreicher Execution
                executor = create_executor(
                    str(repo_path), str(spec_path), args.dry_run, args.use_proteus, args.model, args.effort,
                    portal_url=args.portal_url or "",
                    execution_id=args.execution_id or "",
                    reporter_token=args.reporter_token or "",
                )
                executor.generate_summary()

                # Preview-Script generieren für Workspace-Vorschau
                executor.generate_preview_script()

        # Ship only
        if args.phase == "ship":
            executor = create_executor(str(repo_path), str(spec_path), args.dry_run, args.use_proteus, args.model)
            success = executor.ship()
            sys.exit(0 if success else 1)

        logger.info("Dirigent abgeschlossen.")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.stop("Unterbrochen durch Benutzer")
        logger.error_json("Unterbrochen durch Benutzer", fatal=True)
        logger.run_complete(success=False)
        sys.exit(130)

    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}", e)
        logger.error_json(str(e), fatal=True)
        logger.run_complete(success=False)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
