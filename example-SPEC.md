SteuerPortal PRD v2
Product Requirements Document
SteuerPortal — Private Tax Advisor Collaboration Portal
Version: 1.0
Date: April 2026
Author: Helge Hofmeister
Status: Draft — Ready for Implementation

1. Executive Summary
SteuerPortal is a private, invite-only web application that replaces ad-hoc email chains between Helge Hofmeister (and family/collaborators) and the tax advisory practice (Fischer & Reimann / Kanzlei Pfalz, primary contact Jana Fuhrmann). It provides a structured, role-based portal where the tax advisor can post document requests organized by tax type and entity, and the client can fulfill those requests by linking files directly from Google Drive or uploading them manually.

The application is scoped for a very small user group (< 20 users), deployed as a Next.js app on a Vercel subdomain (e.g., steuer.hofmeister.com), and built for quick iteration (“vibe coding”).

2. Background & Motivation
2.1 Current Pain Points
Emails from Jana Fuhrmann (kanzlei-pfalz.de) illustrate the problem clearly:

Document requests arrive as long unstructured email lists mixing different entities (personal, courtmaster ventures GmbH) and different tax types (EStE, KSt, GewSt) in a single thread
Back-and-forth to clarify which documents were delivered vs. still outstanding
Files are scattered across Gmail attachments and Google Drive — finding and sharing the right ones requires manual lookup
No audit trail of what was requested, when, and what was delivered
No single place to see the overall status of a tax year’s preparation
2.2 Real Document Request Examples (from Gmail analysis)
Corporate Tax (courtmaster ventures GmbH, 2023): - Vermögensberichte LIQID (for 2023 and 2024) - Steuerbescheinigungen LIQID - Darlehensverträge (4 separate loans from shareholder to company) - Fehlende Rechnungen (Grö​tzner & Posch, Apple, Telekom, The Economist, HP) - Spendenbescheinigungen (Ruderclub, Alsterbrüder) - Kontoauszüge Commerzbank (2022 and 2023) - Wertpapierbuchhaltungen (via Fintegra)

Income Tax (Familie Hofmeister, 2023): - Einnahmen/Ausgaben selbständige Tätigkeit (Isabel) - Bescheinigungen über Kapitalerträge (Quirin Bank, Trade Republic, CFB Fonds) - Beitragsbescheinigung Krankenkasse - Spendenbescheinigungen - Kinderbetreuungskosten (Kita-Rechnungen) - Handwerkerrechnungen (inkl. Ferienwohnung) - Fondsbeteiligungsnachweise (CFB Fonds) - Steueridentifikationsnummer (Familienmitglieder) - Hausgeldabrechnung Verwalter

3. Goals & Non-Goals
3.1 Goals
Structured, status-tracked document request workflow between advisor and client
Google Drive integration: client browses their own GDrive and attaches files to requests without leaving the portal
Role-based access: Advisor role vs. Client role
Organized by tax type + entity, with grouped request categories within each
Lightweight and fast to build — minimal ops overhead
GDPR-aware: data stays in EU, no unnecessary copies of sensitive documents
3.2 Non-Goals
Replacing accounting software (DATEV, etc.)
Full document management system / DMS
Automated tax calculation
Public-facing product (this is private-use only)
Native mobile app
Integration with ELSTER or tax authority portals
4. Users & Roles
4.1 Roles
Role	Who	Permissions
Advisor	Jana Fuhrmann + colleagues	Create/edit requests, mark as fulfilled, view all documents, post comments
Client	Helge, Isabel, + any delegated person (e.g. assistant)	View requests, upload/link documents, add comments
Admin	Helge	Manage users, invite new users, assign roles, manage entities
4.2 User Scale
Estimated total users: 5–15. Growth beyond 20 is not anticipated.

5. Information Architecture
5.1 Year-First UX Principle
The tax year is the primary operating context of the entire application. Everything a user does is always “for year X.” This is not a secondary filter or a dropdown buried in the sidebar — the active year is the most prominent UI element at all times.

Design rules: - The year is displayed in a large, persistent banner across the top of every screen (“Steuerjahr 2024”) - Switching year is a deliberate action (large button / modal confirmation), not an accidental dropdown change - When the app is opened, it always defaults to the most recently active working year (not necessarily the current calendar year — tax work for 2023 often happens in 2025) - Every request, attachment, comment, and notification includes the year explicitly in its display and in notification emails - Archive view: past years are accessible via a “Vergangene Jahre” section with a distinct visual treatment (greyed out header, read-only badge) to prevent accidental edits

Year state in URL: The active year is always encoded in the URL path (e.g., /entity/courtmaster/2024/kst) so bookmarks and shared links always resolve to the correct year context.

5.2 Top-Level Taxonomy: Entities
Each entity represents a legal person or household for which taxes are filed:

Entity	Type	Tax Types
Familie Hofmeister	Personal (household)	Einkommensteuer (EStE)
courtmaster ventures GmbH	GmbH	Körperschaftsteuer, Gewerbesteuer
(extensible)	Any	Any
The admin can create and archive entities. Each entity has a display name, legal form, and tax year scope.

5.3 Second Level: Tax Year
Within each entity, content is organized by tax year. The active year is always shown by default. Past years are accessible but visually distinct (see 5.1 above).

5.4 Third Level: Tax Type
Within each entity + year:

Tax Type	Used For
Einkommensteuer (EStE)	Familie Hofmeister
Körperschaftsteuer (KSt)	GmbHs
Gewerbesteuer (GewSt)	GmbHs
Umsatzsteuer (USt)	If applicable
Other / Sonstige	Catch-all
5.5 Fourth Level: Request Groups (Categories)
Within each tax type, document requests are grouped into 3–5 headline categories. These are the “sections” of a checklist. They are predefined as sensible defaults but can be customized by the advisor per entity/year.

