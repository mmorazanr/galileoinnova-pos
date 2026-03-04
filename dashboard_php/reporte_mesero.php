<?php
require_once 'auth.php';
require_once 'config.php';

// ── Parámetros ───────────────────────────────────────────────────────────
$start_date = isset($_GET['start_date']) ? $_GET['start_date'] : date('Y-m-01');
$end_date = isset($_GET['end_date']) ? $_GET['end_date'] : date('Y-m-d');
$mesero = isset($_GET['mesero']) ? $_GET['mesero'] : '';
$restaurante = isset($_GET['restaurante']) ? $_GET['restaurante'] : '';

// ── Listas para selectores ───────────────────────────────────────────────
$stmt_rest = $pdo->query("SELECT DISTINCT restaurante FROM restaurantes_ventas ORDER BY restaurante");
$lista_rest = $stmt_rest->fetchAll(PDO::FETCH_COLUMN);

$q_m = "SELECT DISTINCT mesero FROM restaurantes_ventas";
$p_m = array();
if ($restaurante !== '') {
  $q_m .= " WHERE restaurante = ?";
  $p_m[] = $restaurante;
}
$q_m .= " ORDER BY mesero ASC";
$stmt_m = $pdo->prepare($q_m);
$stmt_m->execute($p_m);
$lista_meseros = $stmt_m->fetchAll(PDO::FETCH_COLUMN);

$days_es = array(
  'Monday' => 'Lunes',
  'Tuesday' => 'Martes',
  'Wednesday' => 'Miércoles',
  'Thursday' => 'Jueves',
  'Friday' => 'Viernes',
  'Saturday' => 'Sábado',
  'Sunday' => 'Domingo'
);
$day_colors = array(
  'Lunes' => '#93c5fd',
  'Martes' => '#c4b5fd',
  'Miércoles' => '#86efac',
  'Jueves' => '#fdba74',
  'Viernes' => '#7dd3fc',
  'Sábado' => '#f9a8d4',
  'Domingo' => '#fca5a5'
);

// ── Ejecutar queries solo si hay mesero ──────────────────────────────────
$data_ready = ($mesero !== '');
$dias_rows = array();
$top_platos = array();
$media_rows = array();
$total_ventas = 0;
$total_items = 0;
$total_tickets = 0;
$dias_trabajados = 0;
$avg_ticket = 0;

