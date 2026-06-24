# Run in PowerShell on Windows.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm packaging\pdf_presenter.spec
Compress-Archive -Path "dist\PDF Presenter\*" -DestinationPath "dist\PDF-Presenter-Windows.zip" -Force
Write-Host "Built: dist\PDF Presenter\PDF Presenter.exe + dist\PDF-Presenter-Windows.zip"
