# Wait for Docker to be ready and start the chatbot system

$dockerPath = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Waiting for Docker Desktop to be ready..." -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

$maxAttempts = 30
$attempt = 0
$ready = $false

while (-not $ready -and $attempt -lt $maxAttempts) {
    $attempt++
    Write-Host "Attempt $attempt/$maxAttempts - Checking Docker daemon..." -ForegroundColor Yellow
    
    try {
        $result = & $dockerPath ps 2>&1
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            Write-Host "✓ Docker is ready!" -ForegroundColor Green
        } else {
            Write-Host "  Docker daemon not ready yet, waiting..." -ForegroundColor Gray
            Start-Sleep -Seconds 5
        }
    } catch {
        Write-Host "  Docker daemon not ready yet, waiting..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
}

if (-not $ready) {
    Write-Host ""
    Write-Host "✗ Docker failed to start after $maxAttempts attempts" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Check if Docker Desktop is running (system tray icon)" -ForegroundColor White
    Write-Host "  2. Wait for it to show 'Docker Desktop is running'" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Docker is ready! Starting chatbot system..." -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file" -ForegroundColor Green
    Write-Host ""
}

# Start the chatbot system
Write-Host "Starting all services with Docker Compose..." -ForegroundColor Cyan
Write-Host "This will take 5-10 minutes on first run (downloading images and building)..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Gray
Write-Host ""

& $dockerPath compose up --build
