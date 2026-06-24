#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm packaging/pdf_presenter.spec
# Result: dist/PDF Presenter.app  +  zip for distribution
cd dist && zip -qr "PDF-Presenter-macOS.zip" "PDF Presenter.app"
echo "Built: dist/PDF Presenter.app and dist/PDF-Presenter-macOS.zip"
