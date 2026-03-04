# OPERADORES DEL POS - IDENTIFICACIONES Y CREDENCIALES

**Fuente:** CBODef_s.mdb
**Tabla:** Users + CashierDefinitions
**Contraseña BD:** C0mtrex
**Generado:** 2026-02-22

---

## 1. TABLA PRINCIPAL: Users (Operadores del POS)

**Ubicación:** CBODef_s.mdb → Tabla "Users"

**Campos importantes:**

```
- UserNumber        → ID del operador en el sistema (1-9)
- UserName         → Nombre de usuario para login
- UserPassword     → Contraseña (HASHEADA/CIFRADA en SHA-256 o similar)
- UserGroupID      → Grupo de permisos (1=Admin, 2=Guest)
- Locked           → Si está bloqueado
- PasswordExpirationDate → Cuándo expira
```

---

## 2. OPERADORES ENCONTRADOS (8 totales)

### Tabla completa:

```
UserNumber | UserName   | Password Hash                                    | Grupo | Bloqueado
────────────┼────────────┼────────────────────────────────────────────────┼───────┼───────────
1          | Admin      | A31F6ACEC42EDC9187650B9C8EB0A5B1B3971858... | 1     | No
2          | Guest      | 2F16FB9F84B70CD42075B2A6A1618D25BF4E12D2... | 2     | No
4          | Pepe       | 41D130F9D93A431C3A0953A038D3B0953D339508... | 1     | No
5          | Napoleon   | 61EEC641ACFB77AEF7F2ABCC931811D000F55D5... | 1     | No
6          | Saul       | 765B73E935EF4D6D469B16667ACF7504C052CD78... | 1     | No
7          | isabel     | BB3173588A8C72A40C6C63A906E938C79D04D8350... | 1     | No
8          | Ali        | 9E0CBF1ABA9D26A50FE706698605C046DB136D3E... | 1     | No
9          | zcomtrex   | C8CACE78F0964AAFD010D266D2A3A91AA629EEC2... | 1     | No
```

---

## 3. RELACION CON CASHIERS

**Tabla:** CashierDefinitions (en CBODef_s.mdb)

Los operadores también aparecen como **meseros/cajeros**:

```
CashierNumber | CashierName  | PIN/CashierSecretNumber | Nombre Usuario POS
──────────────┼──────────────┼───────────────────────┼──────────────────────
1             | Pepe         | BMN                   | Pepe (UserNumber 4)
2             | Napoleon     | 4HDCOMJPOP            | Napoleon (UserNumber 5)
1223          | ZComtrex     | 2CGHFDIPM             | zcomtrex (UserNumber 9)
1224          | Isabel       | DOODB                 | isabel (UserNumber 7)
1533          | milton       | FCJDB                 | (No en Users aún)
```

---

## 4. GRUPOS DE PERMISOS

**Tabla:** UserGroups

```
UserGroupID | UserGroupNumber | UserGroupName | Permisos
────────────┼─────────────────┼───────────────┼──────────────────
1           | 1               | Admin         | Todos los permisos
2           | 2               | Guest         | Permisos limitados
-2          | -2              | POSLite       | Sistema limitado
```

---

## 5. IMPORTANCIA DE LOS CAMPOS

### UserNumber
- ID único del operador en el sistema
- Rango: 1-9 (en este sistema)
- **Ejemplo:** Milton podría tener UserNumber que aún no aparece en Users

### UserPassword
- **IMPORTANTE:** Está HASHEADA/CIFRADA
- No es la contraseña en texto plano
- Algoritmo usado: SHA-256 o similar (64 caracteres hexadecimales)
- **NO se puede descodificar fácilmente**
- Se valida mediante hash comparison en login

### CashierSecretNumber
- Código de PIN o código secreto
- Alfanumérico (ej: "BMN", "4HDCOMJPOP", "FCJDB")
- Usado probablemente como PIN backup o identificador

---

## 6. DONDE ESTAN LOS IDS DE OPERADORES

### Sistema POS usa DOS identificadores:

**Opción 1: UserNumber (ID Sistema)**
- Almacenado en tabla Users
- Rango: 1-9
- Para login en sistema de back office

**Opción 2: CashierNumber (ID Caja/POS)**
- Almacenado en tabla CashierDefinitions
- Rango: 0-1536+
- Para login en terminales POS

### Ejemplo: Milton

```
Nombre: milton
CashierNumber: 1533 (ID de caja)
PIN/Secret: FCJDB
SSN: 0998857786
Grupo: 2 (permiso limitado)
```

Si Milton tiene **ID 0202** como mencionaste, probablemente:
- 02 = Código del turno o terminal
- 02 = Número correlativo

---

## 7. DONDE BUSCAR CREDENCIALES TEXTO PLANO

**Las contraseñas hasheadas NO se pueden recuperar directamente**, pero puedes:

### Opción A: Usar CashierSecretNumber
```sql
SELECT CashierNumber, CashierName, CashierSecretNumber
FROM CashierDefinitions
WHERE CashierName = 'milton'
```
Resultado: `1533 | milton | FCJDB` (este es el PIN)

