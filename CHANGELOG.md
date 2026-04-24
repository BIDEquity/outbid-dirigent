# Changelog

## [2.4.0](https://github.com/BIDEquity/outbid-dirigent/compare/outbid-dirigent-v2.3.0...outbid-dirigent-v2.4.0) (2026-04-24)


### Features

* **executor:** add SPEC validator before compaction ([7e726ab](https://github.com/BIDEquity/outbid-dirigent/commit/7e726ab1b174a96a8a61d5bd4ac90eadfd41e19f))
* **executor:** final commit sweep before ship ([c0d911c](https://github.com/BIDEquity/outbid-dirigent/commit/c0d911c3962380aa1d5beafed66dc2795c647d5c))
* **executor:** final review step for greenfield route (structured output + fix loop) ([d3c60ba](https://github.com/BIDEquity/outbid-dirigent/commit/d3c60ba932cd1c0ff0611875eeee622510894fe3))
* **greenfield:** add Clerk stack (managed auth, Keyless Mode) ([b26c29f](https://github.com/BIDEquity/outbid-dirigent/commit/b26c29f33dcf8815793cf5f25373affff9964269))
* **greenfield:** mandate BID Equity design system for web archetypes ([a0dc4ab](https://github.com/BIDEquity/outbid-dirigent/commit/a0dc4ab15d7ede56a7dd107b017506764481312c))
* **greenfield:** use Opus 4.7 for greenfield-scaffold ([284bed6](https://github.com/BIDEquity/outbid-dirigent/commit/284bed6106edf170c9816a614728cf9a3bda03b6))


### Bug Fixes

* **generate-spec:** sync category enum with spec_compactor ([abb21d6](https://github.com/BIDEquity/outbid-dirigent/commit/abb21d6d45cf1a9c3ab5168a44d631a30d7d942b))

## [2.3.0](https://github.com/BIDEquity/outbid-dirigent/compare/outbid-dirigent-v2.2.2...outbid-dirigent-v2.3.0) (2026-04-23)


### Features

* **scaffold:** backend fallback chain — Supabase → Postgres → SQLite ([c08a962](https://github.com/BIDEquity/outbid-dirigent/commit/c08a9624f62ba3a7c66e4bb9e3555a111def9908))
* **scaffold:** mandate navigable entry (dashboard + nav shell) for web archetypes with auth ([bc56ed3](https://github.com/BIDEquity/outbid-dirigent/commit/bc56ed3b1aed3a67e697f4b43307d9e0b423d583))


### Bug Fixes

* **implementer:** forbid loosening test assertions during review-fix ([d617819](https://github.com/BIDEquity/outbid-dirigent/commit/d6178191c963cde79136eb294fd238f3f239ae5b))
* **prompts:** make context7 lookup unconditional for version-sensitive APIs ([7c633f2](https://github.com/BIDEquity/outbid-dirigent/commit/7c633f2771d14ba07d6536e0adffdb38afe58416))

## [2.2.2](https://github.com/BIDEquity/outbid-dirigent/compare/outbid-dirigent-v2.2.1...outbid-dirigent-v2.2.2) (2026-04-22)


### Bug Fixes

* **agents:** wildcard MCP tools in implementer + plugin-writer frontmatter ([2843cfe](https://github.com/BIDEquity/outbid-dirigent/commit/2843cfe66c5ed491bc4e50833df4f936756535a2))

## [2.2.1](https://github.com/BIDEquity/outbid-dirigent/compare/outbid-dirigent-v2.2.0...outbid-dirigent-v2.2.1) (2026-04-22)


### Bug Fixes

* **task-runner:** whitelist MCP tools with proper __* wildcards ([4594fd3](https://github.com/BIDEquity/outbid-dirigent/commit/4594fd3f91b570cd45afb1147034a200fa042097))

## [2.2.0](https://github.com/BIDEquity/outbid-dirigent/compare/outbid-dirigent-v2.1.0...outbid-dirigent-v2.2.0) (2026-04-22)


### Features

* **contract:** warn when user-facing phase has no e2e-framework criterion ([a3e6bb4](https://github.com/BIDEquity/outbid-dirigent/commit/a3e6bb404b1e2db2cd2c7e79163cf21123e11fed))
* **dirigent:** probe claude plugin/mcp toolbox at startup ([8cebe11](https://github.com/BIDEquity/outbid-dirigent/commit/8cebe11d9380357af76ccaf67a00607d6611d336))
* **scaffold:** mandate Playwright install for web archetypes ([4b3470a](https://github.com/BIDEquity/outbid-dirigent/commit/4b3470a1d054bae8de385b7158305903cb3b67a9))
* **scaffold:** replace stock create-next-app / vite landing immediately ([31c9aaa](https://github.com/BIDEquity/outbid-dirigent/commit/31c9aaac39408db11b93b625b21130b0d2346356))
* **scaffold:** seed test credentials and document them visibly ([9179544](https://github.com/BIDEquity/outbid-dirigent/commit/917954472afe3f96e58d934cc944465097ad436d))
* **scaffold:** smoke spec asserts zero console and page errors ([7a36a81](https://github.com/BIDEquity/outbid-dirigent/commit/7a36a81bfb6d2596f88def93ab4be6805fbc5776))
* **scaffold:** start.sh honours PORT env and prints test credentials ([8d6023a](https://github.com/BIDEquity/outbid-dirigent/commit/8d6023a50f6ad808e33edcf72e6f2f7484b35120))

## [2.1.0](https://github.com/BIDEquity/outbid-dirigent/compare/outbid-dirigent-v2.0.0...outbid-dirigent-v2.1.0) (2026-04-21)


### Features

* Add --execution-mode flag, remove start question ([5a2cfa3](https://github.com/BIDEquity/outbid-dirigent/commit/5a2cfa3a72bfc71c3c30806f034639bde0c89c6e))
* add --force-continue flag to skip past failed phase reviews ([8f797e3](https://github.com/BIDEquity/outbid-dirigent/commit/8f797e3863d166ca65b2335eb5f70d9a03dcec3a))
* Add --output json flag for structured JSONL event streaming ([ae77132](https://github.com/BIDEquity/outbid-dirigent/commit/ae771325aac491aa17c37f7a9752b0a50c71a356))
* Add --phase manifest and session recall for manifest generation ([d507b2a](https://github.com/BIDEquity/outbid-dirigent/commit/d507b2a7d1088ca259f7efc8800fb465adf0c1c0))
* add --route flag for manual route override ([d845a14](https://github.com/BIDEquity/outbid-dirigent/commit/d845a14e9bb2025f99dd91a8138a9c05e3b273fc))
* Add API cost calculation based on model pricing ([49849ad](https://github.com/BIDEquity/outbid-dirigent/commit/49849adb2699497c0dc6280eb532fd0fff8465a1))
* Add API usage tracking, summary generation, and interactive questions ([23189b1](https://github.com/BIDEquity/outbid-dirigent/commit/23189b1ca6e117373109eaa3ece6a7e970d8d376))
* add architecture manifest, enforce evidence-based reviews, scalable agent instructions ([a1893c6](https://github.com/BIDEquity/outbid-dirigent/commit/a1893c64d92639f3ae1af2bb33a7d930c72184ef))
* add BRV awareness to pipeline agents ([39307f1](https://github.com/BIDEquity/outbid-dirigent/commit/39307f18e6bff6796425ee7601719968ece9abfc))
* add BRV awareness to pipeline skills ([b062b75](https://github.com/BIDEquity/outbid-dirigent/commit/b062b754731eae4279add07992f916a353224fe1))
* add BRV bridge for ByteRover context-tree integration ([fd8d0de](https://github.com/BIDEquity/outbid-dirigent/commit/fd8d0de8e3d8fbca985b5946dcf3bb1587f71dfc))
* Add build-manifest and validate-manifest plugin skills ([7505951](https://github.com/BIDEquity/outbid-dirigent/commit/75059518a75788e659f9699d88d09915beca0b52))
* add build-plugin skill — auto-generates .claude/ config for any codebase ([a3bdc41](https://github.com/BIDEquity/outbid-dirigent/commit/a3bdc41e6cae68011d2de4e0075578b417b91bd8))
* add confidence and verification_tier fields to contract schema ([fc4b08f](https://github.com/BIDEquity/outbid-dirigent/commit/fc4b08fe80010d0417bcdc086801e89fdaa362a3))
* Add contract events to portal reporter ([82b7bde](https://github.com/BIDEquity/outbid-dirigent/commit/82b7bde0747a1d55ea94315b1b018579a0556fe3))
* Add contract events to portal reporter ([a978b87](https://github.com/BIDEquity/outbid-dirigent/commit/a978b874e97389391bc0effcb4d51c16af91d8c0))
* add contract system, skill-based prompts, init phase, and progress tools ([e5c5a69](https://github.com/BIDEquity/outbid-dirigent/commit/e5c5a698762c06b5472db7150c694c8e657cfc18))
* Add contract tests for Portal ↔ Dirigent integration ([9e5c37d](https://github.com/BIDEquity/outbid-dirigent/commit/9e5c37d5aab7df5f78ffac12c12b7cb1c8666cd6))
* Add demo mode for simulated execution events ([578b0a4](https://github.com/BIDEquity/outbid-dirigent/commit/578b0a4c66787e49a0f92119c3d0881ce7b30faa))
* Add DuckDB session recall plugin for subprocesses ([e718d20](https://github.com/BIDEquity/outbid-dirigent/commit/e718d206c5ea44e80fe128c63310b675909c3e37))
* Add E2E tests against real Portal API ([310d17c](https://github.com/BIDEquity/outbid-dirigent/commit/310d17cd35807b8deece2c2c7cc773cab4bc315f))
* add entropy minimization step to all routes ([9f5b2b7](https://github.com/BIDEquity/outbid-dirigent/commit/9f5b2b7695c9d008e03d135bdbed089881a3643f))
* add generate-architecture skill, run during init phase ([444d97f](https://github.com/BIDEquity/outbid-dirigent/commit/444d97f543fb77d6873f9f0b21304343042aaeb7))
* Add HTTP summary call and interactive mode questions ([6f51033](https://github.com/BIDEquity/outbid-dirigent/commit/6f51033f0d04b835ce900a55c88836c416e4aec2))
* add infra_schema.py — tiered infrastructure Pydantic models ([0e700cf](https://github.com/BIDEquity/outbid-dirigent/commit/0e700cf9f16bb3b557e85162723ca68b14088479))
* add infra_tier field to TestHarness schema ([5a6d22b](https://github.com/BIDEquity/outbid-dirigent/commit/5a6d22b807017c75ab622cf12cb94b89fefda631))
* add InfraDetector to init_phase.py — tiered infra detection and provisioning ([40317c3](https://github.com/BIDEquity/outbid-dirigent/commit/40317c38a1175b0afcbcbbbeb133d5cd7ca3ee1b))
* Add integration test framework ([20c6f19](https://github.com/BIDEquity/outbid-dirigent/commit/20c6f19eff32922d0d5992c0097708d69b231217))
* Add lifecycle hooks to dirigent plugin ([60f6da3](https://github.com/BIDEquity/outbid-dirigent/commit/60f6da352554b2f26d6b956d42d8d5ae1b07cc9a))
* Add plan_first flow and improved branch names ([f6a056a](https://github.com/BIDEquity/outbid-dirigent/commit/f6a056a845812e01babe3a45e4049dec3191fc55))
* Add post-phase code review + fix cycle ([4a2770d](https://github.com/BIDEquity/outbid-dirigent/commit/4a2770d2ca5691747e3b5d318812b8cfb65395a8))
* Add pre-Claude stage events to PortalReporter ([fc7f0ec](https://github.com/BIDEquity/outbid-dirigent/commit/fc7f0ecf4f0b96e38a418cfec7d05fa3b60eff2e))
* Add Proteus integration for deep domain extraction ([d41a1b6](https://github.com/BIDEquity/outbid-dirigent/commit/d41a1b630976317fe27e135312680389b28e7cc9))
* add query-brv skill for active BRV interaction ([9e3b649](https://github.com/BIDEquity/outbid-dirigent/commit/9e3b649105960291102638b8d50b56ec7c4df1c2))
* add quick route for small specs doable in one run ([260ac85](https://github.com/BIDEquity/outbid-dirigent/commit/260ac85c231998d731966b661315db170a657d28))
* add quick-feature skill — plan, implement, review via subagents ([30a2235](https://github.com/BIDEquity/outbid-dirigent/commit/30a2235aa06796f0a8f1b13cdec7152f11a5b2fe))
* add RouteRecord + StateRecord Pydantic validation to router.py ([0e60667](https://github.com/BIDEquity/outbid-dirigent/commit/0e60667615fef07aa3c1d56781fa302b24828105))
* add RunDir module for persistent per-run artifact storage ([9b10256](https://github.com/BIDEquity/outbid-dirigent/commit/9b102569d226b671a977510bf7740faac357019b))
* Add runtime analysis and preview script generation ([fcc70a1](https://github.com/BIDEquity/outbid-dirigent/commit/fcc70a1857ae71ba7971c6ba6075270dcbac7ae5))
* Add semantic versioning with bump-my-version and CI/CD ([604b63f](https://github.com/BIDEquity/outbid-dirigent/commit/604b63fd2625b3a34908a3e552f272ede914b775))
* Add smoke tests and GitHub Actions CI ([e9e37b2](https://github.com/BIDEquity/outbid-dirigent/commit/e9e37b2354bd4efb6b5b4eb8af7b8cfce2991590))
* Add spec image support for Claude Code tasks ([f5b855f](https://github.com/BIDEquity/outbid-dirigent/commit/f5b855fe2b19bd5841d7a61961d343d7783c27c6))
* Add startup confirmation question in interactive mode ([a4f4d15](https://github.com/BIDEquity/outbid-dirigent/commit/a4f4d15b9160b550baf4c0c7c92805a2d4e0bb91))
* Add test instructions and manual hints to summary ([26be508](https://github.com/BIDEquity/outbid-dirigent/commit/26be5080961e449a1e3c2335046d0a2c828766c3))
* add testability and tracking routes with PostHog skill ([99d16ff](https://github.com/BIDEquity/outbid-dirigent/commit/99d16ff8ca199584921163046d28880368ab93c4))
* add Verification section to PR body in shipper.py ([dec80cd](https://github.com/BIDEquity/outbid-dirigent/commit/dec80cd88634375c48e76c20298ca5b9dec037ec))
* **agents:** wire context7 MCP for framework/SDK doc lookups ([b001383](https://github.com/BIDEquity/outbid-dirigent/commit/b001383bd80cab78b1b8338ff7324f3b68c03b3a))
* Allow spec from stdin via --spec - or --spec . ([f9ecf84](https://github.com/BIDEquity/outbid-dirigent/commit/f9ecf8416159638ecbc7f6fa862a4dfaae8be5dc))
* Ask user confirmation right after routing (before planning) ([a15996f](https://github.com/BIDEquity/outbid-dirigent/commit/a15996fc3b710da7cd2f5fb736d95354b2644712))
* Clean subprocess env and inject plugin-dir ([da9e3b5](https://github.com/BIDEquity/outbid-dirigent/commit/da9e3b57d7ae0290e97224827ff02530e01aa4e3))
* **cli:** add --version / -V flag ([9d008a3](https://github.com/BIDEquity/outbid-dirigent/commit/9d008a3476f4803e617a895188eb2a62335843a3))
* collect token usage from hook events and send in summary ([c5acdb2](https://github.com/BIDEquity/outbid-dirigent/commit/c5acdb24eec123464576eb399886fb0fd40b40e0))
* **contract:** harden contract creation with ARCHITECTURE.md + mandatory e2e ([bd15700](https://github.com/BIDEquity/outbid-dirigent/commit/bd1570088ce8fc5637a00c985cfd2f6549079973))
* create-plan skill generates spec from user input when SPEC.md is missing ([1a8ae2c](https://github.com/BIDEquity/outbid-dirigent/commit/1a8ae2cd014fe098b1d9ee17de1a11735292a1c0))
* Enhanced portal logging with full task details and hooks support ([45305d6](https://github.com/BIDEquity/outbid-dirigent/commit/45305d65c6cc7293d4799a5109f053e7eb5e6e19))
* **executor:** capture ADRs after each phase in greenfield and hybrid routes ([d240e71](https://github.com/BIDEquity/outbid-dirigent/commit/d240e71b6ad31f827135a4a66579b32d21b4e68e))
* Expand test manifest schema to match Claude output ([05a95c8](https://github.com/BIDEquity/outbid-dirigent/commit/05a95c8469922303b942e71babf77593bc65320f))
* focused agents, schema validation scripts, skill-agent routing ([084ee4a](https://github.com/BIDEquity/outbid-dirigent/commit/084ee4abd930626042bfe529ca127d1e1ca64b06))
* formalize contracts and reviews as Pydantic-validated JSON with XML-tagged skills ([66e9d32](https://github.com/BIDEquity/outbid-dirigent/commit/66e9d3257836b63a6a82e996824f1ebd52d37ed5))
* generate-spec emits stable R1..Rn requirement IDs ([6222d46](https://github.com/BIDEquity/outbid-dirigent/commit/6222d46b0078f2d74ad1755fbd71c5b2f2d78109))
* **greenfield:** add AI, mobile, and vector DB stacks ([aeb3f5b](https://github.com/BIDEquity/outbid-dirigent/commit/aeb3f5b37cf7fa240dad06a516e62798a91680f2))
* **greenfield:** architecture pattern dimension + routing table ([27f0ec6](https://github.com/BIDEquity/outbid-dirigent/commit/27f0ec68fc30d97d88dc1326d45c0e9e89d907ab))
* **greenfield:** rewrite greenfield route with opinionated stacks ([1117228](https://github.com/BIDEquity/outbid-dirigent/commit/1117228169e1de7f7b18bbcc2fe8faf2e5ea419f))
* **greenfield:** three-axis architecture + evolution thresholds ([ebe73f5](https://github.com/BIDEquity/outbid-dirigent/commit/ebe73f52588022e8668a952290cdae4b05938e80))
* implementer agent discovers and uses codebase skills, agents, conventions ([54991c6](https://github.com/BIDEquity/outbid-dirigent/commit/54991c6a9b27b9490e5701c7b39c64ab80a91e6b))
* include confidence + infra_tier in portal testing events ([0ddbf6a](https://github.com/BIDEquity/outbid-dirigent/commit/0ddbf6aad70c7875edbd324535da64e0c6bd8ba0))
* include Getting Started section in PR body for greenfield projects ([2a2294d](https://github.com/BIDEquity/outbid-dirigent/commit/2a2294d5b2ff28f2eaeb15ad3f4f3f919f750bcc))
* **init:** require source citations in ARCHITECTURE.md and test-harness.json ([d0e00dd](https://github.com/BIDEquity/outbid-dirigent/commit/d0e00dd69faff1849e69816d23cc6852c6c51867))
* inject DIRIGENT_RUN_DIR into subprocess system prompts and env ([79b14b2](https://github.com/BIDEquity/outbid-dirigent/commit/79b14b2c2d608fa5fdf8f7d2556f9788fe194df4))
* **install:** add one-liner install.sh with version selection and nuke-and-pave plugin registration ([4683ae8](https://github.com/BIDEquity/outbid-dirigent/commit/4683ae8790c1c994c3d5ef21854302ffced02489))
* Integrate questioner with Oracle and dirigent main ([284fca3](https://github.com/BIDEquity/outbid-dirigent/commit/284fca32187428d69bad60961b2d134a201006ac))
* **legacy:** integrate Proteus business rules into CompactSpec ([3835dbd](https://github.com/BIDEquity/outbid-dirigent/commit/3835dbd48fe272cecdba521d35afd881798dbd8b))
* LLM-based route discriminator with heuristic fallback ([5cf35d6](https://github.com/BIDEquity/outbid-dirigent/commit/5cf35d64538342cd4137c17d2373c7371d808cca))
* **logger:** emit service and trace_id on every structured log record ([d945df7](https://github.com/BIDEquity/outbid-dirigent/commit/d945df7b83b42cbb203934dbcaef42e7feb44464))
* **maintainer:** add repo-internal skill for stack/pattern changes ([1fe8b4b](https://github.com/BIDEquity/outbid-dirigent/commit/1fe8b4bf5bcf18f5e278349acf29f8e3eb0afdd5))
* make --spec optional, add inline descriptions and --yolo mode ([9cb0a89](https://github.com/BIDEquity/outbid-dirigent/commit/9cb0a899d8bee81908038f1a7d3bfeaf598a3dd8))
* Make test manifest source of truth for preview scripts ([481c583](https://github.com/BIDEquity/outbid-dirigent/commit/481c583bb2432302387ae768beb6b7d2c1d7c628))
* **observability:** cost + subagent output logging on every orchestrator call; bump rc4 ([a7f1ae2](https://github.com/BIDEquity/outbid-dirigent/commit/a7f1ae29132b56af6e0278b221481154bef77b16))
* OpenCode bridge, artifact stripping, greenfield scaffold, conventions fallback ([5fadf84](https://github.com/BIDEquity/outbid-dirigent/commit/5fadf8451acdf37d12b3066b8160fcb84329c1ac))
* Outbid Dirigent - headless autonomous coding agent controller ([173097a](https://github.com/BIDEquity/outbid-dirigent/commit/173097af97ba33a4d3c2386bb73545076d08f438))
* Parse transcript for token usage in SessionEnd hook ([4f4adee](https://github.com/BIDEquity/outbid-dirigent/commit/4f4adee848e95ddeda79a33ab7675c7c17a42dfe))
* **planner:** enforce phase caps, classify phases by kind, require merge justifications ([609ef2a](https://github.com/BIDEquity/outbid-dirigent/commit/609ef2a13bc0cd7ffb355ab254bd5de5d8049579))
* **planner:** enforce vertical slicing — max 1 setup task per plan ([11b284a](https://github.com/BIDEquity/outbid-dirigent/commit/11b284a79f306c627fac39eb1a0b3bffbd8df2b3))
* **plugin:** /dirigent:hi coach, vibecoding playbook, and Track B enforcement ([82a6759](https://github.com/BIDEquity/outbid-dirigent/commit/82a67599696f030ec4ef6bc6ede519acd316525d))
* **plugin:** built-in glue — statusline, SessionStart UX hook, MCP state server ([6e686b4](https://github.com/BIDEquity/outbid-dirigent/commit/6e686b4557c86386b1f049afc6521453aa800be8))
* **polish:** spec→code gap-audit mode with subagent-driven user-outcome checks ([758b424](https://github.com/BIDEquity/outbid-dirigent/commit/758b42442344b96623679ef5cf320634dc544914))
* propagate InfraContext confidence through executor pipeline ([12d6166](https://github.com/BIDEquity/outbid-dirigent/commit/12d6166aa738ce01031a78451810631a7369f6e3))
* Refactor executor, add model selection, and improve plan schema ([5fb4ab6](https://github.com/BIDEquity/outbid-dirigent/commit/5fb4ab6bbc27bc3972a9aa0033c7473cb20926c1))
* remove outbid-test-manifest, add testability score and increase-testability skill ([2f50f70](https://github.com/BIDEquity/outbid-dirigent/commit/2f50f70a7e7639fb5f50b8e532f0232c4579c071))
* replace init phase with test harness that enables e2e verification ([9f58076](https://github.com/BIDEquity/outbid-dirigent/commit/9f580760ac1a11be46f6ba39fa073c4906871828))
* require official scaffolders instead of manual config files ([15a05fc](https://github.com/BIDEquity/outbid-dirigent/commit/15a05fceca1ff09150140df91d813686a7abcf20))
* revamp contract system — three-layer behavioral testing pyramid ([65f8323](https://github.com/BIDEquity/outbid-dirigent/commit/65f832331f3017c863e24fcb07a271475c6676b1))
* **router:** install outbid-harness as first step of every route ([3988947](https://github.com/BIDEquity/outbid-dirigent/commit/39889479545b9b562ec9d00a7e729817a61d306d))
* **skills:** polish 5 route skills for v2 publication ([a49836f](https://github.com/BIDEquity/outbid-dirigent/commit/a49836f8c81bb62b508c5b597374534fa70ef377))
* spec compaction pipeline with per-task req filtering ([905c2ec](https://github.com/BIDEquity/outbid-dirigent/commit/905c2eca8d78a449ab23b0d75dfc82afd0be3d5e))
* **task-runner:** migrate subprocess Claude execution to claude-agent-sdk ([480eb3c](https://github.com/BIDEquity/outbid-dirigent/commit/480eb3cd8a5a7025a83d41a649933c51a0a004e9))
* wire BRV bridge into executor and task prompt builder ([395fb33](https://github.com/BIDEquity/outbid-dirigent/commit/395fb330b16322cdff42721fb677595036c3300c))
* wire LLM router into analyzer with heuristic fallback ([9525219](https://github.com/BIDEquity/outbid-dirigent/commit/95252190b7362a893d8be49d7a70da130da7d2cc))
* wire RunDir into executor and main orchestration loop ([e4d7cad](https://github.com/BIDEquity/outbid-dirigent/commit/e4d7cade61336a7adb8ab032a0b8e43a72a24119))


### Bug Fixes

* Add --break-system-packages for PEP 668 compatibility ([116c741](https://github.com/BIDEquity/outbid-dirigent/commit/116c741749fe0f68c970215d0d48cac21b013086))
* Add is_active() method to DummyQuestioner ([cb08fcc](https://github.com/BIDEquity/outbid-dirigent/commit/cb08fcceac20decc9bf7edacb9d59d270159943e))
* Add pytest-timeout to dev dependencies ([5eabe68](https://github.com/BIDEquity/outbid-dirigent/commit/5eabe68cd2fce4a377ec3904f75ac2e66fc17d2e))
* Add requests dependency for questioner module ([0de90ff](https://github.com/BIDEquity/outbid-dirigent/commit/0de90ff563a402cb572383f24a6e37fd944d4f6a))
* Add set_logger and is_active methods to Questioner ([74dbda3](https://github.com/BIDEquity/outbid-dirigent/commit/74dbda30eefdfafce0a8ab609fc05ac152fed661))
* Add warn method to DirigentLogger ([15e6e60](https://github.com/BIDEquity/outbid-dirigent/commit/15e6e602a48299f9c10a412c483c7510960c1d3f))
* auto-commit when agent forgets to commit after task execution ([d3ddb4c](https://github.com/BIDEquity/outbid-dirigent/commit/d3ddb4c48aad3dbf931058ba89a09d701c9685f0))
* backward compat in Review.load() for old review schema ([0c5471f](https://github.com/BIDEquity/outbid-dirigent/commit/0c5471fe8813bc537f95b76d1d338f58be068453))
* build-plugin takes output dir as argument, defaults to .claude ([a36d44b](https://github.com/BIDEquity/outbid-dirigent/commit/a36d44b99334e785faa99fe4041ae274a681fd00))
* **ci:** unblock PR [#15](https://github.com/BIDEquity/outbid-dirigent/issues/15) — replace removed CriterionLayer.BEHAVIORAL and widen version regex for PEP 440 pre-releases ([112388b](https://github.com/BIDEquity/outbid-dirigent/commit/112388b03e02c748b0e00afc88d1c1330e57bcc6))
* **compactor:** add 'testing' to ReqCategory literal ([4122689](https://github.com/BIDEquity/outbid-dirigent/commit/4122689e08c7fb0dac7137e09b856d470366c1ab))
* **contract:** don't override PASS→FAIL for missing evidence ([1eb4c80](https://github.com/BIDEquity/outbid-dirigent/commit/1eb4c80d1cbdfadb401f2265268c24709464e043))
* **contract:** increase contract creation timeout to 600s ([0d744fd](https://github.com/BIDEquity/outbid-dirigent/commit/0d744fd21cea39379aaf4f65c0e13e4e54a1b122))
* **contract:** normalize phase IDs with "phase-" prefix ([0667e46](https://github.com/BIDEquity/outbid-dirigent/commit/0667e4609e215b0da08e003197a7655fa62f71b0))
* Convert cost_cents to integer before sending to Portal ([20e98a7](https://github.com/BIDEquity/outbid-dirigent/commit/20e98a715fab190d6ca69fc16ec1ce2949d32898))
* dirigent_dir fixture uses exist_ok=True to avoid conflict with logger ([502fd90](https://github.com/BIDEquity/outbid-dirigent/commit/502fd907ed20ebb4c84afd21f28b32aeabdc4813))
* disable tracking route — too sensitive, triggers on common words ([8df7545](https://github.com/BIDEquity/outbid-dirigent/commit/8df75453b4f10d0cc993cafde84c62ec14444186))
* Don't ask Oracle in autonomous mode ([2294281](https://github.com/BIDEquity/outbid-dirigent/commit/22942816e43c73575f68922fba51df5ee845abfc))
* Don't fallback to Oracle for interactive questions ([6c2fbc1](https://github.com/BIDEquity/outbid-dirigent/commit/6c2fbc176fbec152849ef74d2cacbbb5ff3594fc))
* Don't send PostToolUse events to Portal ([4376c78](https://github.com/BIDEquity/outbid-dirigent/commit/4376c78594f3dab01251511786456b0e27b8c58b))
* Ensure completed_tasks key exists in state ([d3b3f6c](https://github.com/BIDEquity/outbid-dirigent/commit/d3b3f6c947f4e291f071e3033521224a033a3657))
* Ensure plugin directory is included in wheel package ([3d9fb11](https://github.com/BIDEquity/outbid-dirigent/commit/3d9fb11a7ead9a7fa8a1e590e6999197b92a2fc1))
* **executor:** tolerate non-numeric phase IDs in legacy logger calls ([dc0f676](https://github.com/BIDEquity/outbid-dirigent/commit/dc0f6769f8ab0df62e8f645d30cfd1273740609e))
* Filter transcript entries by timestamp, not just file mtime ([44c6488](https://github.com/BIDEquity/outbid-dirigent/commit/44c64880bd3b77768252bff85fec07d2e45bc78b))
* **greenfield:** force opinionated defaults + clarify missing stacks ([36c7901](https://github.com/BIDEquity/outbid-dirigent/commit/36c790180da4b8cce0751907762899a2f34342cc))
* Handle BrokenPipeError in logger ([0236b5f](https://github.com/BIDEquity/outbid-dirigent/commit/0236b5fbde2714e0dc6ec1a74d75d4bf61724229))
* Handle dict from cache in router.determine_route() ([b26c2cc](https://github.com/BIDEquity/outbid-dirigent/commit/b26c2cc011bb60584cd59deb04aa5aae918774f6))
* Handle phase-1 format IDs in executor and demo_runner ([79ad52f](https://github.com/BIDEquity/outbid-dirigent/commit/79ad52f4a2d1150b924ca7eba3dc89181c4c884b))
* Improve token usage collection and summary sending ([cc4b58c](https://github.com/BIDEquity/outbid-dirigent/commit/cc4b58c403ac0920f32fb86276da869e79ba5c25))
* Increase plan creation timeout to 30 minutes ([ba4caf0](https://github.com/BIDEquity/outbid-dirigent/commit/ba4caf0fd5f29b0bea3cd7e0f5f696d9e8b6f4d0))
* Increase task timeout from 10 to 15 minutes ([1f0a55d](https://github.com/BIDEquity/outbid-dirigent/commit/1f0a55d2fea15ef2c538859666533ef0ed4bce32))
* Increase task timeout to 30 minutes ([d50a79e](https://github.com/BIDEquity/outbid-dirigent/commit/d50a79e25f1b30c2580b30bdc50c64f19c887cbc))
* **install:** harden settings.json ref pinning against non-dict shapes ([00fd9ab](https://github.com/BIDEquity/outbid-dirigent/commit/00fd9abf4aca6ee994615f2d7a55d6b0a011d2f3))
* log Plan.load() validation errors instead of swallowing silently ([ab76d5d](https://github.com/BIDEquity/outbid-dirigent/commit/ab76d5d1c1ce550c9968fe3732000cda05bb728e))
* log Review.load() errors and normalize enum casing ([92f6bd8](https://github.com/BIDEquity/outbid-dirigent/commit/92f6bd8c50ed7428e91a309c97ad25ac0a5c4ca2))
* make review parsing robust with aggressive normalization and verdict fallback ([6d9e30e](https://github.com/BIDEquity/outbid-dirigent/commit/6d9e30e09a3671eca5ecfbf7f92c9cdc772859f0))
* Make summary event optional in contract tests ([17002be](https://github.com/BIDEquity/outbid-dirigent/commit/17002be0978fef6b24edbd52bdc14345cd5339f3))
* Merge conftest.py fixtures from both branches ([feaeb82](https://github.com/BIDEquity/outbid-dirigent/commit/feaeb8272d51e2c6a02cfba9430086eabcd8a054))
* Move get_portal_reporter import to avoid circular dependency ([225add6](https://github.com/BIDEquity/outbid-dirigent/commit/225add65f579e471e522dc7697b423fa43ab96eb))
* Move get_portal_reporter import to avoid circular dependency ([da51e15](https://github.com/BIDEquity/outbid-dirigent/commit/da51e15b2fa26d32ffb619c6d959424b5c1b36ec))
* NameError in summary upload - use token_usage instead of hook_usage ([0b533e0](https://github.com/BIDEquity/outbid-dirigent/commit/0b533e004f4a0e683a9a78f8f0d85a57cf078038))
* normalize phase IDs to zero-padded format in contract/review paths ([54bf52d](https://github.com/BIDEquity/outbid-dirigent/commit/54bf52d47d0e18340762e7fbd950f40f8c2c05e8))
* Only count files/tokens from current execution ([793528b](https://github.com/BIDEquity/outbid-dirigent/commit/793528b8710dec7ea3439c5b534d941183a541cf))
* Pass portal credentials to Executor for summary upload ([10db970](https://github.com/BIDEquity/outbid-dirigent/commit/10db970aa42c3feb19c7f42bd3dfa5dfa16accda))
* Plan first mode and phase ID compatibility ([d301e2f](https://github.com/BIDEquity/outbid-dirigent/commit/d301e2f983206ecbb1a5095ea949ba5b7815ab94))
* **plan:** constrain effort and model ([2a8407e](https://github.com/BIDEquity/outbid-dirigent/commit/2a8407e231ca840b25da4f5026ce46e235c96263))
* **polish:** scoped git staging + scoped revert per fix ([ffd3b67](https://github.com/BIDEquity/outbid-dirigent/commit/ffd3b67c8cf3e8b1fbd2453687b6fd4bc86bfef7))
* prevent brv query from prompting for credentials interactively ([a361557](https://github.com/BIDEquity/outbid-dirigent/commit/a3615573986db35d7f9337c55c810f7c5cac3b2c))
* prevent reviewer from spawning sub-agents that overwrite review JSON ([c9c424f](https://github.com/BIDEquity/outbid-dirigent/commit/c9c424fe6a73710c49bdebbfeba13f3ca7b907a2))
* programmatic schema validation+retry in contract/review orchestrator ([8779c07](https://github.com/BIDEquity/outbid-dirigent/commit/8779c07fa1005a59fe6efb6434908a5f102df9ba))
* quick-feature must create tests for every new feature ([fd3da7f](https://github.com/BIDEquity/outbid-dirigent/commit/fd3da7f486682aef8451af174c255472d0b603df))
* Read token usage directly from Claude Code transcripts ([1915b67](https://github.com/BIDEquity/outbid-dirigent/commit/1915b6708c377efd85e9ab3a1d4d92a113420bd1))
* remove duplicate hooks reference from plugin manifest ([a7e6963](https://github.com/BIDEquity/outbid-dirigent/commit/a7e6963eefb49905681ea32fa8fc3dd33759326f))
* Remove duplicate summary event from legacy logger ([8894513](https://github.com/BIDEquity/outbid-dirigent/commit/8894513651f8e133a8be21bffc2801fd20ef5f62))
* remove legacy commands that shadow skills and block context:fork ([9963d57](https://github.com/BIDEquity/outbid-dirigent/commit/9963d57e9d5af6960ae7514eacbfc6a203e8fd85))
* rename execute-task skill to implement-task to avoid name clash ([70fd03b](https://github.com/BIDEquity/outbid-dirigent/commit/70fd03b6dda20977d76b13016a61bf45b9308e7b))
* **review:** promote WARN-only reviews to PASS instead of blocking pipeline ([7e30f4c](https://github.com/BIDEquity/outbid-dirigent/commit/7e30f4cadebe4b93282449f2aedfb065987a02fc))
* **sdk:** drain generator + disable setting_sources; bump to rc3 ([6fd7841](https://github.com/BIDEquity/outbid-dirigent/commit/6fd78418645b8aa12004ea8629557f54f780352c))
* Send 'complete' event after shipping, not after execute_plan ([e0bab4c](https://github.com/BIDEquity/outbid-dirigent/commit/e0bab4c9d55427b19bddb946350223765c754f55))
* Set DIRIGENT_HOOK_LOG_DIR for Claude Code hooks ([ecd83f8](https://github.com/BIDEquity/outbid-dirigent/commit/ecd83f8fd27868a8ec1fdad43edfd8cb7f7679a4))
* Skip local DB services when Doppler is used ([3b576a8](https://github.com/BIDEquity/outbid-dirigent/commit/3b576a8c51acd54f2cef3a7c5ea27f5b4569cda6))
* type errors in executor.py logger calls and portal guard ([90377c4](https://github.com/BIDEquity/outbid-dirigent/commit/90377c419bd1a7ddc0f9d50e21e58e6482d6b52c))
* unbound proc in init_phase + wire testing_complete in executor ([f79f85a](https://github.com/BIDEquity/outbid-dirigent/commit/f79f85ad6c75836cc6f15cca9193a1f2e892e98d))
* Update contract tests to match actual Dirigent v1.1.0 events ([59476b0](https://github.com/BIDEquity/outbid-dirigent/commit/59476b04d7a26d40f7013bc5617b7e04e0cbc750))
* Use correct attribute name 'timeout' in QuestionResult ([874e4ae](https://github.com/BIDEquity/outbid-dirigent/commit/874e4aee41a1fbb55e0d44338be75e8e472db5c6))
* use correct Route fields (oracle_needed, repo_context_needed) instead of confidence ([60e09f5](https://github.com/BIDEquity/outbid-dirigent/commit/60e09f5768f6c4f4c2ae05461557be86e24ec823))
* use explicit agent dispatch instead of skill invocation for contract/review ([ee18a6e](https://github.com/BIDEquity/outbid-dirigent/commit/ee18a6e4d0d966a677270baf99c23fb67ffbf159))
* Use venv Python for E2E tests and fix Python 3.9 compatibility ([a101aa2](https://github.com/BIDEquity/outbid-dirigent/commit/a101aa25353e005fbfe5adf6c1b504f5bd946d61))
* **version:** sync plugin.json to v1.6.1 + wire into bumpversion ([2cd24f6](https://github.com/BIDEquity/outbid-dirigent/commit/2cd24f6c8c2a6d4dd6daf4bbcb69b5bca7b8c291))


### Reverts

* Keep sending tool_use events to Portal ([db07ff6](https://github.com/BIDEquity/outbid-dirigent/commit/db07ff680e6686a5283db5a5ab572ba322a05cab))


### Documentation

* Add OUTBID_CONTEXT.md for AI search indexing ([11df5b4](https://github.com/BIDEquity/outbid-dirigent/commit/11df5b4c989c111d4e0ab27fb01d29eb747bcb33))
* add tiered infra & verification confidence design spec ([fcc7d15](https://github.com/BIDEquity/outbid-dirigent/commit/fcc7d158b39d401749bc67c7d0b5cd47cda1e8bf))
* **adr:** record Anthropic SDK → Claude Agent SDK migration as ADR-0001 ([04de629](https://github.com/BIDEquity/outbid-dirigent/commit/04de629f3967ebad8ed4d48fad0f3f93e76a23cd))
* **agentic:** declare Semi-autonomous workflow and Section 10 policies ([daa4143](https://github.com/BIDEquity/outbid-dirigent/commit/daa41432d0a07857610a4d57ef10b83d2cd3c6fe))
* **harness:** add portfolio engineering standards assessment ([59e6d29](https://github.com/BIDEquity/outbid-dirigent/commit/59e6d2990d22bf7a09c1ca079435cd574b68eba3))
* **harness:** add working agreement and PR template ([66d44df](https://github.com/BIDEquity/outbid-dirigent/commit/66d44dfcb6e1e645e3414f365970cf8ec7ed9502))
* **harness:** rerun verify-assessment and refresh standards status ([2836458](https://github.com/BIDEquity/outbid-dirigent/commit/2836458f004899c2d1f9d455b68c9a0a3e05cb44))
* **harness:** track portfolio engineering standards and document templates ([e4f6b08](https://github.com/BIDEquity/outbid-dirigent/commit/e4f6b081030ad211730fd2d8a78fda50801a6bb6))
* map existing codebase ([3d3de7f](https://github.com/BIDEquity/outbid-dirigent/commit/3d3de7f091662c596fd77eca58d8f6f88fe308ac))
* regenerate ARCHITECTURE.md via /generate-architecture --update ([0bf20bc](https://github.com/BIDEquity/outbid-dirigent/commit/0bf20bc929699631e21f8e457af19888649864ea))
* Rewrite README in English with Proteus docs and updated timeouts ([a99a836](https://github.com/BIDEquity/outbid-dirigent/commit/a99a836c39a4f37cb79b0ba91227c8a26eb8ac47))
