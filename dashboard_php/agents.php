<?php
require_once 'auth.php';
require_once 'config.php';

$page_title = 'Sync Agents';
$msg = '';

// ── Handle Command Submit ─────────────────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !empty($_POST['id_sync'])) {
    if (!can_delete_days()) {
        $msg = "Error: Permisos insuficientes para administrar agentes.";
    }
    else {
        $id = $_POST['id_sync'];

        if (!empty($_POST['command'])) {
            $cmd = $_POST['command'];
            $allowed = ['clear_logs', 'pause', 'resume', 'sync_now', 'get_config', 'set_config'];
            if (in_array($cmd, $allowed)) {
                $stmt = $pdo->prepare("UPDATE sync_agents SET pending_command = :cmd WHERE id_sync = :id");
                $stmt->execute([':cmd' => $cmd, ':id' => $id]);
                $msg = "Command '$cmd' queued for agent: " . htmlspecialchars($id);
            }
        }
        elseif (!empty($_POST['action'])) {
            if ($_POST['action'] === 'clear_dashboard_logs') {
                $stmt = $pdo->prepare("DELETE FROM agent_sync_history WHERE id_sync = :id");
                $stmt->execute([':id' => $id]);
                $msg = "Dashboard sync history deleted for agent: " . htmlspecialchars($id);
            }
            elseif ($_POST['action'] === 'delete_agent') {
                $stmt1 = $pdo->prepare("DELETE FROM agent_sync_history WHERE id_sync = :id");
                $stmt1->execute([':id' => $id]);

                $stmt2 = $pdo->prepare("DELETE FROM sync_agents WHERE id_sync = :id");
                $stmt2->execute([':id' => $id]);

                $msg = "Agente eliminado del dashboard exitosamente: " . htmlspecialchars($id);
            }
            elseif ($_POST['action'] === 'save_config' && isset($_POST['config_json'])) {
                $config_json = $_POST['config_json'];
                // Validate JSON
                json_decode($config_json);
                if (json_last_error() === JSON_ERROR_NONE) {
                    // Guardar el JSON en la DB Y enviar el comando set_config para que el agente lo escriba
                    $stmt = $pdo->prepare("UPDATE sync_agents SET config_json = :cfg, pending_command = 'set_config' WHERE id_sync = :id");
                    $stmt->execute([':cfg' => $config_json, ':id' => $id]);
                    $msg = "Configuración guardada y enviada al agente: " . htmlspecialchars($id) . ". Se aplicará en el próximo heartbeat.";
                }
                else {
                    $msg = "Error: El JSON proporcionado no es válido para el agente: " . htmlspecialchars($id);
                }
            }
        }
    }
}

