"""
Public window — what the audience sees in Zoom.
Renders ONLY the slide half. Notes are never reachable from here.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QWidget


class PublicWindow(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Présentation (à partager dans Zoom)")
        self.setStyleSheet("background:#000;")
        self.setAutoFillBackground(True)
        self._pixmap = None
        self.resize(1280, 720)

    def set_slide(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0))
        if self._pixmap is None or self._pixmap.isNull():
            return
        # Re-render at exact window size for crispness
        dpr = self.devicePixelRatioF()
        pm = self.controller.render_slide_for(self.width(), self.height(), dpr)
        if pm is None or pm.isNull():
            pm = self._pixmap
        w = int(pm.width() / pm.devicePixelRatio())
        h = int(pm.height() / pm.devicePixelRatio())
        x = (self.width() - w) // 2
        y = (self.height() - h) // 2
        p.drawPixmap(x, y, pm)

    def keyPressEvent(self, ev):
        self.controller.handle_key(ev)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.controller.request_redraw()
