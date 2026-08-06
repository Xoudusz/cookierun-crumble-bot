import logging
import os
import cv2
import numpy as np
import pytesseract
from PIL import Image

import config
from adb import ADB
from detector import find_template

logger = logging.getLogger(__name__)
_unknown_log = open("unknown_quests.log", "a", buffering=1)


def ocr_quest_text(img: np.ndarray) -> str:
    x, y, w, h = config.QUEST_TEXT_REGION
    crop = img[y:y+h, x:x+w]
    # upscale 2x — Tesseract accuracy improves significantly on larger text
    crop = cv2.resize(crop, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    pil = Image.fromarray(thresh)
    text = pytesseract.image_to_string(pil, config="--psm 6")
    return text.strip().lower()


def dispatch_quest(text: str) -> str:
    t = text.lower()
    if "gacha" in t and "pet" in t:
        return "pull_pet_gacha"
    if "gacha" in t and ("cookie" in t or "character" in t):
        return "pull_cookie_gacha"
    if "chest" in t or "inventory" in t:
        return "use_chest"
    if "oven" in t or "bake" in t or "furnace" in t or "gear" in t:
        return "bake_oven"
    if "enem" in t:
        return "wait_enemies"
    if "stage" in t or "clear" in t:
        return "wait_stage"
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
    dismiss_claimed_popup(adb)


def pull_pet_gacha(adb: ADB) -> None:
    adb.tap(*config.NAV["gacha_nav"])    # open gacha screen from main
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["pet_gacha"])    # switch to Pet Gacha tab
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["pull_x10"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["back"])
    adb.sleep(config.NAV_WAIT)


def pull_cookie_gacha(adb: ADB) -> None:
    adb.tap(*config.NAV["gacha_nav"])    # open gacha screen from main
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["cookie_gacha"]) # switch to Cookie Gacha tab
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["pull_x10"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["back"])
    adb.sleep(config.NAV_WAIT)


def use_chest(adb: ADB) -> None:
    adb.tap(*config.NAV["inventory"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["select_chest"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["use_chest_btn"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.TOP_CENTER_DISMISS)  # dismiss result popup (tap upper half)
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["back"])         # close inventory screen
    adb.sleep(config.NAV_WAIT)


def wait_stage(adb: ADB) -> None:
    adb.sleep(config.CHECK_INTERVAL)


def wait_enemies(adb: ADB) -> None:
    adb.sleep(config.CHECK_INTERVAL)


_START_BAKE_TEMPLATE = os.path.join("templates", "start_bake_btn.png")


def bake_oven(adb: ADB, get_screenshot, check_interrupts=None) -> None:
    adb.tap(*config.NAV["oven"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["start_bake_btn"])
    adb.sleep(config.NAV_WAIT)
    while True:
        img = get_screenshot()
        if check_interrupts is not None:
            if check_interrupts(img, adb):
                img = get_screenshot()   # refresh after interrupt handled
        if find_template(img, _START_BAKE_TEMPLATE) is not None:
            break
        adb.sleep(config.CHECK_INTERVAL)
    adb.tap(*config.NAV["back"])
    adb.sleep(config.NAV_WAIT)


HANDLERS = {
    "pull_pet_gacha":  pull_pet_gacha,
    "pull_cookie_gacha": pull_cookie_gacha,
    "use_chest":       use_chest,
    "wait_stage":      wait_stage,
    "wait_enemies":    wait_enemies,
    "bake_oven":       bake_oven,
}
