$ErrorActionPreference = "Stop"

Write-Host "Setting up Python Environment (using 'py' launcher)..."
if (-not (Test-Path "venv")) {
    py -m venv venv
    Write-Host "Virtual environment created."
} else {
    Write-Host "Virtual environment already exists."
}

Write-Host "Installing dependencies..."
.\venv\Scripts\python -m pip install -r requirements.txt

Write-Host "`nSetup Complete!"
Write-Host "To run the API:"
Write-Host "  .\venv\Scripts\python main.py"
Write-Host "To run the Monitor:"
Write-Host "  .\venv\Scripts\python monitor.py"
