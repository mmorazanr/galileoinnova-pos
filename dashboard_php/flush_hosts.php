<?php
$host = 'localhost';
$user = 'recetas';
$pass = 'gcode2025!';

try {
    $pdo = new PDO("mysql:host=$host", $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->exec('FLUSH HOSTS;');
    echo "SUCCESS: Hosts flushed.";
}
catch (PDOException $e) {
    echo "ERROR: " . $e->getMessage();
}
?>
