# ANÁLISIS COMPLETO: CBOData_s.mdb - Base de Datos Principal

**Versión:** 2026-02-22
**Base de Datos:** CBOData_s.mdb (BD TOTAL)
**Tamaño:** ~200 MB
**Tablas:** 1,628 tablas (muchas son procesos/temporales)
**Contraseña:** C0mtrex

---

## 1. DESCRIPCION GENERAL

**CBOData_s.mdb** es la base de datos PRINCIPAL del sistema POS que contiene:

- ✓ Historial COMPLETO de transacciones (24,481 transacciones)
- ✓ Detalles de items vendidos (140,209 registros)
- ✓ Definiciones y configuraciones del sistema
- ✓ Historial de días de venta
- ✓ Información de empleados y personal
- ✗ NO contiene datos maestros de productos (esos podrían estar en otra BD o configuración)

**Comparación:**
```
CBOData_s.mdb (TOTAL)       vs     CBODaily.mdb (DIARIA)
- Historial completo               - Solo datos recientes
- 24,481 transacciones             - 918 transacciones
- 140,209 detalles                 - 5,551 detalles
- Archivos maestros (vacíos)       - Datos operacionales activos
```

---

## 2. TABLAS PRINCIPALES Y DATOS

### 2.1 TRANSACTIONHEADER (24,481 registros)

**Descripción:** Encabezado de cada transacción/ticket en el historial completo

**Estructura:**

```
Campos clave:
┌─ IDENTIFICACION ────────────────────────────────────────
├─ TransactionHeaderID      → ID único de la transacción
├─ TransactionID            → ID secundario
├─ SalesDayNumber           → Día de venta (número correlativo: 6059, 6088, etc.)
├─ StoreNumber              → Sucursal (ej: 1)
│
├─ FECHA/HORA ───────────────────────────────────────────
├─ DateTimeStart            → Inicio: 2025-05-10 11:05:38
├─ DateTimeStop             → Fin:    2025-05-10 11:05:38
│
├─ UBICACION/RESPONSABLE ─────────────────────────────────
├─ TerminalName             → Nombre terminal: "*"
├─ TerminalNumberTH         → Número terminal: 5 o 1
├─ TableNumber              → Mesa: 0-39
├─ CashierNumber            → Mesero/Cajero: 1, 1239, 1244, 1270, 1325, etc.
├─ EmployeeNumber           → Empleado (SSN): "111111111", "668325867", etc.
├─ SlotNbr                  → Slot/posición: 45
│
├─ DETALLES DE OPERACION ─────────────────────────────────
├─ TransactionTypeID        → Tipo transacción: 2,3,4,5,8,9,10,13,18,19,20,21,22
├─ SalesTypeNumber          → Tipo de venta: 1, 2
├─ ShiftNumber              → Turno: 0, 1
├─ SalesTypeNumber          → Tipo de venta: 1, 2
├─ POSRevenueCenterNumber   → Centro de ingresos
├─ RevenueCenterNumber      → Centro de ingresos
├─ CtlAcctNumber            → Cuenta de control: 10000
│
├─ DETALLES ADICIONALES ─────────────────────────────────
├─ CoversChange             → Número de personas: 0, 1, 2...
├─ TransactionOrCheckNumber → Número de cheque
├─ GuestCheckNumber         → Número de cheque de huésped
├─ TrainingTransaction      → Si es entrenamiento: True/False
```

**Datos de ejemplo:**
```
CashierNumber: 1524
EmployeeNumber: 668325867
TableNumber: 51 (mesa)
DateTimeStart: 2025-05-10 11:05:51
CoversChange: 1 (una persona)
SalesTypeNumber: 2
```

---

### 2.2 TRANSACTIONDETAILS (140,209 registros)

**Descripción:** Detalles línea por línea de cada item/producto vendido

**Estructura:**

