# Cookie Run: Crumble — Quest Automation Bot

## Overview

Python script running on Windows that automates daily quest completion in Cookie Run: Crumble via ADB connection to MuMu Player v6. Uses OpenCV for visual state detection and pytesseract for quest text OCR.

## Architecture

```
cookierun-bot/
├── main.py          # main loop
├── config.py        # coordinates, thresholds, timings
├── adb.py           # ADB wrapper (connect, screenshot, tap, swipe, wait)
├── detector.py      # OpenCV: color state detection + template matching
├── quests.py        # quest type handlers
└── templates/       # PNG crops for template matching (buttons, screens)
```

## ADB Connection

MuMu Player v6 default ADB port: `127.0.0.1:7555`

Script connects on startup and verifies device is available before entering the main loop.

## Quest UI

One quest shown at a time. Quest card states:

- **Grey/dark** — quest incomplete, action required or waiting
- **Yellow/gold** — quest claimable, "Repeat" label visible

State detected by HSV color analysis on the quest card region crop. Yellow threshold: H 20–35, S >150, V >150. If >30% of card pixels fall in range → claimable.

## Main Loop

Every tick (default 5s):

1. Take ADB screenshot
2. Check **better item popup** — if visible, dismiss (tap top-center)
3. Check **repeatable quest overlay** — if visible and yellow, claim
4. Check **main quest card** state
   - If yellow → tap claim button → continue
   - If grey → OCR quest text → dispatch to handler → continue
5. Sleep `CHECK_INTERVAL`

## Global Interrupts

Checked every tick, including during wait states:

### Better Item Popup
Triggered when the oven crafts an item better than equipped. Shows two item cards side-by-side with "Equip"/"Sell" buttons.
Detection: template match against a saved crop of the "Equip" button (distinctive blue button, only appears in this popup).
Action: tap `TOP_CENTER_DISMISS` (640, 50 at 1280×720) to close.

### Repeatable Quest Overlay
Short quests that pop up on top of the main stage quest when complete.
Detection: check `REPEATABLE_REGION` for yellow HSV range.
Action: tap claim button.

## Quest Handlers

OCR reads quest text from `QUEST_TEXT_REGION`. Keyword matching dispatches to handler:

| Keywords | Handler | Action |
|---|---|---|
| `gacha` + `pet` | `pull_pet_gacha` | Navigate to pet gacha → pull 10x → back → claim |
| `gacha` + `cookie` or `character` | `pull_cookie_gacha` | Navigate to cookie gacha → pull 10x → back → claim |
| `chest` + `inventory` | `use_chest` | Navigate to inventory → use 1 chest → back → claim |
| `stage` or `clear` | `wait_stage` | Sleep and recheck (auto-completes) |
| `defeat` + `enemies` | `wait_enemies` | Sleep and recheck (auto-completes during stages) |
| `oven` or `bake` or `gear` | `bake_oven` | Navigate to oven → start bake → wait → back → claim |
| no match | `unknown` | Log quest text → sleep → retry |

### `bake_oven` detail
- Navigate to oven, start bake
- Enter polling wait loop (checks every tick for better item popup + repeatable overlay)
- Poll every tick: when oven region returns to idle state (detected by template match on "Start Bake" button reappearing), oven is done
- Navigate back → claim

## Config

`config.py` stores all pixel coordinates for a fixed MuMu resolution (default 1280×720). Coordinate placeholders below are filled during first-run calibration: run `python main.py --calibrate` to dump a screenshot, then measure and paste coordinates.

```python
MUMU_ADB = "127.0.0.1:7555"
SCREEN_W, SCREEN_H = 1280, 720
CHECK_INTERVAL = 5          # seconds

QUEST_CARD_REGION  = (x, y, w, h)
QUEST_TEXT_REGION  = (x, y, w, h)
REPEATABLE_REGION  = (x, y, w, h)
BETTER_ITEM_REGION = (x, y, w, h)

CLAIM_BTN          = (x, y)
TOP_CENTER_DISMISS = (640, 50)

# per-screen navigation tap coordinates
NAV = {
    "pet_gacha":   (x, y),
    "cookie_gacha": (x, y),
    "inventory":   (x, y),
    "oven":        (x, y),
    "back":        (x, y),
    "pull_btn":    (x, y),
    "use_chest_btn": (x, y),
    "start_bake_btn": (x, y),
}
```

## Dependencies

```
opencv-python
pytesseract
Pillow
adb (Android platform tools on PATH)
```

## Error Handling

- ADB disconnect → reconnect with retry (3 attempts, 5s apart), then exit
- OCR returns empty → treat as unknown, log, sleep
- Handler navigation fails (expected screen not found after N taps) → log, navigate back to home, continue loop
- Unknown quest type → log quest text to `unknown_quests.log` for manual review
