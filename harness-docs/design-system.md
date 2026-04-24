# BID Equity Design System — Distribution & Integration

## TL;DR

The BID Equity brand system is hosted as a single zip on a public S3 path:

```
https://bid-equity-design-system.s3.eu-central-1.amazonaws.com/design-system.zip
```

Every greenfield web archetype (Next.js, Vite+React, Astro) MUST fetch this
zip during scaffolding, extract it, and follow the embedded `SKILL.md` to
wire colors, type, fonts, logos, and shadcn-style components into the new
prototype. This is enforced by `plugin/skills/greenfield-scaffold/SKILL.md`
(see Step 4c "Apply BID Equity design system").

The zip is updated by re-uploading to the same S3 key. Consumers read the
latest version on every fetch — there is no version pinning today.

## Why public S3 instead of signed URLs

S3 pre-signed URLs cap at 7 days (SigV4 hard limit). A long-running greenfield
flow that the design team updates monthly would silently break. The
alternatives we considered:

| Option | Why we passed |
|---|---|
| Pre-signed URL (7-day cap) | Breaks silently; URL refresh becomes a chore |
| CloudFront signed URLs | Years-long expiry but RSA key pair ops + distribution setup |
| GitHub mirror / Cloudflare Pages | Forces design team to commit to git instead of upload to S3 |
| Lambda proxy | Adds infra to maintain |
| **Public S3 object** | One bucket-policy line, no expiry, no auth dance |

The brand system is intentionally public-facing material (the brand IS the
public face) so an unauthenticated GET is appropriate. We narrow the public
read to a single object (`design-system.zip`), not the whole bucket.

## Bucket policy (one-time AWS setup)

The bucket lives at `s3://bid-equity-design-system` (region: `eu-central-1`).
Only one operator needs to run this, once:

```bash
# 1) Allow object-level public access on this bucket (enables the policy below).
aws s3api put-public-access-block --bucket bid-equity-design-system \
  --public-access-block-configuration \
  "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# 2) Bucket policy: grant s3:GetObject ONLY to design-system.zip — nothing else.
aws s3api put-bucket-policy --bucket bid-equity-design-system --policy '{
  "Version":"2012-10-17",
  "Statement":[{
    "Sid":"PublicReadDesignSystemZip",
    "Effect":"Allow",
    "Principal":"*",
    "Action":"s3:GetObject",
    "Resource":"arn:aws:s3:::bid-equity-design-system/design-system.zip"
  }]
}'

# 3) Verify — should return HTTP/2 200 and the zip's Content-Length.
curl -sI https://bid-equity-design-system.s3.eu-central-1.amazonaws.com/design-system.zip | head -3
```

If step 3 returns 403, the bucket-level Block Public Access is still on
somewhere else (e.g. the AWS account-level S3 settings); check
`aws s3api get-public-access-block --bucket bid-equity-design-system`.

## Updating the design system

Replace the object — same key, same URL. No versioning today. Consumers see
the new version on the next fetch.

```bash
aws s3 cp ./design-system.zip s3://bid-equity-design-system/design-system.zip
```

If we ever need version pinning (e.g. a prototype that must keep using v1
even after v2 ships), add a date-stamped key alongside (e.g.
`design-system-2026-04.zip`) and reference it explicitly.

## What's in the zip (current state)

193 files, ~3.3 MB compressed:

| Path | Purpose |
|---|---|
| `SKILL.md` | Claude Code agent skill manifest — defines how to apply the brand. Read this first. |
| `README.md` | Brand fundamentals — voice (DE/EN), visual rules, content patterns |
| `colors_and_type.css` | Design tokens (Coral #FF564F, Stoney, Navy, Bebas + Swis721 @font-face) |
| `components/ui/` | shadcn-style component set (button, card, dialog, …) |
| `components/` | Custom BID components (Hero, Navbar, Footer, Approach, Portfolio, …) |
| `ui_kits/website/` | Hi-fi React reimplementation of the bidequity.de marketing site |
| `fonts/` | Licensed webfonts: Bebas Neue Pro SemiExpanded, Swis721 family |
| `assets/` | Logos (positive, white, device mark) |
| `preview/` | Token + component cards for visual reference |
| `uploads/` | Original-source files including `User Guidelines_2021_vFINAL.pdf` |

The embedded `SKILL.md` is the canonical reference for how to apply the
brand. The greenfield-scaffold step delegates to it rather than duplicating
the rules here.

## Integration policy (greenfield)

For every greenfield web archetype:

1. **Fetch & cache.** Download the zip into `~/.cache/dirigent/design-system.zip`
   if absent or older than 24h. (Re-download forces possible via
   `DIRIGENT_DESIGN_SYSTEM_REFRESH=1` env var.)
2. **Extract** to a temp directory.
3. **Read** the embedded `SKILL.md` and follow its file-map +
   integration instructions for the chosen frontend stack.
4. **Wire** colors_and_type.css into the global stylesheet, copy
   fonts into the project's public/static assets, drop logos in
   the right places, copy the relevant `components/ui/*` into
   the project's component tree.
5. **Reference** the brand explicitly in the new project's
   `README.md` → `## Branding` section, so downstream phases
   know where the brand rules live.

For non-web archetypes (CLI tools, scheduled batch jobs, AI agents
without a UI), the design system is not applicable — skip silently.

## When this rule does NOT apply

- Non-BID portfolio company prototypes (the brand is BID's, not the
  portcos'). If the dirigent target repo is a portfolio company, the
  greenfield agent should skip the BID design system fetch.
- SPECs that explicitly say "use stack default styling" or "no custom
  branding". Recorded as a deviation in the PR description.
