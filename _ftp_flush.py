import ftplib

ftp = ftplib.FTP('lazydonkeyrestaurant.com')
ftp.login('restaurantes', 'gcode2025!')
ftp.cwd('httpdocs/restaurantes')

file_path = r'c:\ICOM\Database\dashboard_php\flush.php'
with open(file_path, 'rb') as f:
    ftp.storbinary('STOR flush.php', f)
print("Uploaded flush.php")
ftp.quit()
