"""
Presenter window — current slide, next slide, notes, timer, controls.
"""
from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import (
    QPainter, QColor, QPixmap, QFont, QPainterPath,
    QLinearGradient, QRadialGradient, QPen, QBrush,
)
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QFrame,
    QInputDialog, QFileDialog, QSizePolicy, QComboBox, QStackedWidget,
    QListWidget, QListWidgetItem, QGraphicsDropShadowEffect,
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import QByteArray


# ─── Design tokens ────────────────────────────────────────────────────────────
DARK_BG   = "#0f1117"
PANEL_BG  = "#1a1d27"
CARD_BG   = "#1e2130"
ACCENT    = "#4e8cff"
ACCENT2   = "#7c5cfc"
SUCCESS   = "#34d399"
TEXT      = "#eef0f8"
MUTED     = "#6b7280"
BORDER    = "#2a2d3e"
HOVER_BG  = "#252840"

STYLE = f"""
QWidget {{
    background: {DARK_BG};
    color: {TEXT};
    font-family: -apple-system, "Inter", "Segoe UI", sans-serif;
}}
QFrame#panel {{
    background: {PANEL_BG};
    border-radius: 12px;
    border: 1px solid {BORDER};
}}
QLabel#title {{
    color: {MUTED};
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-weight: 600;
}}
QLabel#timer {{
    color: {TEXT};
    font-size: 30px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    letter-spacing: -1px;
}}
QLabel#counter {{
    color: {TEXT};
    font-size: 16px;
    font-weight: 500;
}}
QPushButton {{
    background: {PANEL_BG};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{ background: {HOVER_BG}; border-color: #3a3f5c; }}
QPushButton#accent {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT}, stop:1 {ACCENT2});
    border: none;
    color: white;
    font-weight: 700;
}}
QPushButton#accent:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6aa0ff, stop:1 #9474ff);
}}
QComboBox {{
    background: {PANEL_BG};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 13px;
    min-width: 200px;
}}
QComboBox QAbstractItemView {{
    background: {PANEL_BG};
    color: {TEXT};
    selection-background-color: {ACCENT};
    border: 1px solid {BORDER};
}}

/* ── Welcome page ── */
QLabel#welcomeSection {{
    color: {MUTED};
    font-size: 11px;
    letter-spacing: 2px;
    font-weight: 700;
    text-transform: uppercase;
}}
QPushButton#welcomeOpen {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT}, stop:1 {ACCENT2});
    color: white;
    border: none;
    font-size: 15px;
    font-weight: 700;
    padding: 14px 40px;
    border-radius: 12px;
    letter-spacing: 0.3px;
}}
QPushButton#welcomeOpen:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6aa0ff, stop:1 #9474ff);
}}
QListWidget#recents {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 4px;
    font-size: 13px;
    outline: none;
}}
QListWidget#recents::item {{
    padding: 10px 14px;
    border-radius: 8px;
    border: 1px solid transparent;
}}
QListWidget#recents::item:hover {{
    background: {HOVER_BG};
    border-color: {BORDER};
}}
QListWidget#recents::item:selected {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(78,140,255,0.25), stop:1 rgba(124,92,252,0.25));
    color: white;
    border-color: rgba(78,140,255,0.4);
}}
QFrame#hintCard {{
    background: {CARD_BG};
    border-radius: 12px;
    border: 1px solid {BORDER};
}}
QLabel#hintText {{
    color: {MUTED};
    font-size: 13px;
}}
QLabel#hintKey {{
    color: {TEXT};
    background: #2a2d3e;
    padding: 3px 9px;
    border-radius: 5px;
    font-family: "SF Mono", "Fira Code", "Consolas", monospace;
    font-size: 11px;
    font-weight: 600;
    border: 1px solid {BORDER};
}}
"""


# ─── Custom logo path (même dossier que ce fichier) ──────────────────────────
import os as _os

def _logo_path() -> str | None:
    """Retourne le chemin du logo personnalisé s'il existe, sinon None."""
    here = _os.path.dirname(_os.path.abspath(__file__))
    for name in ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp"):
        p = _os.path.join(here, name)
        if _os.path.isfile(p):
            return p
    return None

