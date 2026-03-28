---
name: extract-business-rules
description: Extract all business rules from a legacy codebase
arguments: none - language context provided via prompt
---

# Extract Business Rules

Analysiere die Codebase systematisch und extrahiere alle Business Rules.

## Output

Erstelle `.dirigent/BUSINESS_RULES.md` mit folgendem Format:

```markdown
# Business Rules – {PROJECT_NAME}

## Kern-Entitaeten
(Alle Domain-Objekte und ihre Felder)

## Geschaeftsregeln
(Validierungen, Berechnungen, Constraints)

## Domain Events
(Was passiert wann? User erstellt X → Y wird ausgeloest)

## API Endpoints
(Alle Routes mit Parametern und Response-Format)

## Datenbank
(Schema, Relationen, Constraints)

## Externe Abhaengigkeiten
(APIs, Services, Integrations)

## Edge Cases
(Bekannte Sonderfaelle und wie sie behandelt werden)
```

## Rules

1. Sei praezise. Keine Annahmen. Nur was du im Code siehst.
2. Dokumentiere numerische Werte exakt (Limits, Timeouts, etc.)
3. Bei Unsicherheit, markiere es mit [UNKLAR]
4. Analysiere alle relevanten Dateien systematisch
5. Vergiss keine Validierungsregeln, Constraints oder Business-Logik
