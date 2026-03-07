<?php
// ── Autenticación centralizada ───────────────────────────────────────────
// Incluir en todas las páginas protegidas ANTES del HTML

session_start();

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

// ── Helper Functions for RBAC ────────────────────────────────────────────

function is_owner()
{
    return isset($_SESSION['gi_role']) && $_SESSION['gi_role'] === 'owner';
}

function can_access_restaurant($rest_name)
{
    if (is_owner())
        return true;
    if (!isset($_SESSION['gi_allowed']) || !is_array($_SESSION['gi_allowed']))
        return false;

    // Check if the user has specific access or if "ALL" is in their allowed array
    return in_array("ALL", $_SESSION['gi_allowed']) || in_array($rest_name, $_SESSION['gi_allowed']);
}

function can_view_days()
{
    return is_owner() || (isset($_SESSION['gi_can_view']) && $_SESSION['gi_can_view']);
}

function can_delete_days() // For sync logs
{
    return is_owner() || (isset($_SESSION['gi_can_delete']) && $_SESSION['gi_can_delete']);
}

function can_delete_admin_data() // For admin_datos
{
    return is_owner() || (isset($_SESSION['gi_can_delete_admin']) && $_SESSION['gi_can_delete_admin']);
}
?>