Default Groups for Einkommensteuer (Familie Hofmeister)
#	Group Name	Example Documents
1	Kapitalerträge & Depots	Steuerbescheinigungen (Quirin Bank, Trade Republic, CFB Fonds), Erträgnisaufstellungen, Depotauszüge
2	Einnahmen & Ausgaben	Einnahmen-Überschuss-Rechnung selbständige Tätigkeit, Betriebsausgaben, Honorarverträge
3	Versicherungen & Sonderausgaben	Beitragsbescheinigung Krankenkasse, Rentenversicherung, Spendenbescheinigungen
4	Immobilien & Handwerker	Handwerkerrechnungen, Hausgeldabrechnung, Hausnebenkosten, Architektenrechnungen
5	Sonstiges & Familienbelege	Kinderbetreuungskosten, Steuer-IDs Familienmitglieder, Fondsbeteiligungen, Sonstiges
Default Groups for Körperschaftsteuer / GewSt (GmbH)
#	Group Name	Example Documents
1	Bankbelege & Kontoauszüge	Kontoauszüge Commerzbank, Zahlungsbelege
2	Kapitalanlagen & Depots	Vermögensberichte LIQID, Steuerbescheinigungen, Wertpapierbuchhaltung (Fintegra)
3	Rechnungen & Belege	Fehlende Ausgangsrechnungen, Eingangsrechnungen (Telekom, Apple, HP, Subscriptions)
4	Verträge & Vereinbarungen	Darlehensverträge (Gesellschafter), sonstige Verträge
5	Spenden & Sonstiges	Spendenbescheinigungen, sonstige Belege
5a. Entity Master Data
Every entity in the system has a structured master data record maintained by the admin. This is the canonical reference for tax-relevant identifiers and contact data that the advisor needs when preparing declarations.

5a.1 Master Data Object
Personal Household Entity (e.g., Familie Hofmeister)
Field	Example
Display Name	Familie Hofmeister
Steuernummer	22/345/12345 (Finanzamt Hamburg-Nord)
Steueridentifikationsnummer (Helge)	12 345 678 901
Steueridentifikationsnummer (Isabel)	98 765 432 100
Steueridentifikationsnummer (Kinder)	One record per child
Zuständiges Finanzamt	Hamburg-Nord
Steuerberater (assigned)	Jana Fuhrmann, Fischer & Reimann
Bankverbindungen (for direct debit)	IBAN, BIC, Bank name
Wohnanschrift	Hauptwohnsitz, ggf. Zweitwohnsitz
Beteiligungen / Kapitalanlagen	LIQID (Depot-Nr.), Quirin Bank, Trade Republic, CFB Fonds Nr. 124
Kinder	Name, Geburtsdatum, Steuer-ID
GmbH Entity (e.g., courtmaster ventures GmbH)
Field	Example
Display Name	courtmaster ventures GmbH
Rechtsform	GmbH
Handelsregisternummer	HRB XXXXX, Amtsgericht Hamburg
Steuernummer (KSt)	22/XXX/XXXXX
Steuernummer (GewSt)	(may differ)
Umsatzsteuer-ID	DE123456789
Zuständiges Finanzamt (KSt/GewSt)	Hamburg-Mitte o.ä.
Zuständiges Finanzamt (USt)	(if different)
Wirtschaftsjahr	01.01.–31.12. (calendar year)
Geschäftsführer	Helge Hofmeister
Gesellschafter	Name + Anteil %
Steuerberater (assigned)	Jana Fuhrmann, Fischer & Reimann
Geschäftsanschrift	Registered address
Bankverbindung	IBAN, BIC, Bank name, Account holder
DATEV-Mandantennummer	(if known)
Kapitalanlagen der Gesellschaft	LIQID Depot-Nr., Commerzbank-Konto
5a.2 Master Data Access
Master data is sensitive but not secret — the advisor needs it, and the admin manages it. Access rules:

Admins: Full read/write access to all master data
Advisors: Read-only access to master data for their assigned entities
Clients: Read-only access to their own entity master data (redacted Steuer-IDs shown as •••)
5a.3 Master Data in Database (Prisma additions)
model Entity {
  id            String   @id @default(cuid())
  name          String
  legalForm     String   // "Privatperson", "GmbH", "GbR", etc.
  active        Boolean  @default(true)
  masterData    EntityMasterData?
  taxYears      TaxYear[]
  members       EntityMember[]
  createdAt     DateTime @default(now())
}

model EntityMasterData {
  id                  String  @id @default(cuid())
  entityId            String  @unique
  entity              Entity  @relation(fields: [entityId], references: [id])

  // Common to all entities
  steuernummer        String? @encrypted  // see Section 13 on encryption
  finanzamt           String?
  steuerberater       String?
  bankIban            String? @encrypted
  bankBic             String?
  bankName            String?
  anschrift           String?

  // Personal entity specific
  steuerIdPersons     Json?   // [{name, geburtsdatum, steuerId}] — stored encrypted
  kinder              Json?   // [{name, geburtsdatum, steuerId}]
  kapitalanlagen      Json?   // [{institution, kontonummer, depotnummer}]
  beteiligungen       Json?   // [{name, anteil}]

  // GmbH specific
  hrNummer            String?
  hrGericht           String?
  ustId               String?
  wirtschaftsjahr     String? // "01.01.-31.12." or custom
  geschaeftsfuehrer   Json?   // [{name, seit}]
  gesellschafter      Json?   // [{name, anteil}]
  datevMandantenNr    String?
  steuernummerGewSt   String? @encrypted

  updatedAt           DateTime @updatedAt
}
Note: The @encrypted annotation is a custom convention — see Section 13 for how sensitive master data fields are encrypted at the application layer before being written to the database.

6.1 Document Requests
6.1.1 Request Object
Each document request has:

Field	Type	Description
id	UUID	Unique identifier
entity_id	FK	Which entity (e.g., courtmaster GmbH)
tax_year	Integer	e.g., 2023
tax_type	Enum	EStE, KSt, GewSt, USt, Other
group	String	One of the 3–5 category groups
title	String	Short name of document needed
description	Text	Detailed explanation from advisor
status	Enum	open, in_review, fulfilled, not_applicable
priority	Enum	normal, urgent
due_date	Date	Optional deadline
created_by	FK	Advisor user who created it
created_at	Timestamp	
updated_at	Timestamp	
6.1.2 Request Lifecycle
[Advisor creates request] 
    → status: open
[Client attaches document(s)]
    → status: in_review  
[Advisor confirms receipt / marks ok]
    → status: fulfilled
[Or: advisor marks as not needed]
    → status: not_applicable
6.1.3 Batch Request Creation
Advisors can create multiple requests at once using a “batch create” form. They can also apply a template (pre-filled set of standard requests) when starting a new tax year for an entity.

6.2 Document Attachments
A request can have one or more documents attached. Each document attachment record stores:

