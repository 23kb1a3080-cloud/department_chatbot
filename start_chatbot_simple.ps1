# Simple script to start the chatbot system
# Make sure Docker Desktop is running first!

$dockerPath = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"

Write-Host "Checking Docker..." -ForegroundColor Yellow

# Test if Docker is ready
$dockerReady = $false
try {
    & $dockerPath ps | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $dockerReady = $true
    }
} catch {
    $dockerReady = $false
}

if (-not $dockerReady) {
    Write-Host "Docker is not ready yet." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please wait for Docker Desktop to fully start (check system tray)" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or wait 30 seconds and I'll try again..." -ForegroundColor Cyan
    Start-Sleep -Seconds 30
    
    & $dockerPath ps | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker still not ready. Please start Docker Desktop and try again." -ForegroundColor Red
        exit 1
    }
}

Write-Host "✓ Docker is ready!" -ForegroundColor Green
Write-Host ""

# Create .env if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting College AI Chatbot System..." -ForegroundColor Cyan
Write-Host "This may take 5-10 minutes on first run..." -ForegroundColor Yellow
Write-Host ""

# Start docker compose
& $dockerPath compose up --build
