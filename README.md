# Cookie Run: Crumble Quest Bot

Automates daily quest completion in Cookie Run: Crumble via ADB to MuMu Player v6.

## Requirements

- Windows 10/11
- [MuMu Player v6](https://www.mumuplayer.com/) with Cookie Run: Crumble installed
- [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools) — `adb` must be on PATH
- Python 3.10+

## Install

```bash
pip install -r requirements.txt
```

EasyOCR downloads its models on first run (~100 MB).

## Setup (first run)

1. Start MuMu Player and launch Cookie Run: Crumble
2. Navigate to the main game screen (quests visible)
3. Run calibration:
   ```bash
   python main.py --calibrate
   ```
4. Open `calibration.png`, measure coordinates, fill in `config.py`
5. Crop template images into `templates/` (see calibration output for instructions)

## Run

```bash
python main.py
```

Press `Ctrl+C` to stop. Unknown quest reads are logged to `unknown_quests.log`.

## Quest types handled

| Quest | Action |
|---|---|
| Clear stage | Loop until claimable (auto-completes in game) |
| Defeat enemies | Loop until claimable (auto-completes in game) |
| Pull gacha 10× | Navigates via quest tap, pulls x10, closes results, returns |
| Use 1 chest | Opens inventory via quest tap, uses chest, dismisses popup, returns |
| Bake gear in oven | Starts Auto Bake, polls for claimable every 2s while baking |

## Loop behaviour

- Runs continuously — each tick: safety back tap → screenshot → orange check → OCR → handler
- Claimable quests (orange card): claimed immediately, `back + quest_tap` to load next
- Repeatable quests overlay: detected and claimed as a global interrupt
- Better-item popup: detected via template match, dismissed, 30s wait for game to settle
- Unknown OCR reads: retried immediately (no sleep)
- During bake: orange checked every 2s without interrupting auto-bake
