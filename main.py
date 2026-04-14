"""
Application entry: on Android (Kivy bootstrap) runs the touch UI; on PC runs the OpenCV desktop app.

Requires: `lbfmodel.yaml` (run `python download_lbf_model.py`), optional `.wav` sounds in CWD.
"""
from __future__ import annotations

import os


def _running_on_android() -> bool:
    return "ANDROID_ARGUMENT" in os.environ


if __name__ == "__main__":
    if _running_on_android():
        from android_main import EyeControlApp

        EyeControlApp().run()
    else:
        import desktop_main

        desktop_main.main()
