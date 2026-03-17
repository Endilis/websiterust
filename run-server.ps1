# Запуск локального сервера сайта из папки website
# После запуска откройте в браузере: http://localhost:3000/
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
Write-Host "Starting server from: $scriptDir" -ForegroundColor Green
Write-Host "Open in browser: http://localhost:3000/" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow
python -m http.server 3000
