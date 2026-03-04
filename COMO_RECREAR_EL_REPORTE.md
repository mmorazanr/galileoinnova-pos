# Cómo Recrear el Reporte TransactionJournal.rpt

## Resumen Ejecutivo

El reporte `TransactionJournal.rpt` es simple de recrear. Utiliza:
- **2 tablas:** TransactionHeaderPOS + TransactionDetailsPOS
- **Relación:** Un JOIN por TransactionHeaderID
- **Datos:** 5,551 registros de detalles + 918 encabezados

---

## Opción 1: EXCEL (La más fácil)

Ya tienes el archivo Excel generado:
```
C:\ICOM\Database\Exports\TransactionJournal_2026-02-22_15-41-48.xlsx
```

**Cómo mejorar el Excel:**

1. Abre el archivo en Excel
2. Selecciona los datos
3. Insert → Pivot Table
4. Agrupa por:
   - Filas: DateTimeStart, TransactionHeaderID, CashierNumber
   - Valores: DetailItemAmount (SUM), DetailItemQuantity (COUNT)
5. Filtra por rango de fechas según necesites

**Ventajas:**
- ✓ Ya tienes los datos
- ✓ Fácil filtrar y formatear
- ✓ Puedes compartir fácilmente
- ✓ Puedes agregar gráficos

---

## Opción 2: ACCESS QUERY (Si tienes Access instalado después)

Cuando instales Access:

### Paso 1: Crear Query
1. File → New Database
2. Tools → Query Wizard
3. O crear Query en SQL View

### Paso 2: Pegar esta consulta SQL

```sql
SELECT
    th.DateTimeStart,
    th.DateTimeStop,
    th.TerminalName,
    th.TransactionOrCheckNumber,
    th.ShiftNumber,
    th.CashierNumber,
    th.TableNumber,
    th.EmployeeNumber,
    td.DetailSequenceNumber,
    td.DetailTypeID,
    td.DetailItemQuantity,
    td.DetailItemAmount,
    td.TransactionBalanceAmount,
    td.ManagerNumber,
    td.ReasonCodeText

FROM
    TransactionHeaderPOS th
    LEFT JOIN TransactionDetailsPOS td
        ON th.TransactionHeaderID = td.TransactionHeaderID

ORDER BY
    th.DateTimeStart DESC,
    th.TransactionHeaderID,
    td.DetailSequenceNumber;
```

### Paso 3: Crear Reporte basado en Query
1. Click en la Query
2. Insert → Report
3. Usa Report Wizard para formatear

---

## Opción 3: POWER BI (Si quieres reportes avanzados)

### Paso 1: Descargar Power BI Desktop
```
https://powerbi.microsoft.com/en-us/desktop/
```

### Paso 2: Conectar a Base de Datos
1. Get Data → Access Database
2. Selecciona: CBODaily.mdb
3. Ingresa contraseña: C0mtrex

### Paso 3: Cargar Tablas
- TransactionHeaderPOS
- TransactionDetailsPOS

### Paso 4: Crear Relación
1. Manage → Relationships
2. Conecta:
   - TransactionHeaderPOS.TransactionHeaderID
   - TransactionDetailsPOS.TransactionHeaderID

### Paso 5: Crear Visualización
1. New Page
2. Insert Table visual
3. Campos:
   - DateTimeStart, TerminalName, CashierNumber, TableNumber
   - DetailItemAmount, DetailItemQuantity, ManagerNumber
4. Agrupa por Fecha y Cajero

**Ventajas:**
- ✓ Reportes interactivos
- ✓ Dashboards profesionales
- ✓ Filtros dinámicos
- ✓ Exportable a PDF

---

## Opción 4: PYTHON AUTOMATIZADO (Script mejorado)

Ya tienes el script: `export_transaction_journal.py`

Para personalizarlo, edita estos parámetros:

```python
# Filtrar por rango de fechas
query = """
SELECT * FROM TransactionDetailsPOS td
JOIN TransactionHeaderPOS th
    ON td.TransactionHeaderID = th.TransactionHeaderID
WHERE th.DateTimeStart >= '2026-01-01'
  AND th.DateTimeStart < '2026-02-28'
ORDER BY th.DateTimeStart DESC
"""

# Agrupar por cajero
df_grouped = df.groupby('CashierNumber').agg({
    'DetailItemAmount': 'sum',
    'DetailItemQuantity': 'count'
})

# Exportar con formato
df_grouped.to_excel('ReportePorCajero.xlsx', sheet_name='Resumen')
```

---

## Opción 5: GOOGLE SHEETS (Online)

1. Copia el archivo Excel a Google Drive
2. Abre en Google Sheets
3. Insert → Pivot Table
4. Analiza como necesites
5. Acceso desde cualquier lugar

---

## Comparativa de Opciones

| Opción | Facilidad | Funcionalidad | Costo | Automatización |
|--------|-----------|---------------|-------|---|
| Excel | Muy Fácil | Media | Gratis | Manual |
| Access Query | Media | Alta | Gratis* | Manual |
| Power BI | Media | Muy Alta | Gratis/Pago | Media |
| Python Script | Difícil | Alta | Gratis | Automática |
| Google Sheets | Fácil | Media | Gratis | Manual |

*Access = requiere instalar

---

## Mi Recomendación por Caso

### "Solo necesito ver los datos"
→ **Excel** (ya tienes el archivo)

### "Necesito reportes regulares sin instalar nada"
→ **Google Sheets** (sube el Excel)

### "Necesito reportes profesionales interactivos"
→ **Power BI** (versión gratis es suficiente)

### "Necesito automatizar diariamente"
→ **Python Script** (con Task Scheduler de Windows)

### "Necesito exactamente como era el .rpt"
→ **Access Query + Report Builder**

---

## Próximos Pasos

1. **¿Cuál opción prefieres?**
   - Dime y te doy guía completa

2. **¿Qué datos específicos necesitas ver?**
   - Por fecha, por cajero, por mesa, etc.

3. **¿Con qué frecuencia necesitas el reporte?**
   - Una vez, diario, semanal, etc.

Una vez entienda tus necesidades, puedo:
- Crear un reporte personalizado
- Automatizarlo
- Mejorarlo con análisis adicionales

---

**Fecha:** 2026-02-22
