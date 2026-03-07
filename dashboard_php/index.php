<?php
require_once 'auth.php';
require_once 'config.php';

// ── Endpoint AJAX: lista de meseros por restaurante ─────────────────────
if (isset($_GET['meseros_ajax'])) {
    $rest_ajax = $_GET['restaurante'] ?? '';
    $q = "SELECT DISTINCT mesero FROM restaurantes_ventas";
    $p = [];
    if ($rest_ajax && can_access_restaurant($rest_ajax)) {
        $q .= " WHERE restaurante = :rest";
        $p['rest'] = $rest_ajax;
    } elseif (!is_owner()) {
        $allowed = $_SESSION['gi_allowed'] ?? [];
        if (empty($allowed)) {
            $q .= " WHERE 1=0";
        } elseif (!in_array('ALL', $allowed)) {
            $inStrs = [];
            foreach($allowed as $i => $ar) {
                $pname = "ajax_rest_$i";
                $inStrs[] = ":$pname";
                $p[$pname] = $ar;
            }
            $q .= " WHERE restaurante IN (" . implode(',', $inStrs) . ")";
        }
    }
    $q .= " ORDER BY mesero ASC";
    $s = $pdo->prepare($q);
    $s->execute($p);
    header('Content-Type: application/json');
    echo json_encode($s->fetchAll(PDO::FETCH_COLUMN));
    exit;
}


// Filtros
$start_date = isset($_GET['start_date']) ? $_GET['start_date'] : date('Y-m-01');
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
$todos_los_restaurantes_raw = $stmt_all_restaurantes->fetchAll(PDO::FETCH_COLUMN);
$todos_los_restaurantes = array_filter($todos_los_restaurantes_raw, 'can_access_restaurant');

// RBAC Global Params
$rbac_clause = "";
$rbac_v_clause = "";
$rbac_params = [];
if (!is_owner() && !in_array("ALL", $_SESSION['gi_allowed'] ?? [])) {
    $allowed = $_SESSION['gi_allowed'] ?? [];
    if (empty($allowed)) {
        $rbac_clause = " AND 1=0 ";
        $rbac_v_clause = " AND 1=0 ";
    } else {
        $inStrs = [];
        foreach($allowed as $i => $ar) {
            $pname = "rbac_rest_$i";
            $inStrs[] = ":$pname";
            $rbac_params[$pname] = $ar;
        }
        $rbac_clause = " AND restaurante IN (" . implode(',', $inStrs) . ") ";
        $rbac_v_clause = " AND v.restaurante IN (" . implode(',', $inStrs) . ") ";
    }
}

// Ensure the chosen filter is valid for this user
if (!empty($restaurante_filter) && !can_access_restaurant($restaurante_filter)) {
    $restaurante_filter = ''; 
    $where_clause = "WHERE fecha >= :start_date AND fecha <= :end_date";
    if (!empty($mesero_filter)) {
        $where_clause .= " AND mesero = :mesero";
    }
}

