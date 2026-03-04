# MAESTROS COMPLETOS: PRODUCTOS, PRECIOS, MESEROS Y CONFIGURACION

**Fuente:** CBODef_s.mdb + POS2100.mdb
**Contraseña:** C0mtrex
**Generado:** 2026-02-22

---

## 1. MESEROS/CAJEROS CON NOMBRES

**Tabla:** CashierDefinitions (124 registros)

### Meseros Principales Encontrados:

```
CashierNumber | CashierName    | SSNumber     | Activo | Tipo | Sección
─────────────┼────────────────┼──────────────┼────────┼──────┼─────────────
0             | No Operator    | (null)       | No     | 1    | Corner
1             | Pepe           | 111111113    | Sí     | 1    | Main Dining
2             | Napoleon       | 111111112    | Sí     | 1    | Main Dining
10            | Linda          | 111111306    | No     | 1    | Main Dining
567           | josse          | No Emp 567   | Sí     | 3    | Main Dining
1223          | ZComtrex       | 999999999    | Sí     | 1    | Main Dining
1224          | Isabel         | 111111117    | Sí     | 1    | Main Dining
1239          | Mustafa        | 111111134    | Sí     | 1    | Main Dining
1244          | Laura          | 111111139    | No     | 1    | Main Dining
1254          | Training       | No Emp 1254  | Sí     | 1    | Main Dining
```

**Total:** 124 meseros/cajeros definidos en el sistema

### Campos Importantes:

```
- CashierNumber          → Código único
- CashierName           → Nombre del mesero
- CashierSecretNumber   → Número secreto (PIN?)
- CashierDrawerNumber   → Número de caja
- Active                → Si está activo
- DefaultTableSection   → Sección asignada
- SSNumber              → Número de Seguro Social
- MasterServer          → Es mesero maestro
- DiscAllow            → Permite descuentos
- MgrAllow             → Permisos de gerente
- Signature            → Firma digital
```

---

## 2. CATEGORIAS DE PRODUCTOS

**Tabla:** CategoryDefinitions (55 registros)

### Categorías de Comida:

```
1  - Appetizers
2  - Nachos
3  - A la Carta
4  - Side Orders
5  - Burritos
6  - Enchiladas
7  - Fajitas
8  - Quesadillas
9  - Platillos Mex
10 - Especialidades
11 - Spcl Combinations
12 - Combinations
13 - Kids Menu
14 - Veggie Plates
37 - Soup-Salad-Tacos
40 - Lunch Only
41 - To go Items
42 - Spcl Dinners
43 - House Combinations
44 - Salads
```

### Categorías de Bebidas:

```
15 - Soft Drinks
16 - Domestic Beer (Department 4)
17 - Imported Beer
18 - Draft Beer
19 - Non-Alcoholic Beer
20 - Wines
21 - Margaritas
22 - Tequilas
23 - Bourbon
24 - Brandy
25 - Call A-E
26 - Call F-J
27 - Call K-O
28 - Call P-T
29 - Call U-Z
30 - Cktl A-E
31 - Cktl F-J
32 - Cktl K-O
33 - Cktl P-T
34 - Cktl U-Z
35 - Daiquiri
46 - Vodka
47 - Gin
48 - Rum
49 - Cognac
50 - American Whiskey
51 - Canadian Whiskey
52 - Michelada
53 - Rum & Coke
54 - Signiture
```

### Categorías Especiales:

```
36 - Desserts
38 - Food Prep (preparación)
39 - Liq Prep (preparación licor, Department 3)
45 - Aguas (Department 2)
0  - Mis-Linked (items mal categorizados)
```

**Estructura:**
```
CategoryNumber   → Código único (0-54)
CategoryName     → Nombre de categoría
DepartmentNumber → Departamento (0=Misc, 1=Food, 2=Beverage, 3=Liquor, 4=Beer)
TargetFoodCost   → Costo objetivo: 0.3 (30%)
CatgListFileIndex → Índice de archivo
```

---

## 3. DEPARTAMENTOS

**Tabla:** DepartmentDefinitions (7 registros)

