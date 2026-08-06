# Cookie Run: Crumble Quest Bot — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Python script that connects to MuMu Player v6 via ADB and automates Cookie Run: Crumble daily quest completion with zero manual interaction.

**Architecture:** A polling main loop screenshots the game every 5 seconds, detects quest card state via HSV color analysis, OCRs quest text to determine type, and dispatches the appropriate handler. Two global interrupts (better-item popup, repeatable quest overlay) are checked every tick before the main quest logic runs.

**Tech Stack:** Python 3.10+, opencv-python, pytesseract, Pillow, Android platform tools (adb on PATH), pytest, unittest.mock

## Global Constraints

- Target platform: Windows (MuMu Player v6, `adb` must be on PATH)
- Tesseract-OCR must be installed: default path `C:\Program Files\Tesseract-OCR\tesseract.exe`
- MuMu ADB address: `127.0.0.1:7555`
- All coordinates are pixel values at the user's configured MuMu resolution (placeholders until calibration)
- Yellow HSV thresholds: H 20–35, S >150, V >150, pixel ratio >0.30 to count as claimable
- Template match confidence threshold: 0.8
- ADB reconnect: 3 attempts, 5 s apart, then raise `RuntimeError`
- Unknown quest text logged to `unknown_quests.log`

---

## Global Additions

- GitHub repo: `Xoudusz/cookierun-crumble-bot` (private)
- `VERSION` file in repo root, start at `0.1.0`
- `CLAUDE.md` in repo root (Claude instructions)
- `README.md` (Windows setup guide for the user)
- `notes/projects/cookierun-bot.md` (source of truth, push to notes repo)

---

## File Map

| File | Responsibility |
|---|---|
| `requirements.txt` | Pinned dependencies |
| `config.py` | All coordinates, thresholds, timings — edit after calibration |
| `adb.py` | ADB subprocess wrapper: connect, screenshot, tap |
| `detector.py` | OpenCV: HSV yellow check, template match |
| `quests.py` | OCR + keyword dispatch + every quest handler |
| `main.py` | Interrupt checks, main loop, `--calibrate` mode |
| `templates/` | PNG crops used for template matching |
| `tests/test_adb.py` | ADB unit tests (mocked subprocess) |
| `tests/test_detector.py` | Detector unit tests (synthetic images) |
| `tests/test_quests.py` | Dispatch + handler unit tests (mocked ADB) |

---

### Task 0: GitHub repo setup

**Files:**
- Create: `VERSION`
- Create: `.gitignore`

**Interfaces:**
- Produces: remote `origin` at `https://github.com/Xoudusz/cookierun-crumble-bot`; all subsequent tasks push to this remote

- [ ] **Step 1: Create `.gitignore`**

```
__pycache__/
*.pyc
*.pyo
.env
calibration.png
unknown_quests.log
templates/equip_button.png
templates/start_bake_btn.png
.superpowers/
```

- [ ] **Step 2: Create `VERSION` file**

```
0.1.0
```

- [ ] **Step 3: Verify repo exists**

```bash
gh repo view Xoudusz/cookierun-crumble-bot
```

Expected: repo visible (already created by user).

- [ ] **Step 4: Add remote and push**

```bash
git remote add origin https://github.com/Xoudusz/cookierun-crumble-bot.git
git add VERSION .gitignore
git commit -m "chore: initial repo setup"
git push -u origin master
```

- [ ] **Step 5: Verify repo is live**

```bash
gh repo view Xoudusz/cookierun-crumble-bot
```

Expected: shows repo description, private, 1 commit.

---

### Task 1: Scaffold — requirements, config, directory skeleton

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `templates/.gitkeep`
- Create: `tests/__init__.py`

**Interfaces:**
- Produces: `config` module with all constants imported by every other module

- [ ] **Step 1: Create `requirements.txt`**

```
opencv-python>=4.9
pytesseract>=0.3.10
Pillow>=10.0
pytest>=8.0
```

- [ ] **Step 2: Create `config.py`**