```
Campos clave:
┌─ IDENTIFICACION ────────────────────────────────────────
├─ TransactionDetailID      → ID único del detalle
├─ DetailSequenceNumber     → Número de línea (orden)
├─ TransactionHeaderID      → Link a TransactionHeader
│
├─ ITEM/PRODUCTO ────────────────────────────────────────
├─ DetailTypeID             → Código de tipo de item
├─ DetailNumber1            → Número adicional 1
├─ DetailNumber2            → Número adicional 2
├─ ItemizerMask             → Máscara de formato
│
├─ CANTIDAD Y PRECIO ────────────────────────────────────
├─ DetailItemQuantity       → Cantidad vendida
├─ DetailItemAmount         → Precio del item
├─ ItemBalanceQuantity      → Cantidad acumulada
├─ TransactionBalanceAmount → Balance acumulado (NOTA: datos dañados)
│
├─ REFERENCIAS ──────────────────────────────────────────
├─ DetailTableID1-4         → IDs de tabla (referencias)
├─ ManagerNumber            → Gerente que autorizó
├─ ReasonCodeText           → Razón/código: "1", "COMPL", etc.
```

**Nota importante:** Algunos campos como `TransactionBalanceAmount` contienen valores dañados/fuera de rango en algunos registros.

---

### 2.3 SALESDDAYS (10 últimos registros)

**Descripción:** Historial de días de venta cerrados/abiertos

**Estructura:**
```
SalesDayNumber    → Número correlativo del día (6059, 6094, 6095, etc.)
SalesDate         → Fecha del día: 2025-06-15
ClosedDay         → Si está cerrado: True/False
ClosingUserNumber → Quién cerró: 1325, 1239 (Mesero que cierra)
ClosingDateTime   → Cuándo se cerró: 2025-06-14 22:57:15
BODRunningGT      → Total acumulado: 8262844.82
```

**Datos:**
```
SalesDayNumber 6095 (2025-06-15) - ABIERTO
SalesDayNumber 6094 (2025-06-14) - Cerrado por mesero 1325
SalesDayNumber 6093 (2025-06-13) - Cerrado por mesero 1239
...
```

---

## 3. CODIGOS Y REFERENCIAS ENCONTRADOS

### 3.1 MESEROS/CAJEROS

**Códigos únicos de CashierNumber en la base total:**

```
1, 1239, 1244, 1270, 1325, 1326, 1374, 1462, 1475, 1479,
1489, 1492, 1495, 1503, 1520, 1522, 1524, 1526, 1527, 1531
(y más...)
```

**Quién cierra días:** 1325, 1239 (aparecen en SalesDays como ClosingUserNumber)

---

### 3.2 EMPLEADOS

**Formato:** Números de Seguro Social (SSN) o documento de identidad

```
Ejemplos:
- '000000000' → (prueba?)
- '111111111' → (prueba?)
- '668325867' → Real
- '674302532' → Real
- '746464747' → Real
- '098787909' → Real
- '296-67-2684' → Con guión (SSN formato)
```

**Personas que aparecen en revisiones:**
- Hardin
- Keefer
- McMonagle
- Moseley
- Rice

---

### 3.3 MESAS

**Números de mesas usadas:**

```
Mesas de 1 a 39:
1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
21, 22, 23, 24, 31, 32, 33, 34, 35, 36, 37, 38, 39

Mesa 0 = Mostrador/Barra (sin número de mesa)
```

---

### 3.4 TIPOS DE TRANSACCION

**TransactionTypeID encontrados:**

```
2, 3, 4, 5, 8, 9, 10, 13, 18, 19, 20, 21, 22
```

Significado: Probablemente diferentes tipos de:
- Venta normal
- Devolución
- Cortesía
- Descuento
- Pago
- etc.

---

### 3.5 TIPOS DE VENTA

**SalesTypeNumber:**

```
1 → Tipo de venta 1
2 → Tipo de venta 2
```

---

### 3.6 TURNOS

**ShiftNumber:**

```
0 → Turno matutino/primero
1 → Turno vespertino/segundo
```

---

## 4. ESTADISTICAS GLOBALES

### De la base de datos TOTAL (CBOData_s.mdb):

```
Período de datos: Junio 2025
Total Días: 10 últimos días disponibles
Total Transacciones: 24,481
Total Líneas/Items: 140,209

Meseros activos: 20+ códigos identificados
Mesas: 39 mesas numeradas + mostrador
Turnos: 2 turnos por día
Sucursales: 1 (StoreNumber = 1)
Terminales: Principalmente terminal 5 y 1
```

