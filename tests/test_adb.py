import numpy as np
import pytest
from unittest.mock import patch, MagicMock, call
from adb import ADB


def _png_bytes():
    """Minimal valid 1x1 red PNG."""
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), (0, 0, 255)).save(buf, format="PNG")
    return buf.getvalue()


def test_connect_success():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=b"connected")
        adb = ADB("127.0.0.1", 7555)
        adb.connect()
        mock_run.assert_called_once_with(
            ["adb", "connect", "127.0.0.1:7555"],
            capture_output=True,
        )


def test_connect_retries_and_raises():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout=b"error")
        with patch("time.sleep"):
            adb = ADB("127.0.0.1", 7555)
            with pytest.raises(RuntimeError, match="ADB connect failed"):
                adb.connect()
        assert mock_run.call_count == 3


def test_screenshot_returns_ndarray():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=_png_bytes())
        adb = ADB("127.0.0.1", 7555)
        img = adb.screenshot()
        assert isinstance(img, np.ndarray)
        assert img.ndim == 3


def test_tap_sends_correct_command():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        adb = ADB("127.0.0.1", 7555)
        adb.tap(100, 200)
        mock_run.assert_called_once_with(
            ["adb", "-s", "127.0.0.1:7555", "shell", "input", "tap", "100", "200"],
            capture_output=True,
        )
