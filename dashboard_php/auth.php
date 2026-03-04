<?php
// ── Autenticación centralizada ───────────────────────────────────────────
// Incluir en todas las páginas protegidas ANTES del HTML

session_start();

define('APP_USER', 'admin');
define('APP_PASS', 'gcode2025!'); // Cambiar según preferencia
define('APP_NAME', 'GalileoInnova Dashboard');
define('APP_BRAND', 'GalileoInnova');
define('APP_URL', 'https://galileoinnova.com');
define('APP_LOGO', 'logo_galileoinnova.jpg');

// Manejar logout
if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: login.php');
    exit;
}

// Verificar sesión
if (!isset($_SESSION['gi_auth']) || $_SESSION['gi_auth'] !== true) {
    header('Location: login.php?next=' . urlencode($_SERVER['REQUEST_URI']));
    exit;
}
?>