Field	Description
source	google_drive or direct_upload
gdrive_file_id	GDrive file ID (if source = google_drive)
gdrive_file_name	Filename as known in GDrive
gdrive_mime_type	MIME type
gdrive_view_link	Stored shareable link for advisor access
blob_url	Vercel Blob URL (if source = direct_upload)
uploaded_by	Client user
uploaded_at	Timestamp
note	Optional note from client
ai_match_score	Float 0–10, LLM relevance score assigned during discovery (see §6.3)
ai_match_reasoning	One-sentence LLM explanation of why this file was matched
ai_year_match	Boolean — did the LLM confirm the document year matches the tax year in scope
6.3 Intelligent Document Discovery
The core UX innovation: when a client opens an unfulfilled request, the portal does not just show an empty attach button — it proactively searches their Google Drive, scores the results with an LLM, and surfaces the most likely matching documents for one-click confirmation. Manual search and direct upload remain available as fallbacks.

6.3.1 Discovery Flow (Step by Step)
[Client opens a request with status: open]
        |
        v
[Portal sends request title + description + tax year
 as a full-text search query to Google Drive API]
        |
        v
[GDrive returns up to 20 candidate files matching the query
 (filename, content snippets, MIME type, modified date)]
        |
        v
[Portal sends candidates + request context to Claude API
 for relevance scoring — see 6.3.3]
        |
        v
[LLM returns scored list with one-sentence reason per candidate]
        |
        v
[Top 3-5 candidates shown as "Vorschlaege" in the UI
 with score badge + reason text]
        |
        v
[Client reviews: clicks confirm to attach, dismiss to skip,
 or "Andere Datei waehlen" for full Picker]
        |
        v
[Confirmed document attached to request, status: in_review]
6.3.2 Google Drive Full-Text Search
The Google Drive API supports full-text content search across file names and document bodies using the fullText contains query operator. The search query is constructed automatically from the request:

// lib/discovery.ts
function buildDriveSearchQuery(request: Request, taxYear: number): string {
  const keywords = extractKeywords(request.title + ' ' + (request.description ?? ''))
  const yearString = String(taxYear)
  return `fullText contains '${keywords}' and fullText contains '${yearString}'`
}

// Example for "Steuerbescheinigung LIQID 2023":
// fullText contains 'Steuerbescheinigung LIQID' and fullText contains '2023'
Candidate files are filtered to exclude: folders, files modified before taxYear - 1, and files already attached to any request.

6.3.3 LLM Scoring via Claude API
The top 20 raw Drive results are sent to Claude claude-sonnet-4-20250514 with a structured scoring prompt. The model returns a JSON array with a score (0-100) and a one-sentence German reason for each candidate.

Prompt template:

You are a scoring assistant for a German tax document portal.

Tax advisor has requested:
- Title: {request.title}
- Description: {request.description}
- Entity: {entity.name} ({entity.legalForm})
- Tax year in scope: {taxYear}

For each candidate document found in Google Drive, return a JSON object:
  - fileId: string
  - score: integer 0-100 (100 = perfect match)
  - reason: one sentence in German explaining the score
  - yearMatch: boolean — does this document clearly relate to {taxYear}?

Scoring rules:
- Score >= 75: almost certainly correct — confirm with user
- 40-74: plausible but uncertain — show as lower-confidence suggestion
- < 40: do not include
- Penalise documents for a different tax year
- A PDF is more likely to be a formal document than a Google Doc

Candidates: {JSON array with name, snippet, mimeType, modifiedDate, fileId}

Return ONLY a valid JSON array. No preamble, no markdown.
Score thresholds displayed in UI: - Score >= 75: “Sehr wahrscheinlich passend” (green badge) - Score 40-74: “Moeglicherweise passend” (amber badge) - No candidates >= 40: “Keine Vorschlaege — bitte manuell auswaehlen”

6.3.4 Discovery UI
+------------------------------------------------------------------+
|  Steuerbescheinigung LIQID 2023                   [Ausstehend]  |
|  Bitte die Jahressteuerbescheinigung von LIQID                  |
|  fuer 2023 hochladen (inkl. aller 5 Konten).                    |
|                                                                  |
|  Vorschlaege aus Google Drive                                    |
|  +------------------------------------------------------------+  |
|  | LIQID_Steuerbescheinigung_2023_Depot_1234.pdf    [95] grn  |  |
|  |   "Enthaelt Steuerbescheinigung 2023 fuer LIQID Depot"     |  |
|  |   [Bestaetigen]  [Ignorieren]  [Vorschau]                  |  |
|  +------------------------------------------------------------+  |
|  | LIQID_Jahresbericht_2023_komplett.pdf            [62] amb  |  |
|  |   "Jahresbericht 2023, enthaelt ggf. Steuerdaten"          |  |
|  |   [Bestaetigen]  [Ignorieren]  [Vorschau]                  |  |
|  +------------------------------------------------------------+  |
|  | LIQID_Depot_Uebersicht_Q4_2023.pdf               [48] amb  |  |
|  |   "Quartalsuebersicht, kein vollstaendiger JA-Beleg"       |  |
|  |   [Bestaetigen]  [Ignorieren]  [Vorschau]                  |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  [Neue Suche]  [Andere Datei waehlen]  [Datei hochladen]       |
|                                                                  |
|  Diskussion  (2 Kommentare)                       [anzeigen]   |
+------------------------------------------------------------------+
6.3.5 Manual Override Options
“Neue Suche”: Editable text field pre-filled with request title; re-runs the full discovery pipeline with the custom query
“Andere Datei waehlen”: Opens Google Picker for full manual browsing; result stored with discovery_method: manual_picked
“Datei hochladen”: For files not yet in GDrive (e.g. downloaded from a bank portal); stored with discovery_method: manual_uploaded
All three paths produce an Attachment record — only discovery_method and the scoring fields differ.

6.3.6 Discovery Caching
Results are cached per (requestId, userId) for 30 minutes in a DiscoveryCache table in Neon. Cache is invalidated when the client clicks “Neue Suche” or when the advisor edits the request description. No Redis needed at this scale.

6.4 Document Discussion (Q&A per Attachment)
Every attached document has its own dedicated discussion thread — a direct Q&A channel between the client and advisor about that specific document. This is distinct from request-level comments (see 6.5) which concern the request as a whole.

