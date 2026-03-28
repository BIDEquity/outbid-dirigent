#!/usr/bin/env python3
"""
Outbid Dirigent – Analyzer
Analysiert Repo-Struktur und Spec-Inhalt um den optimalen Ausführungspfad zu bestimmen.
"""

import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import Counter

from outbid_dirigent.logger import get_logger


@dataclass
class RepoAnalysis:
    """Ergebnis der Repository-Analyse."""
    repo_path: str
    repo_name: str
    primary_language: str
    secondary_languages: List[str]
    framework_detected: Optional[str]
    build_tool: Optional[str]
    commit_count: int
    last_commit_days_ago: int
    last_commit_date: Optional[str]
    file_count: int
    total_lines: int
    has_tests: bool
    has_ci: bool
    directories: List[str]
    config_files: List[str]


@dataclass
class SpecAnalysis:
    """Ergebnis der Spec-Analyse."""
    spec_path: str
    title: str
    has_legacy_keywords: bool
    has_greenfield_keywords: bool
    has_testability_keywords: bool
    has_tracking_keywords: bool
    legacy_keywords_found: List[str]
    greenfield_keywords_found: List[str]
    testability_keywords_found: List[str]
    tracking_keywords_found: List[str]
    target_language: Optional[str]
    complexity: Optional[str]
    estimated_scope: str  # small, medium, large


@dataclass
class RuntimeRequirement:
    """Eine benötigte Runtime-Abhängigkeit (Service, Tool, etc.)."""
    name: str
    type: str  # database, cache, queue, storage, api
    docker_image: Optional[str] = None
    port: Optional[int] = None
    env_vars: Optional[List[str]] = None


@dataclass
class RuntimeAnalysis:
    """Analyse wie das Projekt lokal gestartet wird."""
    start_command: str  # z.B. "npm run dev"
    port: int  # z.B. 3000
    package_manager: str  # npm, yarn, pnpm, pip, go, etc.
    framework: Optional[str]  # Next.js, FastAPI, etc.
    services: List[RuntimeRequirement]  # Benötigte Services (DB, Redis, etc.)
    setup_steps: List[str]  # z.B. ["npm install", "npm run db:migrate"]
    uses_doppler: bool  # Ob Doppler für Secrets verwendet wird
    uses_docker_compose: bool  # Ob docker-compose.yml vorhanden ist
    env_file: Optional[str]  # .env.example oder .env.local
    health_check_path: Optional[str]  # z.B. "/api/health"


@dataclass
class AnalysisResult:
    """Kombiniertes Analyse-Ergebnis."""
    repo: RepoAnalysis
    spec: SpecAnalysis
    runtime: Optional[RuntimeAnalysis]  # NEU: Runtime-Analyse
    route: str  # greenfield, legacy, hybrid
    route_reason: str
    confidence: str  # low, medium, high
    legacy_signals: int
    greenfield_signals: int


# Sprach-Erkennung basierend auf Dateiendungen
LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".go": "Go",
    ".rs": "Rust",
    ".swift": "Swift",
    ".m": "Objective-C",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".scala": "Scala",
    ".clj": "Clojure",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".hs": "Haskell",
    ".lua": "Lua",
    ".r": "R",
    ".jl": "Julia",
    ".dart": "Dart",
    ".vue": "Vue",
    ".svelte": "Svelte",
}

# Framework-Erkennung basierend auf Dateien
FRAMEWORK_INDICATORS = {
    "package.json": {
        "react": "React",
        "vue": "Vue.js",
        "angular": "Angular",
        "next": "Next.js",
        "nuxt": "Nuxt.js",
        "express": "Express.js",
        "fastify": "Fastify",
        "nest": "NestJS",
        "svelte": "Svelte",
    },
    "requirements.txt": {
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI",
        "tornado": "Tornado",
    },
    "Gemfile": {
        "rails": "Ruby on Rails",
        "sinatra": "Sinatra",
    },
    "composer.json": {
        "laravel": "Laravel",
        "symfony": "Symfony",
    },
    "pom.xml": {
        "spring": "Spring Boot",
    },
    "build.gradle": {
        "spring": "Spring Boot",
    },
    "go.mod": {},
    "Cargo.toml": {},
    "pubspec.yaml": {
        "flutter": "Flutter",
    },
}

