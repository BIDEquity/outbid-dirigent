# Outbid Dirigent

Ein headless Python Control Plane das eine SPEC.md liest, das Ziel-Repo analysiert,
den richtigen Ausführungspfad wählt und dann autonom durcharbeitet.

**Kein Mensch in der Loop. Kein interaktives Terminal. Kein Warten auf Input.**

## Installation

### Via uvx (empfohlen)

Keine Installation nötig. Direkt ausführen:

```bash
uvx --from git+https://github.com/BIDEquity/outbid-dirigent.git dirigent \
  --spec .planning/SPEC.md --repo /path/to/repo
```

### Via uv

```bash
uv tool install git+https://github.com/BIDEquity/outbid-dirigent.git
```

### Via pip

```bash
pip install git+https://github.com/BIDEquity/outbid-dirigent.git
```

### Entwicklung

```bash
git clone https://github.com/BIDEquity/outbid-dirigent.git
cd outbid-dirigent
uv sync
```

### Coder Workspaces (Privates Repo)

```hcl
resource "coder_script" "dirigent" {
  agent_id     = coder_agent.main.id
  script       = <<-EOF
    uv tool install git+https://github.com/BIDEquity/outbid-dirigent.git
  EOF
  display_name = "Install Dirigent"
  run_on_start = true
}
```

Das Repo enthält auch `.devcontainer/devcontainer.json` für VS Code / GitHub Codespaces.

### Voraussetzungen

