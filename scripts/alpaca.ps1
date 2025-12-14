param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path $ScriptDir -Parent
$Command = if ($Args.Count -gt 0) { $Args[0] } else { "run" }

Push-Location $ProjectRoot
try {
    switch ($Command) {
        "run" {
            # Default: Run attached with build
            Write-Host "Starting Alpaca Trader (Attached)..." -ForegroundColor Cyan
            docker compose up --build
        }
        "bg" {
            # Run in background
            Write-Host "Starting Alpaca Trader (Background)..." -ForegroundColor Cyan
            docker compose up -d --build
            Write-Host "Started. Use 'alpaca logs' to view output." -ForegroundColor Green
        }
        "stop" {
            Write-Host "Stopping Alpaca Trader..." -ForegroundColor Yellow
            docker compose down
        }
        "logs" {
            docker compose logs -f
        }
        "restart" {
            docker compose restart
            docker compose logs -f
        }
        Default {
            # Check if it helps to fallback or just warn
            Write-Host "Usage: alpaca [run|bg|stop|logs|restart]" -ForegroundColor Yellow
            Write-Host "Default (no args) is 'run' (attached)."
        }
    }
}
finally {
    Pop-Location
}
