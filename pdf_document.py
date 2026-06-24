"""
PDF document wrapper. No text parsing — pure image rendering.

Supported Beamer "notes" layouts:
- SPLIT_H : page wider than tall (ratio > 2.2) → slide on LEFT, notes on RIGHT
- SPLIT_V : page taller than wide (ratio < 0.9) → slide on TOP,  notes on BOTTOM
- INTERLEAVED : normal-aspect pages that alternate slide / notes / slide / notes …
                (BeamerAvecNote1 style — ``\\setbeameroption{show notes on second screen=...}``
                exported as one page per item)
- NORMAL : everything else — slide only, no notes

For SPLIT_H / SPLIT_V the side that holds the slide is fixed (left / top).
The previous "ink density" auto-detection was unreliable and inverted real
Beamer exports — left is always the public slide, right is always the notes.

For INTERLEAVED we sample a few pairs to decide whether the slide is the
even page or the odd page of each pair (Beamer normally puts the slide
first, but we stay defensive).
"""
from __future__ import annotations

import fitz  # PyMuPDF
from PySide6.QtGui import QImage, QPixmap


LAYOUT_NORMAL = "normal"
LAYOUT_SPLIT_H = "split_h"        # left | right
LAYOUT_SPLIT_V = "split_v"        # top  / bottom
LAYOUT_INTERLEAVED = "interleaved"  # slide, notes, slide, notes, …


