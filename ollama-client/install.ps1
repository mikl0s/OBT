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

# Function to download file from GitHub
function Get-GitHubFile {
    param (
        [string]$FileName,
        [string]$TargetPath,
        [switch]$Force
    )
    
    Write-ColorOutput "Blue" "Downloading $FileName from GitHub..."
    $url = "https://raw.githubusercontent.com/mikl0s/OBT/main/ollama-client/$FileName"
    try {
        $webClient = New-Object System.Net.WebClient
        $webClient.Headers.Add("Cache-Control", "no-cache")
        $webClient.Headers.Add("Pragma", "no-cache")
        if ($Force -and (Test-Path $TargetPath)) {
            Remove-Item $TargetPath
        }
        $webClient.DownloadFile($url, $TargetPath)
        if (-not (Test-Path $TargetPath)) {
            throw "Failed to download $FileName"
        }
    }
    catch {
        Write-ColorOutput "Red" "Error downloading $FileName from GitHub: $_"
        exit 1
    }
}

# Get the current directory
$installPath = $PWD.Path
Write-ColorOutput "Green" "Installing in current directory: $installPath"

# Download required files from GitHub
Get-GitHubFile -FileName ".env.example" -TargetPath (Join-Path $installPath ".env.example")
Get-GitHubFile -FileName "requirements.txt" -TargetPath (Join-Path $installPath "requirements.txt")
Get-GitHubFile -FileName "start.ps1" -TargetPath (Join-Path $installPath "start.ps1")
Get-GitHubFile -FileName "main.py" -TargetPath (Join-Path $installPath "main.py")

# Check Python installation
Write-ColorOutput "Blue" "Checking Python installation..."
if (-not (Test-Command "python")) {
    Write-ColorOutput "Red" "Python is not installed. Please install Python 3.10 or later."
    exit 1
}

# Check Ollama installation
Write-ColorOutput "Blue" "Checking Ollama installation..."
if (-not (Test-Command "ollama")) {
    Write-ColorOutput "Yellow" "Warning: Ollama is not installed or not in PATH."
}

# Set up Python virtual environment
Write-ColorOutput "Blue" "Setting up Python virtual environment..."
$venvPath = Join-Path $installPath "venv"

# Remove existing venv if it exists
if (Test-Path $venvPath) {
    Remove-Item -Recurse -Force $venvPath
}

# Create new venv
python -m venv $venvPath

# Activate virtual environment
Write-ColorOutput "Blue" "Activating virtual environment..."
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
. $activateScript

# Install Python dependencies
Write-ColorOutput "Blue" "Installing Python dependencies..."
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$venvPip = Join-Path $venvPath "Scripts\pip.exe"

# Upgrade pip first
Write-ColorOutput "Blue" "Upgrading pip to latest version..."
& $venvPython -m pip install --upgrade pip==25.0.0

# Install dependencies from requirements.txt
Write-ColorOutput "Blue" "Installing dependencies from requirements.txt..."
& $venvPip install -r (Join-Path $installPath "requirements.txt")

# Explicitly install psutil
Write-ColorOutput "Blue" "Installing psutil..."
& $venvPip install psutil

# Set up .env file
Write-ColorOutput "Blue" "Setting up .env file..."
$envFile = Join-Path $installPath ".env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $installPath ".env.example") $envFile
}

# Create desktop shortcut
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\OBT Client.lnk")
$Shortcut.TargetPath = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
$Shortcut.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$installPath\start.ps1`""
$Shortcut.WorkingDirectory = $installPath
$Shortcut.Save()

Write-ColorOutput "Green" "Installation complete!"
Write-ColorOutput "Yellow" "You can:"
Write-ColorOutput "Yellow" "1. Run the client using the desktop shortcut"
Write-ColorOutput "Yellow" "2. Run ./start.ps1 from PowerShell"
Write-ColorOutput "Yellow" "3. Edit .env file to configure the connection to OBT server"
