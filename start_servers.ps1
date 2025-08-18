# ScaleUp-Nvidia Startup Script
# This script intelligently installs dependencies and starts both servers

Write-Host "Starting ScaleUp-Nvidia Platform (Docker)..." -ForegroundColor Green
Write-Host ""

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Function to check if a Python package is installed
function Test-PythonPackage($packageName) {
    try {
        python -c "import $packageName" 2>$null
        return $true
    } catch {
        return $false
    }
}

# Check system requirements
Write-Host "Checking system requirements..." -ForegroundColor Yellow

if (-not (Test-Command "docker")) {
    Write-Host "Docker not found. Please install Docker Desktop and ensure it's running." -ForegroundColor Red
    Write-Host "   Install via winget: winget install -e --id Docker.DockerDesktop" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "Building Docker images..." -ForegroundColor Yellow
docker compose build | Write-Host

Write-Host ""
Write-Host "Starting containers..." -ForegroundColor Yellow

# Check if servers are already running
$backendRunning = $false
$frontendRunning = $false

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $backendRunning = $true
        Write-Host "Backend server already running on port 8000" -ForegroundColor Yellow
    }
} catch {
    # Backend not running, which is what we want
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $frontendRunning = $true
        Write-Host "Frontend server already running on port 3000" -ForegroundColor Yellow
    }
} catch {
    # Frontend not running, which is what we want
}

docker compose up -d

Write-Host ""
Write-Host "ScaleUp-Nvidia Platform is running in Docker!" -ForegroundColor Green
Write-Host ""
Write-Host "Access your application:" -ForegroundColor White
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Admin Login:" -ForegroundColor White
Write-Host "   Email: admin@gmail.com" -ForegroundColor Cyan
Write-Host "   Password: admin" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Documentation:" -ForegroundColor White
Write-Host "   Root: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Health: http://localhost:8000/health (Admin only)" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop the platform, type 'stop'..." -ForegroundColor Yellow
Write-Host ""

# Keep the script running
Write-Host "Type 'stop' to stop the servers..." -ForegroundColor Gray
do {
    $input = Read-Host "Enter command"
    if ($input -eq "stop") {
        break
    } else {
        Write-Host "Type 'stop' to stop the servers" -ForegroundColor Yellow
    }
} while ($true)

# Stop the servers
Write-Host ""
Write-Host "Stopping containers..." -ForegroundColor Yellow
docker compose down

Write-Host ""
Write-Host "ScaleUp-Nvidia Platform stopped. Goodbye!" -ForegroundColor Green
