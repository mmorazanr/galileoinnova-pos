# ESTRUCTURA DE DATOS - CODIGOS, MAESTROS Y REFERENCIAS

## Base de Datos POS del Restaurante

**Dos bases de datos principales:**
- `CBOData_s.mdb` - Base de datos TOTAL (historial completo, 250 tablas)
- `CBODaily.mdb` - Base de datos DIARIA (datos actuales, 28 tablas)
- **Contraseña:** C0mtrex

---

## 1. CODIGOS DE MESEROS (Empleados/Cashiers)

### Fuente: TransactionHeaderPOS o CashierStatus

**Tabla:** `CashierStatus` (en CBODaily.mdb)

```sql
SELECT DISTINCT CashierNumber, TableSectionName
FROM CashierStatus
ORDER BY CashierNumber
```

**Campos disponibles:**
- `CashierNumber` → Código único del mesero/cajero
- `SignedOn` → Si está activo (True/False)
- `TableSectionName` → Sección asignada (ej: "Main Dining")
- `TStatus` → Estado

**Ejemplo de datos:**
```
CashierNumber | SignedOn | TableSectionName | TStatus
1             | True     | Main Dining      | False
2             | True     | (null)           | False
567           | True     | Main Dining      | False
1325          | True     | (null)           | False
```

**Otra fuente:** `TransactionHeaderPOS`
```sql
SELECT DISTINCT CashierNumber
FROM TransactionHeaderPOS
ORDER BY CashierNumber
```

---

## 2. CODIGOS DE MESAS

### Fuente: TransactionHeaderPOS

**Campo:** `TableNumber`

```sql
SELECT DISTINCT TableNumber
FROM TransactionHeaderPOS
WHERE TableNumber > 0
ORDER BY TableNumber
```

**Datos de mesas encontrados:**
```
De las transacciones se extrae que las mesas usan números como:
0, 1, 2, 3, ... N
```

**Tabla relacionada:** `TableKeyFieldValues`
```
Contiene valores de campos clave: 1, 2, 3
```

---

## 3. NUMEROS DE TERMALES/CAJAS

### Fuente: TransactionHeaderPOS

**Campos:**
- `TerminalName` → Nombre de la terminal (ej: "*")
- `TerminalNumberTH` → Número de terminal

```sql
SELECT DISTINCT TerminalName, TerminalNumberTH
FROM TransactionHeaderPOS
ORDER BY TerminalNumberTH
```

**Datos encontrados:**
```
TerminalName | TerminalNumberTH
*            | 1
```

---

## 4. PRECIOS DE ARTICULOS

### Fuente: TransactionDetailsPOS (en la transacción)

**Campos:**
- `DetailItemAmount` → Precio del item
- `DetailItemQuantity` → Cantidad

```sql
SELECT
    td.DetailItemAmount as 'Precio Unitario',
    td.DetailItemQuantity as 'Cantidad',
    (td.DetailItemAmount * td.DetailItemQuantity) as 'Total'
FROM TransactionDetailsPOS td
```

**Nota:** Los precios se encuentran en las transacciones completadas. No hay tabla maestra separada visible en la BD diaria.

---

## 5. ESTRUCTURA DE TRANSACCIONES

### TransactionHeaderPOS (Encabezado)

**922 Campos importantes:**

```
IDENTIFICACION:
- TransactionHeaderID      → ID único (1, 2, 3, ...)
- TransactionID            → ID secundario
- TransactionOrCheckNumber → Número de cheque/transacción

FECHA/HORA:
- DateTimeStart            → Inicio de la transacción
- DateTimeStop             → Cierre de la transacción

UBICACION/RESPONSABLE:
- StoreNumber              → Sucursal (ej: 1)
- TerminalName             → Nombre terminal (ej: "*")
- TerminalNumberTH         → Número terminal (ej: 1)
- TableNumber              → Mesa (ej: 0, 1, 2)
- CashierNumber            → Mesero/Cajero (ej: 1, 2, 567, 1325)
- EmployeeNumber           → Número empleado

OPERACION:
- TransactionTypeID        → Tipo de transacción
- SalesTypeNumber          → Tipo de venta
- ShiftNumber              → Turno (ej: 1, 2)
- SalesDayNumber           → Día de venta
- POSRevenueCenterNumber   → Centro de ingresos POS
- RevenueCenterNumber      → Centro de ingresos

DETALLES:
- CoversChange             → Número de personas
- GuestCheckNumber         → Número de cheque
- TrainingTransaction      → Si es transacción de entrenamiento
```

### TransactionDetailsPOS (Detalles/Items)

**17 Campos:**

```
IDENTFICACION:
- TransactionDetailID       → ID único del detalle
- DetailSequenceNumber      → Número de secuencia (orden)
- TransactionHeaderID       → Referencia a TransactionHeaderPOS

CANTIDAD Y MONTO:
- DetailItemQuantity        → Cantidad del item
- DetailItemAmount          → Monto del item
- TransactionBalanceAmount  → Balance acumulado

CLASIFICACION:
- DetailTypeID              → Tipo de detalle (código)
- ItemizerMask              → Mascara de formato
- DetailNumber1, DetailNumber2 → Números adicionales
- DetailTableID1-4          → IDs de tabla

AUTORIZACION:
- ManagerNumber             → Gerente que autorizo
- ReasonCodeText            → Razón del movimiento
```

---

## 6. RELACIONES ENTRE TABLAS

```
TransactionHeaderPOS (918 registros)
        ↓ TransactionHeaderID
TransactionDetailsPOS (5,551 registros)
        ↓ TransactionDetailID
TransactionDetailFinalizePOS (0 registros)
```

---

## 7. CODIGOS DE TIPOS/CATEGORIAS

### DetailTypeID (Tipos de detalle)

