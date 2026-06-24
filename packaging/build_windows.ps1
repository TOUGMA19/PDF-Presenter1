$ErrorActionPreference = "Stop"

Write-Host "Building PDF Presenter..."

python -m PyInstaller `
 --clean `
 --noconfirm `
 --windowed `
 --onedir `
 --icon logo.png `
 --name "PDF Presenter" `
 --collect-all PySide6 `
 --hidden-import PySide6.QtCore `
 --hidden-import PySide6.QtWidgets `
 main.py


Write-Host "Installing Inno Setup..."

choco install innosetup -y


Write-Host "Creating installer..."

iscc packaging/installer.iss


Write-Host "Build finished"
