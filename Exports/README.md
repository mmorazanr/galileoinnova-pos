# TransactionJournal Reports - Generated Files

Fecha de generación: 2026-02-22

---

## Reportes Generados

### 1. **TransactionJournal_Report.xlsx** (326 KB)
**Reporte Detallado Completo**

- **Contenido:** Todos los detalles línea por línea de cada transacción
- **Registros:** 5,614 líneas
- **Campos:** 16 columnas (fecha, terminal, cajero, mesa, items, montos, etc)
- **Orden:** Por fecha descendente
- **Uso:** Análisis detallado de cada transacción
- **Formato:** Profesional con encabezados, bordes y estilos

**Columnas:**
- Inicio, Cierre, Terminal, Transaccion, Turno, Cajero, Mesa, Empleado, Personas
- Seq (secuencia), TipoDetail, Cantidad, Monto, Balance, Gerente, Razon

---

### 2. **TransactionJournal_Resumen.xlsx** (51 KB)
**Resumen por Transacción**

- **Contenido:** Una fila por transacción con totales
- **Registros:** 918 transacciones
- **Campos:** 10 columnas
- **Orden:** Por fecha descendente
- **Uso:** Vista ejecutiva rápida de todas las transacciones

**Columnas:**
- TransactionID, Fecha, Terminal, NumTransaccion, Turno, Cajero, Mesa
- Items (cantidad de líneas), Cantidad (total de items), Total (monto total)

**Totales Generales:**
- Total Items: 5,545
- Total Cantidad: 4,843.00
- Total Ventas: $53,662.03

---

### 3. **TransactionJournal_Analisis.xlsx** (7 KB)
**Análisis de Datos por Categorías**

**Hoja 1: Por Cajero**
- 13 cajeros
- Resumen de transacciones, cantidad e ingresos por cada cajero
- Ordenado por ventas (mayor a menor)

**Hoja 2: Por Turno**
- 2 turnos identificados
- Total de items, cantidad e ingresos por turno

**Hoja 3: Por Terminal**
- 1 terminal principal
- Resumen de actividad por terminal

**Uso:** Para análisis de desempeño y productividad

---

### 4. **TransactionJournal_2026-02-22_15-41-48.xlsx** (354 KB)
**Reporte Completo Original**

- Primer reporte generado con timestamp automático
- Mismo contenido que TransactionJournal_Report.xlsx
- Archivo de respaldo con fecha/hora de generación

---

## Cómo Usar los Reportes

### Para análisis rápido:
→ Abre **TransactionJournal_Resumen.xlsx**

### Para ver detalles de cada venta:
→ Abre **TransactionJournal_Report.xlsx**

### Para evaluar desempeño de cajeros/turnos:
→ Abre **TransactionJournal_Analisis.xlsx**

### Para presentación gerencial:
→ Usa Resumen + Análisis juntos

---

## Filtros y Análisis en Excel

Todos los reportes permiten:

1. **Filtros automáticos** (en encabezados)
   - Click en encabezado → Filter
   - Elige criterios

2. **Tablas dinámicas** (Pivot Tables)
   - Select datos
   - Insert → Pivot Table
   - Crea análisis personalizado

3. **Gráficos**
   - Select datos
   - Insert → Chart
   - Visualiza tendencias

4. **Búsqueda y ordenamiento**
   - Data → Sort
   - Data → AutoFilter

---

## Datos Clave

| Métrica | Valor |
|---------|-------|
| Total Transacciones | 918 |
| Total Items/Líneas | 5,545 |
| Total Cantidad (unidades) | 4,843 |
| Total Ventas | $53,662.03 |
| Promedio por Transacción | $58.41 |
| Promedio por Item | $9.67 |
| Cajeros | 13 |
| Turnos | 2 |
| Terminales | 1 |

---

## Cómo Recrear Estos Reportes

Si necesitas actualizar los datos, ejecuta:

```bash
python C:\ICOM\Database\export_transaction_journal.py
```

O:

```bash
cd C:\ICOM\Database
python export_transaction_journal.py
```

Esto generará nuevos archivos con fecha/hora actual.

---

## Estructura Original del Reporte .rpt

El reporte original **TransactionJournal.rpt** (Crystal Reports) consultaba:

**Tablas:**
- TransactionHeaderPOS (encabezados de transacciones)
- TransactionDetailsPOS (detalles línea por línea)

**Relación:**
```
TransactionHeaderPOS.TransactionHeaderID =
  TransactionDetailsPOS.TransactionHeaderID
```

**Ordenamiento:** Por fecha descendente, luego por transacción, luego por secuencia

**Campos:** Los mismos que se encuentran en estos reportes

---

## Notas Técnicas

- Base de datos: CBODaily.mdb
- Contraseña: C0mtrex
- Sistema: POS de Restaurante
- Periodo de datos: Historial completo de la BD
- Generado: Python 3.14.2 + pandas + openpyxl
- Formato: Microsoft Excel .xlsx (compatible con Excel, LibreOffice, Google Sheets)

---

**Última actualización:** 2026-02-22 16:06

Para preguntas o actualizaciones de reportes, contacta al equipo de tecnología.
