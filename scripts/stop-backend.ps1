param(
  [int]$Port = 8001
)

$ErrorActionPreference = "Stop"

function Get-PortProcessIds {
  param([int]$TargetPort)

  $ids = @()

  try {
    $ids += Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction SilentlyContinue |
      Select-Object -ExpandProperty OwningProcess
  } catch {
    # Older shells may not have Get-NetTCPConnection.
  }

  $netstatLines = netstat -ano | Select-String ":$TargetPort\s"
  foreach ($line in $netstatLines) {
    if ($line.Line -match "LISTENING\s+(\d+)$") {
      $ids += [int]$Matches[1]
    }
  }

  $ids | Where-Object { $_ -and $_ -ne 0 } | Sort-Object -Unique
}

$processIds = @(Get-PortProcessIds -TargetPort $Port)
if ($processIds.Count -eq 0) {
  Write-Host "No backend listener found on port $Port."
  exit 0
}

$missingProcessIds = @()
foreach ($processId in $processIds) {
  Write-Host "Stopping process $processId on port $Port..."
  try {
    Stop-Process -Id $processId -Force -ErrorAction Stop
  } catch {
    $taskkillOutput = taskkill /PID $processId /F 2>&1
    if ($LASTEXITCODE -ne 0) {
      $message = ($taskkillOutput | Out-String).Trim()
      if ($message -match "not found" -or $message -match "not be found" -or $message -match "ไม่พบ") {
        $missingProcessIds += $processId
        Write-Host "Process $processId is already gone; ignoring stale port entry."
      } else {
        Write-Error $message
      }
    }
  }
}

Start-Sleep -Seconds 1
$remaining = @(Get-PortProcessIds -TargetPort $Port)
$liveRemaining = @(
  $remaining | Where-Object {
    $remainingId = $_
    try {
      Get-Process -Id $remainingId -ErrorAction Stop | Out-Null
      $true
    } catch {
      $false
    }
  }
)

if ($liveRemaining.Count -gt 0) {
  Write-Error "Port $Port is still occupied by live PID(s): $($liveRemaining -join ', ')"
}

if ($remaining.Count -gt 0) {
  $staleRemaining = @($remaining | Where-Object { $liveRemaining -notcontains $_ })
  if ($staleRemaining.Count -gt 0) {
    Write-Host "Ignoring stale port entries with no live process: $($staleRemaining -join ', ')"
  }
}

try {
  $health = Invoke-RestMethod "http://127.0.0.1:$Port/api/health" -TimeoutSec 2
  if ($health) {
    Write-Error "Port $Port still has an HTTP server responding. Close the old backend terminal or use another port."
  }
} catch {
  # No HTTP response means the backend is not reachable.
}

Write-Host "Port $Port is clear."
