# Estructura del Reporte: TransactionJournal.rpt

## Información General

- **Archivo:** TransactionJournal.rpt
- **Nombre Interno:** "Detail Transaction Log"
- **Tipo:** Seagate Crystal Reports
- **Tamaño:** 432 KB
- **Creado:** 21 enero 2000
- **Última modificación:** 8 octubre 2010

---

## Tablas Utilizadas

El reporte utiliza principalmente **2 tablas principales**:

### 1. TransactionHeaderPOS
**Descripción:** Encabezado de transacciones (tickets, órdenes)

**Registros:** 918
**Propósito:** Información general de cada transacción

**Campos:**
```
- TransactionHeaderID      → ID único de la transacción
- TransactionID            → ID secundario
- SalesDayNumber          → Número del día de ventas
- StoreNumber             → Sucursal
- TransactionTypeID       → Tipo de transacción
- DateTimeStart           → Fecha/hora de inicio
- DateTimeStop            → Fecha/hora de cierre
- SlotNbr                 → Número de slot/terminal
- TerminalNumberTH        → Número de terminal
- TerminalName            → Nombre de terminal
- CtlAcctNumber           → Cuenta de control
- TransactionOrCheckNumber → Número de cheque/transacción
- ShiftNumber             → Turno
- CoversChange            → Número de personas
- SalesTypeNumber         → Tipo de venta
- POSRevenueCenterNumber  → Centro de ingresos POS
- RevenueCenterNumber     → Centro de ingresos
- CashierNumber           → Número de cajero
- TableNumber             → Número de mesa
- EmployeeNumber          → Número de empleado
- TrainingTransaction     → Transacción de entrenamiento (S/N)
- GuestCheckNumber        → Número de cheque de huésped
```

### 2. TransactionDetailsPOS
**Descripción:** Detalles de línea de cada transacción

**Registros:** 5,551
**Propósito:** Cada item/línea de la transacción

**Campos:**
```
- TransactionDetailID          → ID único del detalle
- DetailSequenceNumber         → Secuencia del item
- TransactionHeaderID          → FK a TransactionHeaderPOS
- DetailTypeID                 → Tipo de detalle
- TransactionBalanceAmount     → Monto acumulado
- ItemBalanceQuantity          → Cantidad acumulada
- DetailItemQuantity           → Cantidad del item
- DetailItemAmount             → Monto del item
- DetailTableID1 a DetailTableID4 → IDs de tabla (1-4)
- DetailNumber1 a DetailNumber2    → Números adicionales
- ItemizerMask                 → Máscara de formateador
- ManagerNumber                → Número de gerente
- ReasonCodeText               → Texto de código de razón
```

### 3. TransactionDetailFinalizePOS (auxiliar)
**Descripción:** Información de finalización (pagos, autorizaciones)

**Registros:** 0 (vacía)
**Campos principales:**
```
- SalesDayNumber
- TransactionHeaderID
- TransactionDetailID
- AuthorizationCode         → Código de autorización
- ExpirationDate            → Fecha de expiración
- ChargeTextNumber          → Número de cargo
- NumericReference1         → Referencia numérica
```

---

## Relaciones Entre Tablas

```
TransactionHeaderPOS (918 registros)
        |
        | TransactionHeaderID = TransactionHeaderID
        |
        v
TransactionDetailsPOS (5,551 registros)
        |
        | TransactionDetailID = TransactionDetailID
        |
        v
TransactionDetailFinalizePOS (0 registros)
```

---

## Consulta SQL Base (Reproducir el Reporte)

```sql
SELECT
    -- De TransactionHeaderPOS
    th.TransactionHeaderID,
    th.TransactionID,
    th.SalesDayNumber,
    th.StoreNumber,
    th.TransactionTypeID,
    th.DateTimeStart,
    th.DateTimeStop,
    th.TerminalName,
    th.TransactionOrCheckNumber,
    th.ShiftNumber,
    th.CashierNumber,
    th.TableNumber,
    th.EmployeeNumber,

    -- De TransactionDetailsPOS
    td.TransactionDetailID,
    td.DetailSequenceNumber,
    td.DetailTypeID,
    td.TransactionBalanceAmount,
    td.ItemBalanceQuantity,
    td.DetailItemQuantity,
    td.DetailItemAmount,
    td.ManagerNumber,
    td.ReasonCodeText

FROM
    TransactionHeaderPOS th
    LEFT JOIN TransactionDetailsPOS td
        ON th.TransactionHeaderID = td.TransactionHeaderID

ORDER BY
    th.DateTimeStart DESC,
    th.TransactionHeaderID,
    td.DetailSequenceNumber
```

---

## Cómo se Construyó el Reporte

El archivo `.rpt` fue construido en **Seagate Crystal Reports** con los siguientes pasos aproximados:

1. **Conectar a la base de datos:** CBODaily.mdb
2. **Seleccionar tabla principal:** TransactionHeaderPOS
3. **Agregar JOIN:** Con TransactionDetailsPOS
4. **Seleccionar campos:** De ambas tablas (campos listados arriba)
5. **Aplicar orden:** Por fecha y número de transacción
6. **Formato:** Tabular con encabezados detallados
7. **Campos calculados:** TransactionBalanceAmount (acumulativo)
8. **Filtros:** Probablemente filtrable por rango de fechas

---

## Cómo Usar Esta Información

### Opción 1: Recrear en SQL Server / Access
```sql
-- Ejecutar la consulta SQL base en Access Query Designer
-- O usar en una herramienta de reporte alternativa
```

### Opción 2: Usar datos extraidos a Excel
Ya hemos exportado los datos a: `C:\ICOM\Database\Exports\TransactionJournal_*.xlsx`

### Opción 3: Recrear en Power BI / Tableau
Usar la consulta SQL base para conectar directamente a la BD

### Opción 4: Crear reporte en Access
1. Abre Access
2. Crear nuevo reporte basado en una consulta
3. Usar la consulta SQL base
4. Aplicar el mismo formato que el .rpt original

---

## Campos Importantes por Negocio

Para un **sistema POS de restaurante**, los campos clave son:

```
TRANSACCION:
- DateTimeStart/DateTimeStop → Horario de venta
- CashierNumber             → Cajero responsable
- TableNumber              → Mesa/mostrador
- TransactionBalanceAmount → Total de la transacción

DETALLES:
- DetailItemAmount         → Precio por item
- DetailItemQuantity       → Cantidad ordenada
- DetailTypeID             → Tipo (bebida, comida, etc)
- ManagerNumber            → Gerente que lo aprobó
```

---

## Próximos Pasos

Para mantener y actualizar el reporte sin Crystal Reports:

1. **Ejecutar script Python:** `export_transaction_journal.py`
2. **O crear una consulta en Access**
3. **O usar Power BI para visualizaciones más avanzadas**

---

## Notas Técnicas

- El archivo `.rpt` es un OLE Compound Document (como ZIP interno)
- Contiene la definición binaria del reporte compilado
- No puede editarse sin Crystal Reports
- La estructura SQL fue extraida analizando el binario
- Los datos siguen siendo accesibles a través de las tablas subyacentes

---

**Generado:** 2026-02-22
**Fuente:** Análisis del archivo TransactionJournal.rpt y estructura de CBODaily.mdb
