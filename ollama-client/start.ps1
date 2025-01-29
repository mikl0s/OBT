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

# Activate virtual environment
Write-ColorOutput "Blue" "Activating virtual environment..."
. .\venv\Scripts\Activate.ps1

# Start the client
Write-ColorOutput "Blue" "Starting OBT Ollama client..."
python main.py
