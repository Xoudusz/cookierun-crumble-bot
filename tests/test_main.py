import numpy as np
import pytest
from unittest.mock import patch, MagicMock
import config
from main import check_global_interrupts


def _black(h=100, w=100):
    return np.zeros((h, w, 3), dtype=np.uint8)


def test_check_global_interrupts_dismisses_better_item():
    adb = MagicMock()
    config.TOP_CENTER_DISMISS = (540, 50)
    config.BETTER_ITEM_WAIT = 0
    with patch("main.os.path.exists", return_value=True):
        with patch("main.find_template", return_value=(200, 300)):
            result = check_global_interrupts(_black(), adb)
    assert result is True


def test_check_global_interrupts_claims_repeatable():
    adb = MagicMock()
    config.REPEATABLE_REGION = (0, 0, 100, 100)
    config.CLAIM_BTN = (50, 50)
    config.CLAIM_WAIT = 0
    config.NAV_WAIT = 0
    config.NAV = {"back": (540, 1860), "quest_tap": (820, 1101)}
    with patch("main.os.path.exists", return_value=False):
        with patch("main.is_yellow", return_value=True):
            result = check_global_interrupts(_black(), adb)
    assert result is True


def test_check_global_interrupts_returns_false_when_clear():
    adb = MagicMock()
    config.REPEATABLE_REGION = (0, 0, 100, 100)
    with patch("main.os.path.exists", return_value=False):
        with patch("main.is_yellow", return_value=False):
            result = check_global_interrupts(_black(), adb)
    assert result is False
    adb.tap.assert_not_called()
