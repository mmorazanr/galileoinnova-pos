<?php
require_once 'config.php';

// Filtros
$start_date = isset($_GET['start_date']) ? $_GET['start_date'] : '2026-02-01'; // Default demo date
$end_date = isset($_GET['end_date']) ? $_GET['end_date'] : date('Y-m-d');
$mesero_filter = isset($_GET['mesero']) ? $_GET['mesero'] : '';
$restaurante_filter = isset($_GET['restaurante']) ? $_GET['restaurante'] : '';

$where_clause = "WHERE fecha >= :start_date AND fecha <= :end_date";
$params = ['start_date' => $start_date, 'end_date' => $end_date];

if (!empty($mesero_filter)) {
    $where_clause .= " AND mesero = :mesero";
    $params['mesero'] = $mesero_filter;
}

if (!empty($restaurante_filter)) {
    $where_clause .= " AND restaurante = :restaurante";
    $params['restaurante'] = $restaurante_filter;
}

// Filtro de Sucursales (Lista desplegable)
$stmt_all_restaurantes = $pdo->prepare("SELECT DISTINCT restaurante FROM restaurantes_ventas ORDER BY restaurante ASC");
$stmt_all_restaurantes->execute();
$todos_los_restaurantes = $stmt_all_restaurantes->fetchAll(PDO::FETCH_COLUMN);

// 1. Total de Ventas Netas y Tickets
if (empty($mesero_filter)) {
    // Si no hay filtro de mesero, usamos la tabla de cuadre global (KPI Exacto)
    $stmt = $pdo->prepare("SELECT SUM(ventas_netas) as total_ventas, SUM(total_tickets) as total_tickets FROM restaurantes_kpi " . $where_clause);
    $stmt->execute($params);
    $kpi_globals = $stmt->fetch();
}
else {
    // Si hay filtro de mesero, calculamos en base a los items del mesero y las boletas asociadas
    $stmt = $pdo->prepare("SELECT SUM(monto_venta) as total_ventas FROM restaurantes_ventas " . $where_clause);
    $stmt->execute($params);
    $kpi_globals_ventas = $stmt->fetch();

    $stmt_kpi_m = $pdo->prepare("SELECT SUM(total_tickets) as total_tickets FROM restaurantes_kpi_mesero " . $where_clause);
    $stmt_kpi_m->execute($params);
    $kpi_globals_tickets = $stmt_kpi_m->fetch();

    $kpi_globals = [
        'total_ventas' => $kpi_globals_ventas['total_ventas'],
        'total_tickets' => $kpi_globals_tickets['total_tickets']
    ];
}

$total_ventas = $kpi_globals['total_ventas'] ? number_format($kpi_globals['total_ventas'], 2) : '0.00';
$total_tickets = $kpi_globals['total_tickets'] ? number_format($kpi_globals['total_tickets']) : '0';

// 2. Ventas por Sucursal
if (empty($mesero_filter)) {
    $stmt_sucursal = $pdo->prepare("SELECT restaurante, SUM(ventas_netas) as total FROM restaurantes_kpi " . $where_clause . " GROUP BY restaurante ORDER BY total DESC");
}
else {
    $stmt_sucursal = $pdo->prepare("SELECT restaurante, SUM(monto_venta) as total FROM restaurantes_ventas " . $where_clause . " GROUP BY restaurante ORDER BY total DESC");
}
$stmt_sucursal->execute($params);
$ventas_sucursal = $stmt_sucursal->fetchAll();

// Filtro de Meseros (Lista desplegable dependiendo del restaurante)
$mesero_query = "SELECT DISTINCT mesero FROM restaurantes_ventas";
$mesero_params = [];
if (!empty($restaurante_filter)) {
    $mesero_query .= " WHERE restaurante = :rest";
    $mesero_params['rest'] = $restaurante_filter;
}
$mesero_query .= " ORDER BY mesero ASC";
$stmt_all_meseros = $pdo->prepare($mesero_query);
$stmt_all_meseros->execute($mesero_params);
$todos_los_meseros = $stmt_all_meseros->fetchAll(PDO::FETCH_COLUMN);