6.4.1 Use Cases
Advisor: “Diese Bescheinigung zeigt nur 4 der 5 LIQID-Konten. Fehlt Depot Nr. 56789?”
Client: “Das ist der vorlaeufige Jahresbericht — der finale kommt Ende Februar.”
Advisor: “Seite 3, Zeile 12: Was bedeutet die Position ‘Sonstige Kapitalertraege EUR 1.240’?”
Client: “Ich habe eine neuere Version — soll ich austauschen oder als zweiten Anhang beifuegen?”
6.4.2 Document Comment Model
model DocumentComment {
  id           String     @id @default(cuid())
  attachmentId String
  attachment   Attachment @relation(fields: [attachmentId], references: [id])
  authorId     String     // Clerk user ID
  authorRole   String     // "advisor" | "client" — denormalized for display
  content      String     // Markdown supported
  resolved     Boolean    @default(false)
  resolvedBy   String?
  resolvedAt   DateTime?
  createdAt    DateTime   @default(now())
  updatedAt    DateTime   @updatedAt
}
Design decisions: - Thread lives on Attachment not Request — moves with the document if re-attached - Unresolved advisor questions block the advisor from marking the request fulfilled - Flat thread (no nested replies) — keeps it simple; this is Q&A not a forum - Markdown supported for referencing amounts, page numbers, and positions

6.4.3 Discussion UI (Attachment Card)
+------------------------------------------------------------------+
|  LIQID_Steuerbescheinigung_2023.pdf           [Bestaetigt]      |
|  Hochgeladen 12. Mai 2025 · Vorschlag-Score: 95                 |
|  [In Drive oeffnen]                                              |
|                                                                  |
|  Diskussion (1 offene Frage)                                     |
|                                                                  |
|  [Jana F. · Steuerberater]  12. Mai 2025                        |
|  Bescheinigung zeigt nur 4 der 5 LIQID-Konten.                 |
|  Bitte pruefen: Fehlt Depot 56789?                              |
|                                                    [Offen]       |
|                                                                  |
|  [Dr. Helge H. · Mandant]  13. Mai 2025                         |
|  Depot 56789 wurde im Maerz 2023 aufgeloest.                   |
|  Kein weiterer Beleg noetig.                                     |
|                                     [Als erledigt markieren]    |
|                                                                  |
|  Antwort schreiben...                                            |
|  [Senden]                                                        |
+------------------------------------------------------------------+
6.4.4 Discussion Notifications
Trigger	Notified
Advisor posts document comment	All client members of the entity
Client replies	The advisor
Comment resolved	Both parties
Unresolved discussion exists	Badge on request card: “Offene Frage”
Unresolved document discussions block fulfilled status — the advisor must resolve or explicitly override.

6.4.5 Two-Level Comment Architecture
Type	Attached to	Scope
RequestComment	Request	About the whole request (“Trade Republic Zugang fehlt”)
DocumentComment	Attachment	About a specific file (“Seite 3, Zeile 12: Was ist diese Position?”)
Both appear in the request detail view but are visually distinct — request thread at top, per-document threads inline with each attachment card.

6.5 Request-Level Comments & Notifications
Each request also has a top-level comment thread for general communication: scope questions, deadline discussions, explanations of why something is unavailable.

Supports plain text with Markdown and @mentions.

Email notifications sent via Resend: - New request created: all entity clients - Discovery suggestions ready: the client (optional per user) - Document attached: advisor - Document discussion comment: counterparty - Request status changed: all participants - All documents fulfilled and no open discussions: advisor (summary)

6.6 Dashboard / Overview
The main dashboard shows: - Year banner (large, persistent — see §5.1): “Steuerjahr 2024” - Per tax type: collapsible sections showing all groups - Within each group: requests with status, title, quick-action buttons - AI discovery indicator on open requests (“3 Vorschläge aus Drive verfügbar”) - Document discussion badge: requests with open unresolved discussions show 💬 - Progress indicators per group and per tax type (e.g. “3 von 7 erfüllt”) - “Urgent / overdue” requests highlighted at top - “All fulfilled” completion state per section

For advisors: cross-entity overview of all open requests + all open document discussions across all entities and years.

7. User Interface Sketches
7.1 Main View (Client) — Year-Banner + Group Overview
+-------------------------------------------------------------+
|  STEUERJAHR 2023                          [Jahr wechseln]   |
|  Familie Hofmeister                                         |
+-------------------------------------------------------------+
|  Einkommensteuer 2023              [========--]  8/10       |
|  -----------------------------------------------------------  |
|  v Kapitalertraege & Depots        [======---]   3/4        |
|    OK  Steuerbescheinigung Quirin Bank        [Erledigt]    |
|    OK  Steuerbescheinigung Trade Republic     [Erledigt]    |
|    >>  Steuerbescheinigung CFB Fonds Nr. 124  [Offen]       |
|        3 Vorschlaege aus Drive verfuegbar                   |
|        [Vorschlaege anzeigen]  [Manuell auswaehlen]         |
|    OK  Ertraegnisaufstellung Quirin Bank      [Erledigt]    |
|                                                              |
|  v Versicherungen & Sonderausgaben [====------]  2/5        |
|    OK  Beitragsbescheinigung Krankenkasse     [Erledigt]    |
|    !!  Spendenbescheinigung Ruderclub  DRINGEND [Offen]     |
|        1 Dokument angehaengt — Offene Frage                 |
|        [Diskussion ansehen]                                  |
|    ...                                                       |
+-------------------------------------------------------------+
The year banner persists across all screens. “Jahr wechseln” opens a modal with a list of available years; past years are shown with a “Archiv / Lesezugriff” badge.

7.1b Request Detail View (Client) — Discovery + Discussion
+-------------------------------------------------------------+
|  STEUERJAHR 2023  >  Kapitalertraege  >  Steuerbescheinigung CFB Fonds
+-------------------------------------------------------------+
|  Steuerbescheinigung CFB Fonds Nr. 124       [Offen]        |
|  Bitte pruefen ob die Beteiligung an CFB Fonds Nr. 124      |
|  in 2023 noch bestand. Falls ja, bitte die Jahres-          |
|  Steuerbescheinigung einreichen.                            |
|                                                              |
|  Vorschlaege aus Drive (3 Treffer)                          |
|  +-----------------------------------------------------------+|
|  | CFB_Fonds_124_Steuerbescheinigung_2023.pdf  Score: 91   ||
|  |   "Steuerbescheinigung CFB Fonds 124 fuer 2023"         ||
|  |   [Bestaetigen]  [Ignorieren]  [Vorschau]               ||
|  +-----------------------------------------------------------+|
|  | CFB_Jahresbericht_2023.pdf                  Score: 55   ||
|  |   "Jahresbericht, nicht Steuerbescheinigung"            ||
|  |   [Bestaetigen]  [Ignorieren]  [Vorschau]               ||
|  +-----------------------------------------------------------+|
|  [Neue Suche]  [Andere Datei waehlen]  [Datei hochladen]    |
|                                                              |
|  -- Beigefuegte Dokumente (1) ----------------------------   |
|  CFB_Fonds_124_Steuerbescheinigung_2022.pdf   [Hochgeladen] |
|  Score: 45 — "Bescheinigung fuer 2022, nicht 2023"          |
|  [In Drive oeffnen]                                         |
|                                                              |
|  Diskussion zu diesem Dokument  (1 offene Frage)            |
|  Jana F. (Steuerberater): "Dies ist die 2022er             |
|  Bescheinigung — bestand die Beteiligung auch in 2023?"     |
|                                              [Offen]        |
|  [Antworten...]  [Als erledigt markieren]                   |
|                                                              |
|  -- Anfrage-Kommentare -----------------------------------   |
|  [Kommentar zur gesamten Anfrage schreiben...]              |
+-------------------------------------------------------------+
7.2 Advisor View — Request Creation
The advisor sees an “Add Request” button within each group that opens a side panel: - Entity / Tax Year / Tax Type (pre-filled from context) - Group (dropdown from 3–5 options) - Title (short, e.g. “Steuerbescheinigung LIQID 2023”) - Description (free text — this is the detailed explanation) - Priority (Normal / Urgent) - Due Date (optional)

