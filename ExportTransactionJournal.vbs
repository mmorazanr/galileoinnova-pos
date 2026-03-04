' Script VBScript para exportar TransactionJournal a Excel
' No requiere Access ni dependencias especiales
' Simplemente ejecuta: cscript ExportTransactionJournal.vbs

Option Explicit

Dim objAccess
Dim strDBPath
Dim strReportName
Dim strOutputPath
Dim strFileName
Dim strDateTimeStamp
Dim fso

Set fso = CreateObject("Scripting.FileSystemObject")

' Configuración
strDBPath = "C:\ICOM\Database\CBODaily.mdb"
strReportName = "TransactionJournal"
strOutputPath = "C:\ICOM\Database\Exports\"
strDateTimeStamp = Format(Now(), "yyyy-mm-dd_hh-mm-ss")
strFileName = strOutputPath & "TransactionJournal_" & strDateTimeStamp & ".xlsx"

' Crear carpeta si no existe
If Not fso.FolderExists(strOutputPath) Then
    fso.CreateFolder(strOutputPath)
    WScript.Echo "Carpeta creada: " & strOutputPath
End If

' Intentar exportar
On Error Resume Next

WScript.Echo "Iniciando Access..."
Set objAccess = CreateObject("Access.Application")

If Err.Number <> 0 Then
    WScript.Echo "ERROR: No se pudo crear instancia de Access"
    WScript.Echo "Por favor instala Microsoft Access"
    WScript.Quit(1)
End If

objAccess.Visible = False

WScript.Echo "Abriendo base de datos: " & strDBPath
objAccess.OpenCurrentDatabase strDBPath

If Err.Number <> 0 Then
    WScript.Echo "ERROR: No se pudo abrir la base de datos"
    WScript.Echo "Verifica que la ruta sea correcta: " & strDBPath
    objAccess.Quit
    WScript.Quit(1)
End If

' Exportar el reporte
WScript.Echo "Exportando reporte: " & strReportName
objAccess.DoCmd.OpenReport strReportName, 4 ' 4 = acViewPreview

If Err.Number <> 0 Then
    WScript.Echo "ERROR: No se pudo abrir el reporte"
    WScript.Echo "Verifica que el nombre sea correcto: " & strReportName
Else
    objAccess.DoCmd.OutputTo 3, strReportName, 14, strFileName ' 3=acOutputReport, 14=acFormatXLSX

    If Err.Number <> 0 Then
        WScript.Echo "ERROR: No se pudo exportar"
    Else
        WScript.Echo "EXITO: Archivo creado en:"
        WScript.Echo strFileName
    End If

    objAccess.DoCmd.Close
End If

objAccess.Quit
Set objAccess = Nothing

WScript.Quit(0)
