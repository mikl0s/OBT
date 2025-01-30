# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Set console colors
$Host.UI.RawUI.ForegroundColor = "White"

# Create a function for colored output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Check if Ollama is installed
Write-ColorOutput "Blue" "Checking Ollama service..."
if (-not (Test-Command ollama)) {
    Write-ColorOutput "Red" "Ollama is not installed. Please run install.ps1 first"
    exit 1
}

# Check if Ollama service is running
$ollamaRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $ollamaRunning = $true
    }
}
catch {}

if (-not $ollamaRunning) {
    Write-ColorOutput "Blue" "Starting Ollama service..."
    Start-Process "ollama" -ArgumentList "serve" -NoNewWindow
    
    Write-ColorOutput "Blue" "Waiting for Ollama to be ready..."
    do {
        Start-Sleep -Seconds 1
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $ollamaRunning = $true
            }
        }
        catch {}
    } while (-not $ollamaRunning)
}

# Check Ollama service
Write-Host "Checking Ollama service..." -ForegroundColor Blue

# Get the current directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Blue
$venvPath = Join-Path $scriptPath "venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-Host "Virtual environment not found. Please run install.ps1 first." -ForegroundColor Red
    exit 1
}

# Activate the virtual environment
. $activateScript

# Start the client
Write-Host "Starting OBT Ollama client..." -ForegroundColor Green
$pythonPath = Join-Path $venvPath "Scripts\python.exe"
& $pythonPath main.py