8. Authentication & User Management
8.1 Recommendation: Clerk
Clerk is the recommended auth solution for this project for the following reasons:

Criterion	Clerk	NextAuth.js	Auth0
Setup time	~30 min	2–4 hours	1–2 hours
RBAC (roles)	✅ Built-in	❌ Manual	✅ Built-in
Admin panel (user mgmt)	✅	❌	✅
Next.js App Router support	✅ Native	✅	Partial
Vercel integration	✅ First-class	✅	✅
Free tier	10,000 MAU	Free (self-host)	7,000 MAU
SOC 2 Type II	✅	N/A (you manage)	✅
MFA	✅ Out-of-box	Manual	✅
Invite-only users	✅	Manual	✅
Google Sign-In	✅	✅	✅
For this use case (< 20 users, invite-only, two clear roles), Clerk’s free tier is more than sufficient and the RBAC + admin panel completely eliminates the need to build a user management UI.

8.2 Role Model in Clerk
Two Clerk roles are created: - advisor — can create/edit requests, mark status, view all - client — can view requests for their entities, attach documents, comment

The Admin (Helge) has full access through the Clerk dashboard to: - Invite users by email - Assign roles - Remove users - See login history

8.3 Authentication Flow
Login page at /sign-in (Clerk’s <SignIn /> component, fully styled)
Google Sign-In as primary method for clients (since Helge + Isabel use Google accounts)
Email/password as fallback for advisors who may not use Google
No public registration — all users are invite-only via Clerk’s invitation emails
Session management handled by Clerk (JWT, edge-compatible)
9. Document Storage Architecture
9.1 Architectural Decision
Two storage mechanisms are used, chosen for cost efficiency and avoiding unnecessary file duplication:

Path A: Google Drive Linking (Zero-Copy, Preferred)
For documents that already exist in the user’s Google Drive:

Client authenticates to GDrive via Google OAuth (scope: drive.file — minimal, user-selected files only)
Google Picker API opens in modal browser window — client selects file
Portal receives file metadata (ID, name, size, MIME type) and stores it in the database
Portal calls GDrive API to generate a shareable link (role: reader) for the advisor
The advisor accesses the file via the view link — file never leaves Google infrastructure
No storage costs. No duplication.
Important: The drive.file scope means the app can only access files the user explicitly selects through the Picker — it cannot see the user’s entire Drive. This satisfies Google’s OAuth review requirements for non-public apps and ensures minimal permissions.

Path B: Direct Upload to Vercel Blob (For Files Not in GDrive)
For documents not yet in Google Drive (e.g., downloaded bank statements to be uploaded directly):

Client selects file from device
File uploaded to Vercel Blob via the Vercel Blob SDK
Blob URL stored in database
Advisor accesses via a signed Vercel Blob URL (time-limited, secure)
Vercel Blob pricing: $0.023/GB/month storage + $0.10/GB egress. For a private portal with < 100 documents totaling perhaps 2–3 GB, this is under $1/month.

Why Not AWS S3 or Cloudflare R2?
Option	Complexity	Cost	Verdict
Vercel Blob	Minimal (SDK, same platform)	~$0–2/month	✅ Recommended
Cloudflare R2	Low (separate setup)	~$0–1/month (free egress)	🟡 Good alternative
AWS S3	Higher (IAM, bucket config)	~$0–2/month	❌ Overkill for this
Store in DB (base64)	Zero infra	Scales poorly	❌ Bad practice
Verdict: Use Vercel Blob for direct uploads. It integrates natively with the Vercel project, requires zero separate account setup, and the costs are negligible.

9.2 Access Control for Documents
Document Type	Advisor Access	Client Access
GDrive-linked	View via stored share link (read-only)	Own GDrive file (full access)
Direct upload (Blob)	Signed URL (time-limited, 1hr)	Signed URL (time-limited, 1hr)
Document URLs are never exposed publicly. All access goes through the Next.js API layer which validates the user’s Clerk session and their entity membership before issuing a redirect or signed URL.

10. Technical Architecture
10.1 Tech Stack
Layer	Technology	Rationale
Framework	Next.js 15 (App Router)	Vercel-native, modern, vibe-coding-friendly
Hosting	Vercel (subdomain of personal site)	Existing infra, zero-config deploys
Authentication	Clerk	Plug-and-play, RBAC, invite-only
Database	Neon (serverless PostgreSQL)	Free tier generous, Vercel native, SQL
ORM	Prisma	Type-safe, great DX
File Storage	Vercel Blob (direct uploads)	Same platform, minimal setup
GDrive Integration	Google Picker API + Drive API v3	OAuth-based, user-initiated
Email Notifications	Resend	Simple API, Vercel-native, free up to 3k/month
UI Library	shadcn/ui + Tailwind CSS	Radix-based, accessible, vibe-coding-friendly
Icons	Lucide	Consistent with shadcn ecosystem
10.2 Database Schema (Prisma)
model Entity {
  id        String   @id @default(cuid())
  name      String
  legalForm String   // "GmbH", "Privatperson", etc.
  active    Boolean  @default(true)
  taxYears  TaxYear[]
  members   EntityMember[]
  createdAt DateTime @default(now())
}

model EntityMember {
  id       String @id @default(cuid())
  entityId String
  userId   String // Clerk user ID
  entity   Entity @relation(fields: [entityId], references: [id])
}

