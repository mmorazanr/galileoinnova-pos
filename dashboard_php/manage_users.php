<?php
require_once 'auth.php';
require_once 'config.php';

// Solo el rol Owner puede acceder a esta página
if (!is_owner()) {
    die("<h1>Access Denied</h1><p>You do not have permission to access the User Management panel.</p>");
}

$page_title = 'User Management';
$msg = '';
$err = '';

// ── Handle Form Submissions ───────────────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';

    if ($action === 'create') {
        $username = trim($_POST['username'] ?? '');
        $password = trim($_POST['password'] ?? '');
        $role = $_POST['role'] ?? 'manager';
        $allowed_rests = $_POST['allowed_restaurants'] ?? [];
        if ($role === 'owner') {
            $allowed_rests = ["ALL"];
        }
        $can_view = isset($_POST['can_view_days']) ? 1 : 0;
        $can_delete = isset($_POST['can_delete_days']) ? 1 : 0;

        if (empty($username) || empty($password)) {
            $err = "Username and password are required for new users.";
        }
        else {
            // Hash the password with PHP's native bcrypt wrapper
            $hash = password_hash($password, PASSWORD_DEFAULT);
            $rests_json = json_encode($allowed_rests, JSON_UNESCAPED_UNICODE);

            try {
                $stmt = $pdo->prepare("INSERT INTO dashboard_users (username, password_hash, role, allowed_restaurants, can_view_days, can_delete_days) VALUES (:u, :p, :r, :a, :cv, :cd)");
                $stmt->execute([
                    ':u' => $username, ':p' => $hash, ':r' => $role,
                    ':a' => $rests_json, ':cv' => $can_view, ':cd' => $can_delete
                ]);
                $msg = "User '$username' created successfully.";
            }
            catch (PDOException $e) {
                if ($e->getCode() == 23000) { // Integrated Integrity constraint violation / Duplicate key
                    $err = "User '$username' already exists.";
                }
                else {
                    $err = "Database error: " . $e->getMessage();
                }
            }
        }
    }
    elseif ($action === 'delete') {
        $del_id = (int)($_POST['user_id'] ?? 0);
        // Evitar que el admin se borre a sí mismo accidentalmente
        if ($del_id != $_SESSION['gi_user_id'] && $del_id > 0) {
            $stmt = $pdo->prepare("DELETE FROM dashboard_users WHERE id = :id");
            $stmt->execute([':id' => $del_id]);
            $msg = "User deleted successfully.";
        }
        else {
            $err = "Cannot delete the currently logged-in user.";
        }
    }
}

// ── Fetch Data ────────────────────────────────────────────────────────────
// Fetch all users
$users = $pdo->query("SELECT id, username, role, allowed_restaurants, can_view_days, can_delete_days, created_at FROM dashboard_users ORDER BY role ASC, username ASC")->fetchAll();

// Fetch all distinct restaurants for the checkbox list
$stmt_all = $pdo->query("SELECT DISTINCT restaurante FROM restaurantes_diario_media ORDER BY restaurante ASC");
$all_db_restaurants = $stmt_all->fetchAll(PDO::FETCH_COLUMN);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manage Users — GalileoInnova</title>
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
        .form-input {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255,255,255,0.1);
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            width: 100%;
            font-size: 14px;
        }
        .form-input:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.2); }
        .checkbox-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
        }
        .role-badge {
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 9999px;
            text-transform: uppercase;
            font-weight: bold;
        }
        .role-owner { background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.4); }
        .role-manager { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }
    </style>
</head>
<body class="font-sans pb-16">
<?php require_once 'navbar.php'; ?>

