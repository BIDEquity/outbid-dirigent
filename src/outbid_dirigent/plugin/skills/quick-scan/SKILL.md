---
name: quick-scan
description: Quick scan of relevant files for a feature (Hybrid route)
arguments: none - spec content provided via prompt
---

# Quick Scan

Analysiere die Codebase um das Feature zu implementieren. Fokussiere dich NUR auf die relevanten Teile.

## Output

Erstelle `.dirigent/CONTEXT.md` mit:

```markdown
# Relevante Dateien fuer Feature

## Hauptdateien
(Die Dateien die direkt modifiziert werden muessen)

## Abhaengigkeiten
(Dateien die verstanden werden muessen aber nicht geaendert werden)

## Patterns
(Coding-Patterns die im Projekt verwendet werden)

## Integration Points
(Wo das neue Feature sich einfuegen muss)
```

## Constraints

- Fokussiere dich NUR auf die fuer dieses Feature relevanten Teile
- Keine vollstaendige Codebase-Analyse noetig
- Identifiziere die minimale Menge an Dateien die verstanden werden muessen
- Dokumentiere existierende Patterns die das neue Feature befolgen sollte
