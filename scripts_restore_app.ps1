param(
  [string]$Backup = "app.py.bak",
  [string]$Target = "app.py"
)

if (-not (Test-Path $Backup)) {
  Write-Error "Backup file not found: $Backup"
  exit 1
}

Copy-Item $Backup $Target -Force
Write-Output "Restored: $Target from $Backup"
