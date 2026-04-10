<?php
/**
 * Kontaktformular — Hauptseite
 *
 * Zeigt das Formular an und verarbeitet Submissions.
 * Business Rules:
 * - Maximal 3 Submissions pro Stunde pro IP (Rate Limiting)
 * - E-Mail-Adressen von Wegwerf-Domains werden abgelehnt
 * - Admin bekommt Benachrichtigung bei "urgent" Priority
 */

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/lib/database.php';
require_once __DIR__ . '/lib/validation.php';
require_once __DIR__ . '/lib/rate_limiter.php';
require_once __DIR__ . '/lib/mailer.php';

session_start();

$db = new Database(DB_HOST, DB_NAME, DB_USER, DB_PASS);
$rateLimiter = new RateLimiter($db);
$validator = new ContactValidator();
$mailer = new Mailer(SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS);

$errors = [];
$success = false;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = trim($_POST['name'] ?? '');
    $email = trim($_POST['email'] ?? '');
    $subject = trim($_POST['subject'] ?? '');
    $message = trim($_POST['message'] ?? '');
    $priority = $_POST['priority'] ?? 'normal';

    // Validate
    $errors = $validator->validate($name, $email, $subject, $message, $priority);

    // Rate limit check
    if (empty($errors) && !$rateLimiter->canSubmit($_SERVER['REMOTE_ADDR'])) {
        $errors[] = 'Zu viele Anfragen. Bitte warten Sie eine Stunde.';
    }

    if (empty($errors)) {
        // Save to database
        $contactId = $db->insertContact($name, $email, $subject, $message, $priority);

        // Log the submission
        $db->logAction('contact_submitted', $contactId, $_SERVER['REMOTE_ADDR']);

        // Rate limiter increment
        $rateLimiter->recordSubmission($_SERVER['REMOTE_ADDR']);

        // Notify admin for urgent messages
        if ($priority === 'urgent') {
            $mailer->sendAdminNotification($name, $email, $subject, $message);
        }

        // Send confirmation to user
        $mailer->sendConfirmation($email, $name, $contactId);

        $success = true;
        $_SESSION['flash'] = 'Nachricht erfolgreich gesendet!';
        header('Location: /danke.php?id=' . $contactId);
        exit;
    }
}
?>
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Kontakt</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <div class="container">
        <h1>Kontaktformular</h1>

        <?php if (!empty($errors)): ?>
            <div class="errors">
                <?php foreach ($errors as $error): ?>
                    <p class="error"><?= htmlspecialchars($error) ?></p>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>

        <form method="POST" action="/">
            <label>Name *</label>
            <input type="text" name="name" value="<?= htmlspecialchars($name ?? '') ?>" required>

            <label>E-Mail *</label>
            <input type="email" name="email" value="<?= htmlspecialchars($email ?? '') ?>" required>

            <label>Betreff *</label>
            <input type="text" name="subject" value="<?= htmlspecialchars($subject ?? '') ?>" required>

            <label>Prioritaet</label>
            <select name="priority">
                <option value="normal">Normal</option>
                <option value="hoch">Hoch</option>
                <option value="urgent">Dringend</option>
            </select>

            <label>Nachricht *</label>
            <textarea name="message" rows="6" required><?= htmlspecialchars($message ?? '') ?></textarea>

            <button type="submit">Absenden</button>
        </form>
    </div>
</body>
</html>
