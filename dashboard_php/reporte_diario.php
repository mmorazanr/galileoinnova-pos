<?php
require_once 'auth.php';
require_once 'config.php';

$start_date = isset($_GET['start_date']) ? $_GET['start_date'] : date('Y-m-01');
$end_date = isset($_GET['end_date']) ? $_GET['end_date'] : date('Y-m-d');
$restaurante_filter = isset($_GET['restaurante']) ? $_GET['restaurante'] : '';

$where_clause = "WHERE fecha >= :start_date AND fecha <= :end_date";
$params = ['start_date' => $start_date, 'end_date' => $end_date];

if (!empty($restaurante_filter)) {
    $where_clause .= " AND restaurante = :restaurante";
    $params['restaurante'] = $restaurante_filter;
}

$stmt_all = $pdo->prepare("SELECT DISTINCT restaurante FROM restaurantes_diario_media ORDER BY restaurante ASC");
$stmt_all->execute();
$todos_los_restaurantes = $stmt_all->fetchAll(PDO::FETCH_COLUMN);

$sql = "SELECT * FROM restaurantes_diario_media " . $where_clause . " ORDER BY fecha DESC, restaurante ASC";
$stmt_report = $pdo->prepare($sql);
$stmt_report->execute($params);
$report_rows = $stmt_report->fetchAll();