model TaxYear {
  id       String    @id @default(cuid())
  entityId String
  year     Int
  entity   Entity    @relation(fields: [entityId], references: [id])
  taxTypes TaxType[]
}

model TaxType {
  id        String    @id @default(cuid())
  taxYearId String
  type      String    // "EStE", "KSt", "GewSt", "USt", "Other"
  taxYear   TaxYear   @relation(fields: [taxYearId], references: [id])
  requests  Request[]
}

model Request {
  id          String       @id @default(cuid())
  taxTypeId   String
  group       String       // e.g. "Kapitalerträge & Depots"
  title       String
  description String?
  status      String       @default("open") // open | in_review | fulfilled | not_applicable
  priority    String       @default("normal") // normal | urgent
  dueDate     DateTime?
  createdBy   String       // Clerk user ID
  taxType     TaxType      @relation(fields: [taxTypeId], references: [id])
  attachments Attachment[]
  comments    Comment[]
  createdAt   DateTime     @default(now())
  updatedAt   DateTime     @updatedAt
}

model Attachment {
  id              String            @id @default(cuid())
  requestId       String
  source          String            // "google_drive" | "direct_upload"
  gdriveFileId    String?
  gdriveFileName  String?
  gdriveMimeType  String?
  gdriveViewLink  String?
  blobUrl         String?
  fileName        String
  fileSize        Int?
  uploadedBy      String            // Clerk user ID
  note            String?
  discoveryScore  Int?              // LLM score 0-100; null if manually picked
  discoveryReason String?           // One-sentence German explanation from LLM
  discoveryMethod String            @default("manual_uploaded") // auto_suggested | manual_picked | manual_uploaded
  request         Request           @relation(fields: [requestId], references: [id])
  comments        DocumentComment[]
  createdAt       DateTime          @default(now())
}

// Q&A discussion thread anchored to a specific document attachment
model DocumentComment {
  id           String     @id @default(cuid())
  attachmentId String
  attachment   Attachment @relation(fields: [attachmentId], references: [id])
  authorId     String     // Clerk user ID
  authorRole   String     // "advisor" | "client"
  content      String     // Markdown supported
  resolved     Boolean    @default(false)
  resolvedBy   String?
  resolvedAt   DateTime?
  createdAt    DateTime   @default(now())
  updatedAt    DateTime   @updatedAt
}

// General comment thread at the request level
model RequestComment {
  id        String   @id @default(cuid())
  requestId String
  authorId  String   // Clerk user ID
  content   String   // Markdown + @mentions
  request   Request  @relation(fields: [requestId], references: [id])
  createdAt DateTime @default(now())
}

// Cache for LLM discovery results to avoid repeated API calls
model DiscoveryCache {
  id          String   @id @default(cuid())
  requestId   String
  userId      String
  queryUsed   String   // The Drive search query that was executed
  results     Json     // Array of {fileId, name, score, reason, yearMatch}
  expiresAt   DateTime
  createdAt   DateTime @default(now())
  @@unique([requestId, userId])
}
10.3 Application Routes
/ (redirect to /dashboard)
/sign-in                         → Clerk SignIn page
/sign-up                         → Disabled (invite-only)
/dashboard                       → Entity/year overview
/entity/[entityId]/[year]/[type] → Requests grouped by category
/entity/[entityId]/[year]/[type]/request/[id] → Single request detail
/admin/users                     → User management (Admin only)
/admin/entities                  → Entity management (Admin only)
/admin/templates                 → Request template management (Admin only)

API routes (Next.js Route Handlers):
/api/requests/[id]/attach/gdrive          → Handle GDrive Picker callback + store metadata
/api/requests/[id]/attach/upload          → Handle direct file upload to Vercel Blob
/api/requests/[id]/discovery              → Run GDrive search + LLM scoring; return candidates
/api/requests/[id]/discovery/search       → Re-run discovery with custom query string
/api/attachments/[id]/url                 → Issue time-limited signed URL for Blob-stored files
/api/attachments/[id]/comments            → GET list / POST new DocumentComment
/api/attachments/[id]/comments/[cid]      → PATCH (resolve/unresolve) a DocumentComment
/api/requests/[id]/comments               → GET list / POST new RequestComment
/api/notify                               → Send email notifications via Resend
10.4 Google Drive OAuth Setup
Create a Google Cloud Project at console.cloud.google.com
Enable Google Drive API and Google Picker API
Create OAuth 2.0 credentials (Web Application type)
Set authorized redirect URI to https://steuer.hofmeister.com/api/auth/google/callback
Configure OAuth consent screen as Internal (only for specific Gmail accounts — Helge, Isabel, etc.)
Request two scopes:
https://www.googleapis.com/auth/drive.readonly — needed for full-text content search across Drive (the discovery feature). This is a sensitive scope but since the app is configured as Internal, no Google verification review is required.
https://www.googleapis.com/auth/drive.file — for the Picker-based manual attach flow (non-sensitive scope)
Store GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_API_KEY (for Picker) in Vercel environment variables
Note on Drive scope choice: drive.readonly is needed specifically for the discovery search (§6.3), because files.list with fullText contains searches across the user’s entire Drive — not just files previously opened by the app. Since the consent screen is configured as Internal (only named Google accounts can authorize), Google’s standard verification process for sensitive scopes does not apply. The user sees a consent screen listing the scopes once on first login; their OAuth token is then stored server-side (encrypted) for subsequent discovery runs without requiring re-authorization.

Storing the OAuth refresh token: After the user authorizes, the server receives a refresh token. This is stored encrypted (AES-256-GCM, same pattern as §13.4) in the database per user. It is used server-side to issue new access tokens for Drive search calls. Tokens are never exposed to advisors or other users.

11. Request Templates
To accelerate new tax year setup, the system supports “templates” — predefined sets of requests that can be applied to an entity + year + tax type with one click.

Template: Einkommensteuer Privat (EStE)
Group: Kapitalerträge & Depots - Steuerbescheinigung [Bank/Depot eintragen] ×N - Erträgnisaufstellung [Bank/Depot eintragen] ×N - Depotauszug zum 31.12.

Group: Einnahmen & Ausgaben
- Einnahmen-Überschuss-Rechnung selbständige Tätigkeit - Belege Betriebsausgaben

Group: Versicherungen & Sonderausgaben
- Beitragsbescheinigung Krankenkasse - Spendenbescheinigungen (alle)

Group: Immobilien & Handwerker
- Handwerkerrechnungen (Hauptwohnsitz) - Handwerkerrechnungen (Ferienwohnung/Ferienhaus) - Hausgeldabrechnung Verwalter

