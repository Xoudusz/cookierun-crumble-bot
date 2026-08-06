import argparse
import logging
import os
import time

import cv2
import numpy as np

import config
from adb import ADB
from detector import is_yellow, find_template
from quests import (
    claim_quest, ocr_quest_text, dispatch_quest,
    HANDLERS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

_EQUIP_BTN_TEMPLATE = os.path.join("templates", "equip_button.png")


def check_global_interrupts(img: np.ndarray, adb: ADB) -> bool:
    """Return True if an interrupt was handled (caller should restart tick)."""
    # 1. Better-item popup (detected by "Equip" button template)
    if os.path.exists(_EQUIP_BTN_TEMPLATE):
        if find_template(img, _EQUIP_BTN_TEMPLATE) is not None:
            logger.info("Better item popup — dismissing")
            adb.tap(*config.TOP_CENTER_DISMISS)
            adb.sleep(config.NAV_WAIT)
            return True

    # 2. Repeatable quest overlay
    if is_yellow(img, config.REPEATABLE_REGION):
        logger.info("Repeatable quest claimable — claiming")
        claim_quest(adb)
        return True

    return False


def run_calibrate(adb: ADB) -> None:
    print("Taking calibration screenshot…")
    img = adb.screenshot()
    path = "calibration.png"
    cv2.imwrite(path, img)
    print(f"Saved to {path}")
    print(
        "\nOpen the image, measure pixel coordinates, then update config.py:\n"
        "  QUEST_CARD_REGION  = (x, y, w, h)\n"
        "  QUEST_TEXT_REGION  = (x, y, w, h)\n"
        "  REPEATABLE_REGION  = (x, y, w, h)\n"
        "  BETTER_ITEM_REGION = (x, y, w, h)\n"
        "  CLAIM_BTN          = (x, y)\n"
        "  CLAIMED_X_BTN      = (x, y)\n"
        "  NAV = { ... }\n"
        "\nAlso crop template PNGs and save to templates/:\n"
        "  equip_button.png      — the blue Equip button from the better-item popup\n"
        "  start_bake_btn.png    — the orange Start button on the Auto Bake screen\n"
    )


def run_loop(adb: ADB) -> None:
    logger.info("Bot starting — press Ctrl+C to stop")
    while True:
        try:
            img = adb.screenshot()

            if check_global_interrupts(img, adb):
                continue

            if is_yellow(img, config.QUEST_CARD_REGION):
                logger.info("Quest claimable — claiming")
                claim_quest(adb)
                continue

            text = ocr_quest_text(img)
            quest_type = dispatch_quest(text)
            logger.info("Quest: %r -> %s", text, quest_type)

            if quest_type == "bake_oven":
                HANDLERS["bake_oven"](adb, adb.screenshot, check_global_interrupts)
            elif quest_type in HANDLERS:
                HANDLERS[quest_type](adb)
            # unknown: dispatch_quest already logged it

            time.sleep(config.CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Stopped by user")
            break
        except (RuntimeError, FileNotFoundError) as exc:
            logger.error("Error: %s — reconnecting", exc)
            adb.connect()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cookie Run: Crumble quest bot")
    parser.add_argument("--calibrate", action="store_true", help="dump calibration screenshot and exit")
    args = parser.parse_args()

    adb = ADB(config.MUMU_ADB_HOST, config.MUMU_ADB_PORT)
    adb.connect()

    if args.calibrate:
        run_calibrate(adb)
    else:
        run_loop(adb)


if __name__ == "__main__":
    main()
