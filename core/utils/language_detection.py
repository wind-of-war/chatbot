import re
import unicodedata

from langdetect import detect

VI_MARKERS = [
    "nhiet do",
    "thuoc",
    "kho",
    "quy dinh",
    "bao quan",
    "duoc",
    "kiem soat",
    "van chuyen",
    "vi sinh",
    "tieu phan",
    "phong sach",
]


def _ascii_lower(text: str) -> str:
    lowered = text.lower().replace("\u0111", "d")
    normalized = unicodedata.normalize("NFD", lowered)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", without_marks).strip()


def detect_language(text: str) -> str:
    plain = _ascii_lower(text)
    if any(marker in plain for marker in VI_MARKERS):
        return "vi"

    try:
        detected = detect(text)
        return "vi" if detected.startswith("vi") else "en"
    except Exception:
        return "en"