```python
import pytesseract

# --- ADB ---
MUMU_ADB_HOST = "127.0.0.1"
MUMU_ADB_PORT = 7555

# --- Timings ---
CHECK_INTERVAL = 5       # seconds between main loop ticks
NAV_WAIT       = 0.8     # seconds after each tap before screenshot
CLAIM_WAIT     = 0.6     # seconds after tapping claim before dismissing popup

# --- Screen ---
SCREEN_W = 720
SCREEN_H = 1280

# --- HSV yellow detection ---
YELLOW_H_LO = 20
YELLOW_H_HI = 35
YELLOW_S_MIN = 150
YELLOW_V_MIN = 150
YELLOW_RATIO = 0.30      # fraction of region pixels that must be yellow

# --- Template confidence ---
TEMPLATE_THRESHOLD = 0.80

# --- Regions (x, y, w, h) — fill after running --calibrate ---
QUEST_CARD_REGION  = (0, 0, 0, 0)
QUEST_TEXT_REGION  = (0, 0, 0, 0)
REPEATABLE_REGION  = (0, 0, 0, 0)
BETTER_ITEM_REGION = (0, 0, 0, 0)

# --- Tap targets (x, y) — fill after running --calibrate ---
CLAIM_BTN           = (0, 0)
CLAIMED_X_BTN       = (0, 0)   # X button on the "Claimed!" reward popup
TOP_CENTER_DISMISS  = (360, 50) # tap to close better-item popup

NAV = {
    "pet_gacha":      (0, 0),
    "cookie_gacha":   (0, 0),
    "inventory":      (0, 0),
    "oven":           (0, 0),
    "back":           (0, 0),
    "pull_x10":       (0, 0),
    "use_chest_btn":  (0, 0),   # "Use" button in chest dialog
    "start_bake_btn": (0, 0),   # "Start" on Auto Bake screen
}

# --- Tesseract ---
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
```

- [ ] **Step 3: Create scaffold files**

```bash
mkdir templates tests
touch templates/.gitkeep tests/__init__.py
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 5: Commit**

```bash
git add requirements.txt config.py templates/.gitkeep tests/__init__.py
git commit -m "feat: project scaffold and config"
```

---

### Task 2: ADB module

**Files:**
- Create: `adb.py`
- Create: `tests/test_adb.py`

**Interfaces:**
- Consumes: `config.MUMU_ADB_HOST`, `config.MUMU_ADB_PORT`
- Produces:
  - `ADB(host: str, port: int)` — constructor
  - `ADB.connect() -> None` — raises `RuntimeError` after 3 failed attempts
  - `ADB.screenshot() -> np.ndarray` — BGR image
  - `ADB.tap(x: int, y: int) -> None`
  - `ADB.sleep(seconds: float) -> None`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_adb.py
import numpy as np
import pytest
from unittest.mock import patch, MagicMock, call
from adb import ADB


def _png_bytes():
    """Minimal valid 1x1 red PNG."""
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), (0, 0, 255)).save(buf, format="PNG")
    return buf.getvalue()


def test_connect_success():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=b"connected")
        adb = ADB("127.0.0.1", 7555)
        adb.connect()
        mock_run.assert_called_once_with(
            ["adb", "connect", "127.0.0.1:7555"],
            capture_output=True,
        )


def test_connect_retries_and_raises():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout=b"error")
        with patch("time.sleep"):
            adb = ADB("127.0.0.1", 7555)
            with pytest.raises(RuntimeError, match="ADB connect failed"):
                adb.connect()
        assert mock_run.call_count == 3


def test_screenshot_returns_ndarray():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=_png_bytes())
        adb = ADB("127.0.0.1", 7555)
        img = adb.screenshot()
        assert isinstance(img, np.ndarray)
        assert img.ndim == 3


def test_tap_sends_correct_command():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        adb = ADB("127.0.0.1", 7555)
        adb.tap(100, 200)
        mock_run.assert_called_once_with(
            ["adb", "-s", "127.0.0.1:7555", "shell", "input", "tap", "100", "200"],
            capture_output=True,
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_adb.py -v
```

Expected: `ImportError: No module named 'adb'`

- [ ] **Step 3: Implement `adb.py`**

