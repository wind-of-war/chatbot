$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
$logDir = Join-Path $root "logs"
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$out = Join-Path $logDir "worker.out.log"
$err = Join-Path $logDir "worker.err.log"

Write-Host "Starting Celery worker ..."
Start-Process -FilePath python `
  -ArgumentList "-m","celery","-A","apps.worker.celery_app.celery_app","worker","-l","info" `
  -WorkingDirectory $root `
  -RedirectStandardOutput $out `
  -RedirectStandardError $err

Write-Host "Worker started. Logs:"
Write-Host "  $out"
Write-Host "  $err"
