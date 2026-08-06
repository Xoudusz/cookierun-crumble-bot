import pytesseract

# --- ADB ---
MUMU_ADB_HOST = "127.0.0.1"
MUMU_ADB_PORT = 7555

# --- Timings ---
CHECK_INTERVAL = 5       # seconds between main loop ticks
NAV_WAIT       = 0.8     # seconds after each tap before screenshot
CLAIM_WAIT     = 0.6     # seconds after tapping claim before dismissing popup

# --- Screen ---
SCREEN_W = 1080
SCREEN_H = 1920

# --- HSV yellow detection ---
YELLOW_H_LO = 20
YELLOW_H_HI = 35
YELLOW_S_MIN = 150
YELLOW_V_MIN = 150
YELLOW_RATIO = 0.30      # fraction of region pixels that must be yellow

# --- Template confidence ---
TEMPLATE_THRESHOLD = 0.95

# --- Regions (x, y, w, h) ---
QUEST_CARD_REGION  = (575, 1048, 490, 107)
QUEST_TEXT_REGION  = (660, 1053, 400, 100)
REPEATABLE_REGION  = (575, 1048, 490, 107)  # same spot as quest card; verify when repeatable appears
BETTER_ITEM_REGION = (0, 0, 0, 0)           # not used in code

# --- Tap targets (x, y) ---
CLAIM_BTN           = (820, 1102)
CLAIMED_X_BTN       = (540, 1860)  # X button on the "Claimed!" reward popup
TOP_CENTER_DISMISS  = (540, 50)    # tap to close better-item popup

NAV = {
    "gacha_nav":     (980, 1835),   # Gacha icon in bottom nav bar
    "pet_gacha":     (810, 1637),   # "► Pet Gacha ◄" tab
    "cookie_gacha":  (270, 1637),   # "► Cookie Gacha ◄" tab
    "inventory":     (820, 1101),   # tap quest card — shortcut navigates to relevant screen
    "select_chest":  (200, 1150),   # tap chest item to select it
    "use_chest_btn": (550, 850),    # "Use" button in popup after selecting chest
    "oven":          (380, 1720),   # oven button on main screen
    "back":          (540, 1860),   # X button to close any panel
    "pull_x10":      (365, 1550),   # x10 pull button on gacha screen
    "start_bake_btn":(500, 1630),   # "Start" button on Auto Bake screen
}

# --- Tesseract ---
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