```python
import subprocess
import time
import io
import numpy as np
import cv2
from PIL import Image


class ADB:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._device = f"{host}:{port}"

    def connect(self, retries: int = 3, delay: float = 5.0) -> None:
        for attempt in range(retries):
            result = subprocess.run(
                ["adb", "connect", self._device],
                capture_output=True,
            )
            if result.returncode == 0 and b"error" not in result.stdout.lower():
                return
            if attempt < retries - 1:
                time.sleep(delay)
        raise RuntimeError(f"ADB connect failed after {retries} attempts to {self._device}")

    def screenshot(self) -> np.ndarray:
        result = subprocess.run(
            ["adb", "-s", self._device, "exec-out", "screencap", "-p"],
            capture_output=True,
        )
        img = cv2.imdecode(np.frombuffer(result.stdout, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError("Screenshot returned empty image")
        return img

    def tap(self, x: int, y: int) -> None:
        subprocess.run(
            ["adb", "-s", self._device, "shell", "input", "tap", str(x), str(y)],
            capture_output=True,
        )

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_adb.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add adb.py tests/test_adb.py
git commit -m "feat: ADB wrapper with connect, screenshot, tap"
```

---

### Task 3: Detector module

**Files:**
- Create: `detector.py`
- Create: `tests/test_detector.py`

**Interfaces:**
- Consumes: `config.YELLOW_*`, `config.YELLOW_RATIO`, `config.TEMPLATE_THRESHOLD`
- Produces:
  - `is_yellow(img: np.ndarray, region: tuple[int,int,int,int], threshold: float) -> bool`
    - `region` = `(x, y, w, h)` crop of `img` to analyse
  - `find_template(img: np.ndarray, template_path: str, threshold: float) -> tuple[int,int] | None`
    - returns center `(x, y)` of best match, or `None` if below threshold

- [ ] **Step 1: Write failing tests**

```python
# tests/test_detector.py
import numpy as np
import cv2
import pytest
import os
import tempfile
from detector import is_yellow, find_template


def _solid_bgr(h, w, bgr):
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = bgr
    return img


def _yellow_bgr():
    """Solid yellow in BGR (H=30, S=255, V=255 in HSV)."""
    hsv = np.full((50, 50, 3), [30, 255, 255], dtype=np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def _grey_bgr():
    return _solid_bgr(50, 50, (100, 100, 100))


def test_is_yellow_detects_yellow_region():
    canvas = np.zeros((200, 200, 3), dtype=np.uint8)
    yellow = _yellow_bgr()
    canvas[50:100, 50:100] = yellow
    assert is_yellow(canvas, (50, 50, 50, 50)) is True


def test_is_yellow_rejects_grey():
    img = _grey_bgr()
    assert is_yellow(img, (0, 0, 50, 50)) is False


def test_is_yellow_uses_custom_threshold():
    # Image that is 20% yellow — below default 30% threshold
    canvas = np.full((100, 100, 3), [100, 100, 100], dtype=np.uint8)
    canvas[0:20, :] = _yellow_bgr()[0:20, :]
    assert is_yellow(canvas, (0, 0, 100, 100), threshold=0.30) is False
    assert is_yellow(canvas, (0, 0, 100, 100), threshold=0.15) is True


def test_find_template_returns_center_on_match():
    bg = _solid_bgr(200, 200, (50, 50, 50))
    tpl = _solid_bgr(20, 20, (200, 100, 50))
    bg[80:100, 90:110] = tpl
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        cv2.imwrite(f.name, tpl)
        result = find_template(bg, f.name, threshold=0.95)
    os.unlink(f.name)
    assert result is not None
    cx, cy = result
    assert abs(cx - 100) <= 2
    assert abs(cy - 90) <= 2


def test_find_template_returns_none_on_no_match():
    bg = _solid_bgr(200, 200, (50, 50, 50))
    tpl = _solid_bgr(20, 20, (200, 100, 50))
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        cv2.imwrite(f.name, tpl)
        result = find_template(bg, f.name, threshold=0.99)
    os.unlink(f.name)
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_detector.py -v
```

Expected: `ImportError: No module named 'detector'`

- [ ] **Step 3: Implement `detector.py`**

