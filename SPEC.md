# Wer wird Promillionär

## Goal

A web-based party quiz & games app (à la Jackbox/Kahoot) where a host runs a game on a shared screen and teams join from their phones via QR code / room code. Supports a mixed-round quiz mode with six question types and a standalone Bingo mode. Hosts can create quizzes manually, import JSON, or generate them with AI assistance. UI is German-first with i18n scaffolding.

## Requirements

- **R1** (infra/must): Web app built with Next.js (App Router) + TypeScript, deployable to Vercel or similar Node host.
- **R2** (ui/must): Two distinct UIs — a **Host view** (large shared screen, shows question, timer, scores) and a **Player view** (mobile-optimized, joins via room code or QR).
- **R3** (integration/must): Realtime room sync between host and players using **Supabase Realtime**; all players in a room see state updates within <500 ms of host action.
- **R4** (data-model/must): Games are organized as **rooms** with a short join code (6 chars), a host, and 2–N **teams**; players join a team, not as individuals.
- **R5** (auth/must): Hosts authenticate via **Supabase Auth** (email magic link) to save quizzes; players join anonymously with just a nickname + team.
- **R6** (workflow/must): Host can create a **Quiz** = ordered list of **Rounds**; each round has a type and a set of questions/items.
- **R7** (workflow/must): Support round type **Multiple Choice** — question + 2–6 answer options, one correct, per-team buzz/select within time limit, points for correct answers.
- **R8** (workflow/must): Support round type **Schätzen** (Estimate) — numeric answer; team closest to the true value wins points; configurable scoring (winner-takes-all or graded by distance).
- **R9** (workflow/must): Support round type **Wer hat's gesagt** (Who said it) — a quote + list of possible authors; teams pick one; correct author scores.
- **R10** (workflow/must): Support round type **Wer kennt mehr** (Who knows more) — a category; teams alternate naming valid items; host marks valid/invalid; team that can't name a new valid item loses the round.
- **R11** (workflow/must): Support round type **Sortierduell** (Sort duel) — an ordered list (e.g. by year, size); two teams alternate placing the next item in order; first team to place an item incorrectly loses the round.
- **R12** (workflow/must): Support round type **Bingo (as round)** — each team gets a 4x4 or 5x5 card of categories/items; host calls items; first team to complete a row/column/diagonal wins.
- **R13** (workflow/must): Support **Standalone Bingo mode** — a game mode independent of the quiz flow, using a bingo card set without surrounding rounds.
- **R14** (ui/must): Host view shows a live scoreboard updated after every round and a final results screen.
- **R15** (workflow/must): Quiz **editor** UI lets authenticated hosts create/edit/delete quizzes and individual rounds of any of the six round types.
- **R16** (workflow/must): **JSON import/export** — hosts can import a quiz from a JSON file matching a documented schema and export existing quizzes to JSON.
- **R17** (integration/must): **AI generation assistance** — in the editor, the host can prompt an LLM (e.g. "90s German pop quiz, 10 MC questions + 1 Sortierduell by release year") and receive a draft quiz that can be edited before saving. LLM provider configurable via env var; API key server-side only.
- **R18** (data-model/must): Quizzes, rounds, questions, rooms, teams, and scores persist in **Supabase Postgres**. Schema includes at minimum: `user`, `quiz`, `round`, `question`, `room`, `team`, `team_member`, `round_result`, `envelope`, `shot_ledger`. Row-Level Security is enabled on all user-owned tables.
- **R19** (ui/must): German UI strings by default; all user-facing text routed through an i18n layer (e.g. `next-intl`) so additional locales can be added without code changes.
- **R20** (ui/should): Player join flow: scan QR → enter nickname → pick/create team → wait-room screen → auto-advance when host starts the game.
- **R21** (workflow/should): Host can pause, skip, or re-open a question; host can manually adjust team scores (for judgment calls in Wer kennt mehr / Sortierduell).
- **R22** (validation/should): Room codes expire after N hours of inactivity; reconnect flow restores player to their team if they refresh or briefly disconnect.
- **R23** (policy/should): Rate-limit AI generation per host account to control LLM cost.
- **R24** (ui/may): Light sound effects and simple animations (timer tick, correct/wrong, bingo) on the host view.
- **R25** (workflow/may): Seed pack with a handful of ready-made quizzes and bingo cards in German so the app is usable out of the box.
- **R26** (workflow/must): **Freemium monetization** — free host accounts are limited per calendar month (suggested defaults: 3 saved quizzes, 5 hosted rooms, 10 AI generations, max 4 teams per room). A **Pro** subscription removes these limits (unlimited quizzes, unlimited rooms, higher AI quota, larger team count). Players are always free; no ads.
- **R27** (integration/must): **Stripe** integration for Pro subscriptions — monthly and yearly plans, Stripe Checkout for purchase, Stripe Customer Portal for self-service management, webhooks to sync subscription status to the `user` record.
- **R28** (data-model/must): Extend schema with `subscription` (user_id, stripe_customer_id, stripe_subscription_id, plan, status, current_period_end) and `usage_counter` (user_id, period, quizzes_created, rooms_hosted, ai_generations) for enforcing free-tier limits.
- **R29** (policy/must): Server-side enforcement of free-tier limits on every gated action (create quiz, start room, invoke AI generation); return a clear "upgrade required" response that the UI surfaces as an upsell modal linking to Stripe Checkout.
- **R30** (ui/should): Billing page in the host account area showing current plan, usage vs. limits, and links to upgrade / manage subscription via Stripe Customer Portal.
- **R31** (workflow/must): **Envelope board** — the host view renders a virtual board of question **envelopes** grouped by **category** (columns = categories, rows = envelopes). Each envelope is tied to one question and displays a short **hint** (teaser text) visible before it is opened. Envelopes are visually marked as available, taken, or resolved.
- **R32** (workflow/must): **Round flow via envelope pick** — each round, every team picks **one envelope** (in a configurable order: fixed, reverse-score, or random). Picked envelopes are locked to that team and reveal the full question on the host view.
- **R33** (workflow/must): **Shot-based scoring** — the "prize" for answering correctly is that the winning team distributes **N shots** (configurable per question, default 1) to members of an opposing team. The player view of the receiving team shows which of their members are selected to drink; the host can also assign shots manually during judgment-call rounds.
- **R34** (data-model/must): `envelope` table fields: `id`, `round_id`, `category`, `hint`, `question_id`, `shot_value` (default 1), `status` (`available`/`taken`/`resolved`), `taken_by_team_id`. `shot_ledger` table records every shot award: `id`, `room_id`, `round_id`, `from_team_id`, `to_team_id`, `to_member_id` (nullable if team-wide), `count`, `created_at`.
- **R35** (ui/must): Host view shows a running **shot scoreboard** per team and per player (total shots received) alongside the point scoreboard; final results screen highlights both the quiz winner and the "Promillionär" (player with the most shots received).
- **R36** (policy/must): Quiz editor lets the host mark each quiz/room as **alcoholic** or **non-alcoholic** (alkoholfrei) mode; in non-alcoholic mode all UI copy and iconography refers to non-alcoholic "shots" (e.g. juice, soft drinks). Default setting is configurable per room at game start.
- **R37** (auth/must): **Role-based access control** — every `user` has a `role` of `admin` or `host`. Roles are stored on the `user` record and enforced via Supabase RLS policies and server-side checks. Players remain anonymous and are not users.
- **R38** (auth/must): **Invite-only signup** — public self-signup is disabled at launch. A new account can only be created by following a valid **invite link** issued by an admin. The magic-link login flow continues to work normally for already-provisioned accounts.
- **R39** (workflow/must): **Invite flow** — admins generate invites (single-use token, configurable expiry, optional pre-assigned role and plan) from the admin board. Invites can be delivered by copyable link or by email. Accepting an invite provisions the `user` record, consumes the token, and logs the inviter in the audit trail.
- **R40** (ui/must): **Admin board** — an authenticated admin-only area (`/admin`) with: (a) user list with search, role, plan, last login, usage; (b) create/revoke invites; (c) change a user's role; (d) suspend/reactivate a user; (e) manually grant or revoke Pro (bypassing Stripe for comps). All admin actions are server-side gated by role check and logged.
- **R41** (data-model/must): Extend schema with `invite` (`id`, `token_hash`, `email` nullable, `role`, `plan`, `created_by`, `expires_at`, `accepted_at`, `accepted_by`) and `admin_audit_log` (`id`, `admin_id`, `action`, `target_user_id`, `metadata` jsonb, `created_at`).
- **R42** (policy/must): A **feature flag** `PUBLIC_SIGNUP_ENABLED` (env var, default `false`) gates the self-signup route. When `false`, `/signup` without a valid invite token returns a "by invitation only" page; when `true`, the normal signup flow is exposed without code changes.
- **R43** (workflow/should): **Bootstrap admin** — a seeded script / one-shot CLI command provisions the first admin user from an env-configured email so the admin board is reachable on a fresh deployment.
- **R44** (workflow/must): **Two-team head-to-head format** is the primary game mode — exactly two teams compete; UI, scoring, envelope-pick alternation, and shot distribution all assume `n_teams = 2` as the default. Larger team counts remain supported but de-emphasized.
- **R45** (workflow/must): **Question story intros** — every question can have an optional **intro block** the quizmaster reveals on the host view before the question itself. An intro block is an ordered list of media items: **text**, **image**, or **video** (uploaded to Supabase Storage or referenced by URL). The quizmaster steps through intro items at their own pace before the question is shown to teams.
- **R46** (workflow/must): **Presenter mode** — a host-only **presenter view** (separate route or second-screen window) shows private quizmaster notes per question (background story, fun facts, trivia, the correct answer, suggested patter) that are NEVER sent to player devices or the shared host screen. Notes are stored on the `question` record.
- **R47** (workflow/must): **Per-question timer** — each question has a configurable time limit (default per round type, override per question, "no timer" allowed). Visible countdown on host view; player view shows remaining time.
- **R48** (workflow/must): **Sudden-death tie-breaker** — when the final scoreboard ends in a tie, the host triggers a sudden-death Schätzen question; the team closest to the true value wins. Tie-breaker question can be authored on the quiz or auto-pulled from a default pool.
- **R49** (workflow/should): **Host disconnect grace period** — if the host's tab closes or loses connection, the room enters a paused state for up to 5 minutes; the host can reconnect and resume from the same state. After the grace period the room is closed and final state persisted.
- **R50** (workflow/should): **Pre-game lobby** — before the host starts the game, players see a lobby screen with team rosters, can edit their nickname, and signal "ready". Host sees ready states and can start when satisfied.
- **R51** (workflow/should): **Player reconnect** — players who refresh or briefly disconnect rejoin the same team automatically via a session token stored in `localStorage`; no re-entering the room code.
- **R52** (workflow/must): **Media attachments on questions and intros** — images and short videos can be uploaded to **Supabase Storage** (per-host bucket, size cap, MIME allow-list) and attached to questions, answer options, intro blocks, and bingo cards. Audio is explicitly out of scope for v1.
- **R53** (workflow/should): **Duplicate quiz** action in the editor that creates a deep copy (rounds, questions, envelopes, intros, notes) under a new name owned by the same host.
- **R54** (workflow/should): **Quiz visibility** — each quiz has a visibility setting: `private` (default), `unlisted` (anyone with link can clone), or `team-shared` (visible to other hosts the owner explicitly grants access to). No public discovery.
- **R55** (data-model/should): Each quiz has a **language tag** (`de`, `en`, …) used by the AI generator and import validator to keep generated content in the right language. Defaults to the host's UI locale.
- **R56** (integration/must): **Per-question regeneration** — the AI assistant can regenerate or edit an individual question (or intro block, or notes) without re-running the whole quiz generation.
- **R57** (policy/must): **Token cost ceiling per generation** — every AI call has a hard max-token cap (input + output) enforced server-side, in addition to the per-host rate limit from R23. Excess requests return a clear error.
- **R58** (policy/must): **AI disclaimer + content safety** — generated content is labeled as "AI-generated, ungeprüft" in the editor until the host explicitly accepts it. Run generated text through a basic safety filter (provider moderation endpoint or simple deny-list) and reject defamatory/sexual/illegal output. Particular care for "Wer hat's gesagt" — never put fabricated quotes in the mouths of real, named living persons without an explicit "fictional" tag.
- **R59** (integration/must): **Stripe Tax** is enabled to compute and collect German MwSt. / EU VAT on Pro subscriptions. Tax IDs (USt-IdNr.) can be entered in the Customer Portal.
- **R60** (integration/must): **Invoices** — Stripe-generated invoices/receipts are downloadable from the billing page (R30). EUR is the primary currency; Pro is offered as monthly and yearly plans with a visible savings indicator on yearly.
- **R61** (workflow/should): **14-day Pro trial** — new host accounts can start a 14-day Pro trial without entering a card; trial expiry downgrades them to free unless they subscribe. Trials are one per account, enforced server-side.
- **R62** (workflow/should): **Dunning grace** — failed renewal payments trigger Stripe's smart retries; the user keeps Pro access for a 7-day grace window before downgrade, and is notified by email.
- **R63** (ui/should): **Polish bundle** — (a) host view typography sized for projector / TV viewing distance; (b) team color palette is color-blind-safe; (c) ICU pluralization rules wired through `next-intl` so strings like "{n, plural, one {1 Shot} other {# Shots}}" render correctly; (d) German number/date formatting in Schätzen rounds and timestamps; (e) player view locks to portrait orientation on mobile.
- **R64** (infra/must): **Hosting on Vercel** — the Next.js app is deployed to **Vercel** (production + preview deployments per PR). Project is configured with the required env vars (Supabase URL/keys, Stripe keys/webhook secret, LLM provider key, `PUBLIC_SIGNUP_ENABLED`, bootstrap admin email). Stripe and Supabase webhooks are wired to Vercel routes. Custom domain support and HTTPS are assumed via Vercel.
- **R65** (infra/must): **Complete local testability for core features** — every core feature (host auth, room create/join, all six round types, envelope board + shot ledger, presenter mode, AI generation, JSON import/export, Stripe checkout, invite/admin flow) must be runnable and testable on a developer machine without touching production services. Specifically: (a) `pnpm dev` (or equivalent) starts the Next.js app against a **local Supabase stack** via `supabase start` (Postgres, Auth, Realtime, Storage); (b) Stripe is exercised against **Stripe test mode** with `stripe listen` forwarding webhooks to localhost; (c) the LLM provider can be swapped for a **mock/fake adapter** via env var so AI features work offline and in CI; (d) a `pnpm seed` command loads deterministic seed data (admin user, sample quiz, sample bingo card) into the local DB; (e) a documented **Playwright e2e suite** exercises a full host+player room end-to-end against the local stack; (f) a single `README` section documents the entire local-bring-up flow from clone to running game.

