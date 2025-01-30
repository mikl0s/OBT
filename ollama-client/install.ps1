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
    finally {
        if ($webClient) {
            $webClient.Dispose()
        }
    }
}

# Use current directory
$installDir = $PWD.Path
Write-ColorOutput "Blue" "Installing in current directory: $installDir"

# Download all required files
$requiredFiles = @(
    ".env.example",
    "requirements.txt",
    "start.ps1",
    "main.py"
)

foreach ($file in $requiredFiles) {
    if ($file -eq ".env") {
        Get-GitHubFile -FileName $file -TargetPath (Join-Path $installDir $file)
    } else {
        Get-GitHubFile -FileName $file -TargetPath (Join-Path $installDir $file) -Force
    }
}

# Check Python installation
Write-ColorOutput "Blue" "Checking Python installation..."
if (-not (Test-Command "python")) {
    Write-ColorOutput "Yellow" "Python is not installed. Installing Python..."
    if (-not (Test-Command "choco")) {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    }
    choco install python -y
    refreshenv
}

# Check Ollama installation
Write-ColorOutput "Blue" "Checking Ollama installation..."
if (-not (Test-Command "ollama")) {
    Write-ColorOutput "Yellow" "Ollama is not installed. Installing Ollama..."
    $ollamaInstaller = Join-Path $env:TEMP "ollama-installer.exe"
    Invoke-WebRequest -Uri "https://ollama.ai/download/ollama-windows-amd64.exe" -OutFile $ollamaInstaller
    Start-Process -FilePath $ollamaInstaller -ArgumentList "/S" -Wait
    refreshenv
}

# Set up Python virtual environment
Write-ColorOutput "Blue" "Setting up Python virtual environment..."
python -m venv venv
if (-not (Test-Path "venv")) {
    Write-ColorOutput "Red" "Failed to create virtual environment"
    exit 1
}

# Activate virtual environment
Write-ColorOutput "Blue" "Activating virtual environment..."
. .\venv\Scripts\Activate.ps1

# Install Python dependencies
Write-ColorOutput "Blue" "Installing Python dependencies..."
$venvPip = Join-Path $PWD.Path "venv\Scripts\pip.exe"
& $venvPip install --upgrade pip
& $venvPip install -r (Join-Path $PWD.Path "requirements.txt")
& $venvPip install psutil

# Create .env file if it doesn't exist
Write-ColorOutput "Blue" "Setting up .env file..."
$envExample = Join-Path $installDir ".env.example"
$envTarget = Join-Path $installDir ".env"
if (-not (Test-Path $envTarget)) {
    Copy-Item $envExample $envTarget
    Write-ColorOutput "Yellow" "Please edit .env file with your OBT server URL"
}

# Create startup shortcut
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\OBT Ollama Client.lnk")
$Shortcut.TargetPath = "powershell.exe"
$startScript = Join-Path $installDir "start.ps1"
$Shortcut.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$startScript`""
$Shortcut.WorkingDirectory = "$installDir"
$Shortcut.Save()

Write-ColorOutput "Green" "Installation complete!"
Write-ColorOutput "Yellow" "You can:"
Write-ColorOutput "Yellow" "1. Run the client using the desktop shortcut"
Write-ColorOutput "Yellow" "2. Run ./start.ps1 from PowerShell"
Write-ColorOutput "Yellow" "3. Edit .env file to configure the connection to OBT server"
