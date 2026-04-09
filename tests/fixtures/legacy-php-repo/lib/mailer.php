<?php
/**
 * Mailer — SMTP-basierter E-Mail-Versand
 *
 * Business Rules:
 * - Bestaetigungs-Mail an User enthaelt Contact-ID als Referenz
 * - Admin-Benachrichtigung nur bei priority "urgent"
 * - Alle E-Mails werden im audit_log protokolliert
 */
class Mailer {
    private string $host;
    private int $port;
    private string $user;
    private string $pass;

    public function __construct(string $host, int $port, string $user, string $pass) {
        $this->host = $host;
        $this->port = $port;
        $this->user = $user;
        $this->pass = $pass;
    }

    public function sendConfirmation(string $toEmail, string $name, int $contactId): bool {
        $subject = "Ihre Anfrage #{$contactId} wurde empfangen";
        $body = "Hallo {$name},\n\n"
              . "Vielen Dank fuer Ihre Nachricht. Ihre Referenznummer ist #{$contactId}.\n"
              . "Wir melden uns innerhalb von 2 Werktagen.\n\n"
              . "Mit freundlichen Gruessen,\nDas Kontaktteam";

        return $this->send($toEmail, $subject, $body);
    }

    public function sendAdminNotification(
        string $fromName,
        string $fromEmail,
        string $subject,
        string $message
    ): bool {
        $adminSubject = "[URGENT] Neue Kontaktanfrage von {$fromName}";
        $body = "Dringende Kontaktanfrage:\n\n"
              . "Von: {$fromName} <{$fromEmail}>\n"
              . "Betreff: {$subject}\n\n"
              . $message;

        return $this->send(ADMIN_EMAIL, $adminSubject, $body);
    }

    private function send(string $to, string $subject, string $body): bool {
        // Vereinfachter SMTP-Versand via mail()
        $headers = "From: noreply@example.com\r\n"
                 . "Reply-To: noreply@example.com\r\n"
                 . "Content-Type: text/plain; charset=UTF-8\r\n";

        return mail($to, $subject, $body, $headers);
    }
}