```python
import numpy as np
import cv2
import config


def is_yellow(
    img: np.ndarray,
    region: tuple[int, int, int, int],
    threshold: float = config.YELLOW_RATIO,
) -> bool:
    x, y, w, h = region
    crop = img[y:y+h, x:x+w]
    if crop.size == 0:
        return False
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    lower = np.array([config.YELLOW_H_LO, config.YELLOW_S_MIN, config.YELLOW_V_MIN])
    upper = np.array([config.YELLOW_H_HI, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    ratio = np.count_nonzero(mask) / mask.size
    return ratio >= threshold


def find_template(
    img: np.ndarray,
    template_path: str,
    threshold: float = config.TEMPLATE_THRESHOLD,
) -> tuple[int, int] | None:
    template = cv2.imread(template_path)
    if template is None:
        raise FileNotFoundError(f"Template not found: {template_path}")
    result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < threshold:
        return None
    th, tw = template.shape[:2]
    return (max_loc[0] + tw // 2, max_loc[1] + th // 2)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_detector.py -v
```

Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add detector.py tests/test_detector.py
git commit -m "feat: HSV yellow detector and template matcher"
```

---

### Task 4: Quest OCR and dispatch

**Files:**
- Create: `quests.py` (OCR + dispatch section only — handlers added in Task 5)
- Create: `tests/test_quests.py` (dispatch tests)

**Interfaces:**
- Consumes: `config.QUEST_TEXT_REGION`, pytesseract
- Produces:
  - `ocr_quest_text(img: np.ndarray) -> str` — lowercase stripped text from quest text region
  - `dispatch_quest(text: str) -> str` — returns one of:
    `"pull_pet_gacha"`, `"pull_cookie_gacha"`, `"use_chest"`,
    `"wait_stage"`, `"wait_enemies"`, `"bake_oven"`, `"unknown"`

- [ ] **Step 1: Write failing dispatch tests**

```python
# tests/test_quests.py
import pytest
from unittest.mock import patch, MagicMock
from quests import dispatch_quest


@pytest.mark.parametrize("text,expected", [
    ("pull in the pet gacha 10 times", "pull_pet_gacha"),
    ("Pull in the Pet Gacha 10 times", "pull_pet_gacha"),
    ("pull the cookie gacha 10 times", "pull_cookie_gacha"),
    ("pull the character gacha 10 times", "pull_cookie_gacha"),
    ("use 1 chest from your inventory", "use_chest"),
    ("clear stage 3-4", "wait_stage"),
    ("clear stages 10 times", "wait_stage"),
    ("defeat 100 enemies", "wait_enemies"),
    ("bake gear in the oven 3 times", "bake_oven"),
    ("use the furnace 2 times", "bake_oven"),
    ("something totally unknown", "unknown"),
    ("", "unknown"),
])
def test_dispatch_quest(text, expected):
    assert dispatch_quest(text) == expected
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_quests.py -v
```

Expected: `ImportError: No module named 'quests'`

- [ ] **Step 3: Implement `quests.py` (OCR + dispatch only)**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_quests.py -v
```

Expected: all PASSED (OCR tests skipped — dispatch is pure string logic)

- [ ] **Step 5: Commit**

```bash
git add quests.py tests/test_quests.py
git commit -m "feat: quest OCR and keyword dispatch"
```

---

### Task 5: Quest handlers and claimed popup

**Files:**
- Modify: `quests.py` — add all handler functions
- Modify: `tests/test_quests.py` — add handler tests

**Interfaces:**
- Consumes: `ADB`, `config.NAV`, `config.CLAIM_BTN`, `config.CLAIMED_X_BTN`, `config.CLAIM_WAIT`, `config.NAV_WAIT`, `detector.is_yellow`, `detector.find_template`
- Produces (all in `quests.py`):
  - `claim_quest(adb: ADB) -> None` — tap claim, dismiss popup
  - `dismiss_claimed_popup(adb: ADB) -> None` — tap X on reward popup
  - `pull_pet_gacha(adb: ADB) -> None`
  - `pull_cookie_gacha(adb: ADB) -> None`
  - `use_chest(adb: ADB) -> None`
  - `wait_stage(adb: ADB) -> None` — sleeps CHECK_INTERVAL
  - `wait_enemies(adb: ADB) -> None` — sleeps CHECK_INTERVAL
  - `bake_oven(adb: ADB, get_screenshot: callable[[], np.ndarray], check_interrupts: callable[[np.ndarray, ADB], bool] | None = None) -> None`
  - `HANDLERS: dict[str, callable]` — maps dispatch key to handler function

- [ ] **Step 1: Add handler tests**

