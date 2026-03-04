# Guía: Descargar e Instalar Microsoft Access Runtime (GRATIS)

## Paso 1: Descargar el Archivo Correcto

Microsoft ofrece diferentes versiones de Access Runtime. Elige según tu sistema:

### Para Windows 11 / Windows 10 (Recomendado):
**Access Runtime 2024 (Más reciente)**

1. Ve a: https://www.microsoft.com/en-us/download/details.aspx?id=105047
2. Busca el archivo: `AccessRuntime_X64_en-us.exe` (64 bits - versión estándar)
3. Haz clic en "Download"

**O si prefieres una versión más estable:**
**Access Runtime 2019**

1. Ve a: https://www.microsoft.com/en-us/download/details.aspx?id=99156
2. Descarga: `AccessRuntime.exe` (tu versión)

---

## Paso 2: Instalar Access Runtime

1. **Localiza el archivo descargado**
   - Generalmente en: `C:\Users\admin\Downloads\AccessRuntime_X64_en-us.exe`

2. **Ejecuta como Administrador**
   - Click derecho en el archivo
   - Selecciona "Run as Administrator"

3. **Acepta los términos**
   - Lee y acepta la licencia de Microsoft
   - Click en "Accept and Continue"

4. **Elige ubicación de instalación**
   - Puedes dejar la ubicación por defecto
   - Click en "Install Now"

5. **Espera a que termine la instalación**
   - Puede tomar 5-10 minutos
   - Tu computadora podría reiniciarse

6. **Verifica la instalación**
   - Abre el "Command Prompt" o PowerShell
   - Escribe: `mdb2sql /help` (debería reconocer el comando)

---

## Paso 3: Verificar que está instalado correctamente

Abre PowerShell y copia esto:

```powershell
$access = New-Object -ComObject Access.Application
$access.Quit()
Write-Host "Access Runtime instalado correctamente!"
```

Si ves el mensaje sin errores = **¡Éxito!**

---

## Paso 4: Exportar el Reporte TransactionJournal

Una vez instalado Access Runtime, puedes usar cualquiera de estos métodos:

### MÉTODO A: PowerShell (Recomendado - con colores y detalles)

1. Abre PowerShell
2. Navega a la carpeta: `cd C:\ICOM\Database`
3. Ejecuta el script:
   ```powershell
   powershell -ExecutionPolicy Bypass -File ExportTransactionJournal.ps1
   ```

4. El archivo se guardará en: `C:\ICOM\Database\Exports\TransactionJournal_FECHA_HORA.xlsx`

---

### MÉTODO B: VBScript (Alternativa)

1. Abre Command Prompt (cmd.exe)
2. Navega a la carpeta: `cd C:\ICOM\Database`
3. Ejecuta:
   ```cmd
   cscript ExportTransactionJournal.vbs
   ```

4. Verás los mensajes de progreso
5. El archivo estará en: `C:\ICOM\Database\Exports\`

---

### MÉTODO C: Manual (Sin scripts)

Si prefieres no usar scripts:

1. Abre File Explorer
2. Navega a: `C:\ICOM\Database\`
3. Haz doble clic en: `CBODaily.mdb`
4. Busca en el panel izquierdo: "Reports"
5. Encuentra: "TransactionJournal"
6. Click derecho → "Export"
7. Elige formato: "Microsoft Excel (*.xlsx)"
8. Selecciona ubicación: `C:\ICOM\Database\Exports\`
9. Dale un nombre al archivo
10. Click "Export"

---

## 🆘 Solucionar Problemas

### Error: "Access Application not found"
**Solución:** Reinstala Access Runtime y asegúrate de reiniciar

### Error: "Cannot open database"
**Solución:** La base de datos podría estar en uso. Cierra cualquier aplicación que use CBODaily.mdb

### Error: "Report not found"
**Solución:** El nombre del reporte podría ser diferente. Abre la BD manualmente y verifica el nombre exacto

### El script se abre pero no hace nada
**Solución:** Ejecuta como Administrador

---

## ✅ Verificación Final

Una vez que tengas el archivo Excel en `C:\ICOM\Database\Exports\`, verifica:
- [ ] El archivo se llama `TransactionJournal_*.xlsx`
- [ ] Contiene datos de transacciones
- [ ] Puedes abrirlo con Excel
- [ ] Los datos se ven correctos

---

## 📞 Si Necesitas Ayuda

1. Comparte el número de versión de Windows (Settings → System → About)
2. Dime si recibiste algún mensaje de error específico
3. Dime cuál método intentaste (A, B o C)

¡Listo! Ahora sigue los pasos y avísame si tienes preguntas.
