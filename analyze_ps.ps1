$connectionString = "Provider=Microsoft.Jet.OLEDB.4.0;Data Source=C:\ICOM\Database\CBODef_s.mdb;Jet OLEDB:Database Password=C0mtrex;"
try {
    $conn = New-Object System.Data.OleDb.OleDbConnection($connectionString)
    $conn.Open()
    
    $tables = @('CategoryDefinitions', 'CategoryPOSItemProfiles', 'POSItemDefinitions', 'ProductDefinitions', 'SizedProductDefinitions')
    
    foreach ($table in $tables) {
        Write-Host "`n=== Table: $table ==="
        $cmd = $conn.CreateCommand()
        $cmd.CommandText = "SELECT TOP 1 * FROM [$table]"
        
        try {
            $reader = $cmd.ExecuteReader()
            $cols = @()
            for ($i = 0; $i -lt $reader.FieldCount; $i++) {
                $cols += $reader.GetName($i)
            }
            Write-Host "Columns: $($cols -join ', ')"
            
            if ($reader.Read()) {
                Write-Host "Sample Data Found."
            }
            $reader.Close()
        } catch {
            Write-Host "Error reading table: $_"
        }
    }
    
    $conn.Close()
} catch {
    Write-Host "Connection error: $_"
}

$connectionString2 = "Provider=Microsoft.Jet.OLEDB.4.0;Data Source=C:\ICOM\Database\POS2100.mdb;Jet OLEDB:Database Password=C0mtrex;"
try {
    $conn = New-Object System.Data.OleDb.OleDbConnection($connectionString2)
    $conn.Open()
    
    $tables = @('ActivePunchInfo')
    
    foreach ($table in $tables) {
        Write-Host "`n=== Table: $table ==="
        $cmd = $conn.CreateCommand()
        $cmd.CommandText = "SELECT TOP 1 * FROM [$table]"
        
        try {
            $reader = $cmd.ExecuteReader()
            $cols = @()
            for ($i = 0; $i -lt $reader.FieldCount; $i++) {
                $cols += $reader.GetName($i)
            }
            Write-Host "Columns: $($cols -join ', ')"
            $reader.Close()
        } catch {
            Write-Host "Error reading table: $_"
        }
    }
    
    $conn.Close()
} catch {
    Write-Host "Connection error: $_"
}
