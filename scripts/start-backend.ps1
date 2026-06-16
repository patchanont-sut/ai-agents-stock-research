param(
  [int]$Port = 8001,
  [string]$HostAddress = "127.0.0.1"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$stopScript = Join-Path $PSScriptRoot "stop-backend.ps1"

& $stopScript -Port $Port

Write-Host "Starting backend on http://${HostAddress}:$Port"
Write-Host "Backend directory: $backendDir"
Write-Host "Use Ctrl+C in this terminal to stop it."

Set-Location $backendDir
python -m uvicorn main:app --host $HostAddress --port $Port