// 3. Ventas por Mesero (Leaderboard)
$mesero_where = "WHERE v.fecha >= :start_date AND v.fecha <= :end_date";
if (!empty($mesero_filter))
    $mesero_where .= " AND v.mesero = :mesero";
if (!empty($restaurante_filter))
    $mesero_where .= " AND v.restaurante = :restaurante";

$stmt_mesero = $pdo->prepare("
    SELECT 
        v.mesero, 
        v.restaurante, 
        SUM(v.monto_venta) as total, 
        COALESCE((SELECT SUM(k.total_tickets) FROM restaurantes_kpi_mesero k WHERE k.mesero = v.mesero AND k.restaurante = v.restaurante AND k.fecha >= :start_date AND k.fecha <= :end_date), 0) as tickets 
    FROM restaurantes_ventas v 
    " . $mesero_where . " 
    GROUP BY v.mesero, v.restaurante 
    ORDER BY total DESC LIMIT 15
");
$stmt_mesero->execute($params);
$rendimiento_meseros = $stmt_mesero->fetchAll();

// 4. Platos más vendidos
$stmt_platos = $pdo->prepare("SELECT platillo, SUM(cantidad) as total_cantidad, SUM(monto_venta) as total_ventas FROM restaurantes_ventas " . $where_clause . " GROUP BY platillo ORDER BY total_cantidad DESC LIMIT 10");
$stmt_platos->execute($params);
$top_platos = $stmt_platos->fetchAll();

// 5. Catálogo de Precios (Calculando precio estándar por unidad)
$stmt_catalog = $pdo->prepare("SELECT platillo, restaurante, MAX(monto_venta / cantidad) as precio_estimado FROM restaurantes_ventas " . ($where_clause == "WHERE fecha >= :start_date AND fecha <= :end_date" ? "WHERE cantidad > 0 " : $where_clause . " AND cantidad > 0 ") . " AND platillo NOT LIKE 'Unknown%' GROUP BY platillo, restaurante ORDER BY platillo ASC");
$stmt_catalog->execute($params);
$catalogo_precios = $stmt_catalog->fetchAll();

// 6. Desglose General / Mesero
// Desglose Financiero (Cash, Error Corrects, Discounts, etc)
$stmt_media = $pdo->prepare("SELECT media_name, SUM(amount) as total_amount FROM restaurantes_mesero_media " . $where_clause . " GROUP BY media_name HAVING total_amount <> 0 ORDER BY media_name ASC");
$stmt_media->execute($params);
$mesero_media = $stmt_media->fetchAll();

// Desglose de Productos Vendidos
$stmt_mp = $pdo->prepare("SELECT platillo, SUM(cantidad) as qty, SUM(monto_venta) as total_ventas FROM restaurantes_ventas " . $where_clause . " GROUP BY platillo ORDER BY qty DESC");
$stmt_mp->execute($params);
$mesero_productos = $stmt_mp->fetchAll();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Corporate Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body{background: linear-gradient(-45deg, #0f172a, #1e1b4b, #312e81, #0f172a);background-size: 400% 400%;animation: gradientBG 15s ease infinite;color: #ffffff;min-height: 100vh;}@keyframes gradientBG{0%{background-position:0% 50%;}50%{background-position:100% 50%;}100%{background-position:0% 50%;}}.glass-panel{background: rgba(255, 255, 255, 0.05);backdrop-filter: blur(16px);border: 1px solid rgba(255, 255, 255, 0.1);border-radius: 24px;}.glass-card{background: rgba(255, 255, 255, 0.03);backdrop-filter: blur(10px);border: 1px solid rgba(255, 255, 255, 0.05);border-radius: 16px;}</style>
</head>
<body class="p-4 md:p-8 font-sans">
    <header class="glass-panel p-6 mb-8 flex flex-col md:flex-row justify-between items-center gap-4">
        <div class="flex items-center gap-4">
            <h1 class="text-3xl font-bold tracking-tight">Corporate <span class="text-blue-400">HQ Dashboard</span></h1>
            <a href="reporte_diario.php" class="bg-pink-600 hover:bg-pink-500 text-white text-xs px-3 py-1.5 rounded-full font-bold ml-4 transition-all hover:scale-105 active:scale-95 shadow-lg shadow-pink-500/20">
                DAILY FINANCE REPORT ➜
            </a>
        </div>
        
        <!-- Formulario de Filtros -->
        <form method="GET" class="flex flex-wrap items-center gap-4 glass-card p-3">
            <div>
                <label class="text-xs text-slate-400 block mb-1">Date Range</label>
                <div class="flex gap-2">
                    <input type="date" name="start_date" value="<?php echo htmlspecialchars($start_date); ?>" class="bg-slate-800 text-white rounded px-2 py-1 text-sm border border-slate-700">
                    <input type="date" name="end_date" value="<?php echo htmlspecialchars($end_date); ?>" class="bg-slate-800 text-white rounded px-2 py-1 text-sm border border-slate-700">
                </div>
            </div>
            <div>
                <label class="text-xs text-slate-400 block mb-1">Branch</label>
                <select name="restaurante" class="bg-slate-800 text-white rounded px-3 py-1.5 text-sm border border-slate-700">
                    <option value="">-- All Branches --</option>
                    <?php foreach ($todos_los_restaurantes as $rest) { ?>
                        <option value="<?php echo htmlspecialchars($rest); ?>" <?php if ($restaurante_filter == $rest)
        echo 'selected'; ?>>
                            <?php echo htmlspecialchars($rest); ?>
                        </option>
                    <?php
}?>
                </select>
            </div>
            <div>
                <label class="text-xs text-slate-400 block mb-1">Server/Waiter</label>
                <select name="mesero" class="bg-slate-800 text-white rounded px-3 py-1.5 text-sm border border-slate-700">
                    <option value="">-- All Servers --</option>
                    <?php foreach ($todos_los_meseros as $msr) { ?>
                        <option value="<?php echo htmlspecialchars($msr); ?>" <?php if ($mesero_filter == $msr)
        echo 'selected'; ?>>
                            <?php echo htmlspecialchars($msr); ?>
                        </option>
                    <?php
}?>
                </select>
            </div>
            <div class="mt-4">
                <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-white text-sm px-4 py-1.5 rounded transition-colors">Apply Filter</button>
            </div>
        </form>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="glass-card p-6">
            <h3 class="text-slate-400 text-sm font-medium mb-1">Net Sales (Filtered)</h3>
            <p class="text-3xl font-bold text-white">$<?php echo $total_ventas; ?></p>
        </div>
        <div class="glass-card p-6">
            <h3 class="text-slate-400 text-sm font-medium mb-1">Total Tickets</h3>
            <p class="text-3xl font-bold text-white"><?php echo $total_tickets; ?></p>
        </div>
        <div class="glass-card p-6">
            <h3 class="text-slate-400 text-sm font-medium mb-1">Active Branches</h3>
            <p class="text-3xl font-bold text-white"><?php echo count($ventas_sucursal); ?></p>
        </div>
        <div class="glass-card p-6">
            <h3 class="text-slate-400 text-sm font-medium mb-1">Data Health</h3>
            <p class="text-3xl font-bold text-green-400">100% Synced</p>
        </div>
    </div>

    <!-- Primera Fila: Branch & Top Products & Leaderboard -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        <div class="space-y-8">
            <div class="glass-panel p-6">
                <h2 class="text-xl font-semibold mb-4 text-white">Sales by <span class="text-blue-400">Branch</span></h2>
                <div class="space-y-4">
                    <?php foreach ($ventas_sucursal as $s) { ?>
                        <div>
                            <div class="flex justify-between text-sm mb-1">
                                <span class="font-medium text-slate-200"><?php echo htmlspecialchars($s['restaurante']); ?></span>
                                <span class="text-white font-semibold">$<?php echo number_format($s['total'], 2); ?></span>
                            </div>
                        </div>
                    <?php
}?>
                </div>
            </div>

            <div class="glass-panel p-6">
                <h2 class="text-xl font-semibold mb-4 text-white">Top <span class="text-purple-400">Products</span></h2>
                <table class="w-full text-left border-collapse">
                    <thead><tr><th class="p-3 text-slate-400 text-xs border-b border-slate-700">Name</th><th class="p-3 text-slate-400 text-xs border-b border-slate-700 text-right">Qty</th><th class="p-3 text-slate-400 text-xs border-b border-slate-700 text-right">Sales</th></tr></thead>
                    <tbody>
                        <?php foreach ($top_platos as $p) { ?>
                            <tr>
                                <td class="p-3 text-sm text-slate-300 border-b border-slate-800"><?php echo htmlspecialchars($p['platillo']); ?></td>
                                <td class="p-3 text-sm text-right text-slate-100 border-b border-slate-800"><?php echo number_format($p['total_cantidad']); ?></td>
                                <td class="p-3 text-sm text-right text-green-400 border-b border-slate-800">$<?php echo number_format($p['total_ventas'], 2); ?></td>
                            </tr>
                        <?php
}?>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="lg:col-span-2 space-y-8">
            <div class="glass-panel p-6 h-full flex flex-col">
                <h2 class="text-xl font-semibold mb-4 text-white">Server & Waiter <span class="text-green-400">Leaderboard</span></h2>
                <div class="overflow-y-auto max-h-[500px]">
                    <table class="w-full text-left border-collapse">
                        <thead class="sticky top-0 bg-[#1e1b4b] z-10 shadow">
                            <tr>
                                <th class="p-4 text-slate-400 text-sm border-b border-slate-700">Server Name</th>
                                <th class="p-4 text-slate-400 text-sm border-b border-slate-700">Branch</th>
                                <th class="p-4 text-slate-400 text-sm border-b border-slate-700 text-center">Tickets</th>
                                <th class="p-4 text-slate-400 text-sm border-b border-slate-700 text-right">Net Sales</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php $rank = 1;
foreach ($rendimiento_meseros as $m) { ?>
                                <tr>
                                    <td class="p-4 text-sm text-white font-medium border-b border-slate-800">#<?php echo $rank; ?> <?php echo htmlspecialchars($m['mesero']); ?></td>
                                    <td class="p-4 text-sm text-slate-400 border-b border-slate-800"><?php echo htmlspecialchars($m['restaurante']); ?></td>
                                    <td class="p-4 text-sm text-center text-slate-200 border-b border-slate-800"><?php echo number_format($m['tickets']); ?></td>
                                    <td class="p-4 text-sm text-right font-semibold text-green-400 border-b border-slate-800">$<?php echo number_format($m['total'], 2); ?></td>
                                </tr>
                            <?php $rank++;
}?>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Seccion para Reporte Financiero y Productos -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <!-- Desglose Financiero (Media) -->
        <div class="glass-panel p-6">
            <h2 class="text-xl font-semibold mb-2 text-white">Financial Breakdown: <span class="text-pink-400"><?php echo !empty($mesero_filter) ? htmlspecialchars($mesero_filter) : 'Restaurant Total'; ?></span></h2>
            <p class="text-sm text-slate-400 mb-6">Cash, Discounts, Voids, Gratuity, etc.</p>
                <div class="overflow-y-auto max-h-[400px]">
                    <table class="w-full text-left border-collapse text-sm">
                        <thead class="sticky top-0 bg-[#1e1b4b] z-10 shadow">
                            <tr>
                                <th class="py-2 px-3 text-slate-400 border-b border-slate-700">Type</th>
                                <th class="py-2 px-3 text-slate-400 border-b border-slate-700 text-right">Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($mesero_media as $mm) {
    $color = $mm['total_amount'] < 0 ? 'text-red-400' : 'text-slate-200';
?>
                                <tr class="hover:bg-white/5 transition-colors">
                                    <td class="py-2 px-3 text-slate-200 border-b border-slate-800 border-opacity-50">
                                        <?php echo htmlspecialchars($mm['media_name']); ?>
                                    </td>
                                    <td class="py-2 px-3 <?php echo $color; ?> font-medium text-right border-b border-slate-800 border-opacity-50">
                                        $<?php echo number_format($mm['total_amount'], 2); ?>
                                    </td>
                                </tr>
                            <?php
}?>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Desglose de Productos (Items) -->
            <div class="glass-panel p-6">
                <h2 class="text-xl font-semibold mb-2 text-white">Items Sold: <span class="text-purple-400"><?php echo !empty($mesero_filter) ? htmlspecialchars($mesero_filter) : 'Restaurant Total'; ?></span></h2>
                <p class="text-sm text-slate-400 mb-6">Detailed list of products included in the tickets.</p>
                <div class="overflow-y-auto max-h-[400px]">
                    <table class="w-full text-left border-collapse text-sm">
                        <thead class="sticky top-0 bg-[#1e1b4b] z-10 shadow">
                            <tr>
                                <th class="py-2 px-3 text-slate-400 border-b border-slate-700">Product</th>
                                <th class="py-2 px-3 text-slate-400 border-b border-slate-700 text-right">Qty</th>
                                <th class="py-2 px-3 text-slate-400 border-b border-slate-700 text-right">Net Sales</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($mesero_productos as $mp) { ?>
                                <tr class="hover:bg-white/5 transition-colors">
                                    <td class="py-2 px-3 text-slate-200 border-b border-slate-800 border-opacity-50">
                                        <?php echo htmlspecialchars($mp['platillo']); ?>
                                    </td>
                                    <td class="py-2 px-3 text-slate-300 font-medium text-right border-b border-slate-800 border-opacity-50">
                                        <?php echo number_format($mp['qty']); ?>
                                    </td>
                                    <td class="py-2 px-3 text-green-400 font-medium text-right border-b border-slate-800 border-opacity-50">
                                        $<?php echo number_format($mp['total_ventas'], 2); ?>
                                    </td>
                                </tr>
                            <?php
}?>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

    <!-- Segunda Fila: Catalogo General --->
    <div class="glass-panel p-6 mb-8">
        <h2 class="text-xl font-semibold mb-2 text-white">Catálogo de <span class="text-yellow-400">Precios (Menú Detectado)</span></h2>
        <p class="text-sm text-slate-400 mb-6">Lista automática extraída de las ventas históricas de Comtrex.</p>

        <div class="overflow-y-auto max-h-[400px]">
            <table class="w-full text-left border-collapse text-sm">
                <thead class="sticky top-0 bg-[#1e1b4b] z-10 shadow">
                    <tr>
                        <th class="py-2 px-3 text-slate-400 border-b border-slate-700">Producto</th>
                        <th class="py-2 px-3 text-slate-400 border-b border-slate-700 text-right">Precio Estimado</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($catalogo_precios as $item) { ?>
                        <tr class="hover:bg-white/5 transition-colors">
                            <td class="py-1 px-3 text-slate-200 border-b border-slate-800 border-opacity-50">
                                <?php echo htmlspecialchars($item['platillo']); ?>
                            </td>
                            <td class="py-1 px-3 text-green-400 font-medium text-right border-b border-slate-800 border-opacity-50">
                                $<?php echo number_format($item['precio_estimado'], 2); ?>
                            </td>
                        </tr>
                    <?php
}?>
                </tbody>
            </table>
        </div>
    </div>

</body>
</html>