# Build-Tool-Erkennung
BUILD_TOOLS = {
    "package.json": "npm/yarn",
    "pom.xml": "Maven",
    "build.gradle": "Gradle",
    "Makefile": "Make",
    "CMakeLists.txt": "CMake",
    "Cargo.toml": "Cargo",
    "go.mod": "Go Modules",
    "requirements.txt": "pip",
    "Pipfile": "Pipenv",
    "pyproject.toml": "Poetry/pip",
    "Gemfile": "Bundler",
    "composer.json": "Composer",
    "pubspec.yaml": "pub",
}

# Keywords für Routing-Entscheidung
LEGACY_KEYWORDS = [
    "refactor", "migrate", "migration", "rewrite", "port", "legacy",
    "convert", "modernize", "upgrade", "replace", "deprecated",
    "technical debt", "tech debt", "overhaul", "replatform",
    "umschreiben", "migrieren", "portieren", "ersetzen", "modernisieren",
]

GREENFIELD_KEYWORDS = [
    "add", "build", "create", "implement", "new feature", "neue",
    "develop", "design", "introduce", "setup", "initialize",
    "hinzufügen", "erstellen", "bauen", "implementieren", "entwickeln",
    "feature", "neu", "anlegen",
]

TESTABILITY_KEYWORDS = [
    "testability", "testbarkeit", "test coverage", "testabdeckung",
    "e2e test", "end-to-end test", "testing infrastructure",
    "test setup", "test harness", "increase testability",
    "improve testing", "add tests", "tests hinzufügen",
    "test framework", "playwright setup", "cypress setup",
    "seed data", "test fixtures", "test environment",
]

TRACKING_KEYWORDS = [
    "tracking", "analytics", "posthog", "feature tracking",
    "event tracking", "user tracking", "product analytics",
    "telemetry", "instrumentation", "feature flags",
    "ab test", "a/b test", "conversion tracking",
    "nutzer tracking", "analyse", "feature usage",
]

# Sprachen die auf Target-Language hinweisen können
LANGUAGE_KEYWORDS = {
    "python": "Python",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "java": "Java",
    "kotlin": "Kotlin",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "ruby": "Ruby",
    "php": "PHP",
    "swift": "Swift",
    "c#": "C#",
    "csharp": "C#",
    "scala": "Scala",
    "elixir": "Elixir",
    "react": "TypeScript",
    "vue": "TypeScript",
    "angular": "TypeScript",
    "django": "Python",
    "flask": "Python",
    "fastapi": "Python",
    "spring": "Java",
    "rails": "Ruby",
    "laravel": "PHP",
    "next.js": "TypeScript",
    "nextjs": "TypeScript",
}