if ($data_ready) {

  // WHERE dinámico para restaurantes_ventas y restaurantes_mesero_media
  $where_base = "mesero = ? AND fecha >= ? AND fecha <= ?";
  $params_base = array($mesero, $start_date, $end_date);
  if ($restaurante !== '') {
    $where_base .= " AND restaurante = ?";
    $params_base[] = $restaurante;
  }

  // WHERE dinámico para restaurantes_kpi_mesero (misma estructura)
  $where_kpi = "mesero = ? AND fecha >= ? AND fecha <= ?";
  $params_kpi = array($mesero, $start_date, $end_date);
  if ($restaurante !== '') {
    $where_kpi .= " AND restaurante = ?";
    $params_kpi[] = $restaurante;
  }

  // 1. KPIs globales del mesero
  $stmt1 = $pdo->prepare(
    "SELECT COALESCE(SUM(monto_venta),0) AS total_ventas,
            COALESCE(SUM(cantidad),0)    AS total_items,
            COUNT(DISTINCT fecha)        AS dias_trabajados
     FROM restaurantes_ventas
     WHERE " . $where_base
  );
  $stmt1->execute($params_base);
  $kpi1 = $stmt1->fetch();
  $total_ventas = floatval($kpi1['total_ventas']);
  $total_items = intval($kpi1['total_items']);
  $dias_trabajados = intval($kpi1['dias_trabajados']);

  // 2. Total tickets
  $stmt2 = $pdo->prepare(
    "SELECT COALESCE(SUM(total_tickets),0) AS total_tickets
     FROM restaurantes_kpi_mesero
     WHERE " . $where_kpi
  );
  $stmt2->execute($params_kpi);
  $kpi2 = $stmt2->fetch();
  $total_tickets = intval($kpi2['total_tickets']);
  $avg_ticket = $total_tickets > 0 ? $total_ventas / $total_tickets : 0;

  // 3a. Ventas por día
  $stmt3a = $pdo->prepare(
    "SELECT fecha,
            COALESCE(SUM(monto_venta),0) AS ventas,
            COALESCE(SUM(cantidad),0)    AS items
     FROM restaurantes_ventas
     WHERE " . $where_base . "
     GROUP BY fecha
     ORDER BY fecha DESC"
  );
  $stmt3a->execute($params_base);
  $ventas_dia = array();
  foreach ($stmt3a->fetchAll() as $row) {
    $k = ($row['fecha'] instanceof DateTime) ? $row['fecha']->format('Y-m-d') : (string)$row['fecha'];
    $ventas_dia[$k] = array('ventas' => floatval($row['ventas']), 'items' => intval($row['items']));
  }

  // 3b. Tickets por día
  $stmt3b = $pdo->prepare(
    "SELECT fecha,
            COALESCE(SUM(total_tickets),0) AS tickets
     FROM restaurantes_kpi_mesero
     WHERE " . $where_kpi . "
     GROUP BY fecha"
  );
  $stmt3b->execute($params_kpi);
  $tickets_dia = array();
  foreach ($stmt3b->fetchAll() as $row) {
    $k = ($row['fecha'] instanceof DateTime) ? $row['fecha']->format('Y-m-d') : (string)$row['fecha'];
    $tickets_dia[$k] = intval($row['tickets']);
  }

  // 3c. Merge en PHP — ordenado por fecha DESC
  $all_fechas = array_unique(array_merge(array_keys($ventas_dia), array_keys($tickets_dia)));
  rsort($all_fechas);
  $dias_rows = array();
  foreach ($all_fechas as $f) {
    $dias_rows[] = array(
      'fecha' => $f,
      'ventas' => isset($ventas_dia[$f]) ? $ventas_dia[$f]['ventas'] : 0,
      'items' => isset($ventas_dia[$f]) ? $ventas_dia[$f]['items'] : 0,
      'tickets' => isset($tickets_dia[$f]) ? $tickets_dia[$f] : 0,
    );
  }

  // 4. Top platillos
  $stmt4 = $pdo->prepare(
    "SELECT platillo,
            COALESCE(SUM(cantidad),0)    AS qty,
            COALESCE(SUM(monto_venta),0) AS total
     FROM restaurantes_ventas
     WHERE " . $where_base . "
     GROUP BY platillo
     ORDER BY qty DESC
     LIMIT 25"
  );
  $stmt4->execute($params_base);
  $top_platos = $stmt4->fetchAll();

  // 5. Desglose financiero media
  $stmt5 = $pdo->prepare(
    "SELECT media_name,
            SUM(amount) AS total_amount
     FROM restaurantes_mesero_media
     WHERE " . $where_base . "
     GROUP BY media_name
     HAVING SUM(amount) <> 0
     ORDER BY ABS(SUM(amount)) DESC"
  );
  $stmt5->execute($params_base);
  $media_rows = $stmt5->fetchAll();
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reporte Mesero · GalileoInnova</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<style>
  body { background: #060d1f; color: #e2e8f0; font-family: 'Segoe UI', system-ui, sans-serif; min-height: 100vh; }
  .glass { background: rgba(255,255,255,0.04); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.09); border-radius: 16px; }
  select, input[type=date] {
    background: #0f172a; color: #e2e8f0; border: 1px solid #334155;
    border-radius: 8px; padding: 8px 12px; font-size: 13px; outline: none;
  }
  select:focus, input[type=date]:focus { border-color: #3b82f6; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th {
    background: #0d1730; color: #64748b; padding: 10px 12px;
    text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: .06em;
    position: sticky; top: 0; z-index: 5; cursor: pointer; user-select: none; white-space: nowrap;
    border-bottom: 1px solid #1e3a5f;
  }
  thead th:hover { background: #111f40; color: #cbd5e1; }
  thead th.sort-asc::after  { content: ' ↑'; color: #60a5fa; font-size: 9px; }
  thead th.sort-desc::after { content: ' ↓'; color: #60a5fa; font-size: 9px; }
  tbody tr { border-bottom: 1px solid #0f1f3a; transition: background .1s; }
  tbody tr:hover { background: rgba(59,130,246,0.05); }
  td { padding: 9px 12px; white-space: nowrap; }
  .badge-day { display: inline-block; font-size: 10px; font-weight: 700;
    padding: 2px 8px; border-radius: 999px; text-transform: uppercase; letter-spacing: .04em; }
  .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 12px; margin-bottom: 18px; }
  .kpi-card { padding: 16px 18px; border-radius: 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07); }
  .kpi-label { font-size: 10px; color: #475569; text-transform: uppercase; letter-spacing: .07em; margin-bottom: 5px; }
  .kpi-value { font-size: 24px; font-weight: 800; line-height: 1.1; }
  .section-title { font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: .07em;
    padding: 13px 16px 10px; border-bottom: 1px solid rgba(255,255,255,0.06); }
  .topbar { background: rgba(6,12,35,0.92); backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(59,130,246,0.12);
    padding: 10px 20px; display: flex; align-items: center; gap: 14px;
    justify-content: space-between; flex-wrap: wrap; }
  .topbar img { width: 34px; height: 34px; object-fit: contain; filter: drop-shadow(0 0 6px rgba(59,130,246,0.5)); }
  .btn { padding: 8px 18px; border-radius: 8px; font-size: 13px; font-weight: 700;
    border: none; cursor: pointer; transition: all .15s; display: inline-flex; align-items: center; gap: 6px; }
  .btn-blue  { background: #1d4ed8; color: white; } .btn-blue:hover  { background: #2563eb; }
  .btn-green { background: #065f46; color: #6ee7b7; } .btn-green:hover { background: #064e3b; }
  .btn-ghost { background: #1e293b; color: #94a3b8; } .btn-ghost:hover { background: #334155; }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  @media(max-width:720px){ .two-col { grid-template-columns: 1fr; } }
  .tr-total { background: rgba(59,130,246,0.08) !important; font-weight: 800; border-top: 2px solid #1e3a5f !important; }
</style>
</head>
<body>

<!-- Topbar -->
<div class="topbar">
  <div style="display:flex;align-items:center;gap:10px;">
    <img src="logo_galileoinnova.jpg" alt="GalileoInnova">
    <div>
      <div style="font-size:15px;font-weight:800;color:#f1f5f9;">GalileoInnova</div>
      <div style="font-size:9px;color:#3b82f6;text-transform:uppercase;letter-spacing:.1em;">Reporte de Mesero</div>
    </div>
  </div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
    <?php if ($data_ready): ?>
    <button onclick="exportExcel()" class="btn btn-green">⬇ Excel</button>
    <?php
endif; ?>
    <button onclick="window.print()" class="btn btn-ghost">🖨 Imprimir</button>
    <button onclick="window.close()" class="btn btn-ghost">✕ Cerrar</button>
  </div>
</div>

<div style="padding:18px;">

<!-- Filtros -->
<div class="glass" style="padding:16px;margin-bottom:16px;">
  <form method="GET" style="display:flex;flex-wrap:wrap;gap:14px;align-items:flex-end;">
    <div>
      <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px;">Sucursal</div>
      <select name="restaurante" id="sel_rest" onchange="actualizarMeseros(this.value)">
        <option value="">-- Todas --</option>
        <?php foreach ($lista_rest as $r): ?>
          <option value="<?php echo htmlspecialchars($r); ?>" <?php if ($r === $restaurante)
    echo 'selected'; ?>>
            <?php echo htmlspecialchars($r); ?>
          </option>
        <?php
endforeach; ?>
      </select>
    </div>
    <div>
      <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px;">Mesero *</div>
      <select name="mesero" id="sel_mesero" required>
        <option value="">-- Seleccione --</option>
        <?php foreach ($lista_meseros as $m): ?>
          <option value="<?php echo htmlspecialchars($m); ?>" <?php if ($m === $mesero)
    echo 'selected'; ?>>
            <?php echo htmlspecialchars($m); ?>
          </option>
        <?php
endforeach; ?>
      </select>
    </div>
    <div>
      <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px;">Desde</div>
      <input type="date" name="start_date" value="<?php echo htmlspecialchars($start_date); ?>">
    </div>
    <div>
      <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px;">Hasta</div>
      <input type="date" name="end_date" value="<?php echo htmlspecialchars($end_date); ?>">
    </div>
    <button type="submit" class="btn btn-blue">📊 Generar</button>
  </form>
</div>

<?php if ($data_ready): ?>

<!-- Encabezado del reporte -->
<div style="margin:16px 0 12px;">
  <div style="font-size:20px;font-weight:800;color:#f1f5f9;">
    👤 <?php echo htmlspecialchars($mesero); ?>
  </div>
  <div style="font-size:12px;color:#475569;margin-top:3px;">
    <?php echo $start_date; ?> → <?php echo $end_date; ?>
    <?php if ($restaurante !== ''): ?>
      &nbsp;·&nbsp; <?php echo htmlspecialchars($restaurante); ?>
    <?php
  endif; ?>
  </div>
</div>

<!-- KPI Cards -->
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-label">Net Sales</div>
    <div class="kpi-value" style="color:#4ade80;">$<?php echo number_format($total_ventas, 2); ?></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">🎫 Tickets</div>
    <div class="kpi-value" style="color:#60a5fa;"><?php echo number_format($total_tickets); ?></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Avg / Ticket</div>
    <div class="kpi-value" style="color:#f472b6;">$<?php echo number_format($avg_ticket, 2); ?></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Items Vendidos</div>
    <div class="kpi-value" style="color:#a78bfa;"><?php echo number_format($total_items); ?></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Días Trabajados</div>
    <div class="kpi-value" style="color:#fb923c;"><?php echo $dias_trabajados; ?></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Net Sales / Día</div>
    <?php $vpd = $dias_trabajados > 0 ? $total_ventas / $dias_trabajados : 0; ?>
    <div class="kpi-value" style="color:#34d399;">$<?php echo number_format($vpd, 2); ?></div>
  </div>
</div>

<!-- Desglose diario -->
<div class="glass" style="margin-bottom:14px;overflow:hidden;">
  <div class="section-title">📅 Desglose por Día</div>
  <div style="max-height:360px;overflow-y:auto;">
    <table id="tblDias">
      <thead>
        <tr>
          <th onclick="sortTbl('tblDias',0)" data-type="text">DÍA</th>
          <th onclick="sortTbl('tblDias',1)" data-type="date">FECHA</th>
          <th onclick="sortTbl('tblDias',2)" data-type="num" style="text-align:right;color:#60a5fa;">🎫 TICKETS</th>
          <th onclick="sortTbl('tblDias',3)" data-type="num" style="text-align:right;">ITEMS</th>
          <th onclick="sortTbl('tblDias',4)" data-type="num" style="text-align:right;color:#4ade80;">NET SALES</th>
          <th onclick="sortTbl('tblDias',5)" data-type="num" style="text-align:right;color:#f472b6;">AVG/TICKET</th>
        </tr>
      </thead>
      <tbody id="bodyDias">
        <?php
  $tot_t = 0;
  $tot_i = 0;
  $tot_v = 0;
  foreach ($dias_rows as $d):
    $fstr = ($d['fecha'] instanceof DateTime) ? $d['fecha']->format('Y-m-d') : (string)$d['fecha'];
    $day_en = date('l', strtotime($fstr));
    $day_es = isset($days_es[$day_en]) ? $days_es[$day_en] : $day_en;
    $color = isset($day_colors[$day_es]) ? $day_colors[$day_es] : '#e2e8f0';
    $tix = intval($d['tickets']);
    $items = intval($d['items']);
    $ventas = floatval($d['ventas']);
    $avg = $tix > 0 ? $ventas / $tix : 0;
    $tot_t += $tix;
    $tot_i += $items;
    $tot_v += $ventas;
?>
        <tr data-fecha="<?php echo $fstr; ?>">
          <td><span class="badge-day" style="background:<?php echo $color; ?>22;color:<?php echo $color; ?>"><?php echo $day_es; ?></span></td>
          <td style="font-weight:600;color:#cbd5e1;"><?php echo date('M d, Y', strtotime($fstr)); ?></td>
          <td style="text-align:right;color:#60a5fa;font-weight:700;" data-val="<?php echo $tix; ?>"><?php echo number_format($tix); ?></td>
          <td style="text-align:right;color:#94a3b8;" data-val="<?php echo $items; ?>"><?php echo number_format($items); ?></td>
          <td style="text-align:right;color:#4ade80;font-weight:700;" data-val="<?php printf('%.2f', $ventas); ?>">$<?php echo number_format($ventas, 2); ?></td>
          <td style="text-align:right;color:#f472b6;" data-val="<?php printf('%.2f', $avg); ?>">$<?php echo number_format($avg, 2); ?></td>
        </tr>
        <?php
  endforeach; ?>
        <tr class="tr-total">
          <td colspan="2" style="color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:.05em;">TOTALES</td>
          <td style="text-align:right;color:#60a5fa;"><?php echo number_format($tot_t); ?></td>
          <td style="text-align:right;color:#94a3b8;"><?php echo number_format($tot_i); ?></td>
          <td style="text-align:right;color:#4ade80;">$<?php echo number_format($tot_v, 2); ?></td>
          <td style="text-align:right;color:#f472b6;">$<?php echo $tot_t > 0 ? number_format($tot_v / $tot_t, 2) : '0.00'; ?></td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

<!-- Dos columnas: Top Platillos + Financiero -->
<div class="two-col">

  <!-- Top platillos -->
  <div class="glass" style="overflow:hidden;">
    <div class="section-title">🍽️ Top Platillos</div>
    <div style="max-height:320px;overflow-y:auto;">
      <table id="tblPlatos">
        <thead>
          <tr>
            <th onclick="sortTbl('tblPlatos',0)" data-type="text">PLATILLO</th>
            <th onclick="sortTbl('tblPlatos',1)" data-type="num" style="text-align:right;">QTY</th>
            <th onclick="sortTbl('tblPlatos',2)" data-type="num" style="text-align:right;color:#4ade80;">VENTAS</th>
          </tr>
        </thead>
        <tbody>
          <?php foreach ($top_platos as $p): ?>
          <tr>
            <td style="color:#e2e8f0;"><?php echo htmlspecialchars($p['platillo']); ?></td>
            <td style="text-align:right;color:#94a3b8;" data-val="<?php echo $p['qty']; ?>"><?php echo number_format((int)$p['qty']); ?></td>
            <td style="text-align:right;color:#4ade80;" data-val="<?php printf('%.2f', $p['total']); ?>">$<?php echo number_format($p['total'], 2); ?></td>
          </tr>
          <?php
  endforeach; ?>
          <?php if (empty($top_platos)): ?>
          <tr><td colspan="3" style="text-align:center;color:#334155;padding:20px;">Sin datos</td></tr>
          <?php
  endif; ?>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Desglose financiero media -->
  <div class="glass" style="overflow:hidden;">
    <div class="section-title">💳 Desglose Financiero</div>
    <div style="max-height:320px;overflow-y:auto;">
      <table id="tblMedia">
        <thead>
          <tr>
            <th data-type="text">TIPO</th>
            <th data-type="num" style="text-align:right;">MONTO</th>
          </tr>
        </thead>
        <tbody>
          <?php foreach ($media_rows as $mm):
    $mcolor = $mm['total_amount'] < 0 ? '#f87171' : '#e2e8f0';
?>
          <tr>
            <td style="color:#cbd5e1;"><?php echo htmlspecialchars($mm['media_name']); ?></td>
            <td style="text-align:right;color:<?php echo $mcolor; ?>;font-weight:600;" data-val="<?php printf('%.2f', $mm['total_amount']); ?>">
              $<?php echo number_format($mm['total_amount'], 2); ?>
            </td>
          </tr>
          <?php
  endforeach; ?>
          <?php if (empty($media_rows)): ?>
          <tr><td colspan="2" style="text-align:center;color:#334155;padding:20px;">Sin datos financieros</td></tr>
          <?php
  endif; ?>
        </tbody>
      </table>
    </div>
  </div>

</div><!-- /two-col -->

<?php
else: ?>

<!-- Estado vacío -->
<div style="text-align:center;padding:60px 20px;">
  <div style="font-size:52px;margin-bottom:14px;">👤</div>
  <div style="font-size:15px;color:#475569;">Seleccione un <strong style="color:#c084fc;">mesero</strong> y rango de fechas para generar el reporte.</div>
</div>

<?php
endif; ?>

<footer style="text-align:center;padding:18px;font-size:11px;color:#1e3a5f;margin-top:10px;">
  &copy; <?php echo date('Y'); ?> <a href="https://galileoinnova.com" target="_blank" style="color:#2563eb;text-decoration:none;">GalileoInnova</a>
  &middot; Restaurant Intelligence Suite
</footer>
</div>

<script>
// ── Meseros dinámicos ──────────────────────────────────────────────
async function actualizarMeseros(rest) {
  var sel = document.getElementById('sel_mesero');
  var current = sel.value;
  sel.innerHTML = '<option value="">-- Seleccione --</option>';
  try {
    var url = 'index.php?meseros_ajax=1&restaurante=' + encodeURIComponent(rest);
    var resp = await fetch(url);
    var data = await resp.json();
    data.forEach(function(m) {
      var opt = document.createElement('option');
      opt.value = m; opt.textContent = m;
      if (m === current) opt.selected = true;
      sel.appendChild(opt);
    });
  } catch(e) { console.error('Error cargando meseros:', e); }
}

// ── Sorting ────────────────────────────────────────────────────────
var sortState = {};
function sortTbl(tableId, col) {
  var tbl   = document.getElementById(tableId);
  var ths   = tbl.querySelectorAll('th');
  var tbody = tbl.querySelector('tbody');
  var rows  = Array.from(tbody.querySelectorAll('tr')).filter(function(r) {
    return !r.classList.contains('tr-total');
  });

  if (!sortState[tableId]) sortState[tableId] = { col: -1, dir: 1 };
  var s = sortState[tableId];
  if (s.col === col) { s.dir *= -1; } else { s.col = col; s.dir = 1; }

  ths.forEach(function(th) { th.classList.remove('sort-asc','sort-desc'); });
  ths[col].classList.add(s.dir === 1 ? 'sort-asc' : 'sort-desc');

  var type = ths[col].dataset.type || 'text';
  rows.sort(function(a, b) {
    var tdA = a.querySelectorAll('td')[col];
    var tdB = b.querySelectorAll('td')[col];
    var va  = (tdA.dataset.val !== undefined) ? tdA.dataset.val : tdA.textContent.trim().replace(/[$,]/g,'');
    var vb  = (tdB.dataset.val !== undefined) ? tdB.dataset.val : tdB.textContent.trim().replace(/[$,]/g,'');
    if (type === 'num' || type === 'date') {
      var na = parseFloat(va), nb = parseFloat(vb);
      if (!isNaN(na) && !isNaN(nb)) return (na - nb) * s.dir;
    }
    return va.toString().localeCompare(vb.toString()) * s.dir;
  });

  var totalRow = tbody.querySelector('.tr-total');
  rows.forEach(function(r) {
    if (totalRow) tbody.insertBefore(r, totalRow);
    else tbody.appendChild(r);
  });
}

// ── Excel Export ───────────────────────────────────────────────────
function exportExcel() {
  var wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, sheetFromTable('tblDias'),   'Por Día');
  XLSX.utils.book_append_sheet(wb, sheetFromTable('tblPlatos'), 'Platillos');
  XLSX.utils.book_append_sheet(wb, sheetFromTable('tblMedia'),  'Financiero');
  var fname = 'Mesero_<?php echo preg_replace('/[^a-zA-Z0-9_]/', '_', $mesero); ?>_<?php echo $start_date; ?>_<?php echo $end_date; ?>.xlsx';
  XLSX.writeFile(wb, fname);
}
function sheetFromTable(id) {
  var tbl = document.getElementById(id);
  var rows = [];
  tbl.querySelectorAll('tr').forEach(function(tr) {
    var cells = tr.querySelectorAll('th, td');
    rows.push(Array.from(cells).map(function(c) {
      if (c.dataset.val !== undefined) {
        var n = parseFloat(c.dataset.val);
        return isNaN(n) ? c.dataset.val : n;
      }
      return c.textContent.trim().replace(/[$,]/g,'');
    }));
  });
  return XLSX.utils.aoa_to_sheet(rows);
}
</script>
</body>
</html>
