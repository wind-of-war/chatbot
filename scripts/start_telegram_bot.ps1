$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
$logDir = Join-Path $root "logs"
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$out = Join-Path $logDir "telegram_bot.out.log"
$err = Join-Path $logDir "telegram_bot.err.log"

Write-Host "Starting Telegram polling bot ..."
Start-Process -FilePath python `
  -ArgumentList "-m","apps.bot.telegram_polling" `
  -WorkingDirectory $root `
  -RedirectStandardOutput $out `
  -RedirectStandardError $err

Write-Host "Telegram bot started. Logs:"
Write-Host "  $out"
Write-Host "  $err"
