---
name: add-structured-logging
description: Use when asked to 'add structured logging', 'set up JSON logs', 'our logs aren't structured', or when assess flags Section 07 logging rows as failing.
---

Configure structured JSON logging for this repository.

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 07 · Observability, Monitoring & Tracking` to understand which logging-related items are currently failing.

## Instructions

1. **Detect existing structured logging library:**
   - TypeScript: look for `winston`, `pino`, or `bunyan` in `package.json`
   - Python: look for `structlog` or `loguru` in `pyproject.toml` or `requirements.txt`
   - Go: check if `log/slog` is imported anywhere (stdlib since Go 1.21), or `go.uber.org/zap`
   - Java: look for `logstash-logback-encoder` in `pom.xml` or `build.gradle`

   If a structured logger is already configured with JSON output and includes the required fields, confirm and skip to step 4.

2. **Install the idiomatic library** if none is configured:

   | Stack | Library | Install command |
   |-------|---------|-----------------|
   | TypeScript (server) | `pino` | `npm install pino` |
   | Python | `structlog` | `pip install structlog` (or add to `pyproject.toml` dependencies) |
   | Go | `log/slog` | No install — stdlib since Go 1.21 |
   | Java | `logstash-logback-encoder` | Add dependency to `pom.xml` / `build.gradle` (see step 3) |

3. **Scaffold a central logger wrapper.** All modules import this file — no direct library calls outside it:

   | Stack | Path |
   |-------|------|
   | TypeScript | `src/lib/logger.ts` |
   | Python | `app/logger.py` (or `src/<package>/logger.py`) |
   | Go | `internal/logger/logger.go` |
   | Java | `src/main/resources/logback-spring.xml` + usage via SLF4J |

   Required JSON fields per engineering-standards.md § 07:
   `timestamp` (ISO 8601) · `service` (from env `SERVICE_NAME`) · `level` · `trace_id` · `message`

   **TypeScript (`src/lib/logger.ts`):**
   ```typescript
   import pino from 'pino';

   export const logger = pino({
     base: { service: process.env.SERVICE_NAME ?? 'unknown-service' },
     timestamp: pino.stdTimeFunctions.isoTime,
     formatters: { level: (label) => ({ level: label }) },
   });

   // Usage:
   // logger.info({ trace_id: req.headers['x-trace-id'] ?? '', user_id: userId }, 'User signed in')
   // logger.error({ trace_id, err }, 'Payment failed')  — pass Error as `err`, not inside message
   ```

   **Python (`app/logger.py`):**
   ```python
   import os
   import structlog

   structlog.configure(
       processors=[
           structlog.processors.TimeStamper(fmt="iso"),
           structlog.stdlib.add_log_level,
           structlog.processors.JSONRenderer(),
       ]
   )

   logger = structlog.get_logger().bind(service=os.getenv("SERVICE_NAME", "unknown-service"))

   # Usage:
   # logger.info("user_signed_in", trace_id=trace_id, user_id=user_id)
   # logger.error("payment_failed", trace_id=trace_id, exc_info=True)
   ```

   **Go (`internal/logger/logger.go`):**
   ```go
   package logger

   import (
       "log/slog"
       "os"
   )

   var Logger = slog.New(slog.NewJSONHandler(os.Stdout, nil)).With(
       "service", getenv("SERVICE_NAME", "unknown-service"),
   )

   func getenv(key, fallback string) string {
       if v := os.Getenv(key); v != "" { return v }
       return fallback
   }

   // Usage:
   // logger.Logger.Info("user_signed_in", "trace_id", traceID, "user_id", userID)
   // logger.Logger.Error("payment_failed", "trace_id", traceID, "err", err)
   ```

   **Java — add to `pom.xml`:**
   ```xml
   <dependency>
     <groupId>net.logstash.logback</groupId>
     <artifactId>logstash-logback-encoder</artifactId>
     <version>7.4</version>
   </dependency>
   ```
   **Create `src/main/resources/logback-spring.xml`:**
   ```xml
   <configuration>
     <appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
       <encoder class="net.logstash.logback.encoder.LogstashEncoder">
         <customFields>{"service":"${SERVICE_NAME:-unknown-service}"}</customFields>
       </encoder>
     </appender>
     <root level="INFO"><appender-ref ref="JSON"/></root>
   </configuration>
   ```
   Usage: standard SLF4J — `LoggerFactory.getLogger(MyClass.class)` with MDC for `trace_id`.

4. **Trace ID propagation note.** Add a comment to the wrapper explaining:
   - `trace_id` must be extracted from the inbound request header (`X-Trace-Id` or `traceparent`)
   - It must be stored in request-scoped context and passed to every log call in that request
   - For Go: use `context.Context`. For TS/Python: use AsyncLocalStorage or contextvars respectively.

5. **Remind the user:**
   - Set `SERVICE_NAME` environment variable to the service's canonical name
   - In development, pipe output through `pino-pretty` (TS) or structlog's dev renderer (Python) for readability

## Update the status file

After configuring structured logging, update `harness-docs/standards-status.md`:

1. Find the section heading `## 07 · Observability, Monitoring & Tracking`.
2. For each row below, update Status to `✅ PASS`, Verified to today's date, Fixed By to `/add-structured-logging`, Notes to the library and wrapper path:
   - Row matching "Use structured logging throughout"
   - Row matching "Emit logs in JSON format with consistent fields"
3. Recalculate the MUST ✅ and MUST ❌ totals in the Summary table for the `07 · Observability, Monitoring & Tracking` row.
