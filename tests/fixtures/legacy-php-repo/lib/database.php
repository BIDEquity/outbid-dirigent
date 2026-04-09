<?php
/**
 * Datenbank-Klasse — PDO-Wrapper fuer MySQL
 */
class Database {
    private PDO $pdo;

    public function __construct(string $host, string $dbname, string $user, string $pass) {
        $dsn = "mysql:host={$host};dbname={$dbname};charset=utf8mb4";
        $this->pdo = new PDO($dsn, $user, $pass, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
    }

    /**
     * Kontakt in die Datenbank einfuegen.
     * Gibt die neue Contact-ID zurueck.
     */
    public function insertContact(
        string $name,
        string $email,
        string $subject,
        string $message,
        string $priority
    ): int {
        $stmt = $this->pdo->prepare(
            'INSERT INTO contacts (name, email, subject, message, priority, created_at, status)
             VALUES (:name, :email, :subject, :message, :priority, NOW(), "new")'
        );
        $stmt->execute([
            ':name' => $name,
            ':email' => $email,
            ':subject' => $subject,
            ':message' => $message,
            ':priority' => $priority,
        ]);
        return (int) $this->pdo->lastInsertId();
    }

    /**
     * Aktions-Log schreiben (fuer Audit Trail).
     */
    public function logAction(string $action, int $contactId, string $ip): void {
        $stmt = $this->pdo->prepare(
            'INSERT INTO audit_log (action, contact_id, ip_address, created_at)
             VALUES (:action, :contact_id, :ip, NOW())'
        );
        $stmt->execute([
            ':action' => $action,
            ':contact_id' => $contactId,
            ':ip' => $ip,
        ]);
    }

    /**
     * Zaehle Submissions einer IP in den letzten N Sekunden.
     */
    public function countRecentSubmissions(string $ip, int $windowSeconds): int {
        $stmt = $this->pdo->prepare(
            'SELECT COUNT(*) FROM rate_limits
             WHERE ip_address = :ip AND created_at > DATE_SUB(NOW(), INTERVAL :window SECOND)'
        );
        $stmt->execute([':ip' => $ip, ':window' => $windowSeconds]);
        return (int) $stmt->fetchColumn();
    }

    /**
     * Rate-Limit-Eintrag erstellen.
     */
    public function recordRateLimit(string $ip): void {
        $stmt = $this->pdo->prepare(
            'INSERT INTO rate_limits (ip_address, created_at) VALUES (:ip, NOW())'
        );
        $stmt->execute([':ip' => $ip]);
    }

    /**
     * Alle Kontakte abrufen (Admin-Ansicht).
     */
    public function getAllContacts(int $limit = 50, int $offset = 0): array {
        $stmt = $this->pdo->prepare(
            'SELECT * FROM contacts ORDER BY created_at DESC LIMIT :limit OFFSET :offset'
        );
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    }

    /**
     * Kontakt-Status aktualisieren (new -> read -> replied -> closed).
     * Business Rule: Status kann nur vorwaerts gehen, nie zurueck.
     */
    public function updateContactStatus(int $id, string $newStatus): bool {
        $validTransitions = [
            'new' => ['read'],
            'read' => ['replied', 'closed'],
            'replied' => ['closed'],
            'closed' => [], // Endstatus
        ];

        $stmt = $this->pdo->prepare('SELECT status FROM contacts WHERE id = :id');
        $stmt->execute([':id' => $id]);
        $current = $stmt->fetchColumn();

        if (!$current || !in_array($newStatus, $validTransitions[$current] ?? [])) {
            return false;
        }

        $stmt = $this->pdo->prepare('UPDATE contacts SET status = :status WHERE id = :id');
        $stmt->execute([':status' => $newStatus, ':id' => $id]);
        return true;
    }
}
