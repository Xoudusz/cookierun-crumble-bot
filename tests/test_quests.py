import pytest
import time
from unittest.mock import patch, MagicMock, call
from quests import (
    dispatch_quest,
    claim_quest, dismiss_claimed_popup,
    pull_pet_gacha, pull_cookie_gacha,
    use_chest, wait_stage, bake_oven,
)
import config


def _mock_adb():
    adb = MagicMock()
    adb.sleep = MagicMock()
    adb.tap = MagicMock()
    return adb


@pytest.mark.parametrize("text,expected", [
    ("pull in the pet gacha 10 times", "pull_pet_gacha"),
    ("Pull in the Pet Gacha 10 times", "pull_pet_gacha"),
    ("pull the cookie gacha 10 times", "pull_cookie_gacha"),
    ("pull the character gacha 10 times", "pull_cookie_gacha"),
    ("use 1 chest from your inventory", "use_chest"),
    ("clear stage 3-4", "wait_stage"),
    ("clear stages 10 times", "wait_stage"),
    ("defeat 100 enemies", "wait_enemies"),
    ("bake gear in the oven 3 times", "bake_oven"),
    ("use the furnace 2 times", "bake_oven"),
    ("something totally unknown", "unknown"),
    ("", "unknown"),
])
def test_dispatch_quest(text, expected):
    assert dispatch_quest(text) == expected


def test_dismiss_claimed_popup_taps_x():
    adb = _mock_adb()
    config.CLAIMED_X_BTN = (360, 900)
    dismiss_claimed_popup(adb)
    adb.tap.assert_called_once_with(360, 900)


def test_claim_quest_taps_claim_then_dismisses():
    adb = _mock_adb()
    config.CLAIM_BTN = (600, 100)
    config.CLAIMED_X_BTN = (360, 900)
    config.CLAIM_WAIT = 0
    claim_quest(adb)
    assert adb.tap.call_args_list[0] == call(600, 100)
    assert adb.tap.call_args_list[1] == call(360, 900)


def test_pull_pet_gacha_navigates_and_pulls():
    adb = _mock_adb()
    config.NAV = {
        "pet_gacha": (100, 200),
        "pull_x10":  (300, 600),
        "back":      (50, 50),
    }
    config.NAV_WAIT = 0
    pull_pet_gacha(adb)
    taps = [c.args for c in adb.tap.call_args_list]
    assert (100, 200) in taps  # navigated to pet gacha
    assert (300, 600) in taps  # tapped x10 pull


def test_pull_cookie_gacha_navigates_and_pulls():
    adb = _mock_adb()
    config.NAV = {
        "cookie_gacha": (150, 200),
        "pull_x10":     (300, 600),
        "back":         (50, 50),
    }
    config.NAV_WAIT = 0
    pull_cookie_gacha(adb)
    taps = [c.args for c in adb.tap.call_args_list]
    assert (150, 200) in taps
    assert (300, 600) in taps


def test_use_chest_navigates_and_uses():
    adb = _mock_adb()
    config.NAV = {
        "inventory":     (200, 900),
        "use_chest_btn": (360, 700),
        "back":          (50, 50),
    }
    config.NAV_WAIT = 0
    use_chest(adb)
    taps = [c.args for c in adb.tap.call_args_list]
    assert (200, 900) in taps
    assert (360, 700) in taps


def test_wait_stage_sleeps():
    adb = _mock_adb()
    config.CHECK_INTERVAL = 1
    wait_stage(adb)
    adb.sleep.assert_called_once_with(1)


def test_bake_oven_starts_bake_and_polls_until_done():
    adb = _mock_adb()
    config.NAV = {
        "oven":           (500, 900),
        "start_bake_btn": (360, 800),
        "back":           (50, 50),
    }
    config.NAV_WAIT = 0
    config.CHECK_INTERVAL = 0

    # find_template: first call returns None (baking), second returns position (done)
    with patch("quests.find_template", side_effect=[None, (360, 800)]):
        screenshots = [MagicMock(), MagicMock()]
        call_count = 0
        def fake_screenshot():
            nonlocal call_count
            s = screenshots[min(call_count, len(screenshots)-1)]
            call_count += 1
            return s
        bake_oven(adb, fake_screenshot, check_interrupts=None)

    taps = [c.args for c in adb.tap.call_args_list]
    assert (500, 900) in taps        # navigated to oven
    assert (360, 800) in taps        # tapped Start


def test_bake_oven_calls_check_interrupts_each_poll():
    adb = _mock_adb()
    config.NAV = {
        "oven":           (500, 900),
        "start_bake_btn": (360, 800),
        "back":           (50, 50),
    }
    config.NAV_WAIT = 0
    config.CHECK_INTERVAL = 0
    interrupt_calls = []

    def fake_check(img, a):
        interrupt_calls.append(1)
        return False

    with patch("quests.find_template", side_effect=[None, (360, 800)]):
        bake_oven(adb, MagicMock(), check_interrupts=fake_check)

    assert len(interrupt_calls) >= 1
