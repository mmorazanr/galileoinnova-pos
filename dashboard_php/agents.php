<?php
require_once 'auth.php';
require_once 'config.php';

$page_title = 'Sync Agents';
$msg = '';

// ── Handle Command Submit ─────────────────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !empty($_POST['id_sync']) && !empty($_POST['command'])) {
    $id = $_POST['id_sync'];
    $cmd = $_POST['command'];
    $allowed = ['clear_logs', 'pause', 'resume', 'sync_now'];
    if (in_array($cmd, $allowed)) {
        $stmt = $pdo->prepare("UPDATE sync_agents SET pending_command = :cmd WHERE id_sync = :id");
        $stmt->execute([':cmd' => $cmd, ':id' => $id]);
        $msg = "Command '$cmd' queued for agent: " . htmlspecialchars($id);
    }
}

// ── Fetch All Agents ──────────────────────────────────────────────────────
$agents = $pdo->query("SELECT * FROM sync_agents ORDER BY last_heartbeat DESC")->fetchAll();
$now = new DateTime();
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
        $hb = $ag['last_heartbeat'] ? new DateTime($ag['last_heartbeat']) : null;
        $diff_min = $hb ? round(($now->getTimestamp() - $hb->getTimestamp()) / 60) : 9999;
        $online_class = $diff_min <= 5 ? 'dot-online' : ($diff_min <= 15 ? 'dot-warn' : 'dot-offline');
        $online_label = $diff_min <= 5 ? 'Online' : ($diff_min <= 15 ? 'Delayed' : 'Offline');
        $status = strtolower($ag['status'] ?? 'stopped');
        $badge_class = "badge-$status";
        $pending = $ag['pending_command'] ?? '';
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
                <div class="flex flex-col items-end gap-2">
                    <span class="text-xs px-2 py-0.5 rounded-full font-semibold <?php echo $badge_class; ?>">
                        <?php echo strtoupper($status); ?>
                    </span>
                    <span class="text-xs text-slate-500"><?php echo $online_label; ?></span>
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
            <form method="POST" class="flex items-center gap-3 border-t border-slate-700 pt-4">
                <input type="hidden" name="id_sync" value="<?php echo htmlspecialchars($ag['id_sync']); ?>">
                <select name="command" class="flex-1 bg-slate-800 border border-slate-600 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500">
                    <option value="">— Select Command —</option>
                    <option value="sync_now">⚡ Force Sync Now</option>
                    <option value="clear_logs">🗑  Clear Logs</option>
                    <option value="pause">⏸  Pause Sync</option>
                    <option value="resume">▶  Resume Sync</option>
                </select>
                <button type="submit"
                    onclick="return this.form.command.value ? confirm('Send command to this agent?') : (alert('Select a command first.'), false)"
                    class="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold py-2 px-4 rounded-lg transition-colors whitespace-nowrap">
                    Send Command
                </button>
            </form>
        </div>
        <?php
    endforeach; ?>
    </div>

    <?php
endif; ?>

    <!-- Auto-refresh note -->
    <p class="text-center text-slate-600 text-xs mt-8">
        Page refreshes automatically every 60 seconds &nbsp;·&nbsp;
        <a href="agents.php" class="text-blue-600 hover:underline">Refresh now</a>
    </p>
</div>

<script>
setTimeout(function(){ location.reload(); }, 60000);
</script>

<footer class="gi-footer">
    &copy; <?php echo date('Y'); ?> <a href="https://galileoinnova.com" target="_blank">GalileoInnova</a>
    &middot; Restaurant Intelligence Suite &middot; All rights reserved.
</footer>
</body>
</html>
