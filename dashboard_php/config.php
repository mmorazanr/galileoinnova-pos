<?php
// Configuración de la base de datos corporativa (MariaDB Central)
define('DB_HOST', 'hawk200.startdedicated.com');
define('DB_NAME', 'Recetas');
define('DB_USER', 'recetas');
define('DB_PASS', 'gcode2025!');

try {
    $pdo = new PDO("mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8", DB_USER, DB_PASS);
    // Configurar el PDO para que lance excepciones en caso de error
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
} catch (PDOException $e) {
    die("<h1>No se pudo conectar a la base de datos centralizada.</h1><p>Error: " . $e->getMessage() . "</p>");
}
?>
