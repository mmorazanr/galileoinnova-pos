<?php
require_once 'config.php';
try {
    $stmt = $pdo->query("TRUNCATE TABLE performance_schema.host_cache;");
    echo "SUCCESS: host_cache truncado, IP desbloqueado!";
}
catch (Exception $e) {
    echo "ERROR: " . $e->getMessage();
}
?>
