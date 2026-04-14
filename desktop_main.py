"""
Desktop: OpenCV window. Run: python main.py (same folder so assets resolve).

Requires: `lbfmodel.yaml` (run `python download_lbf_model.py`), optional `.wav` sounds in CWD.
"""
from __future__ import annotations

import cv2

from engine import APP_H, APP_W, EyeControlEngine


def main():
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("Eye Control System", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Eye Control System", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.resizeWindow("Eye Control System", APP_W, APP_H)

    engine = EyeControlEngine()

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        master_screen = engine.process_frame(frame)

        cv2.imshow("Eye Control System", master_screen)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