$days_es = ['Sunday' => 'Domingo', 'Monday' => 'Lunes', 'Tuesday' => 'Martes',
    'Wednesday' => 'Miércoles', 'Thursday' => 'Jueves', 'Friday' => 'Viernes', 'Saturday' => 'Sábado'];
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Report · GalileoInnova</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- SheetJS for Excel export -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
    <style>
        body { background: #0f172a; color: #fff; font-family: 'Inter', sans-serif; }
        .glass-panel {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
        }
        th {
            background: #1e293b;
            position: sticky;
            top: 0;
            z-index: 10;
            user-select: none;
            cursor: pointer;
            transition: background 0.15s;
        }
        th:hover { background: #273549; }
        th.sort-asc::after  { content: ' ↑'; color: #f472b6; font-size: 10px; }
        th.sort-desc::after { content: ' ↓'; color: #f472b6; font-size: 10px; }
        tr.data-row:hover { background: rgba(255,255,255,0.04); }
        .badge-day {
            display: inline-block;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 999px;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .day-Lunes     { background:#1e3a5f; color:#60a5fa; }
        .day-Martes    { background:#3b1f5e; color:#c084fc; }
        .day-Miércoles { background:#1f3b2e; color:#4ade80; }
        .day-Jueves    { background:#3b2e1f; color:#fb923c; }
        .day-Viernes   { background:#1f2e3b; color:#38bdf8; }
        .day-Sábado    { background:#3b1f2e; color:#f472b6; }
        .day-Domingo   { background:#3b1f1f; color:#f87171; }
    </style>
</head>
<body class="p-4 md:p-8">
<?php require_once 'navbar.php'; ?>


<!-- Header -->
<header class="glass-panel p-5 mb-6 flex flex-col md:flex-row justify-between items-center gap-4">
    <div>
        <h1 class="text-3xl font-bold tracking-tight">Daily <span class="text-pink-400">Financial Report</span></h1>
        <p class="text-slate-400 text-sm mt-1">Consolidated Audit &middot; <a href="https://galileoinnova.com" class="text-blue-400" target="_blank">GalileoInnova</a></p>
    </div>
    <div class="flex gap-3 flex-wrap justify-center">
        <button onclick="exportToExcel()" class="bg-emerald-600 hover:bg-emerald-500 text-white text-sm px-5 py-2 rounded-lg font-semibold transition-colors flex items-center gap-2">
            ⬇ Export Excel
        </button>
    </div>
</header>

<!-- Filters -->
<div class="glass-panel p-5 mb-6">
    <form method="GET" class="flex flex-wrap items-end gap-5">
        <div>
            <label class="text-xs text-slate-400 block mb-1">Start Date</label>
            <input type="date" name="start_date" value="<?php echo htmlspecialchars($start_date); ?>"
                   class="bg-slate-800 text-white rounded-lg px-3 py-2 text-sm border border-slate-700">
        </div>
        <div>
            <label class="text-xs text-slate-400 block mb-1">End Date</label>
            <input type="date" name="end_date" value="<?php echo htmlspecialchars($end_date); ?>"
                   class="bg-slate-800 text-white rounded-lg px-3 py-2 text-sm border border-slate-700">
        </div>
        <div>
            <label class="text-xs text-slate-400 block mb-1">Branch</label>
            <select name="restaurante" class="bg-slate-800 text-white rounded-lg px-3 py-2 text-sm border border-slate-700">
                <option value="">-- All Branches --</option>
                <?php foreach ($todos_los_restaurantes as $r): ?>
                    <option value="<?php echo htmlspecialchars($r); ?>" <?php if ($restaurante_filter == $r)
        echo 'selected'; ?>>
                        <?php echo htmlspecialchars($r); ?>
                    </option>
                <?php
endforeach; ?>
            </select>
        </div>
        <button type="submit" class="bg-pink-600 hover:bg-pink-500 text-white text-sm px-6 py-2 rounded-lg font-semibold transition-colors">
            Generate Report
        </button>
    </form>
</div>

<!-- Table -->
<div class="glass-panel overflow-hidden">
    <div class="overflow-x-auto">
        <table id="reportTable" class="text-left w-full text-sm">
            <thead>
                <tr class="text-slate-400 text-xs uppercase tracking-wider">
                    <th class="p-3 border-b border-slate-700" onclick="sortTable(0)" data-type="text">Day</th>
                    <th class="p-3 border-b border-slate-700" onclick="sortTable(1)" data-type="date">Date</th>
                    <th class="p-3 border-b border-slate-700" onclick="sortTable(2)" data-type="text">Branch</th>
                    <th class="p-3 border-b border-slate-700 text-right text-pink-400" onclick="sortTable(3)" data-type="num">Net Sales</th>
                    <th class="p-3 border-b border-slate-700 text-right text-yellow-400" onclick="sortTable(4)" data-type="num">GC Total</th>
                    <th class="p-3 border-b border-slate-700 text-right" onclick="sortTable(5)" data-type="num">Cash</th>
                    <th class="p-3 border-b border-slate-700 text-right" onclick="sortTable(6)" data-type="num">Emp Disc</th>
                    <th class="p-3 border-b border-slate-700 text-right" onclick="sortTable(7)" data-type="num">Error Corr</th>
                    <th class="p-3 border-b border-slate-700 text-right" onclick="sortTable(8)" data-type="num">Gratuity</th>
                    <th class="p-3 border-b border-slate-700 text-right" onclick="sortTable(9)" data-type="num">MGR Disc</th>
                    <th class="p-3 border-b border-slate-700 text-right" onclick="sortTable(10)" data-type="num">MGR Void</th>
                    <th class="p-3 border-b border-slate-700 text-right" onclick="sortTable(11)" data-type="num">Xfer In</th>
                    <th class="p-3 border-b border-slate-700 text-right" onclick="sortTable(12)" data-type="num">Xfer Out</th>
                    <th class="p-3 border-b border-slate-700 text-right" onclick="sortTable(13)" data-type="num">Service Bal</th>
                    <th class="p-3 border-b border-slate-700 text-right" onclick="sortTable(14)" data-type="num">Tax 1</th>
                    <th class="p-3 border-b border-slate-700 text-right" onclick="sortTable(15)" data-type="num">Tips Paid</th>
                </tr>
            </thead>
            <tbody id="reportBody" class="divide-y divide-slate-800">
                <?php if (empty($report_rows)): ?>
                    <tr><td colspan="16" class="p-8 text-center text-slate-500">No data found for this period.</td></tr>
                <?php
else: ?>
                    <?php foreach ($report_rows as $row):
        $day_name_en = date('l', strtotime($row['fecha']));
        $day_name = $days_es[$day_name_en] ?? $day_name_en;
?>
                    <tr class="data-row" data-fecha="<?php echo $row['fecha']; ?>">
                        <td class="p-3 whitespace-nowrap">
                            <span class="badge-day day-<?php echo $day_name; ?>"><?php echo $day_name; ?></span>
                        </td>
                        <td class="p-3 whitespace-nowrap font-medium text-slate-200"><?php echo date('M d, Y', strtotime($row['fecha'])); ?></td>
                        <td class="p-3 text-slate-400 whitespace-nowrap"><?php echo htmlspecialchars($row['restaurante']); ?></td>
                        <td class="p-3 text-right text-pink-400 font-bold" data-val="<?php echo $row['net_sales']; ?>">$<?php echo number_format($row['net_sales'], 2); ?></td>
                        <td class="p-3 text-right text-yellow-400 font-bold" data-val="<?php echo $row['change_in_gc_total']; ?>">$<?php echo number_format($row['change_in_gc_total'], 2); ?></td>
                        <td class="p-3 text-right text-green-400" data-val="<?php echo $row['cash']; ?>">$<?php echo number_format($row['cash'], 2); ?></td>
                        <td class="p-3 text-right text-orange-300" data-val="<?php echo $row['employee_disc']; ?>">$<?php echo number_format($row['employee_disc'], 2); ?></td>
                        <td class="p-3 text-right text-red-400" data-val="<?php echo $row['error_corrects']; ?>">$<?php echo number_format($row['error_corrects'], 2); ?></td>
                        <td class="p-3 text-right text-blue-300" data-val="<?php echo $row['gratuity']; ?>">$<?php echo number_format($row['gratuity'], 2); ?></td>
                        <td class="p-3 text-right text-yellow-300" data-val="<?php echo $row['mgr_disc']; ?>">$<?php echo number_format($row['mgr_disc'], 2); ?></td>
                        <td class="p-3 text-right text-red-500 font-bold" data-val="<?php echo $row['mgr_void']; ?>">$<?php echo number_format($row['mgr_void'], 2); ?></td>
                        <td class="p-3 text-right text-slate-300" data-val="<?php echo $row['sales_transfer_in']; ?>">$<?php echo number_format($row['sales_transfer_in'], 2); ?></td>
                        <td class="p-3 text-right text-slate-300" data-val="<?php echo $row['sales_transfer_out']; ?>">$<?php echo number_format($row['sales_transfer_out'], 2); ?></td>
                        <td class="p-3 text-right text-purple-300" data-val="<?php echo $row['service_balance']; ?>">$<?php echo number_format($row['service_balance'], 2); ?></td>
                        <td class="p-3 text-right text-teal-300" data-val="<?php echo $row['tax_1']; ?>">$<?php echo number_format($row['tax_1'], 2); ?></td>
                        <td class="p-3 text-right text-pink-400" data-val="<?php echo $row['tips_paid']; ?>">$<?php echo number_format($row['tips_paid'], 2); ?></td>
                    </tr>
                    <?php
    endforeach; ?>
                <?php
endif; ?>
            </tbody>
        </table>
    </div>
</div>

<script>
// ─── SORTING ────────────────────────────────────────────────────
let sortCol = 1, sortDir = -1; // default: date desc

function sortTable(col) {
    const table = document.getElementById('reportTable');
    const ths = table.querySelectorAll('th');
    const tbody = document.getElementById('reportBody');
    const rows = Array.from(tbody.querySelectorAll('tr.data-row'));

    if (sortCol === col) { sortDir *= -1; }
    else { sortCol = col; sortDir = 1; }

    ths.forEach(th => th.classList.remove('sort-asc','sort-desc'));
    ths[col].classList.add(sortDir === 1 ? 'sort-asc' : 'sort-desc');

    const type = ths[col].dataset.type || 'text';

    rows.sort((a, b) => {
        const cellA = a.querySelectorAll('td')[col];
        const cellB = b.querySelectorAll('td')[col];

        let va, vb;
        if (type === 'num') {
            va = parseFloat(cellA.dataset.val || 0);
            vb = parseFloat(cellB.dataset.val || 0);
        } else if (type === 'date') {
            va = a.dataset.fecha || '';
            vb = b.dataset.fecha || '';
        } else {
            va = (cellA.textContent || '').trim().toLowerCase();
            vb = (cellB.textContent || '').trim().toLowerCase();
        }

        if (va < vb) return -1 * sortDir;
        if (va > vb) return  1 * sortDir;
        return 0;
    });

    rows.forEach(r => tbody.appendChild(r));
}

// Set initial sort indicator
document.querySelectorAll('#reportTable th')[1].classList.add('sort-desc');

// ─── EXCEL EXPORT ────────────────────────────────────────────────
function exportToExcel() {
    const table = document.getElementById('reportTable');
    const rows = [];

    // Headers
    const headers = Array.from(table.querySelectorAll('th')).map(th =>
        th.textContent.replace(/[↑↓]/g,'').trim()
    );
    rows.push(headers);

    // Data rows
    table.querySelectorAll('tbody tr.data-row').forEach(tr => {
        const cells = Array.from(tr.querySelectorAll('td'));
        const row = cells.map((td, i) => {
            // For numeric columns use raw value
            if (td.dataset.val !== undefined) return parseFloat(td.dataset.val);
            return td.textContent.trim();
        });
        rows.push(row);
    });

    const ws = XLSX.utils.aoa_to_sheet(rows);

    // Column widths
    ws['!cols'] = [
        {wch:12},{wch:13},{wch:28},{wch:12},{wch:12},{wch:12},{wch:10},
        {wch:12},{wch:10},{wch:10},{wch:10},{wch:10},{wch:10},{wch:12},{wch:8},{wch:10}
    ];

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Daily Report');

    const startDate = '<?php echo $start_date; ?>';
    const endDate   = '<?php echo $end_date; ?>';
    XLSX.writeFile(wb, `Daily_Report_${startDate}_${endDate}.xlsx`);
}
</script>
<footer class="gi-footer">
  &copy; <?php echo date('Y'); ?> <a href="https://galileoinnova.com" target="_blank">GalileoInnova</a> &middot; Restaurant Intelligence Suite
</footer>
</body>
</html>
