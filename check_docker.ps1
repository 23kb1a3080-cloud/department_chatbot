# Docker Installation Verification Script
# Run this after installing Docker Desktop

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Docker Installation Verification" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check if Docker command exists
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker is installed: $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker command failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Docker is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Docker Desktop:" -ForegroundColor Yellow
    Write-Host "  1. Visit: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Write-Host "  2. Download and install Docker Desktop" -ForegroundColor White
    Write-Host "  3. Restart your computer" -ForegroundColor White
    Write-Host "  4. Start Docker Desktop" -ForegroundColor White
    Write-Host "  5. Run this script again" -ForegroundColor White
    exit 1
}

# Check Docker Compose
Write-Host "Checking Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker Compose is available: $composeVersion" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker Compose not available" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Docker Compose not available" -ForegroundColor Red
    exit 1
}

# Check if Docker daemon is running
Write-Host "Checking Docker daemon..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker daemon is running" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker daemon is not running" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please start Docker Desktop from the Start Menu" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "✗ Docker daemon is not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start Docker Desktop from the Start Menu" -ForegroundColor Yellow
    exit 1
}

# Test Docker with hello-world
Write-Host "Testing Docker with hello-world image..." -ForegroundColor Yellow
try {
    $testOutput = docker run --rm hello-world 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker is working correctly" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker test failed" -ForegroundColor Red
        Write-Host $testOutput
        exit 1
    }
} catch {
    Write-Host "✗ Docker test failed" -ForegroundColor Red
    exit 1
}

# Check system resources
Write-Host ""
Write-Host "Checking system resources..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info --format "{{json .}}" | ConvertFrom-Json
    Write-Host "  CPUs: $($dockerInfo.NCPU)" -ForegroundColor White
    Write-Host "  Memory: $([math]::Round($dockerInfo.MemTotal / 1GB, 2)) GB" -ForegroundColor White
} catch {
    Write-Host "  Could not retrieve resource information" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "✓ All checks passed! Docker is ready to use." -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Navigate to your project directory" -ForegroundColor White
Write-Host "  2. Run: docker compose up --build" -ForegroundColor White
Write-Host "  3. Access services at http://localhost:8000-8006" -ForegroundColor White
Write-Host ""
