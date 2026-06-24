# PDF Presenter (Beamer + Zoom)

Lecteur PDF en mode présentateur, conçu pour les PDF LaTeX Beamer générés avec
`\setbeameroption{show notes on second screen=right}` (notes côte-à-côte sur
la même page) — mais fonctionne aussi avec n'importe quel PDF standard.

**Pas de parsing de texte.** Le programme rend la page comme une image et,
si une mise en page « slide + notes » est détectée, il découpe visuellement :

- la **fenêtre Public** n'affiche QUE la moitié slide (zéro risque de fuite des notes) ;
- la **fenêtre Présentateur** affiche la slide, la slide suivante, et les notes (image de la moitié notes).

## Nouveautés v3 — Page d'accueil

- **Logo SVG** intégré (icône d'application + badge dans l'en-tête)
- **Hero animé** : fond dégradé ambiant animé
- **Glisser-déposer** : déposez un PDF directement sur la page d'accueil
- **Design refondu** : palette sombre raffinée, typographie plus claire, cartes avec bordures subtiles
- **Liste des récents** améliorée : nom du fichier + chemin, sélection visuelle

## Installation

```bash
pip install -r requirements.txt
python main.py
```

Au démarrage, choisissez votre PDF. La fenêtre Présentateur s'ouvre sur l'écran
principal, la fenêtre Public s'ouvre en plein écran sur le second écran si
disponible (sinon en fenêtré — déplacez-la sur le bon écran puis F pour plein écran).

**Dans Zoom : partagez UNIQUEMENT la fenêtre « Public ».**

## Raccourcis (actifs dans les deux fenêtres)

| Touche | Action |
|---|---|
| → / Espace / PgDn | slide suivante |
| ← / PgUp | slide précédente |
| Home / End | première / dernière slide |
| P | pause/reprise du chrono |
| R | reset chrono |
| F | plein écran (fenêtre Public) |
| Esc | quitter plein écran |
| Entrée | aller à une slide (numéro) |
| O | ouvrir un autre PDF |
| Q | quitter |

## Détection automatique de la mise en page

Ratio largeur/hauteur de la page :

- `> 2.2` → split horizontal (slide à gauche, notes à droite — Beamer `show notes on second screen=right`)
- `< 0.9` → split vertical (slide en haut, notes en bas)
- sinon → page normale (pas de notes)

## Build .app / .exe

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "PDFPresenter" main.py
```

## Structure

```
main.py
pdf_document.py
presenter_window.py
public_window.py
requirements.txt
```

---

## Packaging desktop (macOS / Windows)
Voir `packaging/README_PACKAGING.md`. Un workflow GitHub Actions construit
automatiquement les binaires macOS et Windows à chaque tag `v*`.

## Android
Non supporté par cette base de code PySide6 — voir la note dans
`packaging/README_PACKAGING.md`.
