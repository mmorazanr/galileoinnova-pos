# OPERADOR MILTON - CREDENCIALES COMPLETAS Y IDS

**Generado:** 2026-02-22
**Base de Datos:** CBODef_s.mdb, CBODaily.mdb, CBOData_s.mdb
**Contraseña BD:** C0mtrex

---

## RESUMEN EJECUTIVO

El operador **Milton** en el sistema POS del restaurante tiene **múltiples identificadores** según el contexto de uso:

| Contexto | ID | Tipo | Ubicación |
|----------|----|----|-----------|
| **POS Terminal Login** | 0202 | POSSwipeNumber | EmpMain |
| **Database Cashier ID** | 1533 | CashierNumber | CashierDefinitions |
| **Sistema Back-Office** | [Buscar] | UserNumber | Users (si existe) |
| **Link de Base Datos** | 0998857786 | SSNumber | Común en todas tablas |

---

## 1. IDENTIFICACION POS TERMINAL (ID 0202)

**Tabla:** EmpMain (en CBODef_s.mdb)
**Campo clave:** POSSwipeNumber

```
POSSwipeNumber:      0202          ← ID DE LOGIN EN TERMINAL POS
ComtrexEmpID:        202
SSNumber:            0998857786     ← Link a otras tablas
FirstName:           milton
LastName:            morazan
DateHired:           2025-05-17
Terminated:          False
```

**Uso:** Este es el ID que se usa para loguearse en las terminales POS del restaurante.
**Consulta SQL:**
```sql
SELECT POSSwipeNumber, SSNumber, FirstName, LastName, ComtrexEmpID
FROM EmpMain
WHERE FirstName = 'milton' OR POSSwipeNumber = '0202'
```

---

## 2. CREDENCIAL EN TERMINAL POS (Contraseña 2812)

**Ubicación:** Terminal POS local (NO en base de datos central)

```
Terminal ID:         0202
Contraseña:          2812           ← Almacenada localmente en terminal
Tipo:                PIN de 4 dígitos
```

**Nota Importante:** La contraseña "2812" NO se encuentra en la base de datos central. Es almacenada:
- Localmente en la memoria de la terminal POS
- Potencialmente en archivos de configuración locales
- O sincronizada desde servidor local

**Para obtener/cambiar:** Necesitaría acceso directo a la terminal POS o archivo de configuración local.

---

## 3. IDENTIFICACION DATABASE (ID 1533)

**Tabla:** CashierDefinitions (en CBODef_s.mdb)
**Campo clave:** CashierNumber

```
CashierNumber:       1533           ← ID en base de datos
CashierName:         milton
CashierSecretNumber: FCJDB          ← PIN alfanumérico backup
SSNumber:            0998857786     ← Link a EmpMain
DefaultTableSection: Main Dining
PosOpGroupNumber:    2 (Server)
Active:              True (Activo)
MasterServer:        False
DiscAllow:           True (Permite descuentos)
MgrAllow:            False
CashierDrawerNumber: [No especificado en datos]
```

**Uso:** Este ID se usa en:
- Transacciones de historial
- Reportes de ventas
- Tracking de actividad
- Base de datos de transacciones (CBOData_s.mdb)

**Consulta SQL:**
```sql
SELECT CashierNumber, CashierName, CashierSecretNumber, SSNumber,
       DefaultTableSection, Active, PosOpGroupNumber
FROM CashierDefinitions
WHERE CashierName = 'milton' OR CashierNumber = 1533
```

---

## 4. PIN/CREDENCIAL EN DATABASE (FCJDB)

**Tabla:** CashierDefinitions
**Campo:** CashierSecretNumber

```
CashierSecretNumber: FCJDB          ← PIN alfanumérico
Tipo:                Código secreto (6 caracteres)
Propósito:           Backup o acceso alternativo en terminal
Formato:             Alfanumérico (letras mayúsculas + números)
```

**Nota:** Este código NO es la contraseña de terminal (2812). Es un código adicional que podrá:
- Servir como PIN backup
- Identificador de autorización
- Código de acceso a caja de la terminal

**Posibles ubicaciones de uso:**
- Abridor/Cierre de caja
- Devoluciones o transacciones especiales
- Sincronización con servidor

---

## 5. GRUPO DE PERMISO EN POS (Servidor)

**Tabla:** POSOperatorGroups (en CBODef_s.mdb)
**Campo referenciado:** PosOpGroupNumber

```
PosOpGroupNumber:    2
PosOpGroupName:      Server         ← Mesero/Servidor
MasterServer:        False
RingSales:           True            ← Permite registrar ventas
AllowVoid:           [Check needed]
AllowDiscount:       True            ← Permite descuentos (de CashierDef)
ReceivePayment:      [Check needed]
```

**Significado:** Milton tiene rol de **SERVIDOR** en el POS, lo que significa:
- Puede registrar órdenes y ventas
- Puede aplicar descuentos
- Acceso limitado (no es administrador)

---