## Scope

### In Scope
- Next.js + TypeScript web app, host + player views.
- Realtime multi-team rooms with QR/code join.
- Six round types listed above + standalone Bingo mode.
- Host auth, quiz editor, JSON import/export, AI-assisted quiz generation.
- Postgres persistence, German-first UI with i18n scaffolding.
- Minimal seed content pack.

### Out of Scope
- Native mobile apps (iOS/Android).
- Public quiz marketplace / social features / user-to-user sharing beyond JSON export.
- Voice/video chat between players.
- Full translation into languages other than German (only i18n scaffolding + English fallback strings).
- Advanced analytics or admin dashboards.
- Moderation tooling for user-generated content.
- Offline mode.
- Audio attachments on questions (deferred from v1).

## Technical Notes

- Fresh repo — no existing ARCHITECTURE.md or stack constraints detected in `/Users/jk/projects/outbid-dirigent` (this repo is unrelated; the app should be scaffolded in a new directory or new repo).
- **Backend locked to Supabase**: Supabase Postgres (with RLS), Supabase Auth (magic link) for hosts, Supabase Realtime for room sync, Supabase Storage for any quiz images. Use `@supabase/ssr` for Next.js App Router integration.
- Recommended stack: **Next.js 15 App Router + TypeScript**, **Tailwind CSS + shadcn/ui** for the UI kit, **Drizzle ORM** pointed at the Supabase Postgres connection string, **next-intl** for i18n, **Stripe** for subscriptions.
- Realtime channels are per room (`room:{code}`). Authoritative game state lives in Postgres; Realtime is used for state-change notifications and lightweight presence. Avoid using Realtime as the source of truth.
- AI generation: server-side route handler calling an LLM via a provider SDK (Anthropic/OpenAI). Key stays in env; structured output via JSON schema matching the quiz import format so generated quizzes round-trip through the same importer.
- JSON quiz schema should be the single source of truth — editor, importer, and AI generator all produce/consume the same shape. Version the schema (`"schemaVersion": 1`) from day one.
- Round-type logic should live behind a common interface (`RoundEngine` with `start`, `handlePlayerAction`, `score`, `isComplete`) so new round types can be added without touching room orchestration.
- Host and player views should share components but render different layouts; use route groups `(host)` and `(player)` under the App Router.
