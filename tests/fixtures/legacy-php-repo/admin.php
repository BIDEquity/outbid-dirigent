<?php
/**
 * Admin-Ansicht — Alle Kontakte anzeigen und Status verwalten
 *
 * Business Rules:
 * - Nur eingeloggte Admins (Session-Check)
 * - Status-Uebergaenge: new -> read -> replied -> closed (nur vorwaerts)
 * - Loeschung nicht moeglich (Audit-Anforderung)
 */

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/lib/database.php';

session_start();

// Einfache Auth — in Produktion durch richtiges Auth ersetzen
if (!isset($_SESSION['admin_logged_in'])) {
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['password'])) {
        if ($_POST['password'] === getenv('ADMIN_PASSWORD') ?: 'admin123') {
            $_SESSION['admin_logged_in'] = true;
        } else {
            $loginError = 'Falsches Passwort';
        }
    }

    if (!isset($_SESSION['admin_logged_in'])) {
        ?>
        <!DOCTYPE html>
        <html lang="de">
        <head><title>Admin Login</title></head>
        <body>
            <h1>Admin Login</h1>
            <?php if (isset($loginError)): ?>
                <p style="color:red"><?= $loginError ?></p>
            <?php endif; ?>
            <form method="POST">
                <input type="password" name="password" placeholder="Passwort" required>
                <button type="submit">Login</button>
            </form>
        </body>
        </html>
        <?php
        exit;
    }
}

$db = new Database(DB_HOST, DB_NAME, DB_USER, DB_PASS);

// Status-Update verarbeiten
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['contact_id'], $_POST['new_status'])) {
    $updated = $db->updateContactStatus((int)$_POST['contact_id'], $_POST['new_status']);
    if ($updated) {
        $db->logAction('status_changed_to_' . $_POST['new_status'], (int)$_POST['contact_id'], $_SERVER['REMOTE_ADDR']);
    }
}

$contacts = $db->getAllContacts();
?>
<!DOCTYPE html>
<html lang="de">
<head><title>Admin — Kontakte</title></head>
<body>
    <h1>Kontakte (<?= count($contacts) ?>)</h1>
    <table border="1" cellpadding="5">
        <tr>
            <th>ID</th><th>Name</th><th>E-Mail</th><th>Betreff</th>
            <th>Prioritaet</th><th>Status</th><th>Datum</th><th>Aktion</th>
        </tr>
        <?php foreach ($contacts as $c): ?>
        <tr>
            <td><?= $c['id'] ?></td>
            <td><?= htmlspecialchars($c['name']) ?></td>
            <td><?= htmlspecialchars($c['email']) ?></td>
            <td><?= htmlspecialchars($c['subject']) ?></td>
            <td><?= $c['priority'] ?></td>
            <td><?= $c['status'] ?></td>
            <td><?= $c['created_at'] ?></td>
            <td>
                <?php if ($c['status'] === 'new'): ?>
                    <form method="POST" style="display:inline">
                        <input type="hidden" name="contact_id" value="<?= $c['id'] ?>">
                        <input type="hidden" name="new_status" value="read">
                        <button type="submit">Gelesen</button>
                    </form>
                <?php elseif ($c['status'] === 'read'): ?>
                    <form method="POST" style="display:inline">
                        <input type="hidden" name="contact_id" value="<?= $c['id'] ?>">
                        <input type="hidden" name="new_status" value="replied">
                        <button type="submit">Beantwortet</button>
                    </form>
                    <form method="POST" style="display:inline">
                        <input type="hidden" name="contact_id" value="<?= $c['id'] ?>">
                        <input type="hidden" name="new_status" value="closed">
                        <button type="submit">Schliessen</button>
                    </form>
                <?php elseif ($c['status'] === 'replied'): ?>
                    <form method="POST" style="display:inline">
                        <input type="hidden" name="contact_id" value="<?= $c['id'] ?>">
                        <input type="hidden" name="new_status" value="closed">
                        <button type="submit">Schliessen</button>
                    </form>
                <?php else: ?>
                    —
                <?php endif; ?>
            </td>
        </tr>
        <?php endforeach; ?>
    </table>
</body>
</html>
