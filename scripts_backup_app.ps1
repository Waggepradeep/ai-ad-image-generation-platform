param(
  [string]$Source = "app.py",
  [string]$Backup = "app.py.bak"
)

if (-not (Test-Path $Source)) {
  Write-Error "Source file not found: $Source"
  exit 1
}

Copy-Item $Source $Backup -Force
Write-Output "Backup created: $Backup"