$where_clause .= $rbac_clause;
$params = array_merge($params, $rbac_params);

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
$mesero_query = "SELECT DISTINCT mesero FROM restaurantes_ventas WHERE 1=1 " . $rbac_clause;
$mesero_params = $rbac_params;
if (!empty($restaurante_filter)) {
    $mesero_query .= " AND restaurante = :rest";
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
$mesero_where .= $rbac_v_clause;

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
$top_where = "WHERE fecha >= :start_date AND fecha <= :end_date" . $rbac_clause;
$top_params = array_merge(['start_date' => $start_date, 'end_date' => $end_date], $rbac_params);
if (!empty($restaurante_filter)) {
    $top_where .= " AND restaurante = :restaurante";
    $top_params['restaurante'] = $restaurante_filter;
}
$stmt_platos = $pdo->prepare("SELECT platillo, SUM(cantidad) as total_cantidad, SUM(monto_venta) as total_ventas FROM restaurantes_ventas " . $top_where . " GROUP BY platillo ORDER BY total_ventas DESC");
$stmt_platos->execute($top_params);
$top_platos = $stmt_platos->fetchAll();

// 5. Catálogo de Precios — filtrado por restaurante seleccionado
$catalog_where = "WHERE cantidad > 0 AND platillo NOT LIKE 'Unknown%'" . $rbac_clause;
$catalog_params = $rbac_params;
if (!empty($restaurante_filter)) {
    $catalog_where .= " AND restaurante = :rest";
    $catalog_params['rest'] = $restaurante_filter;
}
if (!empty($start_date)) {
    $catalog_where .= " AND fecha >= :start_date2";
    $catalog_params['start_date2'] = $start_date;
}
if (!empty($end_date)) {
    $catalog_where .= " AND fecha <= :end_date2";
    $catalog_params['end_date2'] = $end_date;
}
$stmt_catalog = $pdo->prepare(
    "SELECT platillo, restaurante, MAX(monto_venta / cantidad) as precio_estimado "
    . "FROM restaurantes_ventas " . $catalog_where
    . " GROUP BY platillo, restaurante ORDER BY platillo ASC"
);
$stmt_catalog->execute($catalog_params);
$catalogo_precios = $stmt_catalog->fetchAll();

// 6. Desglose General / Mesero
// Desglose Financiero (Cash, Error Corrects, Discounts, etc)
$stmt_media = $pdo->prepare("SELECT media_name, SUM(amount) as total_amount FROM restaurantes_mesero_media " . $where_clause . " GROUP BY media_name HAVING total_amount <> 0 ORDER BY media_name ASC");
$stmt_media->execute($params);
$mesero_media = $stmt_media->fetchAll();

// 7. Desglose de Productos Vendidos (Items Sold MATRIX)
$stmt_mp = $pdo->prepare("SELECT platillo, mesero, SUM(cantidad) as qty, SUM(monto_venta) as total_ventas FROM restaurantes_ventas " . $where_clause . " GROUP BY platillo, mesero");
$stmt_mp->execute($params);
$raw_items = $stmt_mp->fetchAll();

$waiters_set = [];
$pivot_data = [];

foreach ($raw_items as $row) {
    if (empty($row['platillo'])) continue;
    $p = $row['platillo'];
    $m = empty($row['mesero']) ? 'Unknown' : $row['mesero'];
    
    $waiters_set[$m] = true;
    
    if (!isset($pivot_data[$p])) {
        $pivot_data[$p] = [
            'platillo' => $p,
            'waiters'  => [],
            'tot_qty'  => 0,
            'tot_val'  => 0.0
        ];
    }
    
    $qty = (int)$row['qty'];
    $val = (float)$row['total_ventas'];
    
    $pivot_data[$p]['waiters'][$m] = $qty;
    $pivot_data[$p]['tot_qty'] += $qty;
    $pivot_data[$p]['tot_val'] += $val;
}

$waiter_cols = array_keys($waiters_set);
sort($waiter_cols);

usort($pivot_data, function($a, $b) {
    return $b['tot_val'] <=> $a['tot_val'];
});
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard · GalileoInnova</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body{background: linear-gradient(-45deg, #0f172a, #1e1b4b, #312e81, #0f172a);background-size: 400% 400%;animation: gradientBG 15s ease infinite;color: #ffffff;min-height: 100vh;}@keyframes gradientBG{0%{background-position:0% 50%;}50%{background-position:100% 50%;}100%{background-position:0% 50%;}}.glass-panel{background: rgba(255, 255, 255, 0.05);backdrop-filter: blur(16px);border: 1px solid rgba(255, 255, 255, 0.1);border-radius: 24px;}.glass-card{background: rgba(255, 255, 255, 0.03);backdrop-filter: blur(10px);border: 1px solid rgba(255, 255, 255, 0.05);border-radius: 16px;}</style>
</head>
<body class="font-sans">
<?php require_once 'navbar.php'; ?>
<div class="p-4 md:p-8">
    <!-- Formulario de Filtros -->
    <div class="glass-panel p-4 mb-8">
    <form method="GET" class="flex flex-wrap items-center gap-4">
            <div>
                <label class="text-xs text-slate-400 block mb-1">Date Range</label>
                <div class="flex gap-2">
                    <input type="date" name="start_date" value="<?php echo htmlspecialchars($start_date); ?>" class="bg-slate-800 text-white rounded px-2 py-1 text-sm border border-slate-700">
                    <input type="date" name="end_date" value="<?php echo htmlspecialchars($end_date); ?>" class="bg-slate-800 text-white rounded px-2 py-1 text-sm border border-slate-700">
                </div>
            </div>
            <div>
                <label class="text-xs text-slate-400 block mb-1">Branch</label>
                <select id="sel_restaurante" name="restaurante" class="bg-slate-800 text-white rounded px-3 py-1.5 text-sm border border-slate-700" onchange="actualizarMeseros(this.value)">
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
                <select id="sel_mesero" name="mesero" class="bg-slate-800 text-white rounded px-3 py-1.5 text-sm border border-slate-700">
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
    </div>

    <!-- Script: actualizar meseros sin recargar -->
    <script>
    // Meseros pre-cargados desde PHP (para el restaurante actual)
    const meserosActuales = <?php echo json_encode($todos_los_meseros); ?>;
    const meserosCache    = {};
    const meserosSeleccionado = <?php echo json_encode($mesero_filter); ?>;

    async function actualizarMeseros(restaurante) {
        const sel = document.getElementById('sel_mesero');
        sel.innerHTML = '<option value="">-- All Servers --</option>';

        if (!restaurante) {
            // Todos los restaurantes: mostrar todos
            meserosActuales.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m; opt.textContent = m;
                sel.appendChild(opt);
            });
            return;
        }

        if (meserosCache[restaurante]) {
            meserosCache[restaurante].forEach(m => {
                const opt = document.createElement('option'); opt.value = m; opt.textContent = m; sel.appendChild(opt);
            });
            return;
        }

        try {
            // Reutilizamos el mismo PHP pasando el restaurante por GET
            const url = `?meseros_ajax=1&restaurante=${encodeURIComponent(restaurante)}`;
            const resp = await fetch(url);
            const data = await resp.json();
            meserosCache[restaurante] = data;
            data.forEach(m => {
                const opt = document.createElement('option'); opt.value = m; opt.textContent = m; sel.appendChild(opt);
            });
        } catch(e) { console.error('Error cargando meseros', e); }
    }
    </script>

    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-8">
        <div class="glass-card p-6 h-full">
            <h3 class="text-slate-400 text-sm font-medium mb-1">Net Sales (Filtered)</h3>
            <p class="text-3xl font-bold text-white">$<?php echo $total_ventas; ?></p>
        </div>
        <div class="glass-card p-6 h-full">
            <h3 class="text-slate-400 text-sm font-medium mb-1">Total Tickets</h3>
            <p class="text-3xl font-bold text-white"><?php echo $total_tickets; ?></p>
        </div>
        <div class="glass-card p-6 h-full">
            <h3 class="text-slate-400 text-sm font-medium mb-1">Active Branches</h3>
            <p class="text-3xl font-bold text-white"><?php echo count($ventas_sucursal); ?></p>
        </div>
        <div class="glass-card p-6 h-full">
            <h3 class="text-slate-400 text-sm font-medium mb-1">Data Health</h3>
            <p class="text-3xl font-bold text-green-400">100% Synced</p>
        </div>
        <div class="glass-card p-6 h-full overflow-y-auto max-h-[120px]">
            <h3 class="text-slate-400 text-sm font-medium mb-2">Sales by Branch</h3>
            <div class="space-y-2">
                <?php foreach ($ventas_sucursal as $s) { ?>
                    <div class="flex justify-between text-sm">
                        <span class="font-medium text-slate-200"><?php echo htmlspecialchars($s['restaurante']); ?></span>
                        <span class="text-white font-semibold">$<?php echo number_format($s['total'], 2); ?></span>
                    </div>
                <?php
}?>
            </div>
        </div>
    </div>

    <!-- Segunda Fila: Top Products & Leaderboard -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div class="glass-panel p-6 h-full flex flex-col">
            <h2 class="text-xl font-semibold mb-4 text-white">Top <span class="text-purple-400">Products</span></h2>
            <div class="overflow-y-auto flex-1 max-h-[500px] pr-2">
                <table class="w-full text-left border-collapse">
                    <thead class="sticky top-0 bg-[#1e1b4b] z-10 shadow"><tr><th class="px-2 py-1 text-slate-400 text-xs border-b border-slate-700">Name</th><th class="px-2 py-1 text-slate-400 text-xs border-b border-slate-700 text-right">Qty</th><th class="px-2 py-1 text-slate-400 text-xs border-b border-slate-700 text-right">Sales</th></tr></thead>
                <tbody>
                    <?php foreach ($top_platos as $p) { ?>
                        <tr>
                            <td class="px-2 py-1 text-sm text-slate-300 border-b border-slate-800"><?php echo htmlspecialchars($p['platillo']); ?></td>
                            <td class="px-2 py-1 text-sm text-right text-slate-100 border-b border-slate-800"><?php echo number_format($p['total_cantidad']); ?></td>
                            <td class="px-2 py-1 text-sm text-right text-green-400 border-b border-slate-800">$<?php echo number_format($p['total_ventas'], 2); ?></td>
                        </tr>
                    <?php
}?>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="glass-panel p-6 h-full flex flex-col">
            <h2 class="text-xl font-semibold mb-4 text-white">Server & Waiter <span class="text-green-400">Leaderboard</span></h2>
                <div class="overflow-y-auto max-h-[500px]">
                    <table class="w-full text-left border-collapse">
                        <thead class="sticky top-0 bg-[#1e1b4b] z-10 shadow">
                            <tr>
                                <th class="px-2 py-1 text-slate-400 text-xs border-b border-slate-700">Server Name</th>
                                <th class="px-2 py-1 text-slate-400 text-xs border-b border-slate-700">Branch</th>
                                <th class="px-2 py-1 text-slate-400 text-xs border-b border-slate-700 text-center">Tickets</th>
                                <th class="px-2 py-1 text-slate-400 text-xs border-b border-slate-700 text-right">Net Sales</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php $rank = 1;
foreach ($rendimiento_meseros as $m) { ?>
                                <tr>
                                    <td class="px-2 py-1 text-xs text-white font-medium border-b border-slate-800">#<?php echo $rank; ?> <?php echo htmlspecialchars($m['mesero']); ?></td>
                                    <td class="px-2 py-1 text-xs text-slate-400 border-b border-slate-800"><?php echo htmlspecialchars($m['restaurante']); ?></td>
                                    <td class="px-2 py-1 text-xs text-center text-slate-200 border-b border-slate-800"><?php echo number_format($m['tickets']); ?></td>
                                    <td class="px-2 py-1 text-xs text-right font-semibold text-green-400 border-b border-slate-800">$<?php echo number_format($m['total'], 2); ?></td>
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
                                <th class="py-1 px-2 text-slate-400 text-xs border-b border-slate-700">Type</th>
                                <th class="py-1 px-2 text-slate-400 text-xs border-b border-slate-700 text-right">Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($mesero_media as $mm) {
    $color = $mm['total_amount'] < 0 ? 'text-red-400' : 'text-slate-200';
?>
                                <tr class="hover:bg-white/5 transition-colors">
                                    <td class="py-1 px-2 text-xs border-b border-slate-800 border-opacity-50">
                                        <?php echo htmlspecialchars($mm['media_name']); ?>
                                    </td>
                                    <td class="py-1 px-2 <?php echo $color; ?> font-medium text-right border-b border-slate-800 border-opacity-50">
                                        $<?php echo number_format($mm['total_amount'], 2); ?>
                                    </td>
                                </tr>
                            <?php
}?>
                        </tbody>
                    </table>
                </div>
        </div>
    </div>
    
    <!-- Matriz de Productos (Items Sold MATRIX) -->
    <div class="glass-panel p-6 mb-8">
        <div class="flex flex-wrap justify-between items-center mb-6 gap-4">
            <div>
                <h2 class="text-xl font-semibold mb-2 text-white">Items Sold: <span class="text-purple-400"><?php echo !empty($mesero_filter) ? htmlspecialchars($mesero_filter) : 'Restaurant Total'; ?></span></h2>
                <p class="text-sm text-slate-400">Detailed matrix list of products showing quantity sold per waiter.</p>
            </div>
            <button onclick="exportMatrixToExcel()" class="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium py-2 px-4 rounded shadow transition-colors flex items-center">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                Export to Excel
            </button>
        </div>
        
        <div class="overflow-auto max-h-[500px]">
            <table class="w-full text-left border-collapse text-sm whitespace-nowrap" id="itemsSoldMatrix">
                <thead class="sticky top-0 bg-[#1e1b4b] z-10 shadow">
                    <tr>
                        <th class="py-1 px-2 text-slate-200 text-xs font-bold border-b border-slate-700 bg-[#1e1b4b] sticky left-0 z-20">Product</th>
                        <?php foreach ($waiter_cols as $w): ?>
                            <th class="py-1 px-2 text-slate-400 text-xs border-b border-slate-700 text-center"><?php echo htmlspecialchars($w); ?></th>
                        <?php
endforeach; ?>
                        <th class="py-1 px-2 text-slate-200 text-xs font-bold border-b border-slate-700 text-right bg-[#1e1b4b] sticky right-0 z-20 border-l border-slate-700">Qty</th>
                        <th class="py-1 px-2 text-green-400 text-xs font-bold border-b border-slate-700 text-right bg-[#1e1b4b] sticky right-0 z-20">Net Sales</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($pivot_data)): ?>
                        <tr><td colspan="<?php echo count($waiter_cols) + 3; ?>" class="py-4 text-center text-slate-500">Sin datos para los filtros seleccionados</td></tr>
                    <?php
else: ?>
                        <?php foreach ($pivot_data as $row): ?>
                            <tr class="hover:bg-white/5 transition-colors">
                                <td class="py-1 px-2 text-xs text-slate-200 border-b border-slate-800 border-opacity-50 font-medium sticky left-0 bg-[#0f172a] group-hover:bg-[#1a2235]">
                                    <?php echo htmlspecialchars($row['platillo']); ?>
                                </td>
                                
                                <?php foreach ($waiter_cols as $w):
            $qty = isset($row['waiters'][$w]) ? $row['waiters'][$w] : 0;
?>
                                    <td class="py-1 px-2 text-xs text-slate-400 text-center border-b border-slate-800 border-opacity-50">
                                        <?php echo $qty > 0 ? htmlspecialchars($qty) : ''; ?>
                                    </td>
                                <?php
        endforeach; ?>
                                
                                <td class="py-1 px-2 text-xs text-slate-100 font-semibold text-right border-b border-slate-800 border-opacity-50 sticky right-0 bg-[#0f172a] border-l border-slate-700">
                                    <?php echo htmlspecialchars($row['tot_qty']); ?>
                                </td>
                                <td class="py-1 px-2 text-xs text-green-400 font-bold text-right border-b border-slate-800 border-opacity-50 sticky right-0 bg-[#0f172a]">
                                    $<?php echo number_format($row['tot_val'], 2); ?>
                                </td>
                            </tr>
                        <?php
    endforeach; ?>
                    <?php
endif; ?>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Catálogo de Precios: grid 3 columnas -->
    <div class="glass-panel p-6 mb-8">
        <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div>
                <h2 class="text-xl font-semibold text-white">Catálogo de <span class="text-yellow-400">Precios (Menú Detectado)</span></h2>
                <p class="text-sm text-slate-400 mt-1">
                    <?php echo count($catalogo_precios); ?> productos
                    <?php if ($restaurante_filter): ?>
                        &mdash; <span class="text-yellow-300"><?php echo htmlspecialchars($restaurante_filter); ?></span>
                    <?php
else: ?>
                        &mdash; <span class="text-slate-500">Todas las sucursales</span>
                    <?php
endif; ?>
                </p>
            </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-x-6 gap-y-0 max-h-[480px] overflow-y-auto pr-1">
            <?php
$prev_letter = '';
foreach ($catalogo_precios as $item):
    $first = strtoupper($item['platillo'][0] ?? '#');
    if ($first !== $prev_letter):
        $prev_letter = $first;
    endif;
    $precio = round(floatval($item['precio_estimado']), 2);
?>
            <div class="flex items-center justify-between py-1.5 border-b border-slate-800/60 group hover:bg-white/3 transition-colors rounded px-1">
                <span class="text-slate-200 text-xs truncate mr-2 group-hover:text-white" title="<?php echo htmlspecialchars($item['platillo']); ?>">
                    <?php echo htmlspecialchars($item['platillo']); ?>
                </span>
                <span class="text-green-400 font-semibold text-xs whitespace-nowrap">
                    $<?php echo number_format($precio, 2); ?>
                </span>
            </div>
            <?php
endforeach; ?>
        </div>
    </div>

</div><!-- /p-4 md:p-8 -->

<footer class="gi-footer">
  &copy; <?php echo date('Y'); ?> <a href="https://galileoinnova.com" target="_blank">GalileoInnova</a> &middot; Restaurant Intelligence Suite &middot; All rights reserved.
</footer>

<script>
function exportMatrixToExcel() {
    let table = document.getElementById("itemsSoldMatrix");
    let rows = table.querySelectorAll("tr");
    let csv = [];
    
    for (let i = 0; i < rows.length; i++) {
        let row = [], cols = rows[i].querySelectorAll("td, th");
        
        for (let j = 0; j < cols.length; j++) {
            let data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, "").trim();
            // Evitamos que Excel rompa las comas internamente al parsear
            data = data.replace(/"/g, '""');
            row.push('"' + data + '"');
        }
        csv.push(row.join(","));
    }

    let csvFile = new Blob(["\uFEFF" + csv.join("\n")], { type: "text/csv;charset=utf-8;" });
    let downloadLink = document.createElement("a");
    downloadLink.download = "items_sold_matrix.csv";
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = "none";
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}
</script>

</body>
</html>
