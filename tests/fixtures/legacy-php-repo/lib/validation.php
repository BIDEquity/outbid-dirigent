<?php
/**
 * Kontakt-Validierung
 *
 * Business Rules:
 * - Name: 2-100 Zeichen
 * - E-Mail: gueltig + nicht von Wegwerf-Domain
 * - Betreff: 3-200 Zeichen
 * - Nachricht: 10-5000 Zeichen
 * - Prioritaet: nur 'normal', 'hoch', 'urgent'
 */
class ContactValidator {

    public function validate(
        string $name,
        string $email,
        string $subject,
        string $message,
        string $priority
    ): array {
        $errors = [];

        // Name
        if (strlen($name) < 2) {
            $errors[] = 'Name muss mindestens 2 Zeichen lang sein.';
        }
        if (strlen($name) > 100) {
            $errors[] = 'Name darf maximal 100 Zeichen lang sein.';
        }

        // E-Mail
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            $errors[] = 'Bitte geben Sie eine gueltige E-Mail-Adresse ein.';
        } elseif ($this->isDisposableEmail($email)) {
            $errors[] = 'Wegwerf-E-Mail-Adressen sind nicht erlaubt.';
        }

        // Betreff
        if (strlen($subject) < 3) {
            $errors[] = 'Betreff muss mindestens 3 Zeichen lang sein.';
        }
        if (strlen($subject) > 200) {
            $errors[] = 'Betreff darf maximal 200 Zeichen lang sein.';
        }

        // Nachricht
        if (strlen($message) < 10) {
            $errors[] = 'Nachricht muss mindestens 10 Zeichen lang sein.';
        }
        if (strlen($message) > 5000) {
            $errors[] = 'Nachricht darf maximal 5000 Zeichen lang sein.';
        }

        // Prioritaet
        if (!in_array($priority, ['normal', 'hoch', 'urgent'])) {
            $errors[] = 'Ungueltige Prioritaet.';
        }

        return $errors;
    }

    private function isDisposableEmail(string $email): bool {
        $domain = strtolower(substr(strrchr($email, '@'), 1));
        return in_array($domain, BLOCKED_DOMAINS);
    }
}