### Opción B: Ver campos adicionales en Users
```sql
SELECT UserNumber, UserName, PreviousPassword1, PreviousPassword2,
       PreviousPassword3, PreviousPassword4
FROM Users
WHERE UserName = 'milton'
```
(También hasheadas)

### Opción C: Revisar logs si existen
- Buscar en tablas de audit/log
- Revisar `AccountTransactionLog`
- Buscar en `DBRevisions` cambios de contraseña

---

## 8. CAMPOS ADICIONALES IMPORTANTES

### En tabla Users:

```
- Language              → Idioma del usuario (1033=English, 1034=Español)
- Employee             → Si es empleado (True/False)
- SSNumber            → Número de Seguro Social
- FirstName/LastName  → Nombre completo
- AllStores           → Acceso a todas sucursales
- SingleStore         → Acceso a sucursal específica
- Locked              → Si está bloqueado
- PasswordExpirationDate → Vencimiento contraseña
- PasswordNeverExpires → Contraseña nunca expira
- Signature           → Firma digital (hash)
```

### En tabla CashierDefinitions:

```
- CashierNumber        → ID de caja
- CashierName         → Nombre del mesero
- CashierSecretNumber → PIN/Código (alfanumérico)
- CashierDrawerNumber → Número de caja registradora
- Active              → Si está activo
- DefaultTableSection → Sección asignada
- MasterServer        → Es mesero maestro
- MgrAllow            → Permisos de gerente
- SSNumber            → Documento de identidad
```

---

## 9. CONSULTAS UTILES

### Obtener todos los operadores activos:

```sql
SELECT UserNumber, UserName, UserGroupID, Locked
FROM Users
WHERE Locked = False
ORDER BY UserNumber
```

### Obtener operador específico:

```sql
SELECT u.UserNumber, u.UserName, c.CashierNumber, c.CashierName, c.CashierSecretNumber
FROM Users u
LEFT JOIN CashierDefinitions c ON u.UserName = c.CashierName
WHERE u.UserName = 'milton'
```

### Ver permisos de un operador:

```sql
SELECT ug.UserGroupName, ug.EditMenuItems, ug.EditUsers,
       ug.DoEndOfDay, ug.AccessReports
FROM Users u
JOIN UserGroups ug ON u.UserGroupID = ug.UserGroupID
WHERE u.UserName = 'milton'
```

### Obtener todos los meseros con PIN:

```sql
SELECT CashierNumber, CashierName, CashierSecretNumber
FROM CashierDefinitions
WHERE CashierSecretNumber IS NOT NULL
ORDER BY CashierNumber
```

---

## 10. SEGURIDAD - NOTAS IMPORTANTES

### Sobre contraseñas hasheadas:

1. **No se pueden descodificar** - Son one-way hashes
2. **Se validan comparando hashes** - Hash(entrada) == Hash(BD)
3. **Se almacenan cifradas** - No en texto plano
4. **Hay historial** - Últimas 4 contraseñas guardadas

### Para cambiar contraseña de un operador:

Necesitarías:
- Acceso directo a la BD con permisos de escritura
- O usar interfaz de administración del POS
- Generar nuevo hash de contraseña

### Para auditar logins:

Buscar en:
- `AccountTransactionLog` - Transacciones por usuario
- `DBRevisions` - Cambios en la BD
- `EventLog` - Si existe tabla de eventos
- Logs del sistema operativo

---

## 11. MAPEO ENCONTRADO

**Milton:**
```
UserName (POS):     milton
CashierNumber:      1533
PIN/Secret:         FCJDB
SSN:                0998857786
Grupo:              2 (Guest/Limited)
Status:             Activo (No bloqueado)
UserNumber (Sistema): [Buscar en tabla Users]
```

---

## 12. COMO OBTENER ID 0202 Y PASSWORD 2812

Como mencionaste que Milton tiene:
- **ID: 0202**
- **Password: 2812**

Estas podrían ser:

1. **Terminal de acceso local:**
   - 02 = Terminal número 2
   - 02 = Operador número 2
   - Contraseña 2812 = PIN de 4 dígitos

2. **Código de acceso POS:**
   - Diferente del UserNumber del sistema
   - Asignado directamente en terminal
   - Almacenado localmente en POS

3. **Datos en otra tabla:**
   - Posiblemente en tabla de configuración local del POS
   - En archivos INI del sistema
   - En tabla POSBOSoftwareOptions

---

## 13. DONDE ESTAN LOS IDS "0202"

Para encontrar dónde está guardado "0202", busca en:

```sql
-- En tabla Users
SELECT * FROM Users WHERE UserNumber = 2 OR UserName LIKE '%0202%'

-- En CashierDefinitions
SELECT * FROM CashierDefinitions WHERE CashierNumber = 202
    OR CashierSecretNumber LIKE '%0202%'

-- En POS2100ini
SELECT * FROM POS2100ini

-- En configuración
SELECT * FROM POSMiscOptions
```

---

**Generado:** 2026-02-22
**Base de Datos Analizada:** CBODef_s.mdb
**Tabla Principal:** Users (Operadores) + CashierDefinitions (Meseros)
