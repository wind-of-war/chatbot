$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
$logDir = Join-Path $root "logs"
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$out = Join-Path $logDir "api.out.log"
$err = Join-Path $logDir "api.err.log"

Write-Host "Starting API at http://127.0.0.1:8000 ..."
Start-Process -FilePath python `
  -ArgumentList "-m","uvicorn","apps.api.main:app","--host","0.0.0.0","--port","8000" `
  -WorkingDirectory $root `
  -RedirectStandardOutput $out `
  -RedirectStandardError $err

Write-Host "API started. Logs:"
Write-Host "  $out"
Write-Host "  $err"
