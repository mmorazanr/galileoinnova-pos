<?php
require_once 'auth.php';
require_once 'config.php';

// ── Manejar acciones POST ──────────────────────────────────────────────
$mensaje = '';
$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  if (!can_delete_admin_data()) {
    $error = 'No tiene permisos para eliminar registros.';
  }
  else {
    $accion = $_POST['accion'] ?? '';
    $restaurante = $_POST['restaurante'] ?? '';
    $confirm_key = $_POST['confirm_key'] ?? '';

    // ── Eliminar días seleccionados ──
    if ($accion === 'delete_days') {
      $fechas = $_POST['fechas'] ?? [];
      $confirma = trim($_POST['confirma'] ?? '');

      if (empty($fechas)) {
        $error = 'Seleccione al menos un día.';
      }
      elseif ($confirma !== 'CONFIRMAR') {
        $error = 'Debe escribir CONFIRMAR exactamente para proceder.';
      }
      else {
        $tablas = ['restaurantes_ventas', 'restaurantes_kpi', 'restaurantes_kpi_mesero',
          'restaurantes_mesero_media', 'restaurantes_diario_media', 'restaurantes_punches'];
        $total = 0;
        foreach ($tablas as $tabla) {
          $ph = implode(',', array_fill(0, count($fechas), '?'));
          $params = array_merge([$restaurante], $fechas);
          $stmt = $pdo->prepare("DELETE FROM $tabla WHERE restaurante=? AND fecha IN ($ph)");
          $stmt->execute($params);
          $total += $stmt->rowCount();
        }
        $mensaje = "✅ Se eliminaron $total registros de " . count($fechas) . " día(s) de '$restaurante'. El sync puede restaurarlos.";
      }
    }

    // ── Eliminar TODO el restaurante ──
    if ($accion === 'delete_all') {
      $confirma1 = trim($_POST['confirma1'] ?? '');
      $confirma2 = trim($_POST['confirma2'] ?? '');
      $confirma3 = trim($_POST['confirma3'] ?? '');

      if ($confirma1 !== $restaurante) {
        $error = 'El nombre del restaurante no coincide. Operación cancelada.';
      }
      elseif ($confirma2 !== 'CONFIRMAR') {
        $error = 'Debe escribir CONFIRMAR exactamente.';
      }
      elseif ($confirma3 !== 'ELIMINAR TODO') {
        $error = 'Debe escribir ELIMINAR TODO exactamente.';
      }
      else {
        $tablas = ['restaurantes_ventas', 'restaurantes_kpi', 'restaurantes_kpi_mesero',
          'restaurantes_mesero_media', 'restaurantes_diario_media', 'restaurantes_punches'];
        $total = 0;
        foreach ($tablas as $tabla) {
          $stmt = $pdo->prepare("DELETE FROM $tabla WHERE restaurante=?");
          $stmt->execute([$restaurante]);
          $total += $stmt->rowCount();
        }
        $mensaje = "✅ Se eliminaron $total registros de '$restaurante'. Lista limpia para re-sincronizar.";
      }
    }
  }
}

// ── Cargar restaurantes ────────────────────────────────────────────────
$stmt = $pdo->query("SELECT DISTINCT restaurante FROM restaurantes_diario_media ORDER BY restaurante");
$db_restaurantes = $stmt->fetchAll(PDO::FETCH_COLUMN);

$restaurantes = [];
foreach ($db_restaurantes as $r) {
  if (can_access_restaurant($r)) {
    $restaurantes[] = $r;
  }
}

// ── Restaurante seleccionado ───────────────────────────────────────────
$req_rest = $_GET['restaurante'] ?? '';
if (!empty($req_rest) && !can_access_restaurant($req_rest)) {
  $sel_rest = $restaurantes[0] ?? '';
}
else {
  $sel_rest = $req_rest ?: ($restaurantes[0] ?? '');
}
$date_from = $_GET['date_from'] ?? '';
$date_to = $_GET['date_to'] ?? '';