Add to `tests/test_quests.py`:

```python
import time
from unittest.mock import patch, MagicMock, call
from quests import (
    claim_quest, dismiss_claimed_popup,
    pull_pet_gacha, pull_cookie_gacha,
    use_chest, wait_stage, bake_oven,
)
import config


def _mock_adb():
    adb = MagicMock()
    adb.sleep = MagicMock()
    adb.tap = MagicMock()
    return adb


def test_dismiss_claimed_popup_taps_x():
    adb = _mock_adb()
    config.CLAIMED_X_BTN = (360, 900)
    dismiss_claimed_popup(adb)
    adb.tap.assert_called_once_with(360, 900)


def test_claim_quest_taps_claim_then_dismisses():
    adb = _mock_adb()
    config.CLAIM_BTN = (600, 100)
    config.CLAIMED_X_BTN = (360, 900)
    config.CLAIM_WAIT = 0
    claim_quest(adb)
    assert adb.tap.call_args_list[0] == call(600, 100)
    assert adb.tap.call_args_list[1] == call(360, 900)


def test_pull_pet_gacha_navigates_and_pulls():
    adb = _mock_adb()
    config.NAV = {
        "pet_gacha": (100, 200),
        "pull_x10":  (300, 600),
        "back":      (50, 50),
    }
    config.NAV_WAIT = 0
    pull_pet_gacha(adb)
    taps = [c.args for c in adb.tap.call_args_list]
    assert (100, 200) in taps  # navigated to pet gacha
    assert (300, 600) in taps  # tapped x10 pull


def test_pull_cookie_gacha_navigates_and_pulls():
    adb = _mock_adb()
    config.NAV = {
        "cookie_gacha": (150, 200),
        "pull_x10":     (300, 600),
        "back":         (50, 50),
    }
    config.NAV_WAIT = 0
    pull_cookie_gacha(adb)
    taps = [c.args for c in adb.tap.call_args_list]
    assert (150, 200) in taps
    assert (300, 600) in taps


def test_use_chest_navigates_and_uses():
    adb = _mock_adb()
    config.NAV = {
        "inventory":     (200, 900),
        "use_chest_btn": (360, 700),
        "back":          (50, 50),
    }
    config.NAV_WAIT = 0
    use_chest(adb)
    taps = [c.args for c in adb.tap.call_args_list]
    assert (200, 900) in taps
    assert (360, 700) in taps


def test_wait_stage_sleeps():
    adb = _mock_adb()
    config.CHECK_INTERVAL = 1
    wait_stage(adb)
    adb.sleep.assert_called_once_with(1)


def test_bake_oven_starts_bake_and_polls_until_done():
    adb = _mock_adb()
    config.NAV = {
        "oven":           (500, 900),
        "start_bake_btn": (360, 800),
        "back":           (50, 50),
    }
    config.NAV_WAIT = 0
    config.CHECK_INTERVAL = 0

    # find_template: first call returns None (baking), second returns position (done)
    with patch("quests.find_template", side_effect=[None, (360, 800)]):
        screenshots = [MagicMock(), MagicMock()]
        call_count = 0
        def fake_screenshot():
            nonlocal call_count
            s = screenshots[min(call_count, len(screenshots)-1)]
            call_count += 1
            return s
        bake_oven(adb, fake_screenshot, check_interrupts=None)

    taps = [c.args for c in adb.tap.call_args_list]
    assert (500, 900) in taps        # navigated to oven
    assert (360, 800) in taps        # tapped Start


def test_bake_oven_calls_check_interrupts_each_poll():
    adb = _mock_adb()
    config.NAV = {
        "oven":           (500, 900),
        "start_bake_btn": (360, 800),
        "back":           (50, 50),
    }
    config.NAV_WAIT = 0
    config.CHECK_INTERVAL = 0
    interrupt_calls = []

    def fake_check(img, a):
        interrupt_calls.append(1)
        return False

    with patch("quests.find_template", side_effect=[None, (360, 800)]):
        bake_oven(adb, MagicMock(), check_interrupts=fake_check)

    assert len(interrupt_calls) >= 1
```

- [ ] **Step 2: Run to verify new tests fail**

```bash
pytest tests/test_quests.py -v -k "not test_dispatch"
```

