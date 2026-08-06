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
    return bool(ratio >= threshold)


def find_template(
    img: np.ndarray,
    template_path: str,
    threshold: float = config.TEMPLATE_THRESHOLD,
) -> tuple[int, int] | None:
    template = cv2.imread(template_path)
    if template is None:
        raise FileNotFoundError(f"Template not found: {template_path}")
    result = cv2.matchTemplate(img, template, cv2.TM_CCORR_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < threshold:
        return None
    th, tw = template.shape[:2]
    return (max_loc[0] + tw // 2, max_loc[1] + th // 2)
