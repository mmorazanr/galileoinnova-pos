import ftplib
import urllib.request

try:
    ftp = ftplib.FTP('lazydonkeyrestaurant.com')
    ftp.login('restaurantes', 'gcode2025!')
    ftp.cwd('httpdocs/restaurantes')
    with open(r'c:\ICOM\Database\dashboard_php\flush_hosts.php', 'rb') as f:
        ftp.storbinary('STOR flush_hosts.php', f)
    ftp.quit()
    print("Uploaded flush_hosts.php")
    
    # Execute the file via HTTP
    resp = urllib.request.urlopen("https://lazydonkeyrestaurant.com/restaurantes/flush_hosts.php", timeout=10)
    print("Response:", resp.read().decode('utf-8').strip())
except Exception as e:
    print("Error:", e)