def _load_custom_logo(size: int) -> "QPixmap | None":
    path = _logo_path()
    if path is None:
        return None
    pm = QPixmap(path)
    if pm.isNull():
        return None
    return pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


# ─── SVG Logo (fallback) ──────────────────────────────────────────────────────
LOGO_SVG = b"""<svg width="52" height="52" viewBox="0 0 52 52"
     xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#4e8cff"/>
      <stop offset="100%" stop-color="#7c5cfc"/>
    </linearGradient>
    <linearGradient id="arrow" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="1"/>
      <stop offset="100%" stop-color="#c4d8ff" stop-opacity="0.9"/>
    </linearGradient>
  </defs>
  <!-- Rounded square background -->
  <rect width="52" height="52" rx="13" fill="url(#bg)"/>
  <!-- Film / slide frame lines -->
  <rect x="9" y="14" width="34" height="24" rx="3"
        fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/>
  <!-- Play triangle -->
  <path d="M21 20 L21 32 L34 26 Z" fill="url(#arrow)"/>
  <!-- Dot indicators (slide count) -->
  <circle cx="17" cy="42" r="2" fill="rgba(255,255,255,0.55)"/>
  <circle cx="26" cy="42" r="2" fill="rgba(255,255,255,0.9)"/>
  <circle cx="35" cy="42" r="2" fill="rgba(255,255,255,0.35)"/>
</svg>"""


