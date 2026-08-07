import logging
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image

import config
from adb import ADB

logger = logging.getLogger(__name__)
_unknown_log = open("unknown_quests.log", "a", buffering=1)


def ocr_quest_text(img: np.ndarray) -> str:
    x, y, w, h = config.QUEST_TEXT_REGION
    crop = img[y:y+h, x:x+w]
    crop = cv2.resize(crop, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    pil = Image.fromarray(gray)
    text = pytesseract.image_to_string(pil, config="--psm 11 --oem 1")
    return text.strip().lower()


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


def use_chest(adb: ADB) -> None:
    adb.tap(*config.NAV["quest_tap"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["select_chest"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["use_chest_btn"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.TOP_CENTER_DISMISS)    # dismiss reward popup
    adb.sleep(config.POPUP_FADE_WAIT)      # wait for fade-out (0.4s)
    adb.tap(*config.NAV["back"])           # close inventory
    adb.sleep(config.NAV_WAIT)


def wait_stage(adb: ADB) -> None:
    adb.sleep(config.CHECK_INTERVAL)


def wait_enemies(adb: ADB) -> None:
    adb.sleep(config.CHECK_INTERVAL)


def bake_oven(adb: ADB) -> None:
    adb.tap(*config.NAV["oven"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["start_bake_btn"])  # Start closes panel, returns to battle
    adb.sleep(config.NAV_WAIT)


HANDLERS = {
    "pull_gacha":    pull_gacha,
    "use_chest":     use_chest,
    "wait_stage":    wait_stage,
    "wait_enemies":  wait_enemies,
    "bake_oven":     bake_oven,
}
