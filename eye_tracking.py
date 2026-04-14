"""
Face / eye landmarks (OpenCV Facemark LBF, 68 points — compatible with prior dlib indices).

Place `lbfmodel.yaml` next to this file or in the working directory (see download_lbf_model.py).
"""
from __future__ import annotations

import os
from math import hypot

import cv2
import numpy as np

try:
    import cv2.face  # noqa: F401 — opencv-contrib
except ImportError as e:
    raise ImportError(
        "Install opencv-contrib-python (includes cv2.face). "
        "Example: pip install opencv-contrib-python"
    ) from e


def _default_lbf_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("lbfmodel.yaml",):
        p = os.path.join(here, name)
        if os.path.isfile(p):
            return p
        p = os.path.join(os.getcwd(), name)
        if os.path.isfile(p):
            return p
    return os.path.join(here, "lbfmodel.yaml")


class Landmarks:
    """dlib-like .part(i) access for 68-point numpy coordinates."""

    __slots__ = ("_pts",)

    def __init__(self, pts: np.ndarray):
        self._pts = pts.astype(np.float64)

    def part(self, n: int):
        class P:
            pass

        p = P()
        p.x = int(round(self._pts[n, 0]))
        p.y = int(round(self._pts[n, 1]))
        return p


_cascade: cv2.CascadeClassifier | None = None
_facemark = None


def _ensure_models():
    global _cascade, _facemark
    if _cascade is None:
        cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_alt2.xml")
        _cascade = cv2.CascadeClassifier(cascade_path)
        if _cascade.empty():
            raise RuntimeError(f"Failed to load Haar cascade: {cascade_path}")
    if _facemark is None:
        path = _default_lbf_path()
        if not os.path.isfile(path):
            raise FileNotFoundError(
                f"Missing {path}. Run: python download_lbf_model.py"
            )
        _facemark = cv2.face.createFacemarkLbf()
        _facemark.loadModel(path)
    return _cascade, _facemark


def detector(gray: np.ndarray):
    """Return face bounding boxes as (x, y, w, h) tuples (like dlib rects for this app)."""
    cascade, _ = _ensure_models()
    rects = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(48, 48))
    return [tuple(int(v) for v in r) for r in rects]


def predictor(gray: np.ndarray, rect) -> Landmarks | None:
    """Landmarks for one face rect (x, y, w, h). Returns None if fitting fails."""
    _, facemark = _ensure_models()
    x, y, w, h = rect
    faces = np.array([[x, y, w, h]], dtype=np.int32)
    ok, landmarks = facemark.fit(gray, faces)
    if not ok or not landmarks or len(landmarks) == 0:
        return None
    pts = np.asarray(landmarks[0], dtype=np.float64)
    if pts.ndim == 3:
        pts = pts.reshape(-1, 2)
    if pts.shape[0] < 48:
        return None
    return Landmarks(pts)


def midpoint(p1, p2):
    return int((p1.x + p2.x) / 2), int((p1.y + p2.y) / 2)


def get_blinking_ratio(eye_points, facial_landmarks: Landmarks):
    left_point = (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y)
    right_point = (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y)
    center_top = midpoint(facial_landmarks.part(eye_points[1]), facial_landmarks.part(eye_points[2]))
    center_bottom = midpoint(facial_landmarks.part(eye_points[5]), facial_landmarks.part(eye_points[4]))
    hor_line_length = hypot((left_point[0] - right_point[0]), (left_point[1] - right_point[1]))
    ver_line_length = hypot((center_top[0] - center_bottom[0]), (center_top[1] - center_bottom[1]))
    if ver_line_length == 0:
        return 0.0
    return hor_line_length / ver_line_length


def eyes_contour_points(facial_landmarks: Landmarks):
    left_eye = []
    right_eye = []
    for n in range(36, 42):
        left_eye.append([facial_landmarks.part(n).x, facial_landmarks.part(n).y])
    for n in range(42, 48):
        right_eye.append([facial_landmarks.part(n).x, facial_landmarks.part(n).y])
    left_eye = np.array(left_eye, np.int32)
    right_eye = np.array(right_eye, np.int32)
    return left_eye, right_eye


def get_gaze_ratio(eye_points, facial_landmarks: Landmarks, gray, frame_shape):
    """Iris white balance ratio; needs full grayscale frame and frame (H,W) for mask."""
    height, width = frame_shape[:2]
    left_eye_region = np.array(
        [
            (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y),
            (facial_landmarks.part(eye_points[1]).x, facial_landmarks.part(eye_points[1]).y),
            (facial_landmarks.part(eye_points[2]).x, facial_landmarks.part(eye_points[2]).y),
            (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y),
            (facial_landmarks.part(eye_points[4]).x, facial_landmarks.part(eye_points[4]).y),
            (facial_landmarks.part(eye_points[5]).x, facial_landmarks.part(eye_points[5]).y),
        ],
        np.int32,
    )
    mask = np.zeros((height, width), np.uint8)
    cv2.polylines(mask, [left_eye_region], True, 255, 2)
    cv2.fillPoly(mask, [left_eye_region], 255)
    eye = cv2.bitwise_and(gray, gray, mask=mask)
    min_x = int(np.min(left_eye_region[:, 0]))
    max_x = int(np.max(left_eye_region[:, 0]))
    min_y = int(np.min(left_eye_region[:, 1]))
    max_y = int(np.max(left_eye_region[:, 1]))
    if max_y <= min_y or max_x <= min_x:
        return 1.0
    gray_eye = eye[min_y:max_y, min_x:max_x]
    _, threshold_eye = cv2.threshold(gray_eye, 70, 255, cv2.THRESH_BINARY)
    h, w = threshold_eye.shape
    if w < 2:
        return 1.0
    left_side_threshold = threshold_eye[0:h, 0 : int(w / 2)]
    left_side_white = cv2.countNonZero(left_side_threshold)
    right_side_threshold = threshold_eye[0:h, int(w / 2) : w]
    right_side_white = cv2.countNonZero(right_side_threshold)
    if left_side_white == 0:
        return 1.0
    if right_side_white == 0:
        return 5.0
    return left_side_white / right_side_white
