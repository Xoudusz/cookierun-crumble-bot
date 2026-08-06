import numpy as np
import cv2
import pytest
import os
import tempfile
from detector import is_yellow, find_template


def _solid_bgr(h, w, bgr):
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = bgr
    return img


def _yellow_bgr():
    """Solid yellow in BGR (H=30, S=255, V=255 in HSV)."""
    hsv = np.full((50, 50, 3), [30, 255, 255], dtype=np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def _grey_bgr():
    return _solid_bgr(50, 50, (100, 100, 100))


def test_is_yellow_detects_yellow_region():
    canvas = np.zeros((200, 200, 3), dtype=np.uint8)
    yellow = _yellow_bgr()
    canvas[50:100, 50:100] = yellow
    assert is_yellow(canvas, (50, 50, 50, 50)) is True


def test_is_yellow_rejects_grey():
    img = _grey_bgr()
    assert is_yellow(img, (0, 0, 50, 50)) is False


def test_is_yellow_uses_custom_threshold():
    # Image that is 20% yellow — below default 30% threshold
    canvas = np.full((100, 100, 3), [100, 100, 100], dtype=np.uint8)
    yellow_row = _yellow_bgr()[0:20, :50]
    # Tile yellow horizontally to fill 100 width
    for i in range(0, 100, 50):
        w = min(50, 100 - i)
        canvas[0:20, i:i+w] = yellow_row[:, :w]
    assert is_yellow(canvas, (0, 0, 100, 100), threshold=0.30) is False
    assert is_yellow(canvas, (0, 0, 100, 100), threshold=0.15) is True


def test_find_template_returns_center_on_match():
    bg = _solid_bgr(200, 200, (50, 50, 50))
    tpl = _solid_bgr(20, 20, (200, 100, 50))
    bg[80:100, 90:110] = tpl
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        cv2.imwrite(f.name, tpl)
        result = find_template(bg, f.name, threshold=0.95)
    os.unlink(f.name)
    assert result is not None
    cx, cy = result
    assert abs(cx - 100) <= 2
    assert abs(cy - 90) <= 2


def test_find_template_returns_none_on_no_match():
    bg = _solid_bgr(200, 200, (50, 50, 50))
    tpl = _solid_bgr(20, 20, (200, 100, 50))
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        cv2.imwrite(f.name, tpl)
        result = find_template(bg, f.name, threshold=0.99)
    os.unlink(f.name)
    assert result is None
