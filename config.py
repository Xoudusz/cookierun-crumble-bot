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