<div class="p-4 md:p-8 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="mb-8 flex justify-between items-end">
        <div>
            <h1 class="text-3xl font-bold text-white mb-1">User <span class="text-blue-400">Management</span></h1>
            <p class="text-slate-400 text-sm">Create managers and configure granular restaurant permissions (CRUD).</p>
        </div>
        <button onclick="document.getElementById('createUserModal').classList.remove('hidden')" class="bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2 px-5 rounded-lg shadow-lg flex items-center gap-2 transition-all">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            New User
        </button>
    </div>

    <!-- Messages -->
    <?php if ($msg): ?>
        <div class="mb-6 glass-panel px-5 py-4 text-emerald-300 flex items-center gap-3 border-emerald-500/30">
            <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            <?php echo $msg; ?>
        </div>
    <?php
endif; ?>
    <?php if ($err): ?>
        <div class="mb-6 glass-panel px-5 py-4 text-red-300 flex items-center gap-3 border-red-500/30 bg-red-900/10">
            <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
            <?php echo $err; ?>
        </div>
    <?php
endif; ?>

    <!-- User List -->
    <div class="glass-panel overflow-hidden">
        <table class="w-full text-left text-sm">
            <thead class="bg-slate-800/80">
                <tr>
                    <th class="p-4 font-semibold text-slate-300">Username</th>
                    <th class="p-4 font-semibold text-slate-300">Role</th>
                    <th class="p-4 font-semibold text-slate-300">Permissions</th>
                    <th class="p-4 font-semibold text-slate-300">Assigned Restaurants</th>
                    <th class="p-4 font-semibold text-slate-300 text-right">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/50">
                <?php foreach ($users as $u):
    $role_cls = $u['role'] === 'owner' ? 'role-owner' : 'role-manager';
    $rests = json_decode($u['allowed_restaurants'], true) ?? [];
    if (in_array('ALL', $rests))
        $rests_disp = '<span class="text-blue-300 font-medium">All Restaurants</span>';
    else
        $rests_disp = count($rests) > 0 ? implode(', ', array_map('htmlspecialchars', $rests)) : '<span class="text-slate-500 italic">None</span>';
?>
                <tr class="hover:bg-slate-800/30 transition-colors">
                    <td class="p-4 align-top">
                        <div class="font-bold text-base text-white"><?php echo htmlspecialchars($u['username']); ?></div>
                        <div class="text-xs text-slate-500 mt-1">ID: <?php echo $u['id']; ?></div>
                    </td>
                    <td class="p-4 align-top">
                        <span class="role-badge <?php echo $role_cls; ?>"><?php echo htmlspecialchars($u['role']); ?></span>
                    </td>
                    <td class="p-4 align-top text-xs space-y-1">
                        <div class="flex items-center gap-2">
                            <?php if ($u['can_view_days']): ?> <span class="text-emerald-400">✔ View Days</span>
                            <?php
    else: ?> <span class="text-slate-600">✖ View Days</span> <?php
    endif; ?>
                        </div>
                        <div class="flex items-center gap-2">
                            <?php if ($u['can_delete_days']): ?> <span class="text-emerald-400">✔ Delete Syncs</span>
                            <?php
    else: ?> <span class="text-slate-600">✖ Delete Syncs</span> <?php
    endif; ?>
                        </div>
                    </td>
                    <td class="p-4 align-top text-xs text-slate-300 max-w-sm leading-relaxed">
                        <?php echo $rests_disp; ?>
                    </td>
                    <td class="p-4 align-top text-right">
                        <form method="POST" onsubmit="return confirm('Are you sure you want to completely delete user \'<?php echo htmlspecialchars($u['username']); ?>\'?');">
                            <input type="hidden" name="action" value="delete">
                            <input type="hidden" name="user_id" value="<?php echo $u['id']; ?>">
                            <button type="submit" class="text-slate-400 hover:text-red-400 transition-colors p-2" title="Delete User">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                            </button>
                        </form>
                    </td>
                </tr>
                <?php
endforeach; ?>
            </tbody>
        </table>
    </div>
</div>

