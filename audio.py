"""Cross-platform short WAV playback (Windows winsound, Kivy elsewhere)."""
from __future__ import annotations

import os


def play_sound(name: str) -> None:
    if not name or not os.path.isfile(name):
        return
    try:
        import winsound

        winsound.PlaySound(name, winsound.SND_FILENAME | winsound.SND_ASYNC)
        return
    except ImportError:
        pass
    except Exception:
        return
    try:
        from kivy.core.audio import SoundLoader

        s = SoundLoader.load(name)
        if s:
            s.play()
    except Exception:
        pass
