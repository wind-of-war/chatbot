param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$AdminEmail = "hiencdt2011@gmail.com",
    [string]$AdminPassword = "Admin@123456",
    [string]$Question = "GDP quy định nhiệt độ bảo quản thuốc là bao nhiêu?"
)

$ErrorActionPreference = "Stop"

function StepOk($name, $detail = "") {
    Write-Host "[PASS] $name $detail"
}

function StepFail($name, $detail) {
    Write-Host "[FAIL] $name $detail"
    exit 1
}

Write-Host "Health check started: $BaseUrl"

try {
    $health = Invoke-RestMethod -Method Get -Uri "$BaseUrl/health" -TimeoutSec 10
    if ($health.status -eq "ok") {
        StepOk "API health" "(status=ok)"
    } else {
        StepFail "API health" "(unexpected response)"
    }
}
catch {
    StepFail "API health" $_.Exception.Message
}

try {
    $loginBody = @{
        email    = $AdminEmail
        password = $AdminPassword
    } | ConvertTo-Json

    $login = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/login" -ContentType "application/json" -Body $loginBody -TimeoutSec 15
    if (-not $login.access_token) {
        StepFail "Admin login" "(no access_token)"
    }
    $token = $login.access_token
    $headers = @{ Authorization = "Bearer $token" }
    StepOk "Admin login" "(user_id=$($login.user_id), role=$($login.role))"
}
catch {
    StepFail "Admin login" $_.Exception.Message
}

try {
    $chatBody = @{ question = $Question } | ConvertTo-Json -Depth 3
    $chat = Invoke-RestMethod -Method Post -Uri "$BaseUrl/chat" -Headers $headers -ContentType "application/json" -Body $chatBody -TimeoutSec 90
    $citationCount = @($chat.citations).Count
    StepOk "RAG chat" "(tokens=$($chat.tokens_used), citations=$citationCount)"
}
catch {
    StepFail "RAG chat" $_.Exception.Message
}

try {
    $deps = Invoke-RestMethod -Method Get -Uri "$BaseUrl/management/dependencies" -Headers $headers -TimeoutSec 20
    $depsText = ($deps | ForEach-Object { "$($_.name)=$($_.ok)" }) -join ", "
    StepOk "Dependencies" "($depsText)"
}
catch {
    StepFail "Dependencies" $_.Exception.Message
}

try {
    if ($env:TELEGRAM_BOT_TOKEN) {
        $me = Invoke-RestMethod -Method Get -Uri "https://api.telegram.org/bot$($env:TELEGRAM_BOT_TOKEN)/getMe" -TimeoutSec 15
        if ($me.ok -eq $true) {
            StepOk "Telegram token" "(bot=@$($me.result.username))"
        } else {
            StepFail "Telegram token" "(api returned ok=false)"
        }
    } else {
        Write-Host "[WARN] Telegram token check skipped (TELEGRAM_BOT_TOKEN env not set in this shell)"
    }
}
catch {
    StepFail "Telegram token" $_.Exception.Message
}

Write-Host "All checks passed."
