# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Please run this script as Administrator" -ForegroundColor Red
    exit 1
}

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

# Check Python installation
Write-ColorOutput "Blue" "Checking Python installation..."
if (-not (Test-Command python)) {
    Write-ColorOutput "Red" "Python is not installed. Please install Python 3.8 or later from https://www.python.org/"
    exit 1
}

# Check Python version
$pythonVersion = (python --version 2>&1).ToString().Split(" ")[1]
$versionParts = $pythonVersion.Split(".")
if ([int]$versionParts[0] -lt 3 -or ([int]$versionParts[0] -eq 3 -and [int]$versionParts[1] -lt 8)) {
    Write-ColorOutput "Red" "Python version must be 3.8 or later. Current version: $pythonVersion"
    exit 1
}

# Check if Ollama is installed
Write-ColorOutput "Blue" "Checking Ollama installation..."
if (-not (Test-Command ollama)) {
    Write-ColorOutput "Yellow" "Ollama is not installed. Installing Ollama..."
    
    # Download Ollama installer
    $installerUrl = "https://ollama.ai/download/ollama-windows.exe"
    $installerPath = "$env:TEMP\ollama-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
        Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait
        Remove-Item $installerPath
    }
    catch {
        Write-ColorOutput "Red" "Failed to install Ollama: $_"
        exit 1
    }
}

# Create virtual environment
Write-ColorOutput "Blue" "Setting up Python virtual environment..."
if (-not (Test-Path "venv")) {
    python -m venv venv
}

# Activate virtual environment
Write-ColorOutput "Blue" "Activating virtual environment..."
. .\venv\Scripts\Activate.ps1

# Install requirements
Write-ColorOutput "Blue" "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-ColorOutput "Blue" "Creating .env file..."
    Copy-Item ".env.example" ".env"
    Write-ColorOutput "Yellow" "Please edit .env file with your OBT server URL"
}

# Create startup shortcut
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\OBT Ollama Client.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$PWD\start.ps1`""
$Shortcut.WorkingDirectory = $PWD
$Shortcut.Save()

Write-ColorOutput "Green" "Installation complete!"
Write-ColorOutput "Yellow" "You can:"
Write-ColorOutput "Yellow" "1. Run the client using the desktop shortcut"
Write-ColorOutput "Yellow" "2. Run ./start.ps1 from PowerShell"
Write-ColorOutput "Yellow" "3. Edit .env file to configure the connection to OBT server"