---

## 5. TABLAS MAESTRAS VACIAS (Existen pero sin datos)

Las siguientes tablas están definidas pero vacías:

```
- EmployeesExport      → Estructura de empleados (0 registros)
- CrystalScheduleEmployee → Horarios (0 registros)
- ScheduleHeader       → Encabezados de horarios (0 registros)
- ScheduleDetail       → Detalles de horarios (0 registros)
- ComboDefinitions     → Definiciones de combos (0 registros)
- ComboDetails         → Detalles de combos (0 registros)
- InvoiceItems         → Items de facturas (0 registros)
```

---

## 6. CONSULTAS UTILES PARA EXTRAER DATOS

### Obtener todos los meseros con actividad

```sql
SELECT DISTINCT CashierNumber
FROM TransactionHeader
ORDER BY CashierNumber
```

### Obtener actividad completa por mesero

```sql
SELECT
    t.CashierNumber as Mesero,
    COUNT(DISTINCT t.SalesDayNumber) as Dias,
    COUNT(*) as Transacciones,
    SUM(d.DetailItemQuantity) as Items
FROM TransactionHeader t
LEFT JOIN TransactionDetails d ON t.TransactionHeaderID = d.TransactionHeaderID
GROUP BY t.CashierNumber
ORDER BY COUNT(*) DESC
```

### Mesas más usadas

```sql
SELECT
    TableNumber,
    COUNT(*) as Transacciones
FROM TransactionHeader
WHERE TableNumber > 0
GROUP BY TableNumber
ORDER BY COUNT(*) DESC
```

### Transacciones por día

```sql
SELECT
    sd.SalesDayNumber,
    sd.SalesDate,
    COUNT(t.TransactionHeaderID) as Transacciones
FROM SalesDays sd
LEFT JOIN TransactionHeader t ON sd.SalesDayNumber = t.SalesDayNumber
GROUP BY sd.SalesDayNumber, sd.SalesDate
ORDER BY sd.SalesDayNumber DESC
```

### Items más vendidos (por tipo)

```sql
SELECT TOP 50
    DetailTypeID,
    COUNT(*) as Cantidad,
    SUM(DetailItemQuantity) as UnidadesVendidas
FROM TransactionDetails
GROUP BY DetailTypeID
ORDER BY COUNT(*) DESC
```

---

## 7. ARCHIVOS RELACIONADOS

**Base de datos conectada:**
- `CBOData_s.mdb` (Principal - 1,628 tablas)
- `CBODaily.mdb` (Diaria - 28 tablas)
- `CBODef_s.mdb` (Definiciones)
- `POS2100.mdb` (Sistema POS)

---

## 8. NOTAS IMPORTANTES

1. **Los datos maestros (productos, precios) NO están en CBOData_s.mdb**
   - Posiblemente están en `POS2100.mdb` o `CBODef_s.mdb`
   - O se almacenan en el sistema POS en terminal

2. **Los datos de transacciones son históricos**
   - Se sincronizan de `CBODaily.mdb` a `CBOData_s.mdb`
   - `CBODaily.mdb` es la BD diaria de operación

3. **Algunos campos tienen valores dañados**
   - `TransactionBalanceAmount` tiene valores fuera de rango
   - Estos son valores calculados/temporales

4. **Los IDs son códigos internos**
   - `DetailTypeID` = Código del tipo de item
   - `EmployeeNumber` = Formato SSN/documento
   - `CashierNumber` = Código único de la caja/mesero

5. **Las mesas son referencias físicas**
   - Mesa 0 = Mostrador/Bar (sin mesa)
   - Mesas 1-39 = Mesas del restaurante

---

## 9. PROXIMOS PASOS

Para obtener información más completa, sugiero:

1. **Analizar `POS2100.mdb`** - Probable ubicación de maestros
2. **Analizar `CBODef_s.mdb`** - Definiciones del sistema
3. **Buscar archivos de configuración** - Mappeo de códigos
4. **Consultar reportes Crystal** - Para entender estructura

---

**Generado:** 2026-02-22
**Fuente:** Análisis de CBOData_s.mdb con acceso password C0mtrex