- Python 3.10+
- [Claude Code CLI](https://claude.ai/claude-code) (`claude` Befehl)
- `ANTHROPIC_API_KEY` Environment Variable
- Optional: GitHub CLI (`gh`) für automatische PR-Erstellung

## Usage

### Kompletter Durchlauf

```bash
dirigent --spec .planning/SPEC.md --repo /path/to/repo
```

### Nur Analyse

```bash
dirigent --spec SPEC.md --repo /path/to/repo --phase analyze
```

### Fortsetzen nach Unterbrechung

```bash
dirigent --spec SPEC.md --repo /path/to/repo --resume
```

### Dry-Run (keine Änderungen)

```bash
dirigent --spec SPEC.md --repo /path/to/repo --dry-run
```

## Architektur

```
src/outbid_dirigent/
    ├─ dirigent.py              # Einstiegspunkt + Orchestrierung
    ├─ analyzer.py              # Repo + Spec analysieren, Pfad entscheiden
    ├─ router.py                # Routing-Logik (Greenfield / Legacy / Hybrid)
    ├─ executor.py              # Claude Code Aufrufe ausführen
    ├─ oracle.py                # Architektur-Entscheidungen (Claude API direkt)
    ├─ logger.py                # Strukturiertes Logging in .dirigent/logs/
    └─ proteus_integration.py   # Proteus Domain-Extraktion
```

### Dateien im Ziel-Repo

Der Dirigent erstellt folgende Dateien im Ziel-Repository:

```
{repo}/
└── .dirigent/
    ├── ANALYSIS.json     # Ergebnis der Repo-Analyse
    ├── ROUTE.json        # Gewählter Pfad + Begründung
    ├── PLAN.json         # Ausführungsplan (Phasen + Tasks)
    ├── STATE.json        # Aktueller Fortschritt
    ├── DECISIONS.json    # Oracle-Entscheidungen (Cache)
    ├── BUSINESS_RULES.md # Extrahierte Business Rules (nur Legacy)
    ├── CONTEXT.md        # Relevante Dateien (nur Hybrid)
    ├── summaries/        # Task-Summaries
    │   └── 01-01-SUMMARY.md
    └── logs/
        └── run-{timestamp}.log
```

## Routing-Logik

Der Dirigent wählt automatisch einen von drei Ausführungspfaden:

### Pfad A: GREENFIELD

Für neue Features auf bestehenden oder neuen Projekten.

**Wann:**
- Spec enthält "add", "build", "create", "implement", "new feature"
- Aktiv entwickeltes Projekt (letzer Commit < 90 Tage)
- Moderner Stack (TypeScript, JavaScript, Python, Go, Rust)

**Ablauf:**
1. Plan erstellen
2. Tasks ausführen (ein frischer Claude Code Prozess pro Task)
3. Commit + Push + PR

### Pfad B: LEGACY

Für Refactors, Migrationen, Rewrites.

**Wann:**
- Spec enthält "refactor", "migrate", "rewrite", "port", "legacy"
- Inaktives Projekt (letzter Commit > 1 Jahr)
- Sprach-Migration erkannt (z.B. Java → PHP)
- Großes Projekt (> 500 Commits)

**Ablauf:**
1. Business Rule Extraktion (komplette Codebase analysieren)
2. Plan erstellen mit Business Rules als Guardrails
3. Tasks ausführen mit Rule-Check
4. Commit + Push + PR

### Pfad C: HYBRID

Für neue Features auf bestehenden Projekten die verstanden werden müssen.

**Wann:**
- Mischung aus Greenfield- und Legacy-Signalen
- Neues Feature auf existierendem Projekt

**Ablauf:**
1. Quick Scan (nur relevante Dateien)
2. Plan erstellen mit Repo-Kontext
3. Tasks ausführen
4. Commit + Push + PR

## Deviation Rules

Während der Ausführung folgt Claude Code diesen Regeln:

| Rule | Trigger | Aktion |
|------|---------|--------|
| 1 | Bug gefunden | Automatisch fixen, als Deviation loggen |
| 2 | Kritisches fehlt | Hinzufügen, als Deviation loggen |
| 3 | Blocker entdeckt | Beheben, als Deviation loggen |
| 4 | Architektur-Frage | STOPP – Oracle fragen |

## Oracle

Das Oracle beantwortet architekturelle Fragen autonom via Claude API:

- Liest: SPEC.md, PLAN.json, DECISIONS.json, BUSINESS_RULES.md
- Cached alle Entscheidungen in DECISIONS.json
- Verwendet Claude Sonnet für schnelle Antworten

## Prinzipien

- **Headless by design**: Keine stdin reads, keine input() Aufrufe, kein Warten
- **Fresh context per task**: Jeder Task = neuer Claude Code Prozess
- **Oracle statt Mensch**: Bei architekturellen Fragen → Oracle, niemals Rückfrage an User
- **Atomic commits**: Ein Commit pro Task, niemals alles auf einmal
- **Fail fast**: Wenn ein Task 3x fehlschlägt → stoppen, Status in STATE.json loggen
- **Resumable**: Wenn STATE.json existiert → dort weitermachen wo aufgehört wurde

## Beispiel-Ausgabe

```
[2026-03-06 11:30:00] 🎼 Outbid Dirigent gestartet
[2026-03-06 11:30:01] 🔍 Analysiere Repo: medicheck-portal
[2026-03-06 11:30:02] 📊 Erkannt: Java/Spring Boot, 1205 Commits, 4 Jahre alt
[2026-03-06 11:30:02] 🗺️  Route: LEGACY (confidence: high)
[2026-03-06 11:30:02] 📋 Grund: Java Migration-Spec, inaktives Repo
[2026-03-06 11:30:03] 📖 Starte Business Rule Extraktion...
[2026-03-06 11:45:00] ✅ Business Rules extrahiert (47 Regeln gefunden)
[2026-03-06 11:45:01] 📝 Erstelle Ausführungsplan...
[2026-03-06 11:46:00] ✅ Plan: 3 Phasen, 9 Tasks
[2026-03-06 11:46:01] ⚡ Starte Ausführung: Phase 1 – Setup
[2026-03-06 11:46:01] 🔨 Task 01-01: PHP Projektstruktur anlegen
[2026-03-06 11:52:00] ✅ Task 01-01 abgeschlossen (Commit: abc1234)
...
[2026-03-08 14:30:00] 🚢 Shipping: Branch feature/dirigent-20260306
[2026-03-08 14:30:15] 🎉 PR erstellt: https://github.com/org/repo/pull/42
```

## Fehlerbehandlung

- **Task fehlgeschlagen**: Bis zu 3 Retries, dann Stopp
- **Oracle Error**: Fehler loggen, sicherere Option wählen
- **Unterbrechung**: Mit `--resume` fortsetzen
- **Claude CLI fehlt**: Fehlermeldung mit Installationshinweis

## Entwicklung

```bash
# Tests ausführen
uv run pytest tests/

# Linting
uv run ruff check
```

## Lizenz

MIT
