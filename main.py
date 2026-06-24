"""
PDF Presenter — main entry point.

Run:
    pip install -r requirements.txt
    python main.py [chemin/vers/fichier.pdf]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QStandardPaths
from PySide6.QtGui import QGuiApplication, QKeyEvent, QIcon
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import QByteArray, QSize

from pdf_document import PdfDocument
from presenter_window import PresenterWindow, LOGO_SVG
from public_window import PublicWindow


def _make_icon_from_svg(svg_bytes: bytes, size: int = 64) -> QIcon:
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

def _app_icon() -> QIcon:
    """Charge logo.png/jpg si présent, sinon utilise le SVG intégré."""
    from presenter_window import _logo_path
    path = _logo_path()
    if path:
        icon = QIcon(path)
        if not icon.isNull():
            return icon
    return _make_icon_from_svg(LOGO_SVG, 64)


class Controller:
    def __init__(self, app: QApplication):
        self.app = app
        self.doc: PdfDocument | None = None
        self.index: int = 0
        self.total: int = 0

        self.timer_paused = False
        self._timer_start = time.monotonic()
        self._timer_accum = 0.0

        self.presenter = PresenterWindow(self)
        self.public = PublicWindow(self)

        self._redraw_timer = QTimer()
        self._redraw_timer.setSingleShot(True)
        self._redraw_timer.setInterval(40)
        self._redraw_timer.timeout.connect(self.redraw)

        self._recents: list[str] = []
        self._load_recents()
        self.presenter.show_welcome(self._recents)

    # ----- recent files -----
    def _recents_path(self) -> Path:
        base = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        d = Path(base) if base else Path.home() / ".config" / "pdf-presenter"
        d.mkdir(parents=True, exist_ok=True)
        return d / "recents.json"

    def _load_recents(self):
        try:
            data = json.loads(self._recents_path().read_text("utf-8"))
            self._recents = [p for p in data if isinstance(p, str) and Path(p).exists()]
        except Exception:
            self._recents = []

    def _save_recents(self):
        try:
            self._recents_path().write_text(json.dumps(self._recents), "utf-8")
        except Exception:
            pass

    def _push_recent(self, path: str):
        path = str(Path(path).resolve())
        self._recents = [p for p in self._recents if p != path]
        self._recents.insert(0, path)
        self._recents = self._recents[:8]
        self._save_recents()

    # ----- file open -----
    def open(self, path: str) -> bool:
        try:
            doc = PdfDocument(path)
        except Exception as e:
            QMessageBox.critical(self.presenter, "Erreur",
                                 f"Impossible d'ouvrir le PDF :\n{e}")
            return False
        if self.doc is not None:
            self.doc.close()
        self.doc = doc
        self.total = doc.page_count
        self.index = 0
        self.reset_timer()
        self._push_recent(path)
        self.presenter.setWindowTitle(f"Mode Présentateur — {Path(path).name}")
        self.presenter.sync_mode_selector()
        self.presenter.show_presenter()
        self.redraw()
        return True

    def go_home(self):
        self.presenter.show_welcome(self._recents)

    def set_mode(self, mode: str):
        if self.doc is None:
            return
        self.doc.set_mode(mode)
        self.total = self.doc.page_count
        if self.index >= self.total:
            self.index = max(0, self.total - 1)
        self.redraw()

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self.presenter, "Ouvrir un PDF", "", "PDF (*.pdf)")
        if path:
            self.open(path)

    # ----- navigation -----
    def goto(self, i: int):
        if self.doc is None: return
        i = max(0, min(self.total - 1, i))
        if i != self.index:
            self.index = i
            self.redraw()

    def next_slide(self): self.goto(self.index + 1)
    def prev_slide(self): self.goto(self.index - 1)

    # ----- rendering -----
    def request_redraw(self):
        self._redraw_timer.start()

    def redraw(self):
        if self.doc is None:
            self.presenter.set_slides(None, None, None)
            self.presenter.set_counter(0, 0)
            self.public.set_slide(None)
            return
        cv   = self.presenter.current_view
        nv   = self.presenter.next_view
        notv = self.presenter.notes_view
        dpr  = self.presenter.devicePixelRatioF()
        cur = self.doc.render_slide(self.index, cv.width(), cv.height(), dpr)
        nxt = (self.doc.render_slide(self.index + 1, nv.width(), nv.height(), dpr)
               if self.index + 1 < self.total else None)
        nts = self.doc.render_notes(self.index, notv.width(), notv.height(), dpr)
        self.presenter.set_slides(cur, nxt, nts)
        self.presenter.set_counter(self.index, self.total)

        pub_dpr = self.public.devicePixelRatioF()
        pub = self.doc.render_slide(self.index, self.public.width(), self.public.height(), pub_dpr)
        self.public.set_slide(pub)

    def render_slide_for(self, w: int, h: int, dpr: float):
        if self.doc is None: return None
        return self.doc.render_slide(self.index, w, h, dpr)

    # ----- timer -----
    def reset_timer(self):
        self._timer_start = time.monotonic()
        self._timer_accum = 0.0
        self.timer_paused = False

    def toggle_timer(self):
        if self.timer_paused:
            self._timer_start = time.monotonic()
            self.timer_paused = False
        else:
            self._timer_accum += time.monotonic() - self._timer_start
            self.timer_paused = True

    def timer_string(self) -> str:
        elapsed = self._timer_accum
        if not self.timer_paused:
            elapsed += time.monotonic() - self._timer_start
        s = int(elapsed)
        h, rem = divmod(s, 3600); m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    # ----- fullscreen -----
    def toggle_public_fullscreen(self):
        if self.public.isFullScreen():
            self.public.showNormal()
        else:
            self.public.showFullScreen()

    # ----- keyboard -----
    def handle_key(self, ev: QKeyEvent):
        k = ev.key()
        if k in (Qt.Key_Right, Qt.Key_Space, Qt.Key_PageDown):
            self.next_slide()
        elif k in (Qt.Key_Left, Qt.Key_PageUp, Qt.Key_Backspace):
            self.prev_slide()
        elif k == Qt.Key_Home:
            self.goto(0)
        elif k == Qt.Key_End:
            self.goto(self.total - 1)
        elif k == Qt.Key_P:
            self.toggle_timer()
        elif k == Qt.Key_R:
            self.reset_timer()
        elif k == Qt.Key_F:
            self.toggle_public_fullscreen()
        elif k == Qt.Key_Escape:
            if self.public.isFullScreen():
                self.public.showNormal()
        elif k in (Qt.Key_Return, Qt.Key_Enter):
            self.presenter.ask_goto()
        elif k == Qt.Key_O:
            self.open_file_dialog()
        elif k == Qt.Key_Q:
            self.quit_all()

    def quit_all(self):
        if self.doc is not None:
            self.doc.close()
        self.app.quit()


def place_windows(controller: Controller):
    screens = QGuiApplication.screens()
    if len(screens) >= 2:
        primary = screens[0].geometry()
        second  = screens[1].geometry()
        controller.presenter.move(primary.x() + 40, primary.y() + 40)
        controller.public.move(second.x(), second.y())
        controller.public.resize(second.width(), second.height())
        controller.public.showFullScreen()
    else:
        g = screens[0].geometry()
        controller.public.move(g.x() + g.width() // 2, g.y() + 60)
        controller.public.resize(900, 560)
    controller.public.show()
    controller.presenter.show()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Presenter")
    app.setApplicationDisplayName("PDF Presenter")

    # Icône application : logo.png/jpg si présent, sinon SVG intégré
    try:
        app.setWindowIcon(_app_icon())
    except Exception:
        pass

    controller = Controller(app)
    place_windows(controller)

    if len(sys.argv) > 1:
        controller.open(sys.argv[1])

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