Expected: `ImportError` or `AttributeError` (functions not yet defined)

- [ ] **Step 3: Add handlers to `quests.py`**

Append to `quests.py` after `dispatch_quest`:

```python
import os
from detector import find_template


def dismiss_claimed_popup(adb: ADB) -> None:
    x, y = config.CLAIMED_X_BTN
    adb.tap(x, y)


def claim_quest(adb: ADB) -> None:
    x, y = config.CLAIM_BTN
    adb.tap(x, y)
    adb.sleep(config.CLAIM_WAIT)
    dismiss_claimed_popup(adb)


def pull_pet_gacha(adb: ADB) -> None:
    adb.tap(*config.NAV["pet_gacha"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["pull_x10"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["back"])
    adb.sleep(config.NAV_WAIT)


def pull_cookie_gacha(adb: ADB) -> None:
    adb.tap(*config.NAV["cookie_gacha"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["pull_x10"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["back"])
    adb.sleep(config.NAV_WAIT)


def use_chest(adb: ADB) -> None:
    adb.tap(*config.NAV["inventory"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["use_chest_btn"])
    adb.sleep(config.NAV_WAIT)
    adb.tap(*config.NAV["back"])
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
```

- [ ] **Step 4: Run all quest tests**

```bash
pytest tests/test_quests.py -v
```

Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
git add quests.py tests/test_quests.py
git commit -m "feat: quest handlers — gacha, chest, stage wait, oven bake"
```

---

### Task 6: Main loop and calibrate mode

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

**Interfaces:**
- Consumes: `ADB`, `detector.is_yellow`, `detector.find_template`, `quests.*`, `config.*`
- Produces:
  - `check_global_interrupts(img: np.ndarray, adb: ADB) -> bool` — True if interrupt was handled
  - `run_calibrate(adb: ADB) -> None` — dumps screenshot + instructions
  - `run_loop(adb: ADB) -> None` — main polling loop (runs until KeyboardInterrupt)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_main.py
import numpy as np
import pytest
from unittest.mock import patch, MagicMock, call
import config
from main import check_global_interrupts


def _black(h=100, w=100):
    return np.zeros((h, w, 3), dtype=np.uint8)


def test_check_global_interrupts_dismisses_better_item():
    adb = MagicMock()
    config.TOP_CENTER_DISMISS = (360, 50)
    with patch("main.find_template", return_value=(200, 300)):
        result = check_global_interrupts(_black(), adb)
    assert result is True
    adb.tap.assert_called_once_with(360, 50)


def test_check_global_interrupts_claims_repeatable():
    adb = MagicMock()
    config.REPEATABLE_REGION = (0, 0, 100, 100)
    config.CLAIM_BTN = (50, 50)
    config.CLAIMED_X_BTN = (50, 90)
    config.CLAIM_WAIT = 0
    with patch("main.find_template", return_value=None):
        with patch("main.is_yellow", return_value=True):
            result = check_global_interrupts(_black(), adb)
    assert result is True


def test_check_global_interrupts_returns_false_when_clear():
    adb = MagicMock()
    config.REPEATABLE_REGION = (0, 0, 100, 100)
    with patch("main.find_template", return_value=None):
        with patch("main.is_yellow", return_value=False):
            result = check_global_interrupts(_black(), adb)
    assert result is False
    adb.tap.assert_not_called()
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_main.py -v
```

Expected: `ImportError: No module named 'main'`

- [ ] **Step 3: Implement `main.py`**

