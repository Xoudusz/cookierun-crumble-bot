import logging
import re
import time
import warnings

warnings.filterwarnings("ignore", message=r".*pin_memory.*")
warnings.filterwarnings("ignore", message=r".*quantize_per_tensor.*")
warnings.filterwarnings("ignore", message=r".*GPU.*", category=UserWarning)
warnings.filterwarnings("ignore", message=r".*CUDA.*", category=UserWarning)

import cv2
import numpy as np

import os

import config
from adb import ADB
from detector import is_yellow, find_template

_EQUIP_BTN_TEMPLATE = os.path.join("templates", "equip_button.png")

_reader = None

def _get_reader():
    global _reader
    if _reader is None:
        import os
        os.environ.setdefault("EASYOCR_MODULE_PATH", os.path.expanduser("~/.EasyOCR"))
        logging.getLogger("easyocr").setLevel(logging.ERROR)
        logging.getLogger("torch").setLevel(logging.ERROR)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import easyocr
            _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _reader

logger = logging.getLogger(__name__)
_unknown_log = open("unknown_quests.log", "a", buffering=1)


def ocr_quest_text(img: np.ndarray) -> str:
    x, y, w, h = config.QUEST_TEXT_REGION
    crop = img[y:y+h, x:x+w]
    results = _get_reader().readtext(crop, detail=0, paragraph=True)
    return " ".join(results).strip().lower()


def dispatch_quest(text: str) -> str:
    t = re.sub(r'\d+\s*/\s*\d+', '', text.lower())
    if "gacha" in t:
        return "pull_gacha"
    if "chest" in t or "inventory" in t:
        return "use_chest"
    if "oven" in t or "bake" in t or "furnace" in t or "gear" in t:
        return "bake_oven"
    if "enem" in t:
        return "wait_enemies"
    if "stage" in t or "clear" in t:
        return "wait_stage"
    if "times" in t:
        return "bake_oven"
    _unknown_log.write(f"{text}\n")
    logger.warning("Unknown quest: %r", text)
    return "unknown"


def dismiss_claimed_popup(adb: ADB) -> None:
    x, y = config.CLAIMED_X_BTN
    adb.tap(x, y)


def claim_quest(adb: ADB) -> None:
    x, y = config.CLAIM_BTN
    adb.tap(x, y)
    adb.sleep(config.CLAIM_WAIT)


def pull_gacha(adb: ADB) -> None:
    adb.tap(*config.NAV["quest_tap"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["pull_x10"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["back"])           # cancel animation
    adb.sleep(config.GACHA_RESULT_WAIT)    # wait for results cards to flip in
    adb.tap(*config.NAV["back"])           # close results screen
    adb.sleep(config.NAV_WAIT + 0.1)       # extra 0.1s before closing gacha
    adb.tap(*config.NAV["back"])           # close gacha screen
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["quest_tap"])      # reopen quest panel on main screen
    adb.sleep(config.NAV_WAIT + 0.1)


def use_chest(adb: ADB) -> None:
    adb.tap(*config.NAV["quest_tap"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["select_chest"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["use_chest_btn"])
    adb.sleep(config.POPUP_FADE_WAIT)      # wait for reward popup to appear
    adb.tap(*config.TOP_CENTER_DISMISS)    # dismiss reward popup
    adb.sleep(config.POPUP_FADE_WAIT)      # wait for fade-out (0.4s)
    adb.tap(*config.NAV["back"])           # close inventory
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["quest_tap"])      # reopen quest panel on main screen
    adb.sleep(config.NAV_WAIT)


def wait_stage(adb: ADB) -> None:
    pass


def wait_enemies(adb: ADB) -> None:
    pass


_baking = False


def bake_oven(adb: ADB) -> None:
    global _baking
    if not _baking:
        adb.tap(*config.NAV["oven"])
        adb.sleep(config.NAV_WAIT)
        # Tap orange button 3× — dismisses start + up to 2 organize-gear overlays
        for _ in range(3):
            adb.tap(*config.NAV["start_bake_btn"])
            adb.sleep(config.NAV_WAIT)
        _baking = True

    # Poll until claimable; timeout lets main loop clear unexpected popups
    deadline = time.time() + config.BAKE_POLL_TIMEOUT
    while time.time() < deadline:
        adb.sleep(config.BAKE_POLL_INTERVAL)
        img = adb.screenshot()
        # Handle better-item popup inline — reset deadline so it doesn't eat bake time
        if os.path.exists(_EQUIP_BTN_TEMPLATE) and find_template(img, _EQUIP_BTN_TEMPLATE) is not None:
            logger.info("Better item popup during bake — dismissing")
            adb.tap(*config.TOP_CENTER_DISMISS)
            adb.sleep(config.BETTER_ITEM_WAIT)
            deadline = time.time() + config.BAKE_POLL_TIMEOUT  # reset after sleep, not before
            continue
        if is_yellow(img, config.QUEST_CARD_REGION) or is_yellow(img, config.REPEATABLE_REGION):
            claim_quest(adb)
            adb.tap(*config.NAV["back"])
            adb.sleep(config.NAV_WAIT)
            adb.tap(*config.NAV["quest_tap"])
            adb.sleep(config.NAV_WAIT)
            _baking = False
            break
    else:
        # Timed out — game may have cancelled bake (e.g. after better-item transition)
        _baking = False


HANDLERS = {
    "pull_gacha":    pull_gacha,
    "use_chest":     use_chest,
    "wait_stage":    wait_stage,
    "wait_enemies":  wait_enemies,
    "bake_oven":     bake_oven,
}
