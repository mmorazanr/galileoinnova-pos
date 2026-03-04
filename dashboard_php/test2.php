<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);
require_once 'config.php';

$start_date = '2026-02-01';
$end_date = date('Y-m-d');
$where_clause = "WHERE fecha >= :start_date AND fecha <= :end_date";
$params = ['start_date' => $start_date, 'end_date' => $end_date];

$sql = "SELECT * FROM restaurantes_diario_media " . $where_clause . " ORDER BY fecha DESC LIMIT 5";
echo '<p>SQL: ' . htmlspecialchars($sql) . '</p>';

try {
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $rows = $stmt->fetchAll();
    echo '<p>Rows returned: ' . count($rows) . '</p>';
    foreach ($rows as $r) {
        echo '<p>' . $r['fecha'] . ' - net_sales: ' . $r['net_sales'] . '</p>';
    }
}
catch (Exception $e) {
    echo '<p>ERROR: ' . $e->getMessage() . '</p>';
}
?>
