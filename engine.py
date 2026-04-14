"""
One frame of the eye-control UI: processes a BGR camera frame and returns the composed screen.
Shared by desktop (OpenCV window) and Android (Kivy texture).
"""
from __future__ import annotations

import time

import cv2
import numpy as np
import i18n

import eye_tracking as et
from audio import play_sound
from keyboard_ui import (
    KeyboardState,
    advance_scan,
    draw_keyboard,
    on_confirm_key,
    CONFIRM_BACK,
    CONFIRM_ENTER,
    CONFIRM_CLEAR,
    CONFIRM_NORMAL,
)
from shortcuts_ui import (
    CHANGE_POSITION_OPTIONS,
    SHORTCUTS_LIST,
    ShortcutsState,
    advance_shortcuts_dwell,
    draw_mode_selector,
    draw_shortcuts_menu,
)

FONT = cv2.FONT_HERSHEY_PLAIN
BLINK_RATIO_CLOSED = 5.0
FRAMES_TO_BLINK = 6
HOME_BLINKS_REQUIRED = 3
GAZE_KEYBOARD_THRESHOLD = 0.9
GAZE_DWELL_FRAMES = 20
GAZE_MENU_STEPS = 3
INACTIVITY_TIMEOUT = 20.0

APP_W = 1920
APP_H = 1080


def gaze_menu_step(accum: float) -> int:
    if accum <= 0:
        return 1
    seg = GAZE_DWELL_FRAMES / GAZE_MENU_STEPS
    return min(GAZE_MENU_STEPS, int(accum / seg) + 1)


def reset_to_home(
    *,
    program_started,
    language_selected,
    language_selection_frames_L,
    language_selection_frames_R,
    show_home_times,
    eye_closed,
    keyboard_selected,
    selected_keyboard_menu,
    keyboard_selection_frames_L,
    keyboard_selection_frames_R,
    text,
    shortcuts_state,
    keyboard_state,
    blinking_frames,
):
    return dict(
        program_started=False,
        language_selected=False,
        language_selection_frames_L=0.0,
        language_selection_frames_R=0.0,
        show_home_times=0,
        eye_closed=False,
        keyboard_selected="Shortcuts",
        selected_keyboard_menu=True,
        keyboard_selection_frames_L=0.0,
        keyboard_selection_frames_R=0.0,
        text="",
        shortcuts_state=ShortcutsState(),
        keyboard_state=KeyboardState(),
        blinking_frames=0,
        last_activity_time=time.time(),
    )


