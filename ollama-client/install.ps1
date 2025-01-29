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

# Function to download file from GitHub if it doesn't exist
function Get-GitHubFile {
    param (
        [string]$FileName,
        [string]$TargetPath
    )
    
    if (-not (Test-Path $TargetPath)) {
        Write-ColorOutput "Blue" "Downloading $FileName from GitHub..."
        $url = "https://raw.githubusercontent.com/mikl0s/OBT/main/ollama-client/$FileName"
        try {
            Invoke-WebRequest -Uri $url -OutFile $TargetPath
            if (-not (Test-Path $TargetPath)) {
                throw "Failed to download $FileName"
            }
        }
        catch {
            Write-ColorOutput "Red" "Error downloading $FileName from GitHub: $_"
            exit 1
        }
    }
}

# Get the script directory
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path -Parent $scriptPath
if (-not $scriptDir) {
    $scriptDir = $PWD
}

# Create directory if it doesn't exist
if (-not (Test-Path $scriptDir)) {
    New-Item -ItemType Directory -Path $scriptDir | Out-Null
}

# Ensure we have all required files
$requiredFiles = @(
    ".env.example",
    "requirements.txt",
    "start.ps1",
    "main.py"
)

foreach ($file in $requiredFiles) {
    Get-GitHubFile -FileName $file -TargetPath (Join-Path $scriptDir $file)
}

# Create .env file if it doesn't exist
Write-ColorOutput "Blue" "Setting up .env file..."
$envExample = Join-Path $scriptDir ".env.example"
$envTarget = Join-Path $scriptDir ".env"
if (-not (Test-Path $envTarget)) {
    Copy-Item $envExample $envTarget
    Write-ColorOutput "Yellow" "Please edit .env file with your OBT server URL"
}

# Install Python requirements
Write-ColorOutput "Blue" "Installing Python dependencies..."
$requirementsPath = Join-Path $scriptDir "requirements.txt"
pip install -r $requirementsPath

# Create startup shortcut
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\OBT Ollama Client.lnk")
$Shortcut.TargetPath = "powershell.exe"
$startScript = Join-Path $scriptDir "start.ps1"
$Shortcut.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$startScript`""
$Shortcut.WorkingDirectory = $scriptDir
$Shortcut.Save()

Write-ColorOutput "Green" "Installation complete!"
Write-ColorOutput "Yellow" "You can:"
Write-ColorOutput "Yellow" "1. Run the client using the desktop shortcut"
Write-ColorOutput "Yellow" "2. Run ./start.ps1 from PowerShell"
Write-ColorOutput "Yellow" "3. Edit .env file to configure the connection to OBT server"
