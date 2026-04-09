<?php
/**
 * Rate Limiter — max N Submissions pro Zeitfenster pro IP
 */
class RateLimiter {
    private Database $db;

    public function __construct(Database $db) {
        $this->db = $db;
    }

    public function canSubmit(string $ip): bool {
        $count = $this->db->countRecentSubmissions($ip, RATE_LIMIT_WINDOW);
        return $count < RATE_LIMIT_MAX;
    }

    public function recordSubmission(string $ip): void {
        $this->db->recordRateLimit($ip);
    }
}
