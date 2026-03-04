<?php
require_once 'config.php';

// Filtros
$start_date = isset($_GET['start_date']) ? $_GET['start_date'] : '2026-02-01';
$end_date = isset($_GET['end_date']) ? $_GET['end_date'] : date('Y-m-d');
$restaurante_filter = isset($_GET['restaurante']) ? $_GET['restaurante'] : '';

$where_clause = "WHERE fecha >= :start_date AND fecha <= :end_date";
$params = ['start_date' => $start_date, 'end_date' => $end_date];

if (!empty($restaurante_filter)) {
    $where_clause .= " AND restaurante = :restaurante";
    $params['restaurante'] = $restaurante_filter;
}

// Filtro de Sucursales
$stmt_all_restaurantes = $pdo->prepare("SELECT DISTINCT restaurante FROM restaurantes_diario_media ORDER BY restaurante ASC");
$stmt_all_restaurantes->execute();
$todos_los_restaurantes = $stmt_all_restaurantes->fetchAll(PDO::FETCH_COLUMN);

// Consulta de Reporte Diario
$stmt_report = $pdo->prepare("
    SELECT * FROM restaurantes_diario_media 
    $where_clause 
    ORDER BY fecha DESC, restaurante ASC
");
$stmt_report->execute($params);
$report_rows = $stmt_report->fetchAll();

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Financial Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: #0f172a;
            color: #ffffff;
            font-family: 'Inter', sans-serif;
        }
        .glass-panel {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
        }
        table {
            border-spacing: 0;
            width: 100%;
        }
        th {
            background: #1e293b;
            position: sticky;
            top: 0;
            z-index: 10;
        }
    </style>
</head>
<body class="p-4 md:p-8">
    <header class="glass-panel p-6 mb-8 flex flex-col md:flex-row justify-between items-center gap-4">
        <div>
            <h1 class="text-3xl font-bold tracking-tight">Daily <span class="text-pink-400">Financial Report</span></h1>
            <p class="text-slate-400 text-sm mt-1 mx-1">Consolidated Audit - Comtrex Cloud Sync</p>
        </div>
        
        <div class="flex gap-4">
            <a href="index.php" class="bg-slate-700 hover:bg-slate-600 text-white text-sm px-4 py-2 rounded transition-colors flex items-center gap-2">
                <span>← Back to Dashboard</span>
            </a>
        </div>
    </header>

    <div class="glass-panel p-6 mb-8">
        <form method="GET" class="flex flex-wrap items-end gap-6">
            <div>
                <label class="text-xs text-slate-400 block mb-1">Start Date</label>
                <input type="date" name="start_date" value="<?php echo htmlspecialchars($start_date); ?>" class="bg-slate-800 text-white rounded px-3 py-2 text-sm border border-slate-700 w-full">
            </div>
            <div>
                <label class="text-xs text-slate-400 block mb-1">End Date</label>
                <input type="date" name="end_date" value="<?php echo htmlspecialchars($end_date); ?>" class="bg-slate-800 text-white rounded px-3 py-2 text-sm border border-slate-700 w-full">
            </div>
            <div class="min-w-[200px]">
                <label class="text-xs text-slate-400 block mb-1">Branch</label>
                <select name="restaurante" class="bg-slate-800 text-white rounded px-3 py-2 text-sm border border-slate-700 w-full">
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
                <button type="submit" class="bg-pink-600 hover:bg-pink-500 text-white text-sm px-6 py-2 rounded font-semibold transition-colors">Generate Report</button>
            </div>
        </form>
    </div>

    <div class="glass-panel overflow-hidden">
        <div class="overflow-x-auto">
            <table class="text-left">
                <thead>
                    <tr class="text-slate-400 text-xs uppercase tracking-wider">
                        <th class="p-4 border-b border-slate-700 text-right">Date</th>
                        <th class="p-4 border-b border-slate-700 text-right">Branch</th>
                        <th class="p-4 border-b border-slate-700 text-right text-pink-400">Net Sales</th>
                        <th class="p-4 border-b border-slate-700 text-right text-yellow-400">GC Total</th>
                        <th class="p-4 border-b border-slate-700 text-right">Cash</th>
                        <th class="p-4 border-b border-slate-700 text-right">Emp Disc</th>
                        <th class="p-4 border-b border-slate-700 text-right">Error Corr</th>
                        <th class="p-4 border-b border-slate-700 text-right">Gratuity</th>
                        <th class="p-4 border-b border-slate-700 text-right">MGR Disc</th>
                        <th class="p-4 border-b border-slate-700 text-right">MGR Void</th>
                        <th class="p-4 border-b border-slate-700 text-right">Xfer In</th>
                        <th class="p-4 border-b border-slate-700 text-right">Xfer Out</th>
                        <th class="p-4 border-b border-slate-700 text-right">Service Bal</th>
                        <th class="p-4 border-b border-slate-700 text-right">Tax 1</th>
                        <th class="p-4 border-b border-slate-700 text-right">Tips Paid</th>
                    </tr>
                </thead>
                <tbody class="text-sm divide-y divide-slate-800">
                    <?php if (empty($report_rows)) { ?>
                        <tr><td colspan="13" class="p-8 text-center text-slate-500">No data found for this period.</td></tr>
                    <?php
}
else {
    foreach ($report_rows as $row) {
?>
                        <tr class="hover:bg-white/5 transition-colors">
                            <td class="p-4 whitespace-nowrap font-medium text-slate-200"><?php echo date('M d, Y', strtotime($row['fecha'])); ?></td>
                            <td class="p-4 text-slate-400"><?php echo htmlspecialchars($row['restaurante']); ?></td>
                            <td class="p-4 text-right text-pink-400 font-bold">$<?php echo number_format($row['net_sales'], 2); ?></td>
                            <td class="p-4 text-right text-yellow-400 font-bold">$<?php echo number_format($row['change_in_gc_total'], 2); ?></td>
                            <td class="p-4 text-right text-green-400 font-medium">$<?php echo number_format($row['cash'], 2); ?></td>
                            <td class="p-4 text-right text-orange-300">$<?php echo number_format($row['employee_disc'], 2); ?></td>
                            <td class="p-4 text-right text-red-400">$<?php echo number_format($row['error_corrects'], 2); ?></td>
                            <td class="p-4 text-right text-blue-300">$<?php echo number_format($row['gratuity'], 2); ?></td>
                            <td class="p-4 text-right text-yellow-300">$<?php echo number_format($row['mgr_disc'], 2); ?></td>
                            <td class="p-4 text-right text-red-500 font-bold">$<?php echo number_format($row['mgr_void'], 2); ?></td>
                            <td class="p-4 text-right text-slate-300">$<?php echo number_format($row['sales_transfer_in'], 2); ?></td>
                            <td class="p-4 text-right text-slate-300">$<?php echo number_format($row['sales_transfer_out'], 2); ?></td>
                            <td class="p-4 text-right text-purple-300">$<?php echo number_format($row['service_balance'], 2); ?></td>
                            <td class="p-4 text-right text-teal-300">$<?php echo number_format($row['tax_1'], 2); ?></td>
                            <td class="p-4 text-right text-pink-400">$<?php echo number_format($row['tips_paid'], 2); ?></td>
                        </tr>
                    <?php
    }
}
?>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
