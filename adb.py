import random
import subprocess
import time
import numpy as np
import cv2

_TAP_JITTER = 4   # pixels — uniform random offset applied to every tap


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
        if result.returncode != 0:
            raise RuntimeError(f"Screenshot failed: returncode {result.returncode}")
        img = cv2.imdecode(np.frombuffer(result.stdout, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError("Screenshot returned empty image")
        return img

    def tap(self, x: int, y: int) -> None:
        jx = x + random.randint(-_TAP_JITTER, _TAP_JITTER)
        jy = y + random.randint(-_TAP_JITTER, _TAP_JITTER)
        result = subprocess.run(
            ["adb", "-s", self._device, "shell", "input", "tap", str(jx), str(jy)],
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Tap failed: returncode {result.returncode}")

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds * random.uniform(0.9, 1.1))
