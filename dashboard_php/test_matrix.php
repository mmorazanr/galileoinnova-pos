<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

require_once 'config.php';


echo "Columnas en restaurantes_ventas:<br>";
$stmt = $pdo->prepare("SHOW COLUMNS FROM restaurantes_ventas");
$stmt->execute();
$cols = $stmt->fetchAll(PDO::FETCH_ASSOC);
foreach ($cols as $c) {
    echo $c['Field'] . " - ";
}

$start_date = '2026-03-01';
$end_date = '2026-03-04';
$restaurante_filter = 'The Lazy Donkey Restaurant';

$where_clause = "WHERE fecha >= :start_date AND fecha <= :end_date AND restaurante = :restaurante";
$params = [
    'start_date' => $start_date,
    'end_date' => $end_date,
    'restaurante' => $restaurante_filter
];

echo "<hr>Prueba Matrix:<br>";
$stmt_mp = $pdo->prepare("SELECT platillo, mesero, SUM(cantidad) as qty, SUM(monto_venta) as total_ventas FROM restaurantes_ventas " . $where_clause . " GROUP BY platillo, mesero");
if (!$stmt_mp->execute($params)) {
    print_r($stmt_mp->errorInfo());
}
$raw_items = $stmt_mp->fetchAll(PDO::FETCH_ASSOC);

echo "Raw query count: " . count($raw_items) . "<br>";
if (count($raw_items) > 0) {
    print_r($raw_items[0]);
}

$stmt_check = $pdo->prepare("SELECT COUNT(*) FROM restaurantes_ventas " . $where_clause);
$stmt_check->execute($params);
echo "<hr>Conteo total en este filtro: ";
print_r($stmt_check->fetchAll(PDO::FETCH_COLUMN));
?>
