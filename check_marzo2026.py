import pyodbc, os, glob

# Buscar CBOData_s.mdb en la carpeta Marzo2026
folder = r"C:\ICOM\Database\Marzo6026"
if not os.path.exists(folder):
    folder = r"C:\ICOM\Database\Marzo2026"

print(f"Buscando en: {folder}")
print(f"Existe: {os.path.exists(folder)}")
print()

# Listar archivos .mdb en esa carpeta
mdb_files = glob.glob(os.path.join(folder, "*.mdb")) + glob.glob(os.path.join(folder, "*.accdb"))
print("Archivos MDB encontrados:")
for f in mdb_files:
    size = os.path.getsize(f)
    print(f"  {os.path.basename(f)} ({size/1024/1024:.1f} MB)")

print()

# Revisar el CBOData_s.mdb de esa carpeta
cbodata = os.path.join(folder, "CBOData_s.mdb")
if os.path.exists(cbodata):
    print(f"Abriendo {cbodata}...")
    try:
        conn = pyodbc.connect(
            f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={cbodata};PWD=C0mtrex;"
        )
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT SalesDayNumber, MIN(DateTimeStart) FROM TransactionHeader GROUP BY SalesDayNumber ORDER BY MIN(DateTimeStart) DESC")
        rows = cur.fetchall()
        print(f"Dias disponibles (ultimos 20):")
        for row in rows[:20]:
            fecha = row[1].strftime('%Y-%m-%d') if row[1] else 'NULL'
            print(f"  SalesDayNumber={row[0]} -> {fecha}")
        conn.close()
    except Exception as e:
        print(f"  Error: {e}")
else:
    print(f"No se encontro CBOData_s.mdb en {folder}")
    print("Archivos disponibles:")
    for f in os.listdir(folder) if os.path.exists(folder) else []:
        print(f"  {f}")
