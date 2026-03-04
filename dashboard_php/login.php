<?php
session_start();

define('APP_USER', 'admin');
define('APP_PASS', 'gcode2025!');

$error = '';
$next = $_GET['next'] ?? 'index.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  $user = trim($_POST['username'] ?? '');
  $pass = trim($_POST['password'] ?? '');

  if ($user === APP_USER && $pass === APP_PASS) {
    $_SESSION['gi_auth'] = true;
    $_SESSION['gi_user'] = $user;
    $_SESSION['gi_time'] = date('Y-m-d H:i:s');
    // Usar solo el nombre base del archivo destino para evitar path duplicado
    // Ej: /restaurantes/index.php  →  index.php
    $allowed = ['index.php', 'reporte_diario.php', 'admin_datos.php'];
    $raw = $_POST['next'] ?? 'index.php';
    $dest = basename(parse_url($raw, PHP_URL_PATH) ?? 'index.php');
    if (!in_array($dest, $allowed))
      $dest = 'index.php';
    header('Location: ' . $dest);
    exit;
  }
  else {
    $error = 'Usuario o contraseña incorrectos.';
    // Pequeño delay anti-brute force
    sleep(1);
  }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Login · GalileoInnova</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #060d1f;
    background-image:
      radial-gradient(ellipse at 20% 50%, rgba(30,64,175,0.25) 0%, transparent 60%),
      radial-gradient(ellipse at 80% 20%, rgba(79,30,175,0.20) 0%, transparent 55%),
      radial-gradient(ellipse at 60% 80%, rgba(15,50,130,0.15) 0%, transparent 50%);
    font-family: 'Segoe UI', system-ui, sans-serif;
    color: #e2e8f0;
    overflow: hidden;
  }

  /* Partículas / estrellas */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      radial-gradient(1px 1px at 15% 25%, rgba(255,255,255,0.4) 0%, transparent 100%),
      radial-gradient(1px 1px at 45% 10%, rgba(255,255,255,0.3) 0%, transparent 100%),
      radial-gradient(1px 1px at 75% 40%, rgba(255,255,255,0.35) 0%, transparent 100%),
      radial-gradient(1px 1px at 30% 70%, rgba(255,255,255,0.25) 0%, transparent 100%),
      radial-gradient(1px 1px at 60% 85%, rgba(255,255,255,0.3) 0%, transparent 100%),
      radial-gradient(1px 1px at 85% 65%, rgba(255,255,255,0.25) 0%, transparent 100%),
      radial-gradient(1px 1px at 10% 90%, rgba(255,255,255,0.2) 0%, transparent 100%),
      radial-gradient(1px 1px at 90% 10%, rgba(255,255,255,0.35) 0%, transparent 100%);
    pointer-events: none;
    z-index: 0;
  }

  .card {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 400px;
    margin: 16px;
    background: rgba(15, 25, 55, 0.85);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 24px;
    padding: 44px 40px 40px;
    box-shadow: 0 32px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(59,130,246,0.06);
    animation: slideUp .45s cubic-bezier(.16,1,.3,1) both;
  }
  @keyframes slideUp {
    from { opacity: 0; transform: translateY(30px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .logo-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
    margin-bottom: 32px;
  }
  .logo-wrap img {
    width: 90px;
    height: 90px;
    object-fit: contain;
    filter: drop-shadow(0 0 18px rgba(59,130,246,0.5));
  }
  .logo-wrap h1 {
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #f1f5f9;
  }
  .logo-wrap h1 span { color: #60a5fa; }
  .logo-wrap p {
    font-size: 12px;
    color: #475569;
    text-align: center;
    margin-top: -8px;
  }

  .field { margin-bottom: 18px; }
  .field label {
    display: block;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: #64748b;
    margin-bottom: 7px;
  }
  .field input {
    width: 100%;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    color: #f1f5f9;
    font-size: 14px;
    padding: 11px 14px;
    outline: none;
    transition: border-color .2s, box-shadow .2s;
  }
  .field input:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
  }

  .alert {
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 10px;
    color: #fca5a5;
    font-size: 13px;
    padding: 10px 14px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .btn-login {
    width: 100%;
    background: linear-gradient(135deg, #1d4ed8 0%, #4f46e5 100%);
    color: white;
    font-size: 14px;
    font-weight: 700;
    padding: 13px;
    border: none;
    border-radius: 10px;
    cursor: pointer;
    transition: opacity .2s, transform .1s;
    letter-spacing: .02em;
    margin-top: 4px;
    box-shadow: 0 6px 20px rgba(29,78,216,0.4);
  }
  .btn-login:hover { opacity: .92; }
  .btn-login:active { transform: scale(.98); }

  .footer {
    text-align: center;
    margin-top: 28px;
    font-size: 11px;
    color: #1e3a5f;
  }
  .footer a { color: #2563eb; text-decoration: none; }
  .footer a:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="card">
  <!-- Logo -->
  <div class="logo-wrap">
    <img src="logo_galileoinnova.jpg" alt="GalileoInnova Logo">
    <h1>Galileo<span>Innova</span></h1>
    <p>Restaurant Analytics Platform</p>
  </div>

  <!-- Error -->
  <?php if ($error): ?>
  <div class="alert">⚠ <?php echo htmlspecialchars($error); ?></div>
  <?php
endif; ?>

  <!-- Form -->
  <form method="POST" autocomplete="off">
    <input type="hidden" name="next" value="<?php echo htmlspecialchars($next); ?>">

    <div class="field">
      <label for="username">Usuario</label>
      <input type="text" id="username" name="username" placeholder="admin"
             value="<?php echo htmlspecialchars($_POST['username'] ?? ''); ?>"
             autofocus autocomplete="username">
    </div>
    <div class="field">
      <label for="password">Contraseña</label>
      <input type="password" id="password" name="password" placeholder="••••••••"
             autocomplete="current-password">
    </div>
    <button type="submit" class="btn-login">Ingresar →</button>
  </form>

  <div class="footer">
    <a href="https://galileoinnova.com" target="_blank">galileoinnova.com</a> &middot;
    Restaurant Intelligence Suite
  </div>
</div>
</body>
</html>