class Analyzer:
    """Analysiert Repository und Spec für die Routing-Entscheidung."""

    def __init__(self, repo_path: str, spec_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.spec_path = Path(spec_path).resolve()
        self.logger = get_logger()

    def analyze(self) -> AnalysisResult:
        """Führt die komplette Analyse durch."""
        self.logger.analyze(self.repo_path.name)

        repo_analysis = self._analyze_repo()
        spec_analysis = self._analyze_spec()
        runtime_analysis = self._analyze_runtime(repo_analysis)

        # Log Statistiken
        age_info = f"{repo_analysis.last_commit_days_ago} Tage seit letztem Commit"
        if repo_analysis.last_commit_days_ago > 365:
            years = repo_analysis.last_commit_days_ago // 365
            age_info = f"{years} Jahr{'e' if years > 1 else ''} alt"

        self.logger.stats(
            f"{repo_analysis.primary_language}/{repo_analysis.framework_detected or 'kein Framework'}",
            repo_analysis.commit_count,
            age_info
        )

        # Log Runtime-Info
        if runtime_analysis:
            self.logger.debug(
                f"Runtime: {runtime_analysis.start_command} (Port {runtime_analysis.port}), "
                f"{len(runtime_analysis.services)} Services, Doppler: {runtime_analysis.uses_doppler}"
            )

        # Route bestimmen
        route, reason, confidence, legacy_signals, greenfield_signals = self._determine_route(
            repo_analysis, spec_analysis
        )

        self.logger.route(route, confidence)
        self.logger.reason(reason)

        result = AnalysisResult(
            repo=repo_analysis,
            spec=spec_analysis,
            runtime=runtime_analysis,
            route=route,
            route_reason=reason,
            confidence=confidence,
            legacy_signals=legacy_signals,
            greenfield_signals=greenfield_signals,
        )

        # Speichere Analyse
        self._save_analysis(result)

        return result

    def _analyze_repo(self) -> RepoAnalysis:
        """Analysiert die Repository-Struktur."""
        # Dateien sammeln
        all_files = self._get_all_files()

        # Sprachen erkennen
        primary_lang, secondary_langs = self._detect_languages(all_files)

        # Framework erkennen
        framework = self._detect_framework()

        # Build-Tool erkennen
        build_tool = self._detect_build_tool()

        # Git-Statistiken
        commit_count, last_commit_days, last_commit_date = self._get_git_stats()

        # Codezeilen zählen (approximativ)
        total_lines = self._count_lines(all_files)

        # Verzeichnisse
        directories = self._get_top_directories()

        # Config-Dateien
        config_files = self._get_config_files()

        # Tests vorhanden?
        has_tests = self._has_tests()

        # CI vorhanden?
        has_ci = self._has_ci()

        return RepoAnalysis(
            repo_path=str(self.repo_path),
            repo_name=self.repo_path.name,
            primary_language=primary_lang,
            secondary_languages=secondary_langs,
            framework_detected=framework,
            build_tool=build_tool,
            commit_count=commit_count,
            last_commit_days_ago=last_commit_days,
            last_commit_date=last_commit_date,
            file_count=len(all_files),
            total_lines=total_lines,
            has_tests=has_tests,
            has_ci=has_ci,
            directories=directories,
            config_files=config_files,
        )

    def _get_all_files(self) -> List[Path]:
        """Sammelt alle Dateien im Repo (ohne .git, node_modules, etc.)."""
        exclude_dirs = {
            ".git", "node_modules", "vendor", "venv", ".venv",
            "__pycache__", ".idea", ".vscode", "dist", "build",
            "target", ".gradle", ".dirigent",
        }

        files = []
        for root, dirs, filenames in os.walk(self.repo_path):
            # Exclude-Verzeichnisse entfernen
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for filename in filenames:
                if not filename.startswith("."):
                    files.append(Path(root) / filename)

        return files

    def _detect_languages(self, files: List[Path]) -> Tuple[str, List[str]]:
        """Erkennt primäre und sekundäre Sprachen."""
        lang_counts: Counter = Counter()

        for file in files:
            ext = file.suffix.lower()
            if ext in LANGUAGE_EXTENSIONS:
                lang_counts[LANGUAGE_EXTENSIONS[ext]] += 1

        if not lang_counts:
            return "Unknown", []

        sorted_langs = lang_counts.most_common()
        primary = sorted_langs[0][0]
        secondary = [lang for lang, _ in sorted_langs[1:4]]

        return primary, secondary

    def _detect_framework(self) -> Optional[str]:
        """Erkennt das verwendete Framework."""
        for config_file, frameworks in FRAMEWORK_INDICATORS.items():
            config_path = self.repo_path / config_file
            if config_path.exists():
                try:
                    content = config_path.read_text(encoding="utf-8").lower()
                    for keyword, framework in frameworks.items():
                        if keyword in content:
                            return framework
                except Exception:
                    pass

        # Spezielle Checks
        if (self.repo_path / "pom.xml").exists():
            try:
                content = (self.repo_path / "pom.xml").read_text(encoding="utf-8").lower()
                if "spring-boot" in content or "springframework" in content:
                    return "Spring Boot"
            except Exception:
                pass

        return None

    def _detect_build_tool(self) -> Optional[str]:
        """Erkennt das Build-Tool."""
        for filename, tool in BUILD_TOOLS.items():
            if (self.repo_path / filename).exists():
                return tool
        return None

    def _get_git_stats(self) -> Tuple[int, int, Optional[str]]:
        """Holt Git-Statistiken."""
        try:
            # Commit-Anzahl
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            commit_count = int(result.stdout.strip()) if result.returncode == 0 else 0

            # Letzter Commit
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ci"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                last_commit_str = result.stdout.strip()
                # Parse: "2024-01-15 10:30:00 +0100"
                last_commit_date = last_commit_str.split()[0]
                last_commit = datetime.fromisoformat(last_commit_date)
                days_ago = (datetime.now() - last_commit).days
                return commit_count, days_ago, last_commit_date

            return commit_count, 0, None

        except Exception:
            return 0, 0, None

    def _count_lines(self, files: List[Path]) -> int:
        """Zählt Codezeilen (approximativ)."""
        total = 0
        code_extensions = set(LANGUAGE_EXTENSIONS.keys())

        for file in files[:500]:  # Limit für Performance
            if file.suffix.lower() in code_extensions:
                try:
                    total += len(file.read_text(encoding="utf-8", errors="ignore").splitlines())
                except Exception:
                    pass

        return total

    def _get_top_directories(self) -> List[str]:
        """Gibt die wichtigsten Verzeichnisse zurück."""
        important_dirs = ["src", "app", "lib", "api", "components", "pages",
                         "ios", "android", "server", "client", "core", "modules"]

        found = []
        for d in self.repo_path.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                if d.name in important_dirs:
                    found.append(d.name)

        return found

    def _get_config_files(self) -> List[str]:
        """Gibt gefundene Konfigurationsdateien zurück."""
        config_patterns = [
            "package.json", "pom.xml", "build.gradle", "Cargo.toml",
            "go.mod", "requirements.txt", "Gemfile", "composer.json",
            "tsconfig.json", "webpack.config.js", "vite.config.js",
            ".env", ".env.example", "docker-compose.yml", "Dockerfile",
        ]

        found = []
        for pattern in config_patterns:
            if (self.repo_path / pattern).exists():
                found.append(pattern)

        return found

    def _has_tests(self) -> bool:
        """Prüft ob Tests vorhanden sind."""
        test_indicators = [
            "test", "tests", "spec", "specs", "__tests__",
            "pytest.ini", "jest.config.js", "vitest.config.js",
        ]

        for d in self.repo_path.iterdir():
            if d.name.lower() in test_indicators:
                return True

        return False

    def _has_ci(self) -> bool:
        """Prüft ob CI-Konfiguration vorhanden ist."""
        ci_paths = [
            ".github/workflows",
            ".gitlab-ci.yml",
            ".circleci",
            "Jenkinsfile",
            ".travis.yml",
            "azure-pipelines.yml",
        ]

        for path in ci_paths:
            if (self.repo_path / path).exists():
                return True

        return False

    def _analyze_runtime(self, repo: RepoAnalysis) -> Optional[RuntimeAnalysis]:
        """Analysiert wie das Projekt lokal gestartet werden kann."""
        try:
            start_command = "npm run dev"
            port = 3000
            package_manager = "npm"
            framework = repo.framework_detected
            services: List[RuntimeRequirement] = []
            setup_steps: List[str] = []
            uses_doppler = False
            uses_docker_compose = False
            env_file = None
            health_check_path = None

            # 1. Package Manager und Start-Command aus package.json
            package_json_path = self.repo_path / "package.json"
            if package_json_path.exists():
                try:
                    package_data = json.loads(package_json_path.read_text(encoding="utf-8"))
                    scripts = package_data.get("scripts", {})
                    deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}

                    # Package Manager erkennen
                    pkg_manager = package_data.get("packageManager", "")
                    if pkg_manager.startswith("yarn"):
                        package_manager = "yarn"
                    elif pkg_manager.startswith("pnpm"):
                        package_manager = "pnpm"
                    elif (self.repo_path / "yarn.lock").exists():
                        package_manager = "yarn"
                    elif (self.repo_path / "pnpm-lock.yaml").exists():
                        package_manager = "pnpm"

                    # Start-Command erkennen
                    if "dev" in scripts:
                        start_command = f"{package_manager} run dev" if package_manager != "npm" else "npm run dev"
                        # Port aus dev script extrahieren
                        port_match = re.search(r"--port[=\s]+(\d+)|-p[=\s]+(\d+)", scripts["dev"])
                        if port_match:
                            port = int(port_match.group(1) or port_match.group(2))
                    elif "start:dev" in scripts:
                        start_command = f"{package_manager} run start:dev" if package_manager != "npm" else "npm run start:dev"
                    elif "serve" in scripts:
                        start_command = f"{package_manager} run serve" if package_manager != "npm" else "npm run serve"

                    # Framework-spezifische Ports
                    if "next" in deps:
                        framework = "Next.js"
                        port = 3000
                    elif "nuxt" in deps:
                        framework = "Nuxt"
                        port = 3000
                    elif "@angular/core" in deps:
                        framework = "Angular"
                        port = 4200
                    elif "vue" in deps and "nuxt" not in deps:
                        framework = "Vue"
                        port = 5173
                    elif "svelte" in deps or "@sveltejs/kit" in deps:
                        framework = "Svelte/SvelteKit"
                        port = 5173
                    elif "astro" in deps:
                        framework = "Astro"
                        port = 4321

                    # Setup-Steps
                    setup_steps.append(f"{package_manager} install")
                    if "db:migrate" in scripts:
                        setup_steps.append(f"{package_manager} run db:migrate")
                    elif "migrate" in scripts:
                        setup_steps.append(f"{package_manager} run migrate")
                    if "db:seed" in scripts:
                        setup_steps.append(f"{package_manager} run db:seed")

                    # Services aus Dependencies erkennen
                    # WICHTIG: Bei Doppler werden externe Services (Supabase, etc.) genutzt
                    # -> Keine lokalen DB-Container starten!
                    if not uses_doppler:
                        if "pg" in deps or "postgres" in deps or "@prisma/client" in deps:
                            services.append(RuntimeRequirement(
                                name="PostgreSQL",
                                type="database",
                                docker_image="postgres:15",
                                port=5432,
                                env_vars=["POSTGRES_PASSWORD=dev", "POSTGRES_DB=app_dev"]
                            ))
                        if "mysql" in deps or "mysql2" in deps:
                            services.append(RuntimeRequirement(
                                name="MySQL",
                                type="database",
                                docker_image="mysql:8",
                                port=3306,
                                env_vars=["MYSQL_ROOT_PASSWORD=dev", "MYSQL_DATABASE=app_dev"]
                            ))
                        if "mongodb" in deps or "mongoose" in deps:
                            services.append(RuntimeRequirement(
                                name="MongoDB",
                                type="database",
                                docker_image="mongo:7",
                                port=27017
                            ))
                        if "redis" in deps or "ioredis" in deps:
                            services.append(RuntimeRequirement(
                                name="Redis",
                                type="cache",
                                docker_image="redis:7-alpine",
                                port=6379
                            ))

                except Exception as e:
                    self.logger.debug(f"Error parsing package.json: {e}")

            # 2. Python-Projekte
            elif (self.repo_path / "pyproject.toml").exists() or (self.repo_path / "requirements.txt").exists():
                package_manager = "pip"
                setup_steps.append("pip install -r requirements.txt" if (self.repo_path / "requirements.txt").exists() else "pip install -e .")

                # Framework erkennen
                for req_file in ["requirements.txt", "pyproject.toml"]:
                    req_path = self.repo_path / req_file
                    if req_path.exists():
                        content = req_path.read_text(encoding="utf-8").lower()
                        if "fastapi" in content:
                            framework = "FastAPI"
                            start_command = "uvicorn main:app --reload"
                            port = 8000
                        elif "django" in content:
                            framework = "Django"
                            start_command = "python manage.py runserver"
                            port = 8000
                            setup_steps.append("python manage.py migrate")
                        elif "flask" in content:
                            framework = "Flask"
                            start_command = "flask run"
                            port = 5000
                        break

            # 3. Go-Projekte
            elif (self.repo_path / "go.mod").exists():
                package_manager = "go"
                start_command = "go run ."
                port = 8080
                framework = "Go"

            # 4. docker-compose.yml analysieren
            compose_path = self.repo_path / "docker-compose.yml"
            if not compose_path.exists():
                compose_path = self.repo_path / "docker-compose.yaml"

            if compose_path.exists():
                uses_docker_compose = True
                try:
                    compose_content = compose_path.read_text(encoding="utf-8").lower()

                    # Services aus docker-compose extrahieren (vereinfacht)
                    if "postgres" in compose_content and not any(s.name == "PostgreSQL" for s in services):
                        services.append(RuntimeRequirement(
                            name="PostgreSQL",
                            type="database",
                            docker_image="postgres:15",
                            port=5432,
                            env_vars=["POSTGRES_PASSWORD=dev"]
                        ))
                    if "redis" in compose_content and not any(s.name == "Redis" for s in services):
                        services.append(RuntimeRequirement(
                            name="Redis",
                            type="cache",
                            docker_image="redis:7-alpine",
                            port=6379
                        ))
                    if "mongo" in compose_content and not any(s.name == "MongoDB" for s in services):
                        services.append(RuntimeRequirement(
                            name="MongoDB",
                            type="database",
                            docker_image="mongo:7",
                            port=27017
                        ))
                    if "elasticsearch" in compose_content:
                        services.append(RuntimeRequirement(
                            name="Elasticsearch",
                            type="search",
                            docker_image="elasticsearch:8.11.0",
                            port=9200
                        ))
                    if "rabbitmq" in compose_content:
                        services.append(RuntimeRequirement(
                            name="RabbitMQ",
                            type="queue",
                            docker_image="rabbitmq:3-management",
                            port=5672
                        ))
                except Exception as e:
                    self.logger.debug(f"Error parsing docker-compose: {e}")

            # 5. Doppler-Nutzung erkennen
            doppler_indicators = [".doppler.yaml", "doppler.yaml"]
            for indicator in doppler_indicators:
                if (self.repo_path / indicator).exists():
                    uses_doppler = True
                    break

            # Auch in README oder env.example nach Doppler suchen
            for check_file in ["README.md", ".env.example", "CONTRIBUTING.md"]:
                check_path = self.repo_path / check_file
                if check_path.exists():
                    try:
                        content = check_path.read_text(encoding="utf-8").lower()
                        if "doppler" in content:
                            uses_doppler = True
                            break
                    except Exception:
                        pass

            # 6. Env-File finden
            for env_name in [".env.example", ".env.local.example", ".env.sample", ".env.development"]:
                if (self.repo_path / env_name).exists():
                    env_file = env_name
                    break

            # 7. Health-Check-Path erkennen (häufige Patterns)
            health_patterns = ["/api/health", "/health", "/healthz", "/_health"]
            for src_dir in ["src", "app", "api", "."]:
                for pattern in ["health", "healthcheck"]:
                    for ext in [".ts", ".js", ".py", ".go"]:
                        health_file = self.repo_path / src_dir / f"{pattern}{ext}"
                        if health_file.exists():
                            health_check_path = "/api/health"
                            break

            return RuntimeAnalysis(
                start_command=start_command,
                port=port,
                package_manager=package_manager,
                framework=framework,
                services=services,
                setup_steps=setup_steps,
                uses_doppler=uses_doppler,
                uses_docker_compose=uses_docker_compose,
                env_file=env_file,
                health_check_path=health_check_path,
            )

        except Exception as e:
            self.logger.debug(f"Runtime analysis failed: {e}")
            return None

    def _analyze_spec(self) -> SpecAnalysis:
        """Analysiert die Spec-Datei."""
        content = self.spec_path.read_text(encoding="utf-8")
        content_lower = content.lower()

        # Titel extrahieren (erste H1 Zeile)
        title = "Unbekannt"
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Legacy-Keywords suchen
        legacy_found = []
        for keyword in LEGACY_KEYWORDS:
            if keyword.lower() in content_lower:
                legacy_found.append(keyword)

        # Greenfield-Keywords suchen
        greenfield_found = []
        for keyword in GREENFIELD_KEYWORDS:
            if keyword.lower() in content_lower:
                greenfield_found.append(keyword)

        # Testability-Keywords suchen
        testability_found = []
        for keyword in TESTABILITY_KEYWORDS:
            if keyword.lower() in content_lower:
                testability_found.append(keyword)

        # Tracking-Keywords suchen
        tracking_found = []
        for keyword in TRACKING_KEYWORDS:
            if keyword.lower() in content_lower:
                tracking_found.append(keyword)

        # Target-Language erkennen
        target_language = None
        for keyword, lang in LANGUAGE_KEYWORDS.items():
            if keyword in content_lower:
                target_language = lang
                break

        # Komplexität aus Spec lesen
        complexity = None
        complexity_match = re.search(r"complexity:\s*(\w+)", content_lower)
        if complexity_match:
            complexity = complexity_match.group(1)

        # Scope schätzen
        word_count = len(content.split())
        if word_count < 200:
            scope = "small"
        elif word_count < 500:
            scope = "medium"
        else:
            scope = "large"

        return SpecAnalysis(
            spec_path=str(self.spec_path),
            title=title,
            has_legacy_keywords=len(legacy_found) > 0,
            has_greenfield_keywords=len(greenfield_found) > 0,
            has_testability_keywords=len(testability_found) > 0,
            has_tracking_keywords=len(tracking_found) > 0,
            legacy_keywords_found=legacy_found,
            greenfield_keywords_found=greenfield_found,
            testability_keywords_found=testability_found,
            tracking_keywords_found=tracking_found,
            target_language=target_language,
            complexity=complexity,
            estimated_scope=scope,
        )

    def _determine_route(self, repo: RepoAnalysis, spec: SpecAnalysis) -> Tuple[str, str, str, int, int]:
        """Bestimmt die optimale Route basierend auf der Analyse."""

        # ── Specialized routes (take priority over general routes) ──

        # Testability route: triggered when spec focuses on improving test infrastructure
        if spec.has_testability_keywords and len(spec.testability_keywords_found) >= 2:
            reason = f"Testability-Keywords: {', '.join(spec.testability_keywords_found[:3])}"
            return "testability", reason, "high", 0, 0

        # Tracking route: triggered when spec focuses on adding analytics/PostHog
        if spec.has_tracking_keywords and len(spec.tracking_keywords_found) >= 2:
            reason = f"Tracking-Keywords: {', '.join(spec.tracking_keywords_found[:3])}"
            return "tracking", reason, "high", 0, 0

        # ── General routes ──

        legacy_signals = 0
        greenfield_signals = 0
        reasons = []

        # Legacy Signale
        if repo.last_commit_days_ago > 365:
            legacy_signals += 2
            reasons.append(f"Repo seit {repo.last_commit_days_ago // 365} Jahr(en) inaktiv")

        if repo.primary_language in ["Java", "Ruby", "PHP", "Swift", "Objective-C"]:
            if spec.target_language and spec.target_language != repo.primary_language:
                legacy_signals += 3
                reasons.append(f"Sprach-Migration von {repo.primary_language} zu {spec.target_language}")

        if spec.has_legacy_keywords:
            # Scale by keyword density: 1-2 keywords = partial refactor (+1), 3+ = real migration (+2)
            if len(spec.legacy_keywords_found) >= 3:
                legacy_signals += 2
            else:
                legacy_signals += 1
            reasons.append(f"Legacy-Keywords in Spec: {', '.join(spec.legacy_keywords_found[:3])}")

        if repo.commit_count > 2000:
            legacy_signals += 1
            reasons.append(f"Großes Projekt mit {repo.commit_count} Commits")

        # Greenfield Signale
        if spec.has_greenfield_keywords:
            greenfield_signals += 2
            reasons.append(f"Greenfield-Keywords in Spec: {', '.join(spec.greenfield_keywords_found[:3])}")

        if repo.primary_language in ["TypeScript", "JavaScript", "Python", "Go", "Rust"]:
            greenfield_signals += 1

        if repo.last_commit_days_ago < 90:
            greenfield_signals += 1
            reasons.append("Aktiv entwickeltes Projekt")

        if repo.file_count < 50:
            greenfield_signals += 1
            reasons.append("Kleines Projekt")

        # Route bestimmen
        if legacy_signals >= 4:
            route = "legacy"
            confidence = "high"
        elif legacy_signals >= 3:
            route = "legacy"
            confidence = "medium"
        elif greenfield_signals >= 3:
            route = "greenfield"
            confidence = "high"
        elif greenfield_signals >= 2:
            route = "greenfield"
            confidence = "medium"
        else:
            route = "hybrid"
            confidence = "medium"
            reasons.append("Neues Feature auf bestehendem Projekt")

        # Reason zusammensetzen
        reason = "; ".join(reasons[:3]) if reasons else "Standard-Route"

        return route, reason, confidence, legacy_signals, greenfield_signals

    def _save_analysis(self, result: AnalysisResult):
        """Speichert das Analyse-Ergebnis."""
        dirigent_dir = self.repo_path / ".dirigent"
        dirigent_dir.mkdir(parents=True, exist_ok=True)

        analysis_file = dirigent_dir / "ANALYSIS.json"

        # Dataclass zu Dict konvertieren
        data = {
            "repo_path": result.repo.repo_path,
            "repo_name": result.repo.repo_name,
            "primary_language": result.repo.primary_language,
            "secondary_languages": result.repo.secondary_languages,
            "framework_detected": result.repo.framework_detected,
            "build_tool": result.repo.build_tool,
            "commit_count": result.repo.commit_count,
            "last_commit_days_ago": result.repo.last_commit_days_ago,
            "file_count": result.repo.file_count,
            "total_lines": result.repo.total_lines,
            "spec_title": result.spec.title,
            "spec_keywords": result.spec.legacy_keywords_found + result.spec.greenfield_keywords_found,
            "route": result.route,
            "route_reason": result.route_reason,
            "confidence": result.confidence,
            "legacy_signals": result.legacy_signals,
            "greenfield_signals": result.greenfield_signals,
            "analyzed_at": datetime.now().isoformat(),
        }

        # Runtime-Analyse hinzufügen
        if result.runtime:
            data["runtime"] = {
                "start_command": result.runtime.start_command,
                "port": result.runtime.port,
                "package_manager": result.runtime.package_manager,
                "framework": result.runtime.framework,
                "services": [
                    {
                        "name": s.name,
                        "type": s.type,
                        "docker_image": s.docker_image,
                        "port": s.port,
                        "env_vars": s.env_vars,
                    }
                    for s in result.runtime.services
                ],
                "setup_steps": result.runtime.setup_steps,
                "uses_doppler": result.runtime.uses_doppler,
                "uses_docker_compose": result.runtime.uses_docker_compose,
                "env_file": result.runtime.env_file,
                "health_check_path": result.runtime.health_check_path,
            }

        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.logger.debug(f"Analyse gespeichert in {analysis_file}")


def load_analysis(repo_path: str) -> Optional[Dict]:
    """Lädt eine existierende Analyse."""
    analysis_file = Path(repo_path) / ".dirigent" / "ANALYSIS.json"
    if analysis_file.exists():
        with open(analysis_file, encoding="utf-8") as f:
            return json.load(f)
    return None
