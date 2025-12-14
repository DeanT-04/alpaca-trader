$ProfilePath = $PROFILE
$ScriptPath = "$PSScriptRoot\alpaca.ps1"
$AliasName = "alpaca"

Write-Host "Installing global alias '$AliasName'..."

if (-not (Test-Path $ProfilePath)) {
    Write-Host "Creating profile at $ProfilePath..."
    New-Item -ItemType File -Path $ProfilePath -Force
}

$FunctionDef = "`nfunction $AliasName { & '$ScriptPath' @args }"

# Check if already installed
$CurrentContent = Get-Content $ProfilePath -Raw
if ($CurrentContent -match "function $AliasName") {
    Write-Host "Alias already exists in profile." -ForegroundColor Yellow
} else {
    Add-Content -Path $ProfilePath -Value $FunctionDef
    Write-Host "Alias added to $ProfilePath" -ForegroundColor Green
    Write-Host "Please restart your terminal or run: . `$PROFILE" -ForegroundColor Cyan
}
