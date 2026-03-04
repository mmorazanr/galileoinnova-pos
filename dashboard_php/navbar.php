<?php
/**
 * Navbar / header compartido para todas las páginas del dashboard.
 * Variables que acepta:
 *   $page_title  — título de la página actual (string)
 *   $extra_btns  — HTML adicional de botones (string, opcional)
 */
$page_title = $page_title ?? 'Dashboard';
$extra_btns = $extra_btns ?? '';
$gi_user = $_SESSION['gi_user'] ?? 'admin';
?>
<!-- ── GalileoInnova Topbar ─────────────────────────────────────────── -->
<header class="gi-topbar">
  <div class="gi-brand">
    <a href="https://galileoinnova.com" target="_blank" class="gi-logo-link">
      <img src="logo_galileoinnova.jpg" alt="GalileoInnova" class="gi-logo">
    </a>
    <div class="gi-brand-text">
      <span class="gi-brand-name">GalileoInnova</span>
      <span class="gi-brand-subtitle">Restaurant Intelligence</span>
    </div>
  </div>

  <nav class="gi-nav">
    <a href="index.php"        class="gi-nav-btn <?php echo strpos($_SERVER['PHP_SELF'], 'index.php') !== false ? 'active' : ''; ?>">📊 Dashboard</a>
    <a href="reporte_diario.php" class="gi-nav-btn <?php echo strpos($_SERVER['PHP_SELF'], 'reporte_diario') !== false ? 'active' : ''; ?>">📅 Daily Report</a>
    <a href="#" onclick="window.open('reporte_mesero.php','rep_mesero','width=1150,height=820,scrollbars=yes,resizable=yes');return false;"
       class="gi-nav-btn" style="color:#c084fc;">👤 Mesero</a>
    <a href="admin_datos.php"  class="gi-nav-btn gi-nav-admin <?php echo strpos($_SERVER['PHP_SELF'], 'admin_datos') !== false ? 'active' : ''; ?>">🗂 Admin</a>
    <?php echo $extra_btns; ?>
  </nav>

  <div class="gi-user-info">
    <span class="gi-avatar">👤</span>
    <span class="gi-username"><?php echo htmlspecialchars($gi_user); ?></span>
    <a href="?logout=1" class="gi-logout">Salir ↗</a>
  </div>
</header>

<style>
/* ── GalileoInnova topbar styles ────────────────────────────────────── */
.gi-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  background: rgba(6,12,35,0.85);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(59,130,246,0.15);
  padding: 10px 20px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 20px rgba(0,0,0,0.4);
}
.gi-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; }
.gi-logo-link { display: flex; align-items: center; }
.gi-logo { width: 40px; height: 40px; object-fit: contain; filter: drop-shadow(0 0 8px rgba(59,130,246,0.6)); }
.gi-brand-text { display: flex; flex-direction: column; line-height: 1.1; }
.gi-brand-name { font-size: 16px; font-weight: 800; color: #f1f5f9; letter-spacing: -0.02em; }
.gi-brand-subtitle { font-size: 9px; color: #3b82f6; text-transform: uppercase; letter-spacing: .1em; font-weight: 600; }

.gi-nav { display: flex; gap: 4px; flex-wrap: wrap; }
.gi-nav-btn {
  background: transparent;
  color: #94a3b8;
  text-decoration: none;
  font-size: 12px;
  font-weight: 600;
  padding: 7px 14px;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all .15s;
  white-space: nowrap;
}
.gi-nav-btn:hover   { background: rgba(255,255,255,0.06); color: #e2e8f0; }
.gi-nav-btn.active  { background: rgba(59,130,246,0.15); color: #60a5fa; border-color: rgba(59,130,246,0.3); }
.gi-nav-admin       { color: #f59e0b; }
.gi-nav-admin:hover { color: #fbbf24; background: rgba(245,158,11,0.1); }
.gi-nav-admin.active{ background: rgba(245,158,11,0.12); border-color: rgba(245,158,11,0.3); }

.gi-user-info { display: flex; align-items: center; gap: 10px; }
.gi-avatar    { font-size: 18px; }
.gi-username  { font-size: 12px; color: #64748b; display: none; }
@media(min-width:640px){ .gi-username { display: inline; } }
.gi-logout {
  font-size: 11px;
  color: #ef4444;
  text-decoration: none;
  padding: 5px 10px;
  border: 1px solid rgba(239,68,68,0.25);
  border-radius: 6px;
  transition: all .15s;
}
.gi-logout:hover { background: rgba(239,68,68,0.1); }

/* ── GalileoInnova footer ───────────────────────────────────────────── */
.gi-footer {
  text-align: center;
  padding: 16px;
  font-size: 11px;
  color: #1e3a5f;
  border-top: 1px solid rgba(255,255,255,0.04);
  margin-top: 32px;
}
.gi-footer a { color: #2563eb; text-decoration: none; }
.gi-footer a:hover { text-decoration: underline; }
</style>
