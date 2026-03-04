import ftplib, io

ftp = ftplib.FTP('lazydonkeyrestaurant.com')
ftp.login('restaurantes', 'gcode2025!')
ftp.cwd('httpdocs/restaurantes')

with open(r'c:\ICOM\Database\dashboard_php\reporte_mesero.php', 'rb') as f:
    content = f.read().replace(b'\r\n', b'\n')
try: ftp.delete('reporte_mesero.php')
except: pass
ftp.storbinary('STOR reporte_mesero.php', io.BytesIO(content))
sz = ftp.size('reporte_mesero.php')
print(f'reporte_mesero.php: {sz:,} bytes')
ftp.quit()
print('OK')