```
DepartmentNumber | DepartmentName
─────────────────┼────────────────
0                | Mis-Linked
1                | Food
2                | Beverage
3                | (Licor - en categorías)
4                | (Beer - en categorías)
```

---

## 4. ITEMS/LINEAS DE TRANSACCION

**Tabla:** GLLineItems (165 registros)

### Medios de Pago y Tipos de Pago:

```
LineItemNumber | LineItemName              | Tipo
────────────────┼──────────────────────────┼──────
1              | Cash                     | Efectivo
2              | American Express         | Tarjeta
3              | Bank Checks              | Cheque
4              | Carte Blanche            | Tarjeta
5              | Coupons                  | Cupón
6              | Credit Cards             | Tarjeta Crédito
7              | Diner's Club             | Tarjeta
8              | Discover                 | Tarjeta
9              | Employee Meals           | Comida Empleado
10             | Enroute                  | Visa?
... (165 items totales)
```

**Estructura:**
```
LineItemNumber        → Código único
LineItemName          → Nombre (medios de pago, descuentos, etc.)
DebitCOANumber        → Número COA de débito
CreditCOANumber       → Número COA de crédito
PercentageAllocated   → Porcentaje asignado
MediaTypeID           → Tipo de medio
StartDay/EndDay       → Rango de validez
```

---

## 5. NIVELES DE PRECIO

**Tabla:** PriceLevels (6 registros)

```
PriceLevel | PriceLevelName
───────────┼────────────────
1          | Price Level 1
2          | Price Level 2
3          | Price Level 3
4          | Price Level 4
5          | Price Level 5
6          | Price Level 6
```

**Nota:** Los precios actuales están ligados a estos niveles. Para obtener precios específicos de productos, se usa `InvSalesItemPrices` (actualmente vacía) o los datos en transacciones.

---

## 6. MEDIOS DE PAGO (PAYMENT METHODS)

**Tabla:** MediaDefinitions (130 registros)

### Medios Principales:

```
MediaNumber | MediaName              | MediaTypeID | Active | Afecta Balance
────────────┼────────────────────────┼─────────────┼────────┼────────────────
1           | Cash                   | 1           | Sí     | Sí
2           | Equivalent Cash        | 1           | No     | No
3           | Euro                   | 2           | No     | Sí
4           | Gratuity               | 7           | Sí     | No
5           | Bank Checks            | 1           | Sí     | Sí
6           | Service Charge         | 6           | Sí     | No
7           | Service Items         | 6           | Sí     | No
8           | Subtotal Item Disc     | 11          | Sí     | No
9           | Tips Paid              | 8           | No     | No
10          | Item Discounts         | 10          | Sí     | No
11          | POS Paid Out           | 4           | Sí     | No
12          | POS Paid In            | 5           | Sí     | No
13          | Error Corrects         | 9           | Sí     | No
14          | MGR Void               | 9           | Sí     | No
15          | Refund Transaction     | 13          | Sí     | No
16          | MGR Voids              | 14          | Sí     | No
17          | Void Transaction       | 15          | Sí     | No
18          | Account Payment Check  | 3           | Sí     | No
19          | Account Payment Other  | 3           | Sí     | No
```

---

## 7. MESAS/UBICACIONES

**Tabla:** DBTableNumbers (250 registros)

Las primeras 30 son definiciones de estructura de sistema. Para mesas reales del restaurante, ver CBODaily.mdb:
- Mesas: 0-39
- 0 = Mostrador/Bar
- 1-39 = Mesas del comedor

---

## 8. PRODUCTOS/ITEMS VENDIDOS

**Tabla:** ClosedInvoiceItems (POS2100.mdb - 2,822 registros)

Contiene los items reales vendidos con:
- POSItemID
- Name (nombre del producto)
- Type (tipo)
- ValueEach (precio unitario)
- Count (cantidad)

---

## 9. CONSULTAS UTILES PARA EXTRAER MAESTROS

### Obtener todos los meseros activos con nombres:

```sql
SELECT CashierNumber, CashierName, SSNumber, DefaultTableSection, Active
FROM CashierDefinitions
WHERE Active = True
ORDER BY CashierNumber
```

