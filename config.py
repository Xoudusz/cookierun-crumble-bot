# --- ADB ---
MUMU_ADB_HOST = "127.0.0.1"
MUMU_ADB_PORT = 7555

# --- Timings ---
CHECK_INTERVAL = 5       # seconds between main loop ticks
NAV_WAIT            = 0.2   # seconds after each tap (most transitions <0.1s)
CLAIM_WAIT          = 0.4   # seconds after tapping claim (animation clears ~0.3s)
POPUP_FADE_WAIT     = 0.5   # seconds after dismissing chest reward popup (0.4s fade + 0.1)
GACHA_RESULT_WAIT   = 0.8   # seconds after first back to cancel gacha anim (0.7s flip + 0.1)
BETTER_ITEM_WAIT    = 30    # seconds to wait after dismissing better-item popup (game transitions)
BAKE_POLL_INTERVAL  = 2     # seconds between orange checks during auto-bake
BAKE_POLL_TIMEOUT   = 10    # seconds before giving up poll and letting main loop handle popups

# --- Screen ---
SCREEN_W = 1080
SCREEN_H = 1920

# --- HSV yellow detection ---
YELLOW_H_LO = 8    # expanded to catch orange (claimable quest glow)
YELLOW_H_HI = 35
YELLOW_S_MIN = 160  # raised from 140 — filters less-saturated ambient UI orange
YELLOW_V_MIN = 140
YELLOW_RATIO = 0.20  # claimable glow covers large area; raised from 0.15 to reduce false positives on orangy stages

# --- Template confidence ---
TEMPLATE_THRESHOLD = 0.95

# --- Regions (x, y, w, h) ---
QUEST_CARD_REGION  = (575, 1048, 490, 107)
QUEST_TEXT_REGION  = (600, 1048, 470, 107)
REPEATABLE_REGION  = (575, 1048, 490, 107)  # same spot as quest card; verify when repeatable appears
BETTER_ITEM_REGION = (0, 0, 0, 0)           # not used in code

# --- Tap targets (x, y) ---
CLAIM_BTN           = (820, 1102)
CLAIMED_X_BTN       = (540, 1860)  # X button on the "Claimed!" reward popup
TOP_CENTER_DISMISS  = (540, 50)    # tap to close better-item popup

NAV = {
    "quest_tap":     (820, 1101),   # tap quest card — universal shortcut to relevant screen
    "select_chest":  (200, 1150),   # tap chest item to select it
    "use_chest_btn": (550, 850),    # "Use" button in popup after selecting chest
    "oven":          (380, 1720),   # oven button on main screen
    "back":          (540, 1860),   # X button to close any panel
    "pull_x10":      (550, 1550),   # x10 pull button on gacha screen
    "start_bake_btn":(680, 1700),   # orange confirm button — same coords for start + up to 2 organize overlays
}

