# Cookie Run: Crumble Quest Bot

Automates daily quest completion in Cookie Run: Crumble via ADB to MuMu Player v6.

## Requirements

- Windows 10/11
- [MuMu Player v6](https://www.mumuplayer.com/) with Cookie Run: Crumble installed
- [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools) — `adb` must be on PATH
- [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Python 3.10+

## Install

```bash
pip install -r requirements.txt
```

## Setup (first run)

1. Start MuMu Player and launch Cookie Run: Crumble
2. Navigate to the main game screen (quests visible)
3. Run calibration:
   ```bash
   python main.py --calibrate
   ```
4. Open `calibration.png`, measure coordinates, fill in `config.py`
5. Crop template images (see calibration output for instructions)

## Run

```bash
python main.py
```

Press `Ctrl+C` to stop.

## Quest types handled

| Quest | Action |
|---|---|
| Clear stage | Wait (auto-completes) |
| Defeat enemies | Wait (auto-completes) |
| Pull pet gacha 10× | Navigates to pet gacha, pulls, returns |
| Pull cookie gacha 10× | Navigates to cookie gacha, pulls, returns |
| Use 1 chest | Opens inventory, uses chest, returns |
| Bake gear in oven | Starts Auto Bake, waits for completion, returns |

Unknown quest types are logged to `unknown_quests.log`.
