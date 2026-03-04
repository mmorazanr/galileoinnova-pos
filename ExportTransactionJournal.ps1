# Script PowerShell para exportar TransactionJournal.rpt a Excel
# Ejecutar: powershell -ExecutionPolicy Bypass -File ExportTransactionJournal.ps1

param(
    [string]$DBPath = "C:\ICOM\Database\CBODaily.mdb",
    [string]$ReportName = "TransactionJournal",
    [string]$OutputPath = "C:\ICOM\Database\Exports\"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Exportador de TransactionJournal" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Crear carpeta de salida si no existe
if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    Write-Host "[OK] Carpeta creada: $OutputPath" -ForegroundColor Green
}

# Generar nombre de archivo con timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$outputFile = Join-Path $OutputPath "TransactionJournal_$timestamp.xlsx"

# Intentar crear instancia de Access
Write-Host "Intentando conectar a Access..." -ForegroundColor Yellow

try {
    $access = New-Object -ComObject Access.Application
    $access.Visible = $false

    Write-Host "[OK] Access abierto" -ForegroundColor Green

    # Abrir base de datos
    Write-Host "Abriendo: $DBPath" -ForegroundColor Yellow
    $access.OpenCurrentDatabase($DBPath)

    Write-Host "[OK] Base de datos abierta" -ForegroundColor Green

    # Abrir reporte
    Write-Host "Abriendo reporte: $ReportName" -ForegroundColor Yellow
    $access.DoCmd.OpenReport($ReportName, 4)

    # Exportar a Excel
    Write-Host "Exportando a Excel..." -ForegroundColor Yellow
    $access.DoCmd.OutputTo(3, $ReportName, 14, $outputFile)

    # Cerrar reporte
    $access.DoCmd.Close()

    # Cerrar Access
    $access.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($access) | Out-Null

    Write-Host "[SUCCESS] Archivo guardado:" -ForegroundColor Green
    Write-Host "$outputFile" -ForegroundColor Green

} catch {
    Write-Host "[ERROR] No se pudo completar la operación" -ForegroundColor Red
    Write-Host "Detalles: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Posibles soluciones:" -ForegroundColor Yellow
    Write-Host "1. Verifica que Access esté instalado" -ForegroundColor Yellow
    Write-Host "2. Verifica que la ruta de la BD sea correcta" -ForegroundColor Yellow
    Write-Host "3. Verifica que el nombre del reporte sea 'TransactionJournal'" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