Group: Sonstiges & Familienbelege
- Kinderbetreuungskosten (Kita/Schule) - Steueridentifikationsnummern Kinder - Fondsbeteiligungsnachweise

Template: Körperschaftsteuer / GewSt (GmbH)
Group: Bankbelege & Kontoauszüge
- Kontoauszüge [Bankkonto] (vollständiges Jahr)

Group: Kapitalanlagen & Depots
- Vermögensbericht LIQID (Jahresende) - Steuerbescheinigung LIQID - Wertpapierbuchhaltung (Fintegra o.ä.)

Group: Rechnungen & Belege
- Fehlende Eingangsrechnungen laut Kontoauszug - Ausgangsrechnungen (Vollständigkeit prüfen)

Group: Verträge & Vereinbarungen
- Darlehensverträge Gesellschafter - Sonstige Verträge

Group: Spenden & Sonstiges
- Spendenbescheinigungen - Sonstige Belege

12. Notifications
All email notifications are sent via Resend with a clean, simple template matching the portal’s design.

Trigger	Recipients	Subject Template
New request created	All entity clients	“Neue Anforderung: {title} [{entity} {year}]”
Request marked urgent	All entity clients	“⚠️ Dringend: {title} [{entity} {year}]”
Document attached	Advisors	“Dokument eingegangen: {title} [{entity}]”
Request fulfilled	All request participants	“✅ Erledigt: {title}”
Comment posted	All request participants	“Neuer Kommentar: {title}”
13. Security, Privacy & Admin Data Protection
13.1 The Admin Trust Boundary Problem
This is a private portal hosted on Vercel. Vercel employees (and theoretically anyone with platform-level access) can access environment variables, logs, and the database connection string. Similarly, a future technical admin user you invite to help maintain the app could read data in the database or logs. Your tax documents and Steuernummern are sensitive personal and financial data that must be protected even from infrastructure-level access.

The solution is application-layer encryption: sensitive data is encrypted with a key that only you control, before it is ever written to the database or storage layer. Platform admins who can read the database see only ciphertext. This is distinct from “database encryption at rest” (which protects against physical disk theft but not against someone with database credentials).

13.2 Two Tiers of Sensitive Data
Tier	Data Examples	Protection Strategy
Tier 1 — Highly Sensitive	Document content (PDFs), Steuernummern, Steuer-IDs, IBANs, Darlehensverträge content	Client-side or envelope encryption — never stored as plaintext
Tier 2 — Moderately Sensitive	Request descriptions, comments, entity names, user assignments	Standard access control (Clerk RBAC) + TLS in transit + DB encryption at rest
Tier 3 — Metadata	Status fields, timestamps, user IDs, counts	Standard, unencrypted
13.3 Document Content Protection (Tier 1)
For Google Drive-linked files: The document content never touches the SteuerPortal servers at all. The portal stores only the GDrive file ID and a view link. The document bytes remain in Google Drive, which has its own strong encryption. A platform admin at Vercel cannot access the document content — only Google can. ✅ This is the strongest protection and a key advantage of the GDrive-linking approach.

For directly uploaded files (Vercel Blob): Files are uploaded to Vercel Blob and encrypted with AES-256-GCM before upload using a client-held key (envelope encryption). The encryption key is derived from a master key stored as a Vercel environment variable using HKDF, combined with a per-file salt stored in the database. A platform admin who can read environment variables could in principle decrypt, but a database-only admin cannot. For maximum protection, use the GDrive linking path instead of direct upload for truly sensitive documents.

Recommendation for implementation: Default to Google Drive linking. Restrict direct upload to documents that genuinely don’t exist in Google Drive yet. Consider marking directly uploaded documents with a visual indicator (“⬆ direkt hochgeladen”) so users are aware of the storage path.

13.4 Master Data Encryption (Tier 1)
Sensitive master data fields (Steuernummern, Steuer-IDs, IBANs) are encrypted at the application layer using AES-256-GCM before being stored in the Neon database.

Implementation pattern (TypeScript):

// lib/encryption.ts
import { createCipheriv, createDecipheriv, randomBytes } from 'crypto'

const MASTER_KEY = Buffer.from(process.env.ENCRYPTION_MASTER_KEY!, 'hex') // 32 bytes, hex

export function encrypt(plaintext: string): string {
  const iv = randomBytes(12) // 96-bit IV for GCM
  const cipher = createCipheriv('aes-256-gcm', MASTER_KEY, iv)
  const encrypted = Buffer.concat([cipher.update(plaintext, 'utf8'), cipher.final()])
  const tag = cipher.getAuthTag()
  // Store as: iv:tag:ciphertext (all hex)
  return `${iv.toString('hex')}:${tag.toString('hex')}:${encrypted.toString('hex')}`
}

export function decrypt(stored: string): string {
  const [ivHex, tagHex, ciphertextHex] = stored.split(':')
  const iv = Buffer.from(ivHex, 'hex')
  const tag = Buffer.from(tagHex, 'hex')
  const ciphertext = Buffer.from(ciphertextHex, 'hex')
  const decipher = createDecipheriv('aes-256-gcm', MASTER_KEY, iv)
  decipher.setAuthTag(tag)
  return decipher.update(ciphertext).toString('utf8') + decipher.final('utf8')
}
ENCRYPTION_MASTER_KEY is a 64-character hex string (32 bytes) stored as a Vercel environment variable, set only in Production and Preview environments, and never committed to git. Generate it once with openssl rand -hex 32 and store a backup in your personal password manager (1Password, etc.) — losing this key means losing access to all encrypted data.

Fields encrypted in the database: - EntityMasterData.steuernummer - EntityMasterData.steuernummerGewSt - EntityMasterData.bankIban - EntityMasterData.steuerIdPersons (entire JSON blob) - EntityMasterData.kinder (entire JSON blob, contains Steuer-IDs)

13.5 Comment & Request Description Protection (Tier 2)
Request descriptions and comments written by the advisor may contain sensitive financial details. These are protected by: - RBAC via Clerk: only members of the entity can read its requests - TLS in transit (Vercel enforces HTTPS) - Neon database encrypted at rest (AES-256, managed by Neon) - Application-layer access control: every API route checks Clerk session + entity membership

For the MVP, this is sufficient. If full paranoia is required post-MVP, comments and descriptions can be encrypted using the same AES-256-GCM pattern as master data.

