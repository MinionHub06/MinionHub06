from __future__ import annotations

import argparse
import base64
from pathlib import Path

import cv2
import numpy as np

RAMP = " .`:-=+*cs#%@"
COLS = 90
FONT_SIZE = 12.9
CHAR_W = FONT_SIZE * 0.6
ROW_H = 15.5
DISPLAY_W = 460
FG = "#242424"


def remove_background(img: np.ndarray) -> np.ndarray:
    """Return a white-background image.

    rembg is preferred. A lightweight gray-wall fallback is kept so the
    generator remains usable when the rembg model is not installed locally.
    """
    try:
        from rembg import remove  # type: ignore

        rgba = remove(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        rgba = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)
        alpha = rgba[:, :, 3]
        white = np.full_like(img, 255)
        a = (alpha.astype(np.float32) / 255.0)[..., None]
        return (img * a + white * (1 - a)).astype(np.uint8)
    except Exception:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        _, s, v = cv2.split(hsv)
        bg = ((s < 28) & (v > 85) & (v < 190)).astype(np.uint8) * 255
        bg[:105, :] = 255
        bg = cv2.morphologyEx(bg, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        bg = cv2.morphologyEx(bg, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
        n, labels, stats, _ = cv2.connectedComponentsWithStats(bg, 8)
        border = np.zeros_like(bg)
        for i in range(1, n):
            x, y, w, h, _ = stats[i]
            if x == 0 or y == 0 or x + w >= img.shape[1] or y + h >= img.shape[0]:
                border[labels == i] = 255
        out = img.copy()
        out[border > 0] = 255
        return out


def make_svg(image: np.ndarray, font_data: str) -> str:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 50, 50)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = np.power(gray.astype(np.float32) / 255.0, 1.7) * 255.0
    gray = np.clip(gray, 0, 255).astype(np.uint8)

    rows = max(1, round(COLS * (gray.shape[0] / gray.shape[1]) * 0.48))
    small = cv2.resize(gray, (COLS, rows), interpolation=cv2.INTER_AREA)
    ramp_idx = np.rint((255 - small) / 255 * (len(RAMP) - 1)).astype(np.int32)
    lines = ["".join(RAMP[i] for i in row) for row in ramp_idx]

    view_w = COLS * CHAR_W
    view_h = rows * ROW_H
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{DISPLAY_W}" viewBox="0 0 {view_w:.2f} {view_h:.2f}" role="img" aria-label="ASCII portrait">',
        '<defs>',
        f'<style>@font-face{{font-family:NotoMono;src:url(data:font/woff2;base64,{font_data}) format("woff2");font-weight:400}} .ascii{{font-family:NotoMono,monospace;font-size:{FONT_SIZE}px;font-weight:400;letter-spacing:0;fill:{FG};white-space:pre}}</style>',
        '</defs>',
    ]

    for i, line in enumerate(lines):
        y = FONT_SIZE + i * ROW_H
        delay = i * 0.09
        safe = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        parts.append(f'<clipPath id="r{i}"><rect x="0" y="{i*ROW_H:.2f}" width="0" height="{ROW_H:.2f}"><animate attributeName="width" from="0" to="{view_w:.2f}" dur="0.72s" begin="{delay:.2f}s" fill="freeze"/></rect></clipPath>')
        parts.append(f'<text x="0" y="{y:.2f}" class="ascii" clip-path="url(#r{i})">{safe}</text>')
        parts.append(f'<rect x="0" y="{i*ROW_H:.2f}" width="{CHAR_W:.2f}" height="{ROW_H:.2f}" fill="{FG}" opacity="0">'
                     f'<animate attributeName="x" from="0" to="{view_w-CHAR_W:.2f}" dur="0.72s" begin="{delay:.2f}s" fill="freeze"/>'
                     f'<animate attributeName="opacity" values="0;0.9;0" keyTimes="0;0.05;1" dur="0.72s" begin="{delay:.2f}s" fill="freeze"/>'
                     '</rect>')

    parts.append('</svg>')
    return "".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="assets/portrait-source.jpg")
    ap.add_argument("--output", default="portrait.svg")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    src = root / args.input
    out = root / args.output
    font = root / "assets/fonts/ramp.woff2"

    img = cv2.imread(str(src))
    if img is None:
        raise SystemExit(f"Could not read {src}")

    # Tight crop for the supplied portrait. Change only if replacing the source image.
    h, w = img.shape[:2]

    if w >= 1400 and h >= 1400:
        x1, x2 = 180, 1260
        y1, y2 = 50, 1300
        img = img[y1:y2, x1:x2]

    img = remove_background(img)
    font_data = base64.b64encode(font.read_bytes()).decode("ascii")
    out.write_text(make_svg(img, font_data), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
