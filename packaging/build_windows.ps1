Write-Host "Building PDF Presenter..."

python -m PyInstaller `
 --clean `
 --noconfirm `
 --windowed `
 --name "PDF Presenter" `
 --collect-all PySide6 `
 --hidden-import PySide6.QtCore `
 --hidden-import PySide6.QtWidgets `
 main.py


Compress-Archive `
 -Path "dist/PDF Presenter/*" `
 -DestinationPath "dist/PDF-Presenter-Windows.zip" `
 -Force


Write-Host "Build finished"
