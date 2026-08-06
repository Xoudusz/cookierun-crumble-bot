# cookierun-crumble-bot

## Stack
Python 3.10+, opencv-python, pytesseract, Pillow, ADB (Android platform tools)

## Structure
- `main.py` — entry point, main loop, `--calibrate` mode
- `config.py` — ALL coordinates and thresholds — edit here after calibration
- `adb.py` — ADB subprocess wrapper
- `detector.py` — HSV yellow detection + template matching
- `quests.py` — OCR dispatch + all quest handlers
- `templates/` — PNG crops for template matching (not committed)

## Run
```bash
python main.py               # start bot
python main.py --calibrate   # dump calibration.png and print coord guide
pytest tests/ -v             # run tests
```

## After changes
Bump `VERSION`, commit, push.