```python
import argparse
import logging
import os
import sys
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
        except RuntimeError as exc:
            logger.error("ADB error: %s — reconnecting", exc)
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
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```

Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: main loop with interrupt handling and calibrate mode"
```

---

### Task 7: Template crops (manual step)

**Files:**
- Create: `templates/equip_button.png`
- Create: `templates/start_bake_btn.png`

This task is manual — no code to write. The bot will not detect the better-item popup or know when the oven finishes until these exist.

- [ ] **Step 1: Generate calibration screenshot**

```bash
python main.py --calibrate
```

Opens `calibration.png`. If the game is on a bake screen or shows the better-item popup, you can crop templates from that.

- [ ] **Step 2: Fill in `config.py` coordinates**

Open `calibration.png` in any image viewer that shows pixel coordinates (Paint, GIMP, etc.).

Measure and fill every `(0, 0, 0, 0)` region and `(0, 0)` tap target in `config.py`.

- [ ] **Step 3: Crop `equip_button.png`**

Navigate to the better-item popup in game → take screenshot → crop a tight region around the blue "Equip" button → save to `templates/equip_button.png`.

Minimum crop: 40×20 px. Include the full button, no surrounding background.

- [ ] **Step 4: Crop `start_bake_btn.png`**

Navigate to the Auto Bake screen → take screenshot → crop the orange "Start" button → save to `templates/start_bake_btn.png`.

- [ ] **Step 5: Verify templates load correctly**

```python
# run in a Python shell from the project directory
import cv2
tpl = cv2.imread("templates/equip_button.png")
assert tpl is not None, "equip_button.png missing or unreadable"
tpl = cv2.imread("templates/start_bake_btn.png")
assert tpl is not None, "start_bake_btn.png missing or unreadable"
print("Templates OK")
```

- [ ] **Step 6: Smoke test the bot**

```bash
python main.py
```

Watch the log. Confirm it:
- Connects to MuMu
- Prints quest type each tick
- Claims when quest turns yellow
- Dismisses "Claimed!" popup

- [ ] **Step 7: Commit**

```bash
git add templates/ config.py
git commit -m "chore: calibrated coordinates and template crops"
```

---

### Task 8: Documentation

**Files:**
- Create: `CLAUDE.md` (in repo root)
- Create/update: `README.md`
- Create: `/root/projects/notes/projects/cookierun-bot.md`

**Interfaces:**
- Consumes: completed codebase from Tasks 0–7
- Produces: user-facing setup guide, Claude instructions, notes source-of-truth

- [ ] **Step 1: Create `CLAUDE.md` in repo root**

```markdown
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
```

- [ ] **Step 2: Create `README.md`**

```markdown
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
```

- [ ] **Step 3: Create notes source-of-truth**

Create `/root/projects/notes/projects/cookierun-bot.md`:

```markdown
---
project: cookierun-bot
version: 0.1.0
repo: https://github.com/Xoudusz/cookierun-crumble-bot
status: active
---

# Cookie Run: Crumble Quest Bot

Windows Python bot that automates Cookie Run: Crumble daily quests via ADB to MuMu Player v6.

## Stack

- Python 3.10+, opencv-python, pytesseract, Pillow
- ADB (Android platform tools) → MuMu Player v6 at `127.0.0.1:7555`
- OpenCV HSV color detection for quest card state (yellow = claimable)
- pytesseract OCR for quest text → keyword dispatch

## Architecture

```
main loop (5s tick)
  → check_global_interrupts (better-item popup, repeatable overlay)
  → detect quest card state (HSV yellow)
    → if claimable: tap claim → dismiss reward popup
    → if not: OCR text → dispatch to handler
        handlers: pull_pet_gacha, pull_cookie_gacha, use_chest,
                  wait_stage, wait_enemies, bake_oven
```

## Key files

| File | Role |
|---|---|
| `config.py` | All coordinates + thresholds — fill after `--calibrate` |
| `detector.py` | `is_yellow(img, region)` + `find_template(img, path)` |
| `quests.py` | `dispatch_quest(text)` + all handlers |
| `main.py` | `check_global_interrupts` + main loop |
| `templates/` | `equip_button.png`, `start_bake_btn.png` (not committed) |

## Setup

1. Install MuMu Player v6, ADB platform tools, Tesseract-OCR
2. `pip install -r requirements.txt`
3. `python main.py --calibrate` → measure coords in `calibration.png` → fill `config.py`
4. Crop template PNGs from game screenshots
5. `python main.py`

## Roadmap

### Done ✅
- v0.1.0 — Initial implementation: all quest types, global interrupts, calibrate mode
```

- [ ] **Step 4: Commit docs to repo and push**

```bash
cd /root/projects/cookierun-bot
git add CLAUDE.md README.md
git commit -m "docs: add CLAUDE.md and README with Windows setup guide"
git push
```

- [ ] **Step 5: Push notes**

```bash
cd /root/projects/notes
git add projects/cookierun-bot.md
git commit -m "cookierun-bot v0.1.0: initial quest automation bot"
git push
```
