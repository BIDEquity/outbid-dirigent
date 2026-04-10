<?php
/**
 * Konfiguration — Datenbankverbindung und SMTP-Einstellungen
 */

define('DB_HOST', getenv('DB_HOST') ?: 'localhost');
define('DB_NAME', getenv('DB_NAME') ?: 'kontaktformular');
define('DB_USER', getenv('DB_USER') ?: 'root');
define('DB_PASS', getenv('DB_PASS') ?: '');

define('SMTP_HOST', getenv('SMTP_HOST') ?: 'localhost');
define('SMTP_PORT', (int)(getenv('SMTP_PORT') ?: 25));
define('SMTP_USER', getenv('SMTP_USER') ?: '');
define('SMTP_PASS', getenv('SMTP_PASS') ?: '');

define('ADMIN_EMAIL', getenv('ADMIN_EMAIL') ?: 'admin@example.com');

// Rate Limiting: max 3 submissions per hour per IP
define('RATE_LIMIT_MAX', 3);
define('RATE_LIMIT_WINDOW', 3600); // seconds

// Wegwerf-E-Mail-Domains die abgelehnt werden
define('BLOCKED_DOMAINS', [
    'tempmail.com', 'throwaway.email', 'guerrillamail.com',
    'mailinator.com', 'yopmail.com', '10minutemail.com',
]);
