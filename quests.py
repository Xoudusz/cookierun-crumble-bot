import logging
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
    pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    text = pytesseract.image_to_string(pil, config="--psm 6")
    return text.strip().lower()


def dispatch_quest(text: str) -> str:
    t = text.lower()
    if "gacha" in t and "pet" in t:
        return "pull_pet_gacha"
    if "gacha" in t and ("cookie" in t or "character" in t):
        return "pull_cookie_gacha"
    if "chest" in t and "inventory" in t:
        return "use_chest"
    if "oven" in t or "bake" in t or "furnace" in t or "gear" in t:
        return "bake_oven"
    if "defeat" in t and "enem" in t:
        return "wait_enemies"
    if "stage" in t or "clear" in t:
        return "wait_stage"
    _unknown_log.write(f"{text}\n")
    logger.warning("Unknown quest: %r", text)
    return "unknown"
