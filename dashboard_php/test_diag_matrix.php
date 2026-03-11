<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

require_once 'config.php';

$start_date = isset($_GET['start_date']) ? $_GET['start_date'] : date('Y-m-01');
$end_date = isset($_GET['end_date']) ? $_GET['end_date'] : date('Y-m-d');
$restaurante_filter = 'The Lazy Donkey Restaurant';

$where_clause = "WHERE fecha >= :start_date AND fecha <= :end_date AND restaurante = :restaurante";
$params = ['start_date' => $start_date, 'end_date' => $end_date, 'restaurante' => $restaurante_filter];

$stmt_mp = $pdo->prepare("SELECT platillo, mesero, SUM(cantidad) as qty, SUM(monto_venta) as total_ventas FROM restaurantes_ventas " . $where_clause . " GROUP BY platillo, mesero LIMIT 50");
$stmt_mp->execute($params);
$raw_items = $stmt_mp->fetchAll();

echo 'TOTAL ROWS: ' . count($raw_items) . '<br>';
foreach ($raw_items as $row) {
    echo htmlspecialchars($row['platillo']) . ' | ' . htmlspecialchars($row['mesero']) . ' | ' . $row['qty'] . '<br>';
}
?>