class LogoBadge(QWidget):
    """Glass tile that contains the app logo (custom file or built-in SVG)."""
    def __init__(self, size: int = 84):
        super().__init__()
        self._size = size
        self._pad = max(12, size // 7)
        total = size + self._pad * 2
        self.setFixedSize(total, total)

        # Inner logo
        inner_size = size
        custom_pm = _load_custom_logo(inner_size)
        if custom_pm is not None:
            self._inner = QLabel(self)
            self._inner.setPixmap(custom_pm)
            self._inner.setAlignment(Qt.AlignCenter)
        else:
            self._inner = QSvgWidget(self)
            self._inner.load(QByteArray(LOGO_SVG))
        self._inner.setFixedSize(inner_size, inner_size)
        self._inner.move(self._pad, self._pad)
        self._inner.setStyleSheet("background: transparent;")

        # Outer glow on the tile itself
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(40)
        glow.setOffset(0, 10)
        glow.setColor(QColor(78, 140, 255, 160))
        self.setGraphicsEffect(glow)

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)
        radius = max(14, self._size // 4)

        # Gradient tile background
        bg = QLinearGradient(0, 0, r.width(), r.height())
        bg.setColorAt(0.0, QColor(78, 140, 255, 235))
        bg.setColorAt(1.0, QColor(124, 92, 252, 235))
        path = QPainterPath()
        path.addRoundedRect(r, radius, radius)
        p.fillPath(path, QBrush(bg))

        # Inner top highlight
        hi = QLinearGradient(0, r.top(), 0, r.top() + r.height() * 0.55)
        hi.setColorAt(0.0, QColor(255, 255, 255, 70))
        hi.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillPath(path, QBrush(hi))

        # Outer hairline ring
        p.setPen(QPen(QColor(255, 255, 255, 55), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(r, radius, radius)

        # Inner darker ring for depth
        r2 = r.adjusted(3, 3, -3, -3)
        p.setPen(QPen(QColor(0, 0, 0, 40), 1))
        p.drawRoundedRect(r2, radius - 2, radius - 2)


class HeroHeader(QWidget):
    """Animated gradient hero area — twin orbs, soft grid, slow shine sweep."""
    def __init__(self):
        super().__init__()
        self.setFixedHeight(210)
        self._t = 0.0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(40)

    def _tick(self):
        self._t = (self._t + 0.6) % 360
        self.update()

    def paintEvent(self, _ev):
        import math
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()

        # Base
        p.fillRect(self.rect(), QColor(15, 17, 23))

        # Soft dot grid
        p.setPen(QColor(255, 255, 255, 10))
        step = 22
        for y in range(0, H, step):
            for x in range(0, W, step):
                p.drawPoint(x, y)

        # Twin orbital glows
        ox1 = int(math.sin(math.radians(self._t))       * 80)
        oy1 = int(math.cos(math.radians(self._t * 0.7)) * 18)
        g1 = QRadialGradient(W * 0.30 + ox1, H * 0.55 + oy1, 260)
        g1.setColorAt(0.0, QColor(78, 140, 255, 90))
        g1.setColorAt(0.5, QColor(78, 140, 255, 26))
        g1.setColorAt(1.0, QColor(15, 17, 23, 0))
        p.fillRect(self.rect(), g1)

        ox2 = int(math.cos(math.radians(self._t * 1.1)) * 70)
        oy2 = int(math.sin(math.radians(self._t * 0.9)) * 22)
        g2 = QRadialGradient(W * 0.78 + ox2, H * 0.45 + oy2, 240)
        g2.setColorAt(0.0, QColor(124, 92, 252, 80))
        g2.setColorAt(0.5, QColor(124, 92, 252, 22))
        g2.setColorAt(1.0, QColor(15, 17, 23, 0))
        p.fillRect(self.rect(), g2)

        # Slow diagonal shine sweep
        phase = (self._t / 360.0) * 2.0 - 0.5
        shine = QLinearGradient(W * (phase - 0.15), 0, W * (phase + 0.15), H)
        shine.setColorAt(0.0, QColor(255, 255, 255, 0))
        shine.setColorAt(0.5, QColor(255, 255, 255, 14))
        shine.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillRect(self.rect(), shine)

        # Bottom vignette into page bg
        vig = QLinearGradient(0, H - 60, 0, H)
        vig.setColorAt(0.0, QColor(15, 17, 23, 0))
        vig.setColorAt(1.0, QColor(15, 17, 23, 180))
        p.fillRect(self.rect(), vig)


class WelcomeView(QWidget):
    """Enhanced home screen with logo, gradient hero, and polished UI."""
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        # ── Hero header (animated background) ──
        hero = HeroHeader()

        logo = LogoBadge(84)

        app_name = QLabel("PDF Presenter")
        app_name.setStyleSheet(
            f"color: {TEXT}; font-size: 42px; font-weight: 800;"
            "letter-spacing: -1.4px; background: transparent;"
        )
        # subtle gradient text effect via drop shadow tint
        name_glow = QGraphicsDropShadowEffect()
        name_glow.setBlurRadius(28)
        name_glow.setOffset(0, 2)
        name_glow.setColor(QColor(78, 140, 255, 90))
        app_name.setGraphicsEffect(name_glow)

        version_pill = QLabel("v3")
        version_pill.setStyleSheet(
            f"color: {TEXT}; background: rgba(78,140,255,0.18);"
            "border: 1px solid rgba(78,140,255,0.45);"
            "border-radius: 999px; padding: 2px 10px;"
            "font-size: 11px; font-weight: 700; letter-spacing: 1px;"
        )

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.addWidget(app_name, 0, Qt.AlignVCenter)
        title_row.addWidget(version_pill, 0, Qt.AlignVCenter)
        title_row.addStretch()

        tagline = QLabel("Présentez vos diaporamas Beamer avec notes sur second écran")
        tagline.setStyleSheet(
            f"color: {MUTED}; font-size: 14px; background: transparent;"
        )
        tagline.setWordWrap(True)

        # status dot row
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {SUCCESS}; font-size: 12px; background: transparent;")
        status = QLabel("Prêt — glissez un PDF ou utilisez le bouton ci-dessous")
        status.setStyleSheet(
            f"color: {MUTED}; font-size: 12px; background: transparent;"
            "letter-spacing: 0.2px;"
        )
        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.addWidget(dot)
        status_row.addWidget(status)
        status_row.addStretch()

        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        name_col.setContentsMargins(0, 0, 0, 0)
        name_col.addLayout(title_row)
        name_col.addWidget(tagline)
        name_col.addSpacing(4)
        name_col.addLayout(status_row)

        hero_row = QHBoxLayout(hero)
        hero_row.setContentsMargins(44, 36, 44, 30)
        hero_row.setSpacing(0)
        hero_row.addWidget(logo, 0, Qt.AlignVCenter)
        hero_row.addSpacing(22)
        hero_row.addLayout(name_col, 1)

        # ── Open button ──
        btn_open = QPushButton("  Ouvrir un PDF…")
        btn_open.setObjectName("welcomeOpen")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setFixedHeight(50)
        btn_open.clicked.connect(self.controller.open_file_dialog)
        # drop-shadow on button
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(28)
        sh.setOffset(0, 6)
        sh.setColor(QColor(78, 140, 255, 90))
        btn_open.setGraphicsEffect(sh)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_open)
        btn_row.addStretch()

        drag_hint = QLabel("ou faites glisser un fichier PDF ici")
        drag_hint.setAlignment(Qt.AlignCenter)
        drag_hint.setStyleSheet(f"color: {MUTED}; font-size: 12px; background: transparent;")

        # ── Recent files ──
        recents_label = QLabel("RÉCENTS")
        recents_label.setObjectName("welcomeSection")

        self.recents_list = QListWidget()
        self.recents_list.setObjectName("recents")
        self.recents_list.setMaximumHeight(210)
        self.recents_list.setFocusPolicy(Qt.NoFocus)
        self.recents_list.itemActivated.connect(self._on_recent_activated)

        self.recents_empty = QLabel("Aucun fichier récent — ouvrez votre premier PDF ci-dessus.")
        self.recents_empty.setAlignment(Qt.AlignCenter)
        self.recents_empty.setStyleSheet(
            f"color: {MUTED}; font-size: 13px; padding: 24px; background: transparent;"
        )

        recents_box = QVBoxLayout()
        recents_box.setSpacing(8)
        recents_box.addWidget(recents_label)
        recents_box.addWidget(self.recents_list)
        recents_box.addWidget(self.recents_empty)

        # ── Keyboard hints card ──
        hint_card = QFrame()
        hint_card.setObjectName("hintCard")
        hint_lay = QVBoxLayout(hint_card)
        hint_lay.setContentsMargins(20, 16, 20, 18)
        hint_lay.setSpacing(10)

        hint_title = QLabel("RACCOURCIS CLAVIER")
        hint_title.setObjectName("welcomeSection")
        hint_lay.addWidget(hint_title)
        hint_lay.addSpacing(2)

        shortcuts = [
            ("← / →  ·  Espace", "Naviguer entre les diapositives"),
            ("Home / End",        "Première / dernière diapositive"),
            ("F",                 "Plein écran fenêtre public"),
            ("P",                 "Pause / reprise du chronomètre"),
            ("R",                 "Réinitialiser le chronomètre"),
            ("Entrée",            "Aller à une diapositive précise"),
            ("O",                 "Ouvrir un autre PDF"),
            ("Q",                 "Quitter"),
        ]
        grid = QVBoxLayout()
        grid.setSpacing(6)
        for keys, desc in shortcuts:
            row = QHBoxLayout()
            k = QLabel(keys)
            k.setObjectName("hintKey")
            k.setFixedWidth(190)
            d = QLabel(desc)
            d.setObjectName("hintText")
            row.addWidget(k)
            row.addSpacing(12)
            row.addWidget(d, 1)
            grid.addLayout(row)
        hint_lay.addLayout(grid)

        # ── Assemble center column ──
        col = QVBoxLayout()
        col.setSpacing(0)
        col.addLayout(btn_row)
        col.addSpacing(6)
        col.addWidget(drag_hint)
        col.addSpacing(28)
        col.addLayout(recents_box)
        col.addSpacing(20)
        col.addWidget(hint_card)


        inner = QWidget()
        inner.setLayout(col)
        inner.setMaximumWidth(640)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(40, 24, 40, 36)
        content_row.addStretch(1)
        content_row.addWidget(inner, 0)
        content_row.addStretch(1)

        content_widget = QWidget()
        content_widget.setLayout(content_row)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(hero)
        # thin gradient separator
        sep = _GradientSeparator()
        root.addWidget(sep)
        root.addWidget(content_widget, 1)

        # accept drag & drop
        self.setAcceptDrops(True)

    def dragEnterEvent(self, ev):
        if ev.mimeData().hasUrls():
            for url in ev.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    ev.acceptProposedAction()
                    return
        ev.ignore()

    def dropEvent(self, ev):
        for url in ev.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                self.controller.open(path)
                return

    def refresh_recents(self, recents: list[str]):
        from pathlib import Path
        self.recents_list.clear()
        for p in recents:
            name = Path(p).name
            parent = str(Path(p).parent)
            item = QListWidgetItem()
            item.setText(f"{name}\n{parent}")
            item.setData(Qt.UserRole, p)
            self.recents_list.addItem(item)
        has = len(recents) > 0
        self.recents_list.setVisible(has)
        self.recents_empty.setVisible(not has)

    def _on_recent_activated(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        if path:
            self.controller.open(path)


class _GradientSeparator(QWidget):
    """Thin line that fades from accent to transparent."""
    def __init__(self):
        super().__init__()
        self.setFixedHeight(2)

    def paintEvent(self, _ev):
        p = QPainter(self)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0,  QColor(78, 140, 255, 0))
        grad.setColorAt(0.3,  QColor(78, 140, 255, 200))
        grad.setColorAt(0.7,  QColor(124, 92, 252, 200))
        grad.setColorAt(1.0,  QColor(124, 92, 252, 0))
        p.fillRect(self.rect(), grad)


# ─── Slide view ───────────────────────────────────────────────────────────────

class SlideView(QLabel):
    """A QLabel that renders a pixmap centered, on black, scaled to fit."""
    def __init__(self, controller, kind: str):
        super().__init__()
        self.controller = controller
        self.kind = kind
        self.setMinimumSize(200, 120)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background:#000; border-radius:8px;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._pixmap = None

    def set_pixmap(self, pm: QPixmap | None):
        self._pixmap = pm
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0))
        if self._pixmap is None or self._pixmap.isNull():
            p.setPen(QColor(80, 85, 110))
            p.drawText(self.rect(), Qt.AlignCenter,
                       "—" if self.kind != "notes" else "(pas de notes)")
            return
        pm = self._pixmap
        w = int(pm.width() / pm.devicePixelRatio())
        h = int(pm.height() / pm.devicePixelRatio())
        x = (self.width() - w) // 2
        y = (self.height() - h) // 2
        p.drawPixmap(x, y, pm)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.controller.request_redraw()