class EyeControlEngine:
    def __init__(self):
        self.master_screen = np.full((APP_H, APP_W, 3), (245, 245, 245), dtype=np.uint8)
        self.blinking_frames = 0
        self.frames_to_blink = FRAMES_TO_BLINK
        self.program_started = False
        self.language_selected = False
        self.language_selection_frames_L = 0.0
        self.language_selection_frames_R = 0.0
        self.show_home_times = 0
        self.eye_closed = False
        self.keyboard_selected = "Shortcuts"
        self.selected_keyboard_menu = True
        self.keyboard_selection_frames_L = 0.0
        self.keyboard_selection_frames_R = 0.0
        self.text = ""
        self.displayed_keyboard_text = ""
        self.last_confirmed_text = ""
        self.shortcuts_state = ShortcutsState()
        self.keyboard_state = KeyboardState()
        self.last_activity_time = time.time()

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """BGR camera frame in -> BGR UI image out (same fixed size)."""
        ms = self.master_screen
        ms[:] = (245, 245, 245)
        rows, cols, _ = frame.shape
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_display = frame

        if self.program_started and self.selected_keyboard_menu:
            draw_mode_selector(ms, FONT, APP_W, selected=self.keyboard_selected)

        cam_w = 360
        cam_h = int(cam_w * (rows / cols))
        frame_resized = cv2.resize(frame_display, (cam_w, cam_h))
        ms[20 : 20 + cam_h, APP_W - cam_w - 20 : APP_W - 20] = frame_resized
        i18n.draw_rounded_rect(
            ms, (APP_W - cam_w - 22, 18), (APP_W - 18, 20 + cam_h + 2), (200, 200, 200), 4, r=10
        )

        faces = et.detector(gray)

        if self.program_started:
            if time.time() - self.last_activity_time > INACTIVITY_TIMEOUT:
                st = reset_to_home(
                    program_started=self.program_started,
                    language_selected=self.language_selected,
                    language_selection_frames_L=self.language_selection_frames_L,
                    language_selection_frames_R=self.language_selection_frames_R,
                    show_home_times=self.show_home_times,
                    eye_closed=self.eye_closed,
                    keyboard_selected=self.keyboard_selected,
                    selected_keyboard_menu=self.selected_keyboard_menu,
                    keyboard_selection_frames_L=self.keyboard_selection_frames_L,
                    keyboard_selection_frames_R=self.keyboard_selection_frames_R,
                    text=self.text,
                    shortcuts_state=self.shortcuts_state,
                    keyboard_state=self.keyboard_state,
                    blinking_frames=self.blinking_frames,
                )
                self._apply_home_reset(st)
                self.displayed_keyboard_text = ""
                i18n.set_language("en")
                return ms

        if not self.program_started:
            self._draw_home(ms, gray, faces, rows, cols)
            return ms

        if not self.language_selected:
            self._draw_language_select(ms, gray, frame, faces)
            return ms

        self._draw_main(ms, gray, frame, faces)
        return ms

    def _apply_home_reset(self, st):
        self.program_started = st["program_started"]
        self.language_selected = st["language_selected"]
        self.language_selection_frames_L = st["language_selection_frames_L"]
        self.language_selection_frames_R = st["language_selection_frames_R"]
        self.show_home_times = st["show_home_times"]
        self.eye_closed = st["eye_closed"]
        self.keyboard_selected = st["keyboard_selected"]
        self.selected_keyboard_menu = st["selected_keyboard_menu"]
        self.keyboard_selection_frames_L = st["keyboard_selection_frames_L"]
        self.keyboard_selection_frames_R = st["keyboard_selection_frames_R"]
        self.text = st["text"]
        self.shortcuts_state = st["shortcuts_state"]
        self.keyboard_state = st["keyboard_state"]
        self.blinking_frames = st["blinking_frames"]
        self.last_activity_time = st["last_activity_time"]

    def _draw_home(self, master_screen, gray, faces, rows, cols):
        cx = APP_W // 2
        title_text = "Eye Blink Keyboard | لوحة مفاتيح العين"
        i18n.put_text(master_screen, title_text, (cx, 150), 2.0, (30, 30, 30), 4, center=True)
        hint_line_1 = "To start the program | لبدء البرنامج"
        hint_line_2 = "Close your eyes fully, then open. | أغلق عينيك بالكامل، ثم افتحهما."
        hint_line_3 = f"Repeat {HOME_BLINKS_REQUIRED} times | كرر {HOME_BLINKS_REQUIRED} مرات"
        i18n.put_text(master_screen, hint_line_1, (cx, 300), 1.2, (30, 30, 30), 2, center=True)
        i18n.put_text(master_screen, hint_line_2, (cx, 380), 1.2, (30, 30, 30), 2, center=True)
        i18n.put_text(master_screen, hint_line_3, (cx, 460), 1.2, (30, 30, 30), 2, center=True)
        counter_text = f"{self.show_home_times}/{HOME_BLINKS_REQUIRED}"
        i18n.put_text(master_screen, counter_text, (cx, 600), 2.5, (150, 255, 100), 4, center=True)

        for face in faces:
            landmarks = et.predictor(gray, face)
            if landmarks is None:
                continue
            left_eye_ratio = et.get_blinking_ratio([36, 37, 38, 39, 40, 41], landmarks)
            right_eye_ratio = et.get_blinking_ratio([42, 43, 44, 45, 46, 47], landmarks)
            blinking_ratio = (left_eye_ratio + right_eye_ratio) / 2

            if blinking_ratio > BLINK_RATIO_CLOSED:
                self.blinking_frames += 1
                if self.blinking_frames >= self.frames_to_blink:
                    self.eye_closed = True
            else:
                if self.eye_closed:
                    self.show_home_times += 1
                self.eye_closed = False
                self.blinking_frames = 0
            if self.show_home_times >= HOME_BLINKS_REQUIRED:
                self.program_started = True
                self.blinking_frames = 0
                self.keyboard_selection_frames_L = 0.0
                self.keyboard_selection_frames_R = 0.0
                self.last_activity_time = time.time()
            break

        percentage_blinking = self.blinking_frames / self.frames_to_blink
        bar_w = 400
        bar_x = cx - bar_w // 2
        bar_y = 680
        bar_h = 30
        i18n.draw_rounded_rect(
            master_screen, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (200, 200, 200), -1, r=15
        )
        if percentage_blinking > 0:
            fill_w = int(bar_w * min(1.0, percentage_blinking))
            if fill_w < 20:
                fill_w = 20
            i18n.draw_rounded_rect(
                master_screen,
                (bar_x, bar_y),
                (bar_x + fill_w, bar_y + bar_h),
                (150, 255, 100),
                -1,
                r=15,
            )

    def _draw_language_select(self, master_screen, gray, frame, faces):
        cx = APP_W // 2
        title = "Choose Language | اختر اللغة"
        hint_en = "Look Right for English"
        hint_ar = "انظر لليسار للغة العربية"
        i18n.put_text(master_screen, title, (cx, 150), 2.0, (30, 30, 30), 4, center=True)

        is_looking_right = self.language_selection_frames_R > 0
        is_looking_left = self.language_selection_frames_L > 0

        if is_looking_left:
            i18n.draw_rounded_rect(master_screen, (100, 300), (cx - 50, 600), (255, 150, 100), -1, r=30)
            i18n.draw_rounded_rect(master_screen, (100, 300), (cx - 50, 600), (220, 100, 50), 5, r=30)
        else:
            i18n.draw_rounded_rect(master_screen, (100, 300), (cx - 50, 600), (250, 220, 200), -1, r=30)
            i18n.draw_rounded_rect(master_screen, (100, 300), (cx - 50, 600), (255, 150, 100), 3, r=30)
        i18n.put_text(master_screen, hint_ar, (100 + (cx - 150) // 2, 450), 1.5, (30, 30, 30), 3, center=True)

        if is_looking_right:
            i18n.draw_rounded_rect(master_screen, (cx + 50, 300), (APP_W - 100, 600), (150, 255, 100), -1, r=30)
            i18n.draw_rounded_rect(master_screen, (cx + 50, 300), (APP_W - 100, 600), (100, 200, 50), 5, r=30)
        else:
            i18n.draw_rounded_rect(master_screen, (cx + 50, 300), (APP_W - 100, 600), (210, 250, 200), -1, r=30)
            i18n.draw_rounded_rect(master_screen, (cx + 50, 300), (APP_W - 100, 600), (150, 255, 100), 3, r=30)
        i18n.put_text(
            master_screen, hint_en, (cx + 50 + (cx - 150) // 2, 450), 1.5, (30, 30, 30), 3, center=True
        )

        for face in faces:
            landmarks = et.predictor(gray, face)
            if landmarks is None:
                continue
            gaze_ratio_left = et.get_gaze_ratio([36, 37, 38, 39, 40, 41], landmarks, gray, frame.shape)
            gaze_ratio_right = et.get_gaze_ratio([42, 43, 44, 45, 46, 47], landmarks, gray, frame.shape)
            gaze_ratio = (gaze_ratio_right + gaze_ratio_left) / 2

            if gaze_ratio <= GAZE_KEYBOARD_THRESHOLD:
                self.language_selection_frames_R += 0.25
                self.language_selection_frames_L = 0.0
                step = gaze_menu_step(self.language_selection_frames_R)
                i18n.put_text(
                    master_screen,
                    i18n.tr("Right %d/%d") % (step, GAZE_MENU_STEPS),
                    (cx + 50 + (cx - 150) // 2, 530),
                    1.5,
                    (30, 30, 30),
                    3,
                    center=True,
                )
                if self.language_selection_frames_R >= GAZE_DWELL_FRAMES:
                    i18n.set_language("en")
                    self.language_selected = True
                    self.last_activity_time = time.time()
                    play_sound("sound.wav")
            else:
                self.language_selection_frames_L += 0.25
                self.language_selection_frames_R = 0.0
                step = gaze_menu_step(self.language_selection_frames_L)
                i18n.put_text(
                    master_screen,
                    i18n.tr("Left %d/%d") % (step, GAZE_MENU_STEPS),
                    (100 + (cx - 150) // 2, 530),
                    1.5,
                    (30, 30, 30),
                    3,
                    center=True,
                )
                if self.language_selection_frames_L >= GAZE_DWELL_FRAMES:
                    i18n.set_language("ar")
                    self.language_selected = True
                    self.last_activity_time = time.time()
                    play_sound("sound.wav")
            break

    def _draw_main(self, master_screen, gray, frame, faces):
        for face in faces:
            landmarks = et.predictor(gray, face)
            if landmarks is None:
                continue

            left_eye_ratio = et.get_blinking_ratio([36, 37, 38, 39, 40, 41], landmarks)
            right_eye_ratio = et.get_blinking_ratio([42, 43, 44, 45, 46, 47], landmarks)
            blinking_ratio = (left_eye_ratio + right_eye_ratio) / 2

            gaze_ratio_left = et.get_gaze_ratio([36, 37, 38, 39, 40, 41], landmarks, gray, frame.shape)
            gaze_ratio_right = et.get_gaze_ratio([42, 43, 44, 45, 46, 47], landmarks, gray, frame.shape)
            gaze_ratio = (gaze_ratio_right + gaze_ratio_left) / 2

            if self.selected_keyboard_menu:
                if gaze_ratio <= GAZE_KEYBOARD_THRESHOLD:
                    self.keyboard_selected = "Keyboard"
                    self.keyboard_selection_frames_L = 0.0
                    self.keyboard_selection_frames_R += 0.25
                    step_r = gaze_menu_step(self.keyboard_selection_frames_R)
                    i18n.put_text(
                        master_screen,
                        i18n.tr("Right %d/%d") % (step_r, GAZE_MENU_STEPS),
                        (APP_W // 2 + 200, 500),
                        2.0,
                        (30, 30, 30),
                        3,
                        center=True,
                    )
                    if self.keyboard_selection_frames_R >= GAZE_DWELL_FRAMES:
                        self.selected_keyboard_menu = False
                        self.last_activity_time = time.time()
                        play_sound("keyboard.wav")
                        self.keyboard_selection_frames_R = 0.0
                else:
                    self.keyboard_selected = "Shortcuts"
                    self.keyboard_selection_frames_R = 0.0
                    self.keyboard_selection_frames_L += 0.25
                    step_l = gaze_menu_step(self.keyboard_selection_frames_L)
                    i18n.put_text(
                        master_screen,
                        i18n.tr("Left %d/%d") % (step_l, GAZE_MENU_STEPS),
                        (APP_W // 2 - 200, 500),
                        2.0,
                        (30, 30, 30),
                        3,
                        center=True,
                    )
                    if self.keyboard_selection_frames_L >= GAZE_DWELL_FRAMES:
                        self.selected_keyboard_menu = False
                        self.last_activity_time = time.time()
                        play_sound("shortcut.wav")
                        self.keyboard_selection_frames_L = 0.0
            else:
                if blinking_ratio > BLINK_RATIO_CLOSED:
                    self.blinking_frames += 1
                    if self.blinking_frames >= self.frames_to_blink:
                        self.eye_closed = True
                else:
                    if self.eye_closed:
                        self.last_activity_time = time.time()
                        if self.keyboard_selected == "Shortcuts":
                            if self.shortcuts_state.left_menu_state == "main":
                                active_option = SHORTCUTS_LIST[self.shortcuts_state.current_index]
                                if active_option == "Change Position":
                                    self.shortcuts_state.left_menu_state = "sub"
                                    self.shortcuts_state.current_index = 0
                                    self.shortcuts_state.frame_count = 0
                                else:
                                    self.text = "[" + i18n.tr(active_option) + "] "
                                    self.last_confirmed_text = self.text
                                    self.keyboard_selection_frames_L = 0.0
                                    self.keyboard_selection_frames_R = 0.0
                                    self.selected_keyboard_menu = True
                            elif self.shortcuts_state.left_menu_state == "sub":
                                active_option = CHANGE_POSITION_OPTIONS[self.shortcuts_state.current_index]
                                self.keyboard_selection_frames_L = 0.0
                                self.keyboard_selection_frames_R = 0.0
                                self.text = "[" + i18n.tr("Position: ") + i18n.tr(active_option) + "] "
                                self.last_confirmed_text = self.text
                                self.selected_keyboard_menu = True
                                self.shortcuts_state.left_menu_state = "main"
                                self.shortcuts_state.current_index = 0
                                self.shortcuts_state.frame_count = 0

                            if active_option in ("Emergency", i18n.tr("Emergency")):
                                play_sound("alert.wav")
                            else:
                                play_sound("bell-notification.wav")

                        elif self.keyboard_selected == "Keyboard":
                            result = on_confirm_key(self.keyboard_state)
                            if result == CONFIRM_BACK:
                                self.selected_keyboard_menu = True
                                self.keyboard_state.typed_text = ""
                                self.keyboard_state.scan_mode = "row"
                                self.keyboard_state.row_index = 0
                                self.keyboard_state.col_index = 0
                                self.keyboard_selection_frames_L = 0.0
                                self.keyboard_selection_frames_R = 0.0
                            elif result == CONFIRM_ENTER:
                                self.displayed_keyboard_text = self.keyboard_state.displayed_text
                                self.last_confirmed_text = self.displayed_keyboard_text
                                play_sound("bell-notification.wav")
                            elif result == CONFIRM_CLEAR:
                                self.keyboard_state.typed_text = ""
                                self.keyboard_state.displayed_text = ""
                                self.displayed_keyboard_text = ""
                                self.last_confirmed_text = ""
                                play_sound("sound.wav")
                            else:
                                play_sound("sound.wav")
                    self.eye_closed = False
                    self.blinking_frames = 0

                self.last_activity_time = time.time()
            break

        is_blinking = (self.blinking_frames > 0) or self.eye_closed

        if self.program_started and not self.selected_keyboard_menu and self.keyboard_selected == "Shortcuts":
            draw_shortcuts_menu(master_screen, self.shortcuts_state)
            advance_shortcuts_dwell(self.shortcuts_state, is_blinking)

        if self.program_started and not self.selected_keyboard_menu and self.keyboard_selected == "Keyboard":
            draw_keyboard(
                master_screen, self.keyboard_state, origin_x=(APP_W - 700) // 2, origin_y=350
            )
            advance_scan(self.keyboard_state, paused=is_blinking)

        if self.program_started:
            txt_y = APP_H - 110
            i18n.draw_rounded_rect(master_screen, (50, txt_y), (APP_W - 50, APP_H - 20), (200, 200, 200), -1, r=15)
            i18n.draw_rounded_rect(master_screen, (50, txt_y), (APP_W - 50, APP_H - 20), (30, 30, 30), 2, r=15)

            if self.last_confirmed_text:
                i18n.put_text(
                    master_screen, self.last_confirmed_text, (APP_W // 2, txt_y + 35), 1.5, (30, 30, 30), 3, center=True
                )

            if (
                not self.selected_keyboard_menu
                and self.keyboard_selected == "Keyboard"
                and self.keyboard_state.typed_text
            ):
                preview_label = "[ " + self.keyboard_state.typed_text + " ]"
                i18n.put_text(
                    master_screen, preview_label, (APP_W // 2, txt_y + 72), 1.0, (100, 100, 100), 2, center=True
                )

        percentage_blinking = self.blinking_frames / self.frames_to_blink
        if self.program_started and percentage_blinking > 0:
            bar_w = 400
            bar_x = (APP_W - bar_w) // 2
            bar_y = 50
            bar_h = 20
            i18n.draw_rounded_rect(
                master_screen, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (200, 200, 200), -1, r=10
            )
            fill_w = int(bar_w * min(1.0, percentage_blinking))
            if fill_w < 15:
                fill_w = 15
            i18n.draw_rounded_rect(
                master_screen, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), (150, 255, 100), -1, r=10
            )
