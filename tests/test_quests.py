import numpy as np
import pytest
from unittest.mock import MagicMock, call, patch
from quests import (
    dispatch_quest,
    claim_quest, dismiss_claimed_popup,
    pull_gacha, use_chest, wait_stage, bake_oven,
)
import config


def _mock_adb():
    adb = MagicMock()
    adb.sleep = MagicMock()
    adb.tap = MagicMock()
    return adb


@pytest.mark.parametrize("text,expected", [
    ("pull in the pet gacha 10 times", "pull_gacha"),
    ("pull the cookie gacha 10 times", "pull_gacha"),
    ("use 1 chest from your inventory",  "use_chest"),
    ("clear stage 3-4",                  "wait_stage"),
    ("defeat 100 enemies",               "wait_enemies"),
    ("bake gear in the oven 3 times",    "bake_oven"),
    ("use the furnace 2 times",          "bake_oven"),
    ("15 times 200",                     "bake_oven"),
    ("something totally unknown",        "unknown"),
    ("",                                 "unknown"),
])
def test_dispatch_quest(text, expected):
    assert dispatch_quest(text) == expected


def test_dismiss_claimed_popup_taps_x():
    adb = _mock_adb()
    config.CLAIMED_X_BTN = (360, 900)
    dismiss_claimed_popup(adb)
    adb.tap.assert_called_once_with(360, 900)


def test_claim_quest_taps_claim():
    adb = _mock_adb()
    config.CLAIM_BTN = (600, 100)
    config.CLAIM_WAIT = 0
    claim_quest(adb)
    adb.tap.assert_called_once_with(600, 100)


def test_pull_gacha_navigates_and_pulls():
    adb = _mock_adb()
    config.NAV = {
        "quest_tap": (820, 1101),
        "pull_x10":  (550, 1550),
        "back":      (540, 1860),
    }
    config.NAV_WAIT = 0
    config.GACHA_RESULT_WAIT = 0
    pull_gacha(adb)
    taps = [c.args for c in adb.tap.call_args_list]
    assert (820, 1101) in taps
    assert (550, 1550) in taps
    assert taps.count((540, 1860)) == 3   # cancel anim + close results + close gacha
    assert taps.count((820, 1101)) == 2   # initial quest_tap + reopen after gacha


def test_use_chest_navigates_and_uses():
    adb = _mock_adb()
    config.NAV = {
        "quest_tap":     (820, 1101),
        "select_chest":  (200, 1150),
        "use_chest_btn": (550, 850),
        "back":          (540, 1860),
    }
    config.TOP_CENTER_DISMISS = (540, 50)
    config.NAV_WAIT = 0
    config.POPUP_FADE_WAIT = 0
    use_chest(adb)
    taps = [c.args for c in adb.tap.call_args_list]
    assert taps.count((820, 1101)) == 2   # initial quest_tap + reopen after inventory
    assert (200, 1150) in taps
    assert (550, 850) in taps
    assert (540, 50) in taps
    assert (540, 1860) in taps


def test_wait_stage_does_nothing():
    adb = _mock_adb()
    wait_stage(adb)
    adb.sleep.assert_not_called()
    adb.tap.assert_not_called()


def test_bake_oven_taps_oven_then_start():
    import quests
    quests._baking = False  # reset flag before test
    adb = _mock_adb()
    config.NAV = {
        "oven":           (380, 1720),
        "start_bake_btn": (500, 1700),
        "back":           (540, 1860),
        "quest_tap":      (820, 1101),
    }
    config.NAV_WAIT = 0
    config.POPUP_FADE_WAIT = 0
    config.BAKE_POLL_INTERVAL = 0
    config.BAKE_POLL_TIMEOUT = 0
    config.QUEST_CARD_REGION = (0, 0, 10, 10)
    config.REPEATABLE_REGION = (0, 0, 10, 10)
    config.CLAIM_BTN = (820, 1102)
    config.CLAIM_WAIT = 0
    with patch("quests.is_yellow", return_value=False):
        bake_oven(adb)
    taps = [c.args for c in adb.tap.call_args_list]
    assert (380, 1720) in taps
    assert (500, 1700) in taps
