import argparse
import logging
import time

import cv2
import numpy as np

import config
from adb import ADB
from detector import is_yellow
from quests import (
    claim_quest, ocr_quest_text, dispatch_quest,
    HANDLERS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

def check_global_interrupts(img: np.ndarray, adb: ADB) -> bool:
    """Return True if an interrupt was handled (caller should restart tick)."""
    # Repeatable quest overlay
    if is_yellow(img, config.REPEATABLE_REGION):
        logger.info("Quest claimable — claiming")
        claim_quest(adb)
        adb.tap(*config.NAV["back"])
        adb.sleep(config.NAV_WAIT)
        adb.tap(*config.NAV["quest_tap"])
        adb.sleep(config.NAV_WAIT)
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
            adb.tap(*config.NAV["back"])  # safety: return to main screen if lost
            adb.sleep(config.NAV_WAIT)
            img = adb.screenshot()

            if check_global_interrupts(img, adb):
                continue

            if is_yellow(img, config.QUEST_CARD_REGION):
                logger.info("Quest claimable — claiming")
                claim_quest(adb)
                adb.tap(*config.NAV["back"])
                adb.sleep(config.NAV_WAIT)
                adb.tap(*config.NAV["quest_tap"])
                adb.sleep(config.NAV_WAIT)
                continue

            text = ocr_quest_text(img)
            quest_type = dispatch_quest(text)
            logger.info("Quest: %r -> %s", text, quest_type)

            if quest_type == "unknown":
                continue  # retry immediately — don't waste CHECK_INTERVAL on bad OCR read

            if quest_type in HANDLERS:
                HANDLERS[quest_type](adb)

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