# ─── Presenter Window ─────────────────────────────────────────────────────────

class PresenterWindow(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Mode Présentateur")
        self.setStyleSheet(STYLE)
        self.resize(1400, 850)

        # --- top bar ---
        self.counter = QLabel("1 / 1"); self.counter.setObjectName("counter")
        self.timer_label = QLabel("00:00"); self.timer_label.setObjectName("timer")

        btn_open  = QPushButton("Ouvrir…");       btn_open.clicked.connect(self.controller.open_file_dialog)
        btn_home  = QPushButton("⌂ Accueil");     btn_home.clicked.connect(self.controller.go_home)
        btn_goto  = QPushButton("Aller à…");      btn_goto.clicked.connect(self.ask_goto)
        btn_pause = QPushButton("Pause chrono");   btn_pause.clicked.connect(self.controller.toggle_timer)
        self.btn_pause = btn_pause
        btn_reset = QPushButton("Reset chrono");   btn_reset.clicked.connect(self.controller.reset_timer)
        btn_full  = QPushButton("Plein écran public"); btn_full.clicked.connect(self.controller.toggle_public_fullscreen)

        from pdf_document import PdfDocument
        self.mode_combo = QComboBox()
        for label, mode_id in PdfDocument.MANUAL_MODES:
            self.mode_combo.addItem(label, mode_id)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        top = QHBoxLayout()
        top.addWidget(self.counter); top.addStretch(1)
        top.addWidget(QLabel("Mode :")); top.addWidget(self.mode_combo)
        top.addSpacing(10)
        top.addWidget(btn_home); top.addWidget(btn_open); top.addWidget(btn_goto)
        top.addWidget(btn_pause); top.addWidget(btn_reset); top.addWidget(btn_full)
        top.addSpacing(20)
        top.addWidget(self.timer_label)

        # --- main grid ---
        self.current_view = SlideView(controller, "current")
        self.next_view    = SlideView(controller, "next")
        self.notes_view   = SlideView(controller, "notes")

        def panel(title: str, widget: QWidget) -> QFrame:
            f = QFrame(); f.setObjectName("panel")
            lay = QVBoxLayout(f)
            lay.setContentsMargins(10, 8, 10, 10); lay.setSpacing(6)
            lbl = QLabel(title.upper()); lbl.setObjectName("title")
            lay.addWidget(lbl); lay.addWidget(widget)
            return f

        left      = panel("Diapositive actuelle", self.current_view)
        right_top = panel("Suivante", self.next_view)
        right_bot = panel("Notes", self.notes_view)

        right_col = QVBoxLayout(); right_col.setSpacing(10)
        right_col.addWidget(right_top, 1); right_col.addWidget(right_bot, 1)

        main = QHBoxLayout(); main.setSpacing(10)
        main.addWidget(left, 2)
        rc = QWidget(); rc.setLayout(right_col); main.addWidget(rc, 1)

        # --- bottom ---
        btn_prev = QPushButton("◀  Précédente")
        btn_prev.clicked.connect(self.controller.prev_slide)
        btn_next = QPushButton("Suivante  ▶")
        btn_next.setObjectName("accent")
        btn_next.clicked.connect(self.controller.next_slide)
        bottom = QHBoxLayout()
        bottom.addWidget(btn_prev); bottom.addStretch(1); bottom.addWidget(btn_next)

        presenter_page = QWidget()
        pres_lay = QVBoxLayout(presenter_page)
        pres_lay.setContentsMargins(14, 12, 14, 12); pres_lay.setSpacing(10)
        pres_lay.addLayout(top)
        pres_lay.addLayout(main, 1)
        pres_lay.addLayout(bottom)

        # --- welcome / presenter stack ---
        self.welcome = WelcomeView(controller)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.welcome)      # 0
        self.stack.addWidget(presenter_page)    # 1

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(self.stack)

        self._tick = QTimer(self)
        self._tick.timeout.connect(self.refresh_timer)
        self._tick.start(500)

    # ── API used by controller ─────────────────────────────────────────────

    def set_slides(self, current_pm, next_pm, notes_pm):
        self.current_view.set_pixmap(current_pm)
        self.next_view.set_pixmap(next_pm)
        self.notes_view.set_pixmap(notes_pm)

    def set_counter(self, idx: int, total: int):
        self.counter.setText(f"{idx + 1} / {total}")

    def refresh_timer(self):
        self.timer_label.setText(self.controller.timer_string())
        self.btn_pause.setText(
            "Reprendre chrono" if self.controller.timer_paused else "Pause chrono"
        )

    def sync_mode_selector(self):
        doc = self.controller.doc
        if doc is None:
            return
        self.mode_combo.blockSignals(True)
        idx = self.mode_combo.findData(doc.mode)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        self.mode_combo.blockSignals(False)

    def _on_mode_changed(self, _i: int):
        mode = self.mode_combo.currentData()
        if mode is not None:
            self.controller.set_mode(mode)

    def show_welcome(self, recents: list[str]):
        self.welcome.refresh_recents(recents)
        self.stack.setCurrentIndex(0)
        self.setWindowTitle("PDF Presenter")

    def show_presenter(self):
        self.stack.setCurrentIndex(1)

    # ── Events ────────────────────────────────────────────────────────────

    def ask_goto(self):
        n, ok = QInputDialog.getInt(
            self, "Aller à la slide", "Numéro :",
            self.controller.index + 1, 1, self.controller.total
        )
        if ok:
            self.controller.goto(n - 1)

    def keyPressEvent(self, ev):
        self.controller.handle_key(ev)

    def closeEvent(self, ev):
        self.controller.quit_all()
        ev.accept()
