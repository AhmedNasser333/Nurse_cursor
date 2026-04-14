"""
Kivy entry point for Android APK (Buildozer). Desktop: use main.py + OpenCV window.
"""
from __future__ import annotations

import cv2
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivy.utils import platform

from engine import APP_H, APP_W, EyeControlEngine


def _open_camera():
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        return cap
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_ANDROID)
    except Exception:
        pass
    return cap


class EyeControlApp(App):
    def build(self):
        if platform == "android":
            from android.permissions import Permission, request_permissions

            request_permissions([Permission.CAMERA])

        self.engine = EyeControlEngine()
        self.cap = None
        self.img = Image(allow_stretch=True, keep_ratio=False)
        self.texture = Texture.create(size=(APP_W, APP_H), colorfmt="bgr")
        self.img.texture = self.texture
        Window.clearcolor = (0.94, 0.94, 0.94, 1)
        Clock.schedule_once(self._start_camera, 0.5)
        Clock.schedule_interval(self._update, 1.0 / 30.0)
        return self.img

    def _start_camera(self, _dt):
        self.cap = _open_camera()

    def _update(self, _dt):
        if self.cap is None or not self.cap.isOpened():
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        screen = self.engine.process_frame(frame)
        # Kivy texture origin is bottom-left; OpenCV is top-left
        buf = cv2.flip(screen, 0).tobytes()
        self.texture.blit_buffer(buf, colorfmt="bgr", bufferfmt="ubyte")


if __name__ == "__main__":
    EyeControlApp().run()