<!-- Modal Create User -->
<div id="createUserModal" class="hidden fixed inset-0 z-50 flex items-center justify-center p-4" style="background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);">
    <div class="glass-panel w-full max-w-2xl bg-slate-900 border-slate-600 shadow-2xl relative flex flex-col max-h-[90vh]">
        <div class="p-6 border-b border-slate-700 flex justify-between items-center shrink-0">
            <h2 class="text-xl font-bold">Create New User</h2>
            <button onclick="document.getElementById('createUserModal').classList.add('hidden')" class="text-slate-400 hover:text-white">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
        </div>
        
        <div class="p-6 overflow-y-auto custom-scrollbar">
            <form id="createUserForm" method="POST" class="space-y-5">
                <input type="hidden" name="action" value="create">
                
                <div class="grid grid-cols-2 gap-5">
                    <div>
                        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Username</label>
                        <input type="text" name="username" required class="form-input" placeholder="e.g. manager_tx">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Password</label>
                        <input type="password" name="password" required class="form-input" placeholder="••••••••">
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Role Type</label>
                    <select name="role" id="roleSelector" class="form-input" onchange="toggleRestList()">
                        <option value="manager" selected>Manager (Restricted Access)</option>
                        <option value="owner">Owner (Full System Access)</option>
                    </select>
                </div>

                <div class="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                    <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Feature Permissions</label>
                    <div class="flex gap-6">
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" name="can_view_days" value="1" checked class="w-4 h-4 rounded bg-slate-700 border-slate-600 text-blue-500 focus:ring-blue-500">
                            <span class="text-sm">View Days (Daily Report)</span>
                        </label>
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" name="can_delete_days" value="1" class="w-4 h-4 rounded bg-slate-700 border-slate-600 text-blue-500 focus:ring-blue-500">
                            <span class="text-sm">Delete Sync Logs (Agents Area)</span>
                        </label>
                    </div>
                </div>

                <div id="restaurantSelectorGroup">
                    <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Allowed Restaurants</label>
                    <p class="text-xs text-slate-500 mb-3">Select the specific branches this manager is allowed to see data from.</p>
                    
                    <div class="checkbox-grid max-h-48 overflow-y-auto p-4 border border-slate-700 rounded-lg custom-scrollbar bg-slate-900/50">
                        <?php foreach ($all_db_restaurants as $r): ?>
                        <label class="flex items-start gap-2 cursor-pointer hover:bg-slate-800/50 p-1.5 rounded transition-colors">
                            <input type="checkbox" name="allowed_restaurants[]" value="<?php echo htmlspecialchars($r); ?>" class="w-4 h-4 mt-0.5 rounded bg-slate-700 border-slate-600 text-blue-500 focus:ring-blue-500">
                            <span class="text-sm text-slate-300 leading-tight"><?php echo htmlspecialchars($r); ?></span>
                        </label>
                        <?php
endforeach; ?>
                    </div>
                </div>
            </form>
        </div>
        
        <div class="p-6 border-t border-slate-700 bg-slate-800/50 rounded-b-2xl flex justify-end gap-3 shrink-0">
            <button onclick="document.getElementById('createUserModal').classList.add('hidden')" class="px-5 py-2 rounded-lg font-semibold text-sm text-slate-300 hover:bg-slate-700 transition-colors">Cancel</button>
            <button type="submit" form="createUserForm" class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-semibold text-sm transition-colors shadow-lg">Create User</button>
        </div>
    </div>
</div>

<script>
// Hide the restaurant list if 'owner' is selected since owner gets ALL implicitly
function toggleRestList() {
    const role = document.getElementById('roleSelector').value;
    const restGroup = document.getElementById('restaurantSelectorGroup');
    if (role === 'owner') {
        restGroup.style.display = 'none';
        // Uncheck all so we don't send garbage
        const boxes = restGroup.querySelectorAll('input[type="checkbox"]');
        boxes.forEach(b => b.checked = false);
    } else {
        restGroup.style.display = 'block';
    }
}
</script>

</body>
</html>