// ── Cargar días del restaurante ────────────────────────────────────────
$dias = [];
if ($sel_rest) {
  $extra_date = '';
  $all_params = [$sel_rest, $sel_rest, $sel_rest];
  if ($date_from) {
    $extra_date .= ' AND dm.fecha >= ?';
    $all_params[] = $date_from;
  }
  if ($date_to) {
    $extra_date .= ' AND dm.fecha <= ?';
    $all_params[] = $date_to;
  }

  $stmt = $pdo->prepare("
        SELECT dm.fecha,
               COALESCE(dm.net_sales, 0)          AS net_sales,
               COALESCE(v.cnt, 0)                 AS cnt_ventas,
               COALESCE(k.cnt_kpi, 0)             AS cnt_kpi,
               COALESCE(k.total_tickets, 0)       AS total_tickets
        FROM restaurantes_diario_media dm
        LEFT JOIN (
            SELECT fecha, COUNT(*) AS cnt FROM restaurantes_ventas
            WHERE restaurante = ? GROUP BY fecha
        ) v ON v.fecha = dm.fecha
        LEFT JOIN (
            SELECT fecha, COUNT(*) AS cnt_kpi, SUM(total_tickets) AS total_tickets
            FROM restaurantes_kpi
            WHERE restaurante = ? GROUP BY fecha
        ) k ON k.fecha = dm.fecha
        WHERE dm.restaurante = ? $extra_date
        ORDER BY dm.fecha DESC
    ");
  $stmt->execute($all_params);
  $dias = $stmt->fetchAll();
}

$days_es = ['Monday' => 'Lunes', 'Tuesday' => 'Martes', 'Wednesday' => 'Miércoles',
  'Thursday' => 'Jueves', 'Friday' => 'Viernes', 'Saturday' => 'Sábado', 'Sunday' => 'Domingo'];
$day_colors = ['Lunes' => '#93c5fd', 'Martes' => '#c4b5fd', 'Miércoles' => '#86efac',
  'Jueves' => '#fdba74', 'Viernes' => '#7dd3fc', 'Sábado' => '#f9a8d4', 'Domingo' => '#fca5a5'];

$total_ns = array_sum(array_column($dias, 'net_sales'));
$total_tickets = array_sum(array_column($dias, 'total_tickets'));
$total_items = array_sum(array_column($dias, 'cnt_ventas'));
?>
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Admin Datos · Comtrex Sync</title>
<style>
  :root {
    --bg: #0f172a; --surface: #1e293b; --surface2: #0d1b2e;
    --border: #334155; --text: #e2e8f0; --muted: #64748b;
    --green: #22c55e; --red: #ef4444; --yellow: #eab308;
    --blue: #3b82f6; --orange: #f97316; --pink: #ec4899;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; min-height: 100vh; padding: 20px; }
  .glass { background: rgba(255,255,255,0.04); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; }
  header { padding: 18px 24px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
  header h1 { font-size: 20px; font-weight: 700; color: #f1f5f9; }
  header h1 span { color: #f472b6; }
  .back-btn { background: #1e293b; color: #94a3b8; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-size: 13px; transition: background .15s; }
  .back-btn:hover { background: #334155; color: #e2e8f0; }

  /* Alerts */
  .alert { padding: 12px 16px; border-radius: 10px; font-size: 14px; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
  .alert-success { background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.3); color: #86efac; }
  .alert-error   { background: rgba(239,68,68,0.1);  border: 1px solid rgba(239,68,68,0.3);  color: #fca5a5; }
  .alert-warn    { background: rgba(234,179,8,0.1);  border: 1px solid rgba(234,179,8,0.3);  color: #fde047; }

  /* Controls */
  .controls-bar { padding: 16px 20px; margin-bottom: 16px; display: flex; flex-wrap: wrap; align-items: center; gap: 14px; }
  select, input[type=text] { background: #0f172a; color: var(--text); border: 1px solid var(--border); border-radius: 8px; padding: 8px 14px; font-size: 13px; outline: none; }
  select:focus, input[type=text]:focus { border-color: #3b82f6; }
  .stat-chip { background: #0f172a; border: 1px solid var(--border); border-radius: 8px; padding: 6px 14px; font-size: 12px; color: var(--muted); }
  .stat-chip strong { color: var(--text); }

  /* Table */
  .tbl-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th { background: #1e293b; color: #94a3b8; padding: 10px 14px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: .05em; position: sticky; top: 0; cursor: pointer; user-select: none; white-space: nowrap; }
  thead th:hover { background: #273549; color: #e2e8f0; }
  thead th.check-col { width: 48px; text-align: center; cursor: default; }
  tbody tr { border-bottom: 1px solid #1a2540; transition: background .1s; }
  tbody tr:hover { background: rgba(255,255,255,0.03); }
  td { padding: 10px 14px; white-space: nowrap; }
  td.check-col { text-align: center; }
  input[type=checkbox] { width: 16px; height: 16px; accent-color: #3b82f6; cursor: pointer; }
  .badge-day { display: inline-block; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 999px; text-transform: uppercase; letter-spacing: .04em; }
  .net-sales { color: #4ade80; font-weight: 600; }
  .cnt-col { color: var(--muted); }

  /* Select all row */
  .sel-all-row { background: #0a1628; padding: 8px 14px; display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--muted); }
  .sel-all-row label { cursor: pointer; display: flex; align-items: center; gap: 8px; }

  /* Action panels */
  .actions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 20px; }
  @media(max-width: 700px) { .actions-grid { grid-template-columns: 1fr; } }

  .action-panel { padding: 20px; border-radius: 14px; }
  .action-panel.danger-low  { background: rgba(180,83,9,0.12);  border: 1px solid rgba(249,115,22,0.3); }
  .action-panel.danger-high { background: rgba(127,29,29,0.15); border: 1px solid rgba(239,68,68,0.4); }
  .action-panel h3 { font-size: 14px; font-weight: 700; margin-bottom: 6px; }
  .action-panel.danger-low  h3 { color: #fb923c; }
  .action-panel.danger-high h3 { color: #f87171; }
  .action-panel p  { font-size: 12px; color: var(--muted); margin-bottom: 14px; line-height: 1.5; }
  .confirm-field { margin-bottom: 10px; }
  .confirm-field label { display: block; font-size: 11px; color: var(--muted); margin-bottom: 4px; }
  .confirm-field input { width: 100%; font-family: monospace; }
  .hint { font-size: 10px; color: #475569; margin-top: 3px; }

  /* Buttons */
  .btn { padding: 9px 20px; border-radius: 8px; font-size: 13px; font-weight: 700; border: none; cursor: pointer; transition: all .15s; display: inline-flex; align-items: center; gap: 6px; }
  .btn:disabled { opacity: .5; cursor: not-allowed; }
  .btn-orange { background: #c2410c; color: white; } .btn-orange:hover:not(:disabled) { background: #ea580c; }
  .btn-red    { background: #7f1d1d; color: white; } .btn-red:hover:not(:disabled)    { background: #b91c1c; }
  .btn-blue   { background: #1d4ed8; color: white; } .btn-blue:hover:not(:disabled)   { background: #2563eb; }
  .btn-ghost  { background: #1e293b; color: #94a3b8; } .btn-ghost:hover { background: #334155; }
</style>
</head>
<body>

<header class="glass">
  <h1>🗂 <span>Admin</span> Días Contables</h1>
  <a href="index.php" class="back-btn">← Dashboard</a>
</header>
<?php require_once 'navbar.php'; ?>

<?php if ($mensaje): ?>
<div class="alert alert-success">✅ <?php echo htmlspecialchars($mensaje); ?></div>
<?php
endif; ?>
<?php if ($error): ?>
<div class="alert alert-error">❌ <?php echo htmlspecialchars($error); ?></div>
<?php
endif; ?>

<div class="alert alert-warn">
  ⚠️ <strong>Zona administrativa.</strong> Las eliminaciones son permanentes. El sincronizador puede restaurar datos desde el POS local al próxima ejecución.
</div>

<!-- ─── Filtros ──────────────────────────────────────────── -->
<div class="glass controls-bar">
  <form method="GET" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
    <label style="font-size:13px;color:var(--muted);">Restaurante:</label>
    <select name="restaurante">
      <?php foreach ($restaurantes as $r): ?>
        <option value="<?php echo htmlspecialchars($r); ?>" <?php if ($r == $sel_rest)
    echo 'selected'; ?>>
          <?php echo htmlspecialchars($r); ?>
        </option>
      <?php
endforeach; ?>
    </select>
    <label style="font-size:13px;color:var(--muted);margin-left:8px;">Desde:</label>
    <input type="date" name="date_from" value="<?php echo htmlspecialchars($date_from); ?>" style="padding:7px 12px;">
    <label style="font-size:13px;color:var(--muted);">Hasta:</label>
    <input type="date" name="date_to"   value="<?php echo htmlspecialchars($date_to); ?>"   style="padding:7px 12px;">
    <button type="submit" style="background:#1d4ed8;color:white;border:none;padding:8px 18px;border-radius:8px;font-size:13px;font-weight:700;cursor:pointer;">🔍 Filtrar</button>
    <?php if ($date_from || $date_to): ?>
      <a href="?restaurante=<?php echo urlencode($sel_rest); ?>" style="font-size:12px;color:#64748b;text-decoration:none;">✕ Quitar fechas</a>
    <?php
endif; ?>
  </form>
  <?php if ($dias): ?>
  <div class="stat-chip">📅 <strong><?php echo count($dias); ?></strong> días</div>
  <div class="stat-chip">💰 Net Sales: <strong>$<?php echo number_format($total_ns, 2); ?></strong></div>
  <div class="stat-chip">🎫 Tickets: <strong><?php echo number_format((int)$total_tickets); ?></strong></div>
  <div class="stat-chip">🧾 Items: <strong><?php echo number_format((int)$total_items); ?></strong></div>
  <?php
endif; ?>
</div>

<!-- ─── Tabla de días ─────────────────────────────────────────────── -->
<div class="glass" style="margin-bottom:20px;">
  <?php if (empty($dias)): ?>
    <p style="padding:40px;text-align:center;color:var(--muted);">Sin datos para este restaurante.</p>
  <?php
else: ?>
  <div class="sel-all-row">
    <label><input type="checkbox" id="chkAll" onchange="toggleAll(this)"> Seleccionar todos</label>
    <span id="selCount" style="margin-left:auto;font-size:12px;">0 seleccionados</span>
  </div>
  <div class="tbl-wrap">
    <table id="diasTable">
      <thead>
        <tr>
          <th class="check-col">✓</th>
          <th onclick="sortTable(1)">Fecha</th>
          <th onclick="sortTable(2)">Día</th>
          <th onclick="sortTable(3)" style="text-align:right">Net Sales</th>
          <th onclick="sortTable(4)" style="text-align:right;color:#60a5fa">🎫 Tickets</th>
          <th onclick="sortTable(5)" style="text-align:right">Items</th>
          <th onclick="sortTable(6)" style="text-align:right"># KPI</th>
        </tr>
      </thead>
      <tbody id="tblBody">
        <?php foreach ($dias as $dia):
    $fecha_str = $dia['fecha'] instanceof DateTime ? $dia['fecha']->format('Y-m-d') : (string)$dia['fecha'];
    $day_en = date('l', strtotime($fecha_str));
    $day_es = $days_es[$day_en] ?? $day_en;
    $color = $day_colors[$day_es] ?? '#e2e8f0';
?>
        <tr>
          <td class="check-col">
            <input type="checkbox" class="row-chk" value="<?php echo $fecha_str; ?>" onchange="updateCount()">
          </td>
          <td><?php echo $fecha_str; ?></td>
          <td><span class="badge-day" style="background:<?php echo $color; ?>22;color:<?php echo $color; ?>"><?php echo $day_es; ?></span></td>
          <td style="text-align:right" class="net-sales">$<?php echo number_format($dia['net_sales'], 2); ?></td>
          <td style="text-align:right;color:#60a5fa;font-weight:700"><?php echo number_format((int)$dia['total_tickets']); ?></td>
          <td style="text-align:right" class="cnt-col"><?php echo number_format((int)$dia['cnt_ventas']); ?></td>
          <td style="text-align:right" class="cnt-col"><?php echo (int)$dia['cnt_kpi']; ?></td>
        </tr>
        <?php
  endforeach; ?>
      </tbody>
    </table>
  </div>
  <?php
endif; ?>
</div>

<!-- ─── Paneles de acción ─────────────────────────────────────────── -->
<?php if (!empty($dias) && can_delete_admin_data()): ?>
<div class="actions-grid">

  <!-- Eliminar días seleccionados -->
  <form method="POST" id="formDays" onsubmit="return validarElimDias(event)">
    <div class="action-panel danger-low">
      <h3>🗑 Eliminar Días Seleccionados</h3>
      <p>Elimina únicamente los días marcados en la tabla para el restaurante seleccionado, de todas las tablas.</p>
      <input type="hidden" name="accion" value="delete_days">
      <input type="hidden" name="restaurante" value="<?php echo htmlspecialchars($sel_rest); ?>">
      <div id="hidden_fechas"></div>
      <div class="confirm-field">
        <label>Confirmación — escriba exactamente: <code style="color:#fb923c">CONFIRMAR</code></label>
        <input type="text" name="confirma" id="confirma_days" placeholder="CONFIRMAR" autocomplete="off">
        <div class="hint">Se distingue mayúsculas de minúsculas</div>
      </div>
      <button type="submit" class="btn btn-orange" id="btnDays">🗑 Eliminar Días Seleccionados (<span id="cntBtn">0</span>)</button>
    </div>
  </form>

  <!-- Eliminar todo el restaurante -->
  <form method="POST" onsubmit="return validarElimTodo(event)">
    <div class="action-panel danger-high">
      <h3>💣 Eliminar TODOS los Datos del Restaurante</h3>
      <p>Elimina <strong>absolutamente todos</strong> los registros del restaurante de todas las tablas. Esta acción no se puede deshacer manualmente.</p>
      <input type="hidden" name="accion" value="delete_all">
      <input type="hidden" name="restaurante" value="<?php echo htmlspecialchars($sel_rest); ?>">

      <div class="confirm-field">
        <label>1. Escriba el nombre exacto del restaurante:</label>
        <input type="text" name="confirma1" placeholder="<?php echo htmlspecialchars($sel_rest); ?>" autocomplete="off">
      </div>
      <div class="confirm-field">
        <label>2. Escriba: <code style="color:#f87171">CONFIRMAR</code></label>
        <input type="text" name="confirma2" placeholder="CONFIRMAR" autocomplete="off">
      </div>
      <div class="confirm-field">
        <label>3. Escriba: <code style="color:#f87171">ELIMINAR TODO</code></label>
        <input type="text" name="confirma3" placeholder="ELIMINAR TODO" autocomplete="off">
      </div>
      <button type="submit" class="btn btn-red">💣 Eliminar TODO el Restaurante</button>
    </div>
  </form>

</div>
<?php
endif; ?>

<script>
// ── Selección de filas ──────────────────────────────────────────────
function updateCount() {
  const chks = document.querySelectorAll('.row-chk:checked');
  const n = chks.length;
  document.getElementById('selCount').textContent = n + ' seleccionados';
  document.getElementById('cntBtn').textContent = n;
}
function toggleAll(master) {
  document.querySelectorAll('.row-chk').forEach(c => { c.checked = master.checked; });
  updateCount();
}

// ── Validación eliminar días ────────────────────────────────────────
function validarElimDias(e) {
  const chks = document.querySelectorAll('.row-chk:checked');
  if (chks.length === 0) { alert('Seleccione al menos un día.'); e.preventDefault(); return false; }

  const fechas = Array.from(chks).map(c => c.value);
  const lista  = fechas.map(f => '• ' + f).join('\n');

  if (!confirm(`¿Eliminar ${fechas.length} día(s) de "${document.querySelector('[name=restaurante]').value}"?\n\n${lista}\n\nEsta acción borrará los registros de TODAS las tablas.`)) {
    e.preventDefault(); return false;
  }

  // Inyectar campos hidden con fechas
  const container = document.getElementById('hidden_fechas');
  container.innerHTML = '';
  fechas.forEach(f => {
    const inp = document.createElement('input');
    inp.type = 'hidden'; inp.name = 'fechas[]'; inp.value = f;
    container.appendChild(inp);
  });
  return true;
}

// ── Validación eliminar todo ────────────────────────────────────────
function validarElimTodo(e) {
  const rest = '<?php echo addslashes($sel_rest); ?>';
  if (!confirm(`⚠️ ADVERTENCIA CRÍTICA\n\nEstá a punto de eliminar TODOS los datos de:\n"${rest}"\n\nEsto borrará todos los días contables. ¿Continuar?`)) {
    e.preventDefault(); return false;
  }
  return true;
}

// ── Ordenamiento de tabla ───────────────────────────────────────────
let sortCol = 1, sortDir = -1;
function sortTable(col) {
  const tbody = document.getElementById('tblBody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  if (sortCol === col) sortDir *= -1; else { sortCol = col; sortDir = 1; }

  rows.sort((a, b) => {
    const va = a.querySelectorAll('td')[col].textContent.trim().replace(/[$,]/g,'');
    const vb = b.querySelectorAll('td')[col].textContent.trim().replace(/[$,]/g,'');
    const na = parseFloat(va), nb = parseFloat(vb);
    if (!isNaN(na) && !isNaN(nb)) return (na - nb) * sortDir;
    return va.localeCompare(vb) * sortDir;
  });
  rows.forEach(r => tbody.appendChild(r));
}
</script>
</body>
</html>