## 6. HISTORIAL DE TRANSACCIONES DE MILTON

**Datos encontrados:** Milton (CashierNumber 1533) tiene transacciones en:

**Base de Datos:** CBOData_s.mdb (historial completo)
**Período:** Junio 2025 (datos históricos)
**Tabla:** TransactionHeader

```sql
SELECT COUNT(*) as Transacciones, SUM(DetailItemAmount) as Total
FROM TransactionHeader th
JOIN TransactionDetails td ON th.TransactionHeaderID = td.TransactionHeaderID
WHERE th.CashierNumber = 1533
```

---

## 7. MAPEO COMPLETO DE MILTON

```
┌─────────────────────────────────────────────────────────────┐
│                    MILTON (milton morazan)                   │
│                   SSNumber: 0998857786                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ ├─ POS TERMINAL                                              │
│ │  ├─ ID: 0202 (POSSwipeNumber en EmpMain)                  │
│ │  ├─ Contraseña: 2812 (local en terminal, no en BD)        │
│ │  └─ Ubicación: Terminal física del restaurante            │
│ │                                                             │
│ ├─ DATABASE SYSTEM                                           │
│ │  ├─ CashierNumber: 1533 (en CashierDefinitions)           │
│ │  ├─ PIN: FCJDB (CashierSecretNumber)                       │
│ │  ├─ Rol: Server (PosOpGroupNumber 2)                      │
│ │  ├─ Estado: Activo                                        │
│ │  └─ Transacciones: [En CBOData_s.mdb]                    │
│ │                                                             │
│ └─ EMPLOYEE MASTER                                           │
│    ├─ First Name: milton                                     │
│    ├─ Last Name: morazan                                     │
│    ├─ Hired: 2025-05-17                                      │
│    ├─ Terminated: False                                      │
│    └─ ComtrexEmpID: 202                                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. TABLAS CONSULTADAS

Las tablas consultadas para obtener esta información están en:

**CBODef_s.mdb (Definiciones Maestras):**
- `EmpMain` - Registros de empleados con POSSwipeNumber
- `CashierDefinitions` - Definiciones de cajas/meseros
- `POSOperatorGroups` - Grupos de permisos del POS
- `Users` - Usuarios del sistema (si Milton tiene acceso back-office)

**CBODaily.mdb (Operaciones Diarias):**
- `CashierStatus` - Estado actual de meseros activos
- `TransactionHeaderPOS` - Transacciones del día

**CBOData_s.mdb (Historial):**
- `TransactionHeader` - Todas las transacciones históricas
- `TransactionDetails` - Detalles de items vendidos

---

## 9. RESUMEN DE CONTRASEÑAS/CREDENCIALES

| Tipo | Valor | Ubicación | Tipo Datos | Recuperable? |
|------|-------|-----------|-----------|--------------|
| ID Terminal POS | 0202 | EmpMain.POSSwipeNumber | Texto plano | ✓ Sí |
| Contraseña Terminal | 2812 | Local en terminal | NO en BD | ✗ No (local) |
| ID Database | 1533 | CashierDefinitions.CashierNumber | Texto plano | ✓ Sí |
| PIN Database | FCJDB | CashierDefinitions.CashierSecretNumber | Texto plano | ✓ Sí |
| Usuario Back-Office | ? | Users.UserName | Hashed SHA-256 | ✗ No (hashed) |
| SSN Link | 0998857786 | EmpMain.SSNumber, CashierDefinitions.SSNumber | Texto plano | ✓ Sí |

---

## 10. CONSULTAS PARA OBTENER TODOS LOS OPERADORES CON ESTE FORMATO

### Obtener todos los operadores con IDs POS:
```sql
SELECT
    e.POSSwipeNumber as 'POS ID',
    e.FirstName + ' ' + e.LastName as 'Nombre',
    e.SSNumber as 'SSN',
    c.CashierNumber as 'Database ID',
    c.CashierSecretNumber as 'PIN',
    c.DefaultTableSection as 'Sección',
    c.Active as 'Activo'
FROM EmpMain e
LEFT JOIN CashierDefinitions c ON e.SSNumber = c.SSNumber
WHERE e.Terminated = False
ORDER BY e.POSSwipeNumber
```

---

## 11. CONCLUSIONES

✓ **ID Terminal POS de Milton:** 0202
✓ **ID Database de Milton:** 1533
✓ **PIN Database de Milton:** FCJDB
✓ **Link de Base de Datos:** SSNumber 0998857786
⚠ **Contraseña Terminal:** 2812 (almacenada localmente en terminal, no en BD central)

La estructura dual de IDs (Terminal + Database) permite:
- Login independiente en terminal POS
- Tracking de transacciones en base de datos histórica
- Sincronización entre sistemas
- Control de permisos por rol

---

**Generado:** 2026-02-22
**Fuente:** Análisis completo de CBODef_s.mdb, CBODaily.mdb, CBOData_s.mdb
**Contraseña Base de Datos:** C0mtrex

