<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

require_once 'config.php';

echo "<h2>Conexión OK</h2>";

$stmt = $pdo->query("SELECT COUNT(*) as total FROM restaurantes_diario_media");
$row = $stmt->fetch();
echo "<p>Registros en restaurantes_diario_media: " . $row['total'] . "</p>";

$stmt = $pdo->query("SELECT restaurante, fecha, net_sales, change_in_gc_total FROM restaurantes_diario_media ORDER BY fecha DESC LIMIT 5");
$rows = $stmt->fetchAll();
echo "<pre>";
print_r($rows);
echo "</pre>";
?>
