# ScaleUp-Nvidia Startup Script
# This script intelligently installs dependencies and starts both servers

Write-Host "Starting ScaleUp-Nvidia Platform..." -ForegroundColor Green
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

# Check Python
if (Test-Command "python") {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "Python not found. Please install Python 3.8+" -ForegroundColor Red
    Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor Cyan
    exit 1
}

# Check Node.js
if (Test-Command "node") {
    $nodeVersion = node --version
    Write-Host "Node.js found: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "Node.js not found. Please install Node.js 16+" -ForegroundColor Red
    Write-Host "   Download from: https://nodejs.org/" -ForegroundColor Cyan
    exit 1
}

# Check npm
if (Test-Command "npm") {
    $npmVersion = npm --version
    Write-Host "npm found: v$npmVersion" -ForegroundColor Green
} else {
    Write-Host "npm not found. Please install npm" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Checking and installing dependencies..." -ForegroundColor Yellow

# Check and install Python dependencies
Write-Host "Checking Python dependencies..." -ForegroundColor Cyan

# Check PyJWT
if (Test-PythonPackage "jwt") {
    Write-Host "PyJWT already installed" -ForegroundColor Green
} else {
    Write-Host "Installing PyJWT..." -ForegroundColor Yellow
    try {
        pip install PyJWT
        Write-Host "PyJWT installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to install PyJWT" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Check and install Node.js dependencies
Write-Host "Checking Node.js dependencies..." -ForegroundColor Cyan

# Check if node_modules exists
if (Test-Path "frontend/node_modules") {
    Write-Host "Node.js dependencies already installed" -ForegroundColor Green
} else {
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
    try {
        Set-Location frontend
        npm install
        Set-Location ..
        Write-Host "Node.js dependencies installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to install Node.js dependencies" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Starting servers..." -ForegroundColor Yellow

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

# Start backend server if not running
if (-not $backendRunning) {
    Write-Host "Starting backend server..." -ForegroundColor Cyan
    try {
        $backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; python simple_server.py" -WindowStyle Normal -PassThru
        Write-Host "Backend server started on http://localhost:8000" -ForegroundColor Green
    } catch {
        Write-Host "Failed to start backend server" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Wait a moment for backend to start
if (-not $backendRunning) {
    Write-Host "Waiting for backend to initialize..." -ForegroundColor Gray
    Start-Sleep -Seconds 3
}

# Start frontend server if not running
if (-not $frontendRunning) {
    Write-Host "Starting frontend server..." -ForegroundColor Cyan
    try {
        $frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev" -WindowStyle Normal -PassThru
        Write-Host "Frontend server started on http://localhost:3000" -ForegroundColor Green
    } catch {
        Write-Host "Failed to start frontend server" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "ScaleUp-Nvidia Platform is running!" -ForegroundColor Green
Write-Host ""
Write-Host "Access your application:" -ForegroundColor White
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Admin Login:" -ForegroundColor White
Write-Host "   Email: Admin@gmail.com" -ForegroundColor Cyan
Write-Host "   Password: Admin" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Documentation:" -ForegroundColor White
Write-Host "   Root: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Health: http://localhost:8000/health (Admin only)" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop the servers, type 'stop'..." -ForegroundColor Yellow
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
Write-Host "Stopping servers..." -ForegroundColor Yellow

# Close the PowerShell windows we opened
if ($backendProcess) {
    try {
        $backendProcess | Stop-Process -Force
        Write-Host "Backend PowerShell window closed" -ForegroundColor Green
    } catch {
        Write-Host "Could not close backend PowerShell window" -ForegroundColor Yellow
    }
}

if ($frontendProcess) {
    try {
        $frontendProcess | Stop-Process -Force
        Write-Host "Frontend PowerShell window closed" -ForegroundColor Green
    } catch {
        Write-Host "Could not close frontend PowerShell window" -ForegroundColor Yellow
    }
}

# Also stop any remaining Python and Node.js processes as backup
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    $pythonProcesses | Stop-Process -Force
    Write-Host "Python processes stopped" -ForegroundColor Green
}

$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    $nodeProcesses | Stop-Process -Force
    Write-Host "Node.js processes stopped" -ForegroundColor Green
}

Write-Host ""
Write-Host "ScaleUp-Nvidia Platform stopped. Goodbye!" -ForegroundColor Green
