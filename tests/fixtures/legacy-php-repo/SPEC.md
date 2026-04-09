# Migration: PHP Kontaktformular → Python/FastAPI

## Ziel

Die bestehende PHP-Kontaktformular-Anwendung soll nach Python/FastAPI migriert werden.
Die Datenbank wird von MySQL auf PostgreSQL umgestellt.
Alle bestehenden Business Rules muessen exakt erhalten bleiben.

## Anforderungen

### API-Endpunkte

1. `POST /api/contacts` — Neuen Kontakt erstellen (ersetzt das PHP-Formular)
2. `GET /api/contacts` — Alle Kontakte auflisten (Admin, paginiert)
3. `PATCH /api/contacts/{id}/status` — Kontakt-Status aktualisieren
4. `POST /api/auth/login` — Admin-Login (JWT statt Session)

### Datenmodell

- contacts: id, name, email, subject, message, priority (normal/hoch/urgent), status (new/read/replied/closed), created_at
- audit_log: id, action, contact_id, ip_address, created_at
- rate_limits: id, ip_address, created_at

### Business Rules (MUESSEN erhalten bleiben)

- Rate Limiting: Max 3 Submissions pro Stunde pro IP
- Wegwerf-E-Mail-Domains ablehnen (tempmail.com, mailinator.com, etc.)
- Admin-Benachrichtigung bei Priority "urgent"
- Bestaetigungs-Mail an User mit Referenznummer
- Status-Uebergaenge nur vorwaerts: new → read → replied → closed
- Kontakte koennen nicht geloescht werden (Audit-Anforderung)
- Alle Aktionen werden im Audit-Log protokolliert

### Technische Anforderungen

- Python 3.12+, FastAPI, SQLAlchemy, Alembic
- PostgreSQL statt MySQL
- JWT-basierte Auth statt Session
- Pydantic-Modelle fuer Request/Response
- pytest fuer Tests
- Docker Compose fuer lokale Entwicklung

### Nicht im Scope

- Frontend (wird separat migriert)
- SMTP-Integration (Mailer wird als Interface definiert, aber nicht implementiert)
- Deployment
