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
from logger import init_logger, get_logger
from analyzer import Analyzer, load_analysis
from router import Router, Route, RouteType, StepType, load_route, load_state, mark_step_complete
from executor import Executor, create_executor


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

    # Prüfe ob Analyse bereits existiert
    if not force:
        existing = load_analysis(str(repo_path))
        if existing:
            logger.info(f"Existierende Analyse gefunden (Route: {existing['route']})")
            return existing

    # Neue Analyse durchführen
    analyzer = Analyzer(str(repo_path), str(spec_path))
    result = analyzer.analyze()

    return result


def run_routing(repo_path: Path, analysis) -> Route:
    """Bestimmt und speichert die Route."""
    router = Router(str(repo_path))
    route = router.determine_route(analysis)
    router.save_route(route)
    return route


def run_execution(repo_path: Path, spec_path: Path, route: Route, dry_run: bool = False, use_proteus: bool = False) -> bool:
    """Führt alle Schritte basierend auf der Route aus."""
    logger = get_logger()
    executor = create_executor(str(repo_path), str(spec_path), dry_run, use_proteus)

    state = load_state(str(repo_path)) or {"completed_steps": []}
    completed_steps = state.get("completed_steps", [])

    for step in route.steps:
        step_name = step.step_type.value

        # Überspringe bereits abgeschlossene Schritte
        if step_name in completed_steps:
            logger.skip(step_name, "bereits abgeschlossen")
            continue

        success = False

        if step.step_type == StepType.BUSINESS_RULE_EXTRACTION:
            success = executor.extract_business_rules()

        elif step.step_type == StepType.QUICK_SCAN:
            success = executor.quick_scan()

        elif step.step_type == StepType.PLANNING:
            success = executor.create_plan()

        elif step.step_type == StepType.EXECUTION:
            success = executor.execute_plan()

        elif step.step_type == StepType.SHIP:
            success = executor.ship()

        if success:
            mark_step_complete(str(repo_path), step_name)
        else:
            logger.stop(f"Schritt '{step.name}' fehlgeschlagen")
            return False

    return True


def resume_execution(repo_path: Path, spec_path: Path, dry_run: bool = False, use_proteus: bool = False) -> bool:
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
    from analyzer import AnalysisResult, RepoAnalysis, SpecAnalysis
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

    return run_execution(repo_path, spec_path, route, dry_run, use_proteus)


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
        help="Pfad zur SPEC.md Datei",
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

    args = parser.parse_args()

    # Pfade auflösen
    spec_path = Path(args.spec).resolve()
    repo_path = Path(args.repo).resolve()

    # Validierung
    if not validate_inputs(spec_path, repo_path):
        sys.exit(1)

    # Logger initialisieren
    verbose = not args.quiet
    output_json = args.output == "json"
    logger = init_logger(str(repo_path), verbose, output_json)
    logger.start()

    try:
        # Resume-Modus
        if args.resume:
            success = resume_execution(repo_path, spec_path, args.dry_run, args.use_proteus)
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

        # Execution
        if args.phase in ["execute", "all"]:
            if args.dry_run:
                logger.info("[DRY-RUN] Würde Ausführung starten")
                logger.info(f"Route: {route.route_type.value}")
                logger.info(f"Schritte: {[s.name for s in route.steps]}")
                logger.info(f"Geschätzte Tasks: {route.estimated_tasks}")
            else:
                success = run_execution(repo_path, spec_path, route, args.dry_run, args.use_proteus)
                if not success:
                    sys.exit(1)

        # Ship only
        if args.phase == "ship":
            executor = create_executor(str(repo_path), str(spec_path), args.dry_run, args.use_proteus)
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
