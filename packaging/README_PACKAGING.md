# Packaging PDF Presenter

## Builds automatiques via GitHub Actions (recommandé)

À chaque tag `v*` (ex. `git tag v3.1 && git push --tags`), le workflow
`.github/workflows/build.yml` :

1. compile le `.app` macOS **et** le `.exe` Windows,
2. **signe** le `.app` avec votre Developer ID (hardened runtime + entitlements),
3. **notarise** auprès d'Apple puis **staple** le ticket dans le bundle,
4. publie une **Release GitHub** avec les deux ZIP en pièces jointes.

Les ZIP sont aussi disponibles dans l'onglet **Actions** (artefacts).

### Secrets GitHub à configurer

Settings → Secrets and variables → Actions → *New repository secret* :

| Secret | Contenu |
|---|---|
| `MACOS_CERTIFICATE` | Votre certificat *Developer ID Application* exporté en `.p12` puis encodé : `base64 -i cert.p12 \| pbcopy` |
| `MACOS_CERTIFICATE_PWD` | Le mot de passe du `.p12` |
| `MACOS_KEYCHAIN_PWD` | Mot de passe arbitraire pour le keychain temporaire du runner |
| `MACOS_SIGN_IDENTITY` | Identité exacte, ex. `Developer ID Application: Jean Dupont (ABCDE12345)` |
| `MACOS_TEAM_ID` | Votre Team ID Apple (10 caractères) |
| `APPLE_ID` | Votre identifiant Apple Developer (email) |
| `APPLE_APP_SPECIFIC_PASSWORD` | Mot de passe spécifique app créé sur https://appleid.apple.com (Sécurité → *App-Specific Passwords*) |

> Sans ces secrets, le workflow continue de produire un `.app` non signé
> (utilisable localement, mais bloqué par Gatekeeper chez vos utilisateurs).
> Avec les secrets, le `.app` est livré signé + notarisé : double-clic
> direct sans avertissement "développeur non identifié".

### Comment exporter le certificat `.p12`

1. Sur https://developer.apple.com/account/resources/certificates → créez un
   certificat **Developer ID Application** (nécessite un compte Apple
   Developer payant, 99 €/an).
2. Téléchargez le `.cer`, double-cliquez pour l'ajouter au *Trousseau d'accès*.
3. Dans *Trousseau*, clic droit sur le certificat → **Exporter** → format
   `.p12`, donnez un mot de passe → c'est ce fichier qu'on encode en base64.

## Builds locaux

### macOS
```bash
bash packaging/build_macos.sh
```
Résultat : `dist/PDF Presenter.app` + `dist/PDF-Presenter-macOS.zip`.

Signature + notarisation manuelle :
```bash
codesign --force --deep --timestamp --options runtime \
  --entitlements packaging/entitlements.plist \
  --sign "Developer ID Application: <Nom> (<TEAMID>)" \
  "dist/PDF Presenter.app"
ditto -c -k --sequesterRsrc --keepParent "dist/PDF Presenter.app" dist/app.zip
xcrun notarytool submit dist/app.zip --apple-id <…> --team-id <…> \
  --password <app-specific-password> --wait
xcrun stapler staple "dist/PDF Presenter.app"
```

### Windows
```powershell
packaging\build_windows.ps1
```
Résultat : `dist\PDF Presenter\PDF Presenter.exe` + `dist\PDF-Presenter-Windows.zip`.

## Android — non supporté par cette base de code
PySide6 (Qt for Python) ne fournit pas de chemin officiel de packaging
Android. Options : réécrire l'UI en **Kivy** + Buildozer, en **Toga**
via BeeWare/Briefcase, ou exposer une **version web** (Flask/FastAPI +
PDF.js) installable en PWA.

## Icônes (optionnel)
Posez `logo.icns` (macOS), `logo.ico` (Windows) ou `logo.png` à la racine
du projet — le spec PyInstaller les détectera automatiquement.