### Obtener categorías por departamento:

```sql
SELECT CategoryNumber, CategoryName, DepartmentNumber, TargetFoodCost
FROM CategoryDefinitions
WHERE DepartmentNumber = 1  -- 1=Food, 2=Beverage
ORDER BY CategoryNumber
```

### Obtener medios de pago activos:

```sql
SELECT MediaNumber, MediaName, MediaTypeID, Active, AffectsBalance
FROM MediaDefinitions
WHERE Active = True
ORDER BY MediaNumber
```

### Items vendidos (últimos):

```sql
SELECT TOP 100 POSItemID, Name, Type, ValueEach, COUNT(*) as Cantidad
FROM ClosedInvoiceItems
GROUP BY POSItemID, Name, Type, ValueEach
ORDER BY COUNT(*) DESC
```

---

## 10. RESUMEN DE MAESTROS DISPONIBLES

| Maestro | Tabla | Registros | Estado |
|---------|-------|-----------|--------|
| Meseros | CashierDefinitions | 124 | ✓ Completo con nombres |
| Categorías | CategoryDefinitions | 55 | ✓ Completo |
| Departamentos | DepartmentDefinitions | 7 | ✓ Completo |
| Medios Pago | MediaDefinitions | 130 | ✓ Completo |
| Líneas Item | GLLineItems | 165 | ✓ Completo |
| Niveles Precio | PriceLevels | 6 | ✓ Completo |
| Precios Productos | InvSalesItemPrices | 0 | ✗ Vacío |
| Items Vendidos | ClosedInvoiceItems | 2,822 | ✓ Datos históricos |
| Mesas | DBTableNumbers | 250 | ✓ Definiciones sistema |

---

## 11. ESTRUCTURA COMPLETA DEL SISTEMA POS

```
CBODaily.mdb (OPERACIONAL)
├── TransactionHeaderPOS (918 transacciones actuales)
├── TransactionDetailsPOS (5,551 items actuales)
└── CashierStatus (122 meseros en sesión)

CBOData_s.mdb (HISTORIAL)
├── TransactionHeader (24,481 transacciones históricas)
├── TransactionDetails (140,209 items históricos)
└── SalesDays (6,095 días de venta)

CBODef_s.mdb (MAESTROS/DEFINICIONES) ← **AQUI ESTAN LOS CODIGOS**
├── CashierDefinitions (124 meseros con nombres)
├── CategoryDefinitions (55 categorías)
├── DepartmentDefinitions (7 departamentos)
├── MediaDefinitions (130 medios de pago)
├── GLLineItems (165 tipos de línea)
└── PriceLevels (6 niveles de precio)

POS2100.mdb (DATOS POS ADICIONALES)
├── ClosedInvoiceItems (2,822 items vendidos)
├── TerminalNumbers (26 terminales)
└── TableSections (secciones de mesas)
```

---

## 12. NOTAS IMPORTANTES

1. **Meseros:** Encontrados 124 con nombres completos
   - Ejemplos: Pepe, Napoleon, Linda, Mustafa, Isabel, Laura
   - Estados: Activos e inactivos

2. **Productos:** Las 55 categorías cubren comida y bebidas
   - Comida: Apetizers, Burritos, Enchiladas, Fajitas, Quesadillas, etc.
   - Bebidas: Cervezas, vinos, licores, refrescos, aguas

3. **Precios:**
   - 6 niveles de precio definidos
   - Tabla de precios de productos vacía (pero precios están en transacciones)
   - Se usan los montos de `DetailItemAmount` de transacciones

4. **Medios de Pago:** 130 medios incluyendo:
   - Efectivo, Cheques, Tarjetas de crédito
   - Descuentos, Propinas, Devoluciones
   - Errores y ajustes

5. **Departamentos:**
   - Comida (1)
   - Bebidas (2)
   - Licores (3)
   - Cervezas (4)
   - Misc (0)

---

**Generado:** 2026-02-22
**Base de Datos Analizada:** CBODef_s.mdb, POS2100.mdb, CBODaily.mdb, CBOData_s.mdb