13.6 What Admins Can and Cannot See
Who	What they can access	What they CANNOT access
Vercel platform admin	Env vars (incl. ENCRYPTION_MASTER_KEY), logs, Blob storage	Decrypted content without the key and code; GDrive file contents
Neon DB admin	Raw table data	Encrypted fields (ciphertext only); GDrive files
App Admin user (invited)	Full portal UI including master data	Env vars, DB direct access — they go through the app’s API which enforces RBAC
App Advisor user	Entity data for assigned entities	Other entities; encrypted DB fields (seen only through the API/UI)
App Client user	Own entity data	Other entities; master data Steuer-IDs (shown redacted as •••)
Key insight: The most important protection is the GDrive-linking architecture. When documents live in Google Drive and the portal only stores file IDs and metadata, there is simply nothing for a platform admin to read. The document bytes never arrive at the SteuerPortal servers.

13.7 Audit Log
All data access and mutations are logged to a tamper-evident audit table:

model AuditLog {
  id         String   @id @default(cuid())
  userId     String   // Clerk user ID
  action     String   // "view_attachment", "create_request", "read_master_data", etc.
  entityId   String?
  resourceId String?  // ID of the record accessed
  ipAddress  String?
  userAgent  String?
  createdAt  DateTime @default(now())
}
The audit log is append-only (no update/delete routes) and is accessible only to the Admin role in a dedicated /admin/audit page.

13.8 GDPR & German Data Protection (DSGVO)
All infrastructure runs in Vercel’s EU region (Frankfurt/Amsterdam)
Neon database provisioned in eu-central-1
Privacy policy page required before launch (link in footer)
Data retention: audit logs and document metadata retained for 7 years (§147 AO / §257 HGB)
Data deletion: upon user request, personal data anonymized; documents removed from Blob; GDrive sharing links revoked via API
No third-party analytics or tracking pixels
14. Non-Functional Requirements
Requirement	Target
Page load time	< 2s for dashboard
Uptime	Vercel SLA (~99.99%)
Max file size (direct upload)	50 MB per file
Supported file types	PDF, JPG, PNG, XLSX, DOCX, CSV, ZIP
Browser support	Chrome, Safari, Firefox (latest 2 versions)
Mobile responsiveness	Tablet-friendly (not primary use case)
Accessibility	WCAG 2.1 AA (shadcn/ui provides this by default)
15. Phased Rollout
Phase 1 — MVP (2–4 weeks of vibe coding)
Clerk auth (Google Sign-In + email/password)
Entity and TaxYear management (hardcoded: Familie Hofmeister + courtmaster ventures GmbH, 2023 + 2024)
Request CRUD (advisor creates, client views)
Request groups (hardcoded EStE + KSt templates)
Direct file upload to Vercel Blob
Status tracking (open → in_review → fulfilled)
Basic dashboard with progress indicators
Deployed on Vercel subdomain
Phase 2 — Google Drive Integration + Intelligent Discovery (2–3 weeks)
Google OAuth flow for clients (scope: drive.file)
Google Picker API integration (manual file selection)
GDrive file metadata stored in database
Shareable view links generated and stored
Full-text Drive search via GDrive API (fullText contains)
LLM scoring pipeline (Claude API — structured JSON output)
Discovery candidate UI with score badges and confirm/dismiss actions
“Neue Suche” manual re-query with custom search string
DiscoveryCache table (30-min TTL per request+user)
Phase 3 — Document Discussion & Notifications (1–2 weeks)
RequestComment threads (request-level)
DocumentComment threads (per-attachment Q&A)
Resolve/unresolve on document comments
Unresolved discussion badge on request cards
Block fulfilled status when open document questions exist
Email notifications via Resend (all triggers in 6.5)
@mention support in request-level comments
Phase 4 — Admin & Templates (1 week)
Admin panel: invite users, assign to entities
Template system for new tax year setup
Batch request creation for advisors
Archive old tax years
16. Environment Variables
# Clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard

# Database (Neon)
DATABASE_URL=postgresql://...

# Vercel Blob
BLOB_READ_WRITE_TOKEN=vercel_blob_...

# Google Drive / Picker
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
NEXT_PUBLIC_GOOGLE_API_KEY=...        # For Picker (client-side)
NEXT_PUBLIC_GOOGLE_APP_ID=...         # Cloud project number

# Encryption
ENCRYPTION_MASTER_KEY=<64-char hex, generated with: openssl rand -hex 32>
# ⚠️ Back this up in your password manager. Losing it = losing access to all encrypted master data.

# Anthropic (LLM scoring for document discovery)
ANTHROPIC_API_KEY=sk-ant-...

# Email (Resend)
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=noreply@hofmeister.com
17. Cost Estimate (Monthly, at steady state)
Service	Plan	Cost
Vercel	Pro (existing)	~$20/month (shared with other projects)
Clerk	Free (< 10k MAU)	$0
Neon	Free tier (up to 0.5GB, 190 compute hours)	$0
Vercel Blob	~2-3 GB storage + minimal egress	~$1–2/month
Resend	Free (< 3k emails/month)	$0
Google Cloud	GDrive API + Picker (free quota)	$0
Anthropic API	Discovery scoring: ~20 candidates x requests/month	~$0–2/month
Total		~$2–5/month (excluding existing Vercel Pro)
Note on LLM cost: Each discovery call sends ~20 file snippets (~2k tokens input) and returns a scored JSON array (~500 tokens output). At ~$3/M input + $15/M output for claude-sonnet-4-20250514, one discovery run costs roughly $0.01. At 200 discovery runs per month (active tax season), that is ~$2/month. Costs are negligible.

18. Open Questions for Advisor Onboarding
Before launch, confirm with Jana Fuhrmann:

Access preferences: Does she prefer to access GDrive-linked documents via a “View in Drive” link, or should the portal proxy/download files for her?
Group naming: Should German or English be used for UI labels? (Recommendation: German, since all users are German-speaking)
Notification preferences: Does she want email notifications for every document upload, or a daily digest?
Existing documents: Does she need access to historic years (2021, 2022) or only from 2023 onwards?
Additional entities: Are there other entities (e.g., other GmbHs) that should be included from day one?
Appendix A: Taxonomy Reference (Quick Card for Advisor)
When creating requests, use these standard group names for consistency:

EStE (Privat): Kapitalerträge & Depots | Einnahmen & Ausgaben | Versicherungen & Sonderausgaben | Immobilien & Handwerker | Sonstiges & Familienbelege

KSt/GewSt (GmbH): Bankbelege & Kontoauszüge | Kapitalanlagen & Depots | Rechnungen & Belege | Verträge & Vereinbarungen | Spenden & Sonstiges

End of Document