Basado en datos encontrados:
```
262144  → Tipo específico de item
327680  → Otro tipo
196608  → Otro tipo
...
```

### TransactionTypeID (Tipos de transacción)

```
3   → Tipo transacción 3
13  → Tipo transacción 13
21  → Tipo transacción 21
...
```

### SalesTypeNumber (Tipos de venta)

```
1   → Tipo de venta 1
2   → Tipo de venta 2
...
```

---

## 8. COMO OBTENER CADA CODIGO

### Meseros Activos

```sql
SELECT DISTINCT CashierNumber, TableSectionName
FROM CashierStatus
WHERE SignedOn = True
ORDER BY CashierNumber
```

### Todas las Mesas Usadas

```sql
SELECT DISTINCT TableNumber
FROM TransactionHeaderPOS
ORDER BY TableNumber
```

### Todos los Empleados en Transacciones

```sql
SELECT DISTINCT EmployeeNumber
FROM TransactionHeaderPOS
WHERE EmployeeNumber > 0
ORDER BY EmployeeNumber
```

### Todos los Turnos

```sql
SELECT DISTINCT ShiftNumber
FROM TransactionHeaderPOS
ORDER BY ShiftNumber
```

### Rango de Precios

```sql
SELECT
    MIN(DetailItemAmount) as 'Precio Minimo',
    MAX(DetailItemAmount) as 'Precio Maximo',
    AVG(DetailItemAmount) as 'Precio Promedio'
FROM TransactionDetailsPOS
```

### Items por Cantidad Vendida

```sql
SELECT
    DetailTypeID,
    SUM(DetailItemQuantity) as 'Total Cantidad',
    SUM(DetailItemAmount) as 'Total Ventas',
    AVG(DetailItemAmount) as 'Precio Promedio'
FROM TransactionDetailsPOS
GROUP BY DetailTypeID
ORDER BY SUM(DetailItemAmount) DESC
```

---

## 9. DATOS ENCONTRADOS (Ejemplos reales)

### Meseros/Cajeros Activos (13 totales)

```
CashierNumber: 1, 2, 3, 4, 5, 6, 7, 8, 9, 567, 1244, 1325, 1507
```

### Mesas Usadas

```
TableNumber: 0 (mostrador/bar), 1, 2, 3...
```

### Turnos

```
ShiftNumber: 1, 2
```

### Terminales

```
TerminalName: "*"
TerminalNumberTH: 1
```

### Estadisticas de Ventas

```
Total Transacciones: 918
Total Items: 5,545
Total Cantidad Unidades: 4,843
Total Ventas: $53,662.03
Precio Promedio por Item: $9.67
```

---

## 10. TABLAS DISPONIBLES EN CADA BASE DE DATOS

### CBODaily.mdb (28 tablas - DIARIA)

**Datos actuales, operacionales:**
- TransactionHeaderPOS, TransactionDetailsPOS
- InvoiceHeader, InvoiceItems (vacías)
- CashierStatus
- ClosedInvoiceHeader, ClosedInvoiceItems
- TableNames, TableKeyFieldValues, TableFieldNames

### CBOData_s.mdb (250 tablas - TOTAL)

**Historial completo, definiciones maestras:**
- EmployeesExport (estructura de empleados)
- ScheduleItem
- ScheduleDetail, ScheduleHeader
- Definiciones de ítems
- Historial completo de transacciones

---

## 11. NOTAS IMPORTANTES

1. **Meseros:** Se identifican por `CashierNumber`, no hay nombre asociado en la BD diaria
   - Para nombres: buscar en `DBRevision_Persons` o `EmployeesExport`

2. **Precios:** No hay tabla maestra de precios
   - Los precios se encuentran en las transacciones completadas (`DetailItemAmount`)
   - Mismo código puede tener diferentes precios si hay promociones

3. **Items/Productos:** No hay ID de producto visible
   - Se usan `DetailTypeID` como identificador
   - Los nombres/descripciones podrían estar en `InvoiceItems.Name` cuando hay datos

4. **Mesas:** Son simples números
   - Mesa 0 = mostrador/bar (sin número de mesa)
   - Mesa 1, 2, 3... = mesas numeradas

5. **Categorías:** Podrían estar en campos como `DetailTypeID`, `DepartmentNumber`, `CategoryNumber`

---

## 12. CONSULTAS UTILES PARA OBTENER MAESTROS

```sql
-- Meseros con sus transacciones
SELECT c.CashierNumber, c.TableSectionName,
       COUNT(*) as Transacciones,
       SUM(ABS(td.DetailItemAmount)) as Total
FROM CashierStatus c
LEFT JOIN TransactionHeaderPOS t ON c.CashierNumber = t.CashierNumber
LEFT JOIN TransactionDetailsPOS td ON t.TransactionHeaderID = td.TransactionHeaderID
GROUP BY c.CashierNumber, c.TableSectionName
ORDER BY Transacciones DESC

-- Tipos de items más vendidos
SELECT DetailTypeID,
       COUNT(*) as Items,
       SUM(DetailItemQuantity) as Cantidad,
       SUM(DetailItemAmount) as Ventas
FROM TransactionDetailsPOS
GROUP BY DetailTypeID
ORDER BY Ventas DESC

-- Actividad por mesa
SELECT TableNumber,
       COUNT(DISTINCT TransactionHeaderID) as Transacciones,
       SUM(DetailItemAmount) as Total
FROM TransactionHeaderPOS t
LEFT JOIN TransactionDetailsPOS d ON t.TransactionHeaderID = d.TransactionHeaderID
WHERE TableNumber > 0
GROUP BY TableNumber
ORDER BY Total DESC
```

---

**Generado:** 2026-02-22
**Fuente:** Análisis de CBODaily.mdb y CBOData_s.mdb
