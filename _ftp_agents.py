import ftplib

ftp = ftplib.FTP('lazydonkeyrestaurant.com')
ftp.login('restaurantes', 'gcode2025!')
ftp.cwd('httpdocs/restaurantes')

files = {
    'agents.php': r'c:\ICOM\Database\dashboard_php\agents.php',
    'navbar.php':  r'c:\ICOM\Database\dashboard_php\navbar.php',
    'auth.php': r'c:\ICOM\Database\dashboard_php\auth.php',
    'login.php': r'c:\ICOM\Database\dashboard_php\login.php',
    'reporte_diario.php': r'c:\ICOM\Database\dashboard_php\reporte_diario.php',
}

for remote_name, local_path in files.items():
    with open(local_path, 'rb') as f:
        ftp.storbinary(f'STOR {remote_name}', f)
    print(f"Uploaded: {remote_name}")

ftp.quit()
print("FTP DONE")
