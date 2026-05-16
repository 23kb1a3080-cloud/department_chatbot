# Start College AI Chatbot System
# Run this script after Docker is installed and running

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "College AI Chatbot System - Startup Script" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check if Docker is available
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Docker is not available" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please run: .\check_docker.ps1" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✓ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Docker Desktop first." -ForegroundColor Yellow
    Write-Host "See DOCKER_INSTALLATION_GUIDE.md for instructions." -ForegroundColor Yellow
    exit 1
}

# Check if Docker daemon is running
Write-Host "Checking Docker daemon..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Docker daemon is not running" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please start Docker Desktop from the Start Menu" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✓ Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker daemon is not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start Docker Desktop from the Start Menu" -ForegroundColor Yellow
    exit 1
}

# Check if .env file exists
Write-Host "Checking configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "⚠ .env file not found, creating from template..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ Created .env file from template" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠ IMPORTANT: Edit .env file with your configuration before production use" -ForegroundColor Yellow
    } else {
        Write-Host "✗ .env.example not found" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ Configuration file exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Starting College AI Chatbot System..." -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  • Build Docker images for all services" -ForegroundColor White
Write-Host "  • Start PostgreSQL database" -ForegroundColor White
Write-Host "  • Start Redis cache" -ForegroundColor White
Write-Host "  • Start 7 microservices" -ForegroundColor White
Write-Host "  • Start Celery worker" -ForegroundColor White
Write-Host ""
Write-Host "This may take 5-10 minutes on first run..." -ForegroundColor Yellow
Write-Host ""

# Start Docker Compose
Write-Host "Running: docker compose up --build" -ForegroundColor Cyan
Write-Host ""

docker compose up --build

# This will run until you press Ctrl+C