class PdfDocument:
    def __init__(self, path: str):
        self.path = path
        self.doc = fitz.open(path)
        self._raw_page_count = self.doc.page_count
        self.layout = LAYOUT_NORMAL
        # SPLIT_H : "left"/"right"   SPLIT_V : "top"/"bottom"
        self.slide_side = "left"
        # INTERLEAVED : 0 if even pages are the slides, 1 if odd pages are
        self.slide_parity = 0
        # "auto" keeps detection, otherwise one of MANUAL_MODES below.
        self.mode = "auto"
        self._detect_layout()
        self._sync_page_count()

    def _sync_page_count(self) -> None:
        if self.layout == LAYOUT_INTERLEAVED:
            self.page_count = (self._raw_page_count + 1) // 2
        else:
            self.page_count = self._raw_page_count

    # ----- manual mode override -----
    # (label_shown_in_ui, internal_mode_id)
    MANUAL_MODES = (
        ("Auto", "auto"),
        ("Normal (diapo seule)", "normal"),
        ("Côte à côte — diapo à gauche", "split_h_left"),
        ("Côte à côte — diapo à droite", "split_h_right"),
        ("Empilé — diapo en haut", "split_v_top"),
        ("Empilé — diapo en bas", "split_v_bottom"),
        ("Alternées — diapo = pages paires", "interleaved_even"),
        ("Alternées — diapo = pages impaires", "interleaved_odd"),
    )

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        if mode == "auto":
            self._detect_layout()
        elif mode == "normal":
            self.layout = LAYOUT_NORMAL
        elif mode == "split_h_left":
            self.layout = LAYOUT_SPLIT_H; self.slide_side = "left"
        elif mode == "split_h_right":
            self.layout = LAYOUT_SPLIT_H; self.slide_side = "right"
        elif mode == "split_v_top":
            self.layout = LAYOUT_SPLIT_V; self.slide_side = "top"
        elif mode == "split_v_bottom":
            self.layout = LAYOUT_SPLIT_V; self.slide_side = "bottom"
        elif mode == "interleaved_even":
            self.layout = LAYOUT_INTERLEAVED; self.slide_parity = 0
        elif mode == "interleaved_odd":
            self.layout = LAYOUT_INTERLEAVED; self.slide_parity = 1
        self._sync_page_count()

    def detected_mode(self) -> str:
        """Internal mode id corresponding to the current auto-detected layout."""
        if self.layout == LAYOUT_SPLIT_H:
            return "split_h_left" if self.slide_side == "left" else "split_h_right"
        if self.layout == LAYOUT_SPLIT_V:
            return "split_v_top" if self.slide_side == "top" else "split_v_bottom"
        if self.layout == LAYOUT_INTERLEAVED:
            return "interleaved_even" if self.slide_parity == 0 else "interleaved_odd"
        return "normal"

    # ----- layout detection -----
    def _detect_layout(self) -> None:
        if self._raw_page_count == 0:
            return
        page = self.doc.load_page(0)
        w, h = page.rect.width, page.rect.height
        ratio = w / h if h else 1.0
        if ratio > 2.2:
            self.layout = LAYOUT_SPLIT_H
            self.slide_side = "left"        # fixed: left = public, right = notes
            return
        if ratio < 0.9:
            self.layout = LAYOUT_SPLIT_V
            self.slide_side = "top"         # fixed: top  = public, bottom = notes
            return
        # Normal aspect ratio — check for interleaved slide/notes pages.
        if self._raw_page_count >= 2 and self._raw_page_count % 2 == 0 \
                and self._looks_interleaved():
            self.layout = LAYOUT_INTERLEAVED
            self.slide_parity = self._pick_slide_parity()
            return
        self.layout = LAYOUT_NORMAL

    def _avg_text_len(self, parity: int) -> float:
        # Average text length on every other page (parity 0 = even, 1 = odd).
        lens = [len(self.doc.load_page(i).get_text("text"))
                for i in range(parity, self._raw_page_count, 2)]
        return sum(lens) / len(lens) if lens else 0.0

    def _looks_interleaved(self) -> bool:
        # In Beamer "show notes on second screen" exports, the notes page is
        # consistently more text-heavy than the matching slide page. If one
        # parity is ≥30% longer than the other across the whole document,
        # treat it as interleaved.
        even = self._avg_text_len(0)
        odd = self._avg_text_len(1)
        if even <= 0 or odd <= 0:
            return False
        ratio = max(even, odd) / min(even, odd)
        return ratio >= 1.3

    def _pick_slide_parity(self) -> int:
        # Slide pages have less text than notes pages → shorter parity is slides.
        even = self._avg_text_len(0)
        odd = self._avg_text_len(1)
        return 0 if even <= odd else 1

    # ----- region helpers -----
    def _slide_rect(self, page: fitz.Page) -> fitz.Rect:
        r = page.rect
        if self.layout == LAYOUT_SPLIT_H:
            mx = (r.x0 + r.x1) / 2
            return fitz.Rect(r.x0, r.y0, mx, r.y1) if self.slide_side == "left" \
                else fitz.Rect(mx, r.y0, r.x1, r.y1)
        if self.layout == LAYOUT_SPLIT_V:
            my = (r.y0 + r.y1) / 2
            return fitz.Rect(r.x0, r.y0, r.x1, my) if self.slide_side == "top" \
                else fitz.Rect(r.x0, my, r.x1, r.y1)
        return r

    def _notes_rect(self, page: fitz.Page) -> fitz.Rect | None:
        if self.layout not in (LAYOUT_SPLIT_H, LAYOUT_SPLIT_V):
            return None
        r = page.rect
        if self.layout == LAYOUT_SPLIT_H:
            mx = (r.x0 + r.x1) / 2
            return fitz.Rect(mx, r.y0, r.x1, r.y1) if self.slide_side == "left" \
                else fitz.Rect(r.x0, r.y0, mx, r.y1)
        my = (r.y0 + r.y1) / 2
        return fitz.Rect(r.x0, r.y0, r.x1, my) if self.slide_side == "top" \
            else fitz.Rect(r.x0, my, r.x1, r.y1)

    # ----- interleaved page mapping -----
    def _slide_page_index(self, index: int) -> int:
        if self.layout == LAYOUT_INTERLEAVED:
            return 2 * index + self.slide_parity
        return index

    def _notes_page_index(self, index: int) -> int | None:
        if self.layout != LAYOUT_INTERLEAVED:
            return None
        return 2 * index + (1 - self.slide_parity)

    # ----- rendering -----
    @staticmethod
    def _pix_to_qpixmap(pix: fitz.Pixmap) -> QPixmap:
        fmt = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        return QPixmap.fromImage(img.copy())

    def _render_region(self, page_index: int, rect: fitz.Rect, target_w: int,
                       target_h: int, dpr: float = 1.0) -> QPixmap:
        if not (0 <= page_index < self._raw_page_count):
            return QPixmap()
        rw, rh = rect.width, rect.height
        if rw <= 0 or rh <= 0 or target_w <= 0 or target_h <= 0:
            return QPixmap()
        page = self.doc.load_page(page_index)
        scale = min((target_w * dpr) / rw, (target_h * dpr) / rh)
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False, clip=rect)
        qpix = self._pix_to_qpixmap(pix)
        qpix.setDevicePixelRatio(dpr)
        return qpix

    def render_slide(self, index: int, target_w: int, target_h: int, dpr: float = 1.0) -> QPixmap:
        if not (0 <= index < self.page_count):
            return QPixmap()
        pi = self._slide_page_index(index)
        page = self.doc.load_page(pi)
        return self._render_region(pi, self._slide_rect(page), target_w, target_h, dpr)

    def render_notes(self, index: int, target_w: int, target_h: int, dpr: float = 1.0) -> QPixmap | None:
        if not (0 <= index < self.page_count):
            return None
        if self.layout == LAYOUT_INTERLEAVED:
            pi = self._notes_page_index(index)
            if pi is None or not (0 <= pi < self._raw_page_count):
                return None
            page = self.doc.load_page(pi)
            return self._render_region(pi, page.rect, target_w, target_h, dpr)
        if self.layout in (LAYOUT_SPLIT_H, LAYOUT_SPLIT_V):
            pi = self._slide_page_index(index)
            page = self.doc.load_page(pi)
            nr = self._notes_rect(page)
            if nr is None:
                return None
            return self._render_region(pi, nr, target_w, target_h, dpr)
        return None

    def has_notes(self) -> bool:
        return self.layout != LAYOUT_NORMAL

    def close(self) -> None:
        try:
            self.doc.close()
        except Exception:
            pass
