# Guía: Usar LibreOffice para Exportar TransactionJournal a Excel

## Paso 1: Descargar LibreOffice

1. **Ve a:** https://www.libreoffice.org/download/download-libreoffice/

2. **Elige tu versión:**
   - **Windows (Intel x86)** = Selecciona esta (versión estándar de Windows)
   - O **Windows (x64)** si tienes Windows 64 bits (más moderno)

3. **Haz clic en "Download"**
   - Se descargará un archivo `.exe` (ejemplo: `LibreOffice_7.x.x_Win_x86_portable.exe`)
   - Generalmente va a: `C:\Users\admin\Downloads\`

---

## Paso 2: Instalar LibreOffice

1. **Localiza el archivo descargado**
   - Busca en: `C:\Users\admin\Downloads\`
   - Debería llamarse algo como `LibreOffice_*.exe`

2. **Ejecuta como Administrador**
   - Click derecho en el archivo
   - Selecciona: "Run as Administrator"

3. **Sigue el instalador**
   - Acepta la licencia (GPL)
   - Elige ubicación (por defecto está bien)
   - Click en "Install"
   - Espera a que termine (5-10 minutos)

4. **Reinicia (opcional)**
   - Si lo pide, reinicia la computadora
   - Si no, continúa

---

## Paso 3: Abre la Base de Datos con LibreOffice

### Método A: Desde File Explorer (Más fácil)

1. **Abre File Explorer**
   - Presiona: `Windows + E`

2. **Navega a:**
   ```
   C:\ICOM\Database\
   ```

3. **Busca:**
   ```
   CBODaily.mdb
   ```

4. **Click derecho en el archivo**
   - Selecciona: "Open with..." → "LibreOffice Base"
   - O simplemente doble-clic (si LibreOffice es el programa predeterminado)

### Método B: Desde LibreOffice (Alternativa)

1. **Abre LibreOffice Base**
   - Busca en el menú de Inicio: "LibreOffice Base"
   - O presiona `Windows` y escribe: "LibreOffice Base"

2. **File → Open**
   - Navega a: `C:\ICOM\Database\CBODaily.mdb`
   - Click en "Open"

---

## Paso 4: Buscar el Reporte TransactionJournal

Una vez abierta la base de datos en LibreOffice Base:

1. **En el panel izquierdo, busca:**
   ```
   Reports (o Reportes)
   ```

2. **Click en "Reports"** para expandir la carpeta

3. **Busca en la lista:**
   ```
   TransactionJournal
   ```

4. **Click derecho en TransactionJournal**
   - Selecciona: "Export" o "Export to Excel"

---

## Paso 5: Exportar a Excel

### Si aparece un diálogo "Export":

1. **Elige formato:**
   - Selecciona: "Microsoft Excel (.xlsx)" o "Microsoft Excel 2007-365 (.xlsx)"

2. **Elige ubicación:**
   - Navega a: `C:\ICOM\Database\Exports\`
   - O crea una carpeta nueva si no existe

3. **Dale un nombre al archivo:**
   - Ejemplo: `TransactionJournal.xlsx`
   - O: `TransactionJournal_FECHA.xlsx`

4. **Click en "Export" o "Save"**

5. **Espera a que termine**
   - Debería ver un mensaje de confirmación

---

## Paso 6: Verifica que funcione

1. **Abre el archivo exportado:**
   - Ve a: `C:\ICOM\Database\Exports\`
   - Doble-clic en: `TransactionJournal.xlsx`
   - Debería abrir en Excel

2. **Verifica los datos:**
   - ¿Contiene datos de transacciones?
   - ¿Se ve correcto?
   - ¿Tiene todas las columnas esperadas?

---

## ✅ ¡Listo!

Si todo funciona, tienes tu archivo Excel exportado sin necesidad de Access.

---

## 🆘 Solucionar Problemas

### Error: "No puedo encontrar Reports en LibreOffice"

**Solución:**
1. Cierra LibreOffice
2. Abre la BD nuevamente
3. Busca en la parte izquierda:
   - Si ves "Tables" → Hay datos
   - Si ves "Reports" → Hay reportes
   - Si NO ves nada → Probablemente los reportes están guardados diferente

**Alternativa:** Si no ves Reports directamente:
1. En LibreOffice, ve a: View → Reports
2. O busca manualmente en la estructura de la base de datos

### Error: "El archivo no se puede exportar"

**Solución:**
1. Asegúrate que la carpeta `C:\ICOM\Database\Exports\` existe
2. Si no existe, créala:
   - Click derecho en `C:\ICOM\Database\`
   - "New" → "Folder"
   - Nombre: "Exports"

3. Intenta exportar nuevamente

### Error: "Report appears corrupted"

**Solución:**
El reporte podría estar dañado en LibreOffice (limitación de compatibilidad).
En este caso:
1. Prueba con la alternativa: **CloudConvert online**
2. O intenta reparar la BD: Herramientas especializadas

---

## 📞 ¿Necesitas ayuda en algún paso?

Dime:
1. ¿En qué paso te quedaste?
2. ¿Qué mensaje de error ves?
3. ¿Llegaste a ver la estructura de la BD en LibreOffice?

Te ayudaré a completar el proceso.