// ── Fetch All Agents ──────────────────────────────────────────────────────
$all_agents = $pdo->query("SELECT *, TIMESTAMPDIFF(MINUTE, last_heartbeat, NOW()) AS min_ago FROM sync_agents ORDER BY last_heartbeat DESC")->fetchAll();
$agents = [];
foreach ($all_agents as $ag) {
    if (can_access_restaurant($ag['restaurante'])) {
        $agents[] = $ag;
    }
}
// We no longer need a manual PHP timezone calculation since MariaDB handles the diff.
$now = new DateTime('now');
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sync Agents — GalileoInnova</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(-45deg, #0f172a, #1e1b4b, #0f3460, #0f172a);
            background-size: 400% 400%;
            animation: gradientBG 18s ease infinite;
            color: #fff;
            min-height: 100vh;
        }
        @keyframes gradientBG {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .glass-panel {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
        }
        .badge-running  { background: rgba(34,197,94,.2);  color: #4ade80; border: 1px solid rgba(34,197,94,.4); }
        .badge-paused   { background: rgba(234,179,8,.2);  color: #facc15; border: 1px solid rgba(234,179,8,.4); }
        .badge-stopped  { background: rgba(239,68,68,.2);  color: #f87171; border: 1px solid rgba(239,68,68,.4); }
        .badge-error    { background: rgba(239,68,68,.2);  color: #f87171; border: 1px solid rgba(239,68,68,.4); }
        .dot-online  { background: #4ade80; box-shadow: 0 0 8px #4ade80; }
        .dot-offline { background: #f87171; box-shadow: 0 0 8px #f87171; }
        .dot-warn    { background: #facc15; box-shadow: 0 0 8px #facc15; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
        .animate-pulse { animation: pulse 2s infinite; }
        
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.3); }
    </style>
</head>
<body class="font-sans">
<?php require_once 'navbar.php'; ?>

<div class="p-4 md:p-8">

    <div class="mb-8">
        <h1 class="text-3xl font-bold text-white mb-1">Sync <span class="text-blue-400">Agents</span></h1>
        <p class="text-slate-400 text-sm">Monitor and control all registered sync agents in real time.</p>
    </div>

    <?php if ($msg): ?>
    <div class="mb-6 glass-panel px-5 py-3 text-green-300 text-sm flex items-center gap-2">
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
        <?php echo $msg; ?>
    </div>
    <?php
endif; ?>

    <?php if (empty($agents)): ?>
    <div class="glass-panel p-10 text-center text-slate-500">
        No agents have registered yet. Start an agent at a restaurant location to see it here.
    </div>
    <?php
else: ?>

    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <?php foreach ($agents as $ag):
        if (!can_access_restaurant($ag['restaurante']))
            continue;

        $hb_str = $ag['last_heartbeat'];
        $hb = $hb_str ? new DateTime($hb_str) : null;

        // El servidor MySQL calcula "min_ago" de manera exacta con TIMESTAMPDIFF
        $diff_min = is_numeric($ag['min_ago']) ? (int)$ag['min_ago'] : 9999;

        $online_class = $diff_min <= 5 ? 'dot-online' : ($diff_min <= 15 ? 'dot-warn' : 'dot-offline');
        $online_label = $diff_min <= 5 ? 'Online' : ($diff_min <= 15 ? 'Delayed' : 'Offline');
        $status = strtolower($ag['status'] ?? 'stopped');
        $badge_class = "badge-$status";
        $pending = $ag['pending_command'] ?? '';

        // Fetch logs (last 50 global sync attempts) for this agent
        $stmtLogs = $pdo->prepare("SELECT fecha_ciclo, dias_sincronizados, detalle FROM agent_sync_history WHERE id_sync = :id ORDER BY fecha_ciclo DESC LIMIT 50");
        $stmtLogs->execute([':id' => $ag['id_sync']]);
        $agentLogs = $stmtLogs->fetchAll();
?>
        <div class="glass-panel p-6">
            <!-- Header -->
            <div class="flex items-start justify-between mb-4">
                <div>
                    <div class="flex items-center gap-2 mb-1">
                        <span class="w-2.5 h-2.5 rounded-full <?php echo $online_class; ?> <?php echo $diff_min <= 5 ? 'animate-pulse' : ''; ?>"></span>
                        <span class="font-bold text-white text-base"><?php echo htmlspecialchars($ag['restaurante']); ?></span>
                    </div>
                    <code class="text-xs text-slate-500 font-mono"><?php echo htmlspecialchars($ag['id_sync']); ?></code>
                </div>
                <div class="flex flex-col items-end gap-1">
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-slate-500"><?php echo $online_label; ?></span>
                        <span class="text-xs px-2 py-0.5 rounded-full font-semibold <?php echo $badge_class; ?>">
                            <?php echo strtoupper($status); ?>
                        </span>
                    </div>
                    <span class="text-[10px] text-slate-500 mt-1">
                        Page refreshes every 60s &nbsp;·&nbsp; <a href="agents.php" class="text-blue-500 hover:text-blue-400 hover:underline">Refresh now</a>
                    </span>
                </div>
            </div>

            <!-- Details Grid -->
            <div class="grid grid-cols-2 gap-x-4 gap-y-2 text-xs mb-5">
                <div>
                    <span class="text-slate-500 block">IP LAN / WAN</span>
                    <span class="text-slate-200 font-mono">
                        <?php echo htmlspecialchars($ag['ip_lan'] ?? '—'); ?> / 
                        <span class="text-blue-300"><?php echo htmlspecialchars($ag['ip_public'] ?? '—'); ?></span>
                    </span>
                </div>
                <div>
                    <span class="text-slate-500 block">Version</span>
                    <span class="text-slate-200">v<?php echo htmlspecialchars($ag['version'] ?? '?'); ?></span>
                </div>
                <div class="col-span-2">
                    <span class="text-slate-500 block">DB Path</span>
                    <span class="text-slate-400 font-mono break-all"><?php echo htmlspecialchars($ag['db_path'] ?? '—'); ?></span>
                </div>
                <div>
                    <span class="text-slate-500 block">Last Heartbeat</span>
                    <span class="text-slate-200">
                        <?php echo $hb ? $hb->format('Y-m-d H:i:s') : '—'; ?>
                        <?php if ($hb): ?>
                            <span class="text-slate-500">(<?php echo $diff_min; ?> min ago)</span>
                        <?php
        endif; ?>
                    </span>
                </div>
                <div>
                    <span class="text-slate-500 block">Pending Command</span>
                    <?php if ($pending): ?>
                        <span class="text-yellow-400 font-semibold"><?php echo htmlspecialchars($pending); ?></span>
                    <?php
        else: ?>
                        <span class="text-slate-600">—</span>
                    <?php
        endif; ?>
                </div>
            </div>

            <!-- Command Bar -->
            <?php if (can_delete_days()): ?>
            <div class="flex items-center gap-3 mb-4 mt-4">
                <form method="POST" class="flex-1 flex items-center gap-3">
                    <input type="hidden" name="id_sync" value="<?php echo htmlspecialchars($ag['id_sync']); ?>">
                    <select name="command" class="flex-1 bg-slate-800 border border-slate-600 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500">
                        <option value="">— Select Command —</option>
                        <option value="sync_now">⚡ Force Sync Now</option>
                        <option value="clear_logs">🗑  Clear Logs</option>
                        <option value="pause">⏸  Pause Sync</option>
                        <option value="resume">▶  Resume Sync</option>
                        <option value="get_config">📡 Fetch Latest Config from Agent</option>
                    </select>
                    <button type="submit"
                        onclick="return this.form.command.value ? confirm('Send command to this agent?') : (alert('Select a command first.'), false)"
                        class="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold py-2 px-4 rounded-lg transition-colors whitespace-nowrap">
                        Send Command
                    </button>
                </form>
                <form method="POST" class="inline" onsubmit="return confirm('¿Seguro que deseas eliminar este Agente de la lista? Perderás todo el historial de Sync.');">
                    <input type="hidden" name="id_sync" value="<?php echo htmlspecialchars($ag['id_sync']); ?>">
                    <input type="hidden" name="action" value="delete_agent">
                    <button type="submit" class="bg-red-900/40 hover:bg-red-700 text-red-100 text-xs font-semibold py-2 px-3 rounded-lg border border-red-700/50 transition-colors" title="Eliminar Agente">
                        ✕ Eliminar Agente
                    </button>
                </form>
                <button type="button" onclick="openConfigModal('<?php echo htmlspecialchars($ag['id_sync']); ?>', <?php echo htmlspecialchars(json_encode($ag['config_json'] ?? '')); ?>)" class="bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold py-2 px-3 rounded-lg transition-colors border border-slate-600" title="Editar Configuración Remota">
                    🛠️ Config JSON
                </button>
            </div>
            <?php
        endif; ?>

            <!-- Sync Logs -->
            <div class="mb-5 bg-slate-800/50 rounded-lg p-3">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs text-slate-400 font-bold uppercase tracking-wider">Sync History</span>
                    <?php if (can_delete_days()): ?>
                    <form method="POST" class="inline" onsubmit="return confirm('Are you sure you want to permanently delete all sync history for this agent?');">
                        <input type="hidden" name="id_sync" value="<?php echo htmlspecialchars($ag['id_sync']); ?>">
                        <input type="hidden" name="action" value="clear_dashboard_logs">
                        <button type="submit" class="text-slate-500 hover:text-red-400 transition-colors" title="Delete Sync History">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                        </button>
                    </form>
                    <?php
        endif; ?>
                </div>
                <?php if (empty($agentLogs)): ?>
                    <div class="text-slate-500 text-xs italic">No sync logs found yet.</div>
                <?php
        else: ?>
                    <div class="space-y-1 overflow-y-auto max-h-40 pr-2 custom-scrollbar">
                        <?php foreach ($agentLogs as $log): ?>
                            <div class="flex justify-between items-center text-xs">
                                <?php
                $dias_count = (int)$log['dias_sincronizados'];
                $fecha_display = htmlspecialchars($log['fecha_ciclo']);
                if ($dias_count === 0) {
                    echo '<span class="text-slate-500 font-mono">Synced at ' . $fecha_display . ', 0 dias sincronizados.</span>';
                }
                else {
                    echo '<span class="text-emerald-400 font-mono">Synced at ' . $fecha_display . ', ' . htmlspecialchars($log['detalle']) . '</span>';
                }
?>
                            </div>
                        <?php
            endforeach; ?>
                    </div>
                <?php
        endif; ?>
            </div>


        </div>
        <?php
    endforeach; ?>
    </div>

    <?php
endif; ?>

</div>

<!-- Config Modal -->
<div id="configModal" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <div class="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-11/12 max-w-2xl overflow-hidden relative">
        <div class="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
            <h3 class="text-white font-bold text-lg">🛠️ Remote Config</h3>
            <button type="button" onclick="closeConfigModal()" class="text-slate-400 hover:text-white transition-colors text-xl font-bold px-2">&times;</button>
        </div>
        <form method="POST" class="p-5" onsubmit="return confirm('¿Seguro que deseas sobrescribir la configuración remota de este Agente?');">
            <input type="hidden" name="action" value="save_config">
            <input type="hidden" name="id_sync" id="config_id_sync" value="">
            <div class="mb-4">
                <label class="block text-slate-400 text-xs font-bold mb-2 uppercase tracking-wider">Config JSON Payload</label>
                <textarea name="config_json" id="config_json_field" rows="12" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-sm font-mono text-slate-300 focus:outline-none focus:border-blue-500 custom-scrollbar" spellcheck="false"></textarea>
                <p class="text-xs text-slate-500 mt-2">Este JSON se transmitirá al Agente local en su siguiente latido (cada 60s) y se sobreescribirá en el local.</p>
            </div>
            <div class="flex justify-end gap-3 mt-6">
                <button type="button" onclick="closeConfigModal()" class="bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold py-2 px-4 rounded-lg transition-colors border border-slate-700">Cancel</button>
                <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold py-2 px-6 rounded-lg transition-colors shadow-lg shadow-blue-600/20">💾 Save Configuration</button>
            </div>
        </form>
    </div>
</div>

<script>
function openConfigModal(idSync, rawJson) {
    document.getElementById('config_id_sync').value = idSync;
    
    let displayJson = rawJson;
    try {
        if(rawJson) {
            displayJson = JSON.stringify(JSON.parse(rawJson), null, 4);
        } else {
            displayJson = "{\n    \n}";
        }
    } catch(e) { }
    
    document.getElementById('config_json_field').value = displayJson;
    document.getElementById('configModal').classList.remove('hidden');
}
function closeConfigModal() {
    document.getElementById('configModal').classList.add('hidden');
}
// Close on outside click
document.getElementById('configModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeConfigModal();
    }
});

setTimeout(function(){ location.reload(); }, 60000);
</script>

<footer class="gi-footer">
    &copy; <?php echo date('Y'); ?> <a href="https://galileoinnova.com" target="_blank">GalileoInnova</a>
    &middot; Restaurant Intelligence Suite &middot; All rights reserved.
</footer>
</body>
</html>
