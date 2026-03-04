# LibreOffice con Base de Datos Protegida por Contraseña

## Contraseña: C0mtrex

---

## Paso 1: Abre LibreOffice Base

**Opción A (Recomendada):**
1. Abre File Explorer
2. Ve a: `C:\ICOM\Database\`
3. Click derecho en: `CBODaily.mdb`
4. "Open with..." → "LibreOffice Base"

**Opción B:**
1. Abre LibreOffice Base
2. File → Open
3. Selecciona: `C:\ICOM\Database\CBODaily.mdb`
4. Click: Open

---

## Paso 2: Ingresa la Contraseña

Cuando intentes abrir la BD, aparecerá un diálogo:

```
═════════════════════════════════════════
        Enter Database Password
═════════════════════════════════════════

Password: [_______________]

[OK]  [Cancel]
```

**Ingresa:**
```
C0mtrex
```

**Importante:**
- ✓ Mayúsculas/minúsculas importan (es: C0mtrex, no c0mtrex)
- ✓ El "0" es un cero (0), no la letra O
- ✓ Presiona: [OK]

---

## Paso 3: Busca y Exporta el Reporte

Una vez dentro:

1. **Panel izquierdo:**
   - Busca: "Reports"
   - Expande la carpeta

2. **Busca:**
   ```
   TransactionJournal
   ```

3. **Click derecho:**
   - "Export" → "Microsoft Excel (.xlsx)"

4. **Ubicación:**
   ```
   C:\ICOM\Database\Exports\
   ```

5. **Nombre:**
   ```
   TransactionJournal.xlsx
   ```

6. **Click: Export**

---

## ✅ Resultado

El archivo estará en:
```
C:\ICOM\Database\Exports\TransactionJournal.xlsx
```

---

## 🆘 Si no funciona la contraseña

**Si ves error: "Invalid password"**

Verifica:
1. ¿La contraseña es exactamente: `C0mtrex` ?
   - (C mayúscula, luego 0 cero, luego mtrex)
2. ¿Sin espacios antes o después?
3. ¿Copiar/pegar para evitar errores de tipeo?

Si aún no funciona:
- La contraseña podría ser diferente
- Prueba: `contrex`, `Contrex`, `CONTREX`, etc.

---

## Alternativa: Si LibreOffice no pide contraseña

Algunos archivos .mdb están protegidos a nivel de usuario en Windows, no de base de datos.

En ese caso:
1. LibreOffice abre normalmente
2. Pero solo ciertos objetos pueden estar protegidos
3. Los reportes podrían estar disponibles sin contraseña

Continúa con los pasos normales de búsqueda y exportación.

---

## 💡 Nota técnica

LibreOffice Base puede manejar:
- ✓ Contraseñas de apertura de BD (lo que tenemos)
- ✓ Permisos de usuario (más complejos)

Si todo lo demás falla y necesitas máximo acceso:
Consulta también: CloudConvert Online (alternativa sin instalar)
