from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

SRC = Path("source-prepped.png")
OUT = Path("ascii-portrait.svg")

THEME = "light"             # "light" = dark text on a light card, "dark" = light text on a dark card
COLS = 110                  # characters per row; more = more detail
RAMP = " .`:-=+*cs#%@"      # blank -> light -> dense
FLOOR = 2                   # (dark theme only) darkest part of the subject still prints at this level
GAMMA = 1.0                 # below 1 = bolder, above 1 = softer
CROP_X = (0.17, 0.83)       # keep this slice of the width (left, right)
CROP_BOTTOM = 0.74          # keep the top 74% of the height (head + collar)
FONT_SIZE = 8
CW = FONT_SIZE * 0.6        # character width
LH = FONT_SIZE * 1.2        # line height
PAD = 12
FILL = "#c9d1d9" if THEME == "dark" else "#24292f"
BG = "#0d1117" if THEME == "dark" else "#f6f8fa"
ROW_DELAY = 0.04            # stagger between rows (seconds)
ROW_DUR = 0.7               # time for one row to type out


def image_to_rows():
    img = Image.open(SRC).convert("L")
    w, h = img.size
    img = img.crop((int(w * CROP_X[0]), 0, int(w * CROP_X[1]), int(h * CROP_BOTTOM)))
    w, h = img.size
    cols = COLS
    rows = max(1, round(cols * (h / w) * (CW / LH)))

    full = np.asarray(img, dtype=float) / 255.0
    # background = near-white pixels connected to the image border
    lab, _ = ndimage.label(full > 0.97)
    edge = np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    bg = np.isin(lab, [v for v in np.unique(edge) if v != 0])
    bg = ndimage.binary_erosion(bg, iterations=1)
    bg_small = Image.fromarray((bg * 255).astype(np.uint8)).resize(
        (cols, rows), Image.Resampling.BILINEAR
    )
    bg_small = np.asarray(bg_small, dtype=float) / 255.0 > 0.5

    px = np.asarray(img.resize((cols, rows), Image.Resampling.LANCZOS), dtype=float) / 255.0
    fg = ~bg_small
    lo, hi = np.percentile(px[fg], [3, 97])
    n = np.clip((px - lo) / (hi - lo), 0, 1) ** GAMMA          # bright = 1
    if THEME == "dark":      # bright parts of the photo = dense characters
        idx = FLOOR + np.round(n * (len(RAMP) - 1 - FLOOR)).astype(int)
    else:                    # dark parts of the photo = dense characters
        idx = np.round((1 - n) * (len(RAMP) - 1)).astype(int)
    idx = np.where(bg_small, 0, idx)
    # non-breaking spaces so the browser doesn't trim the blank parts
    return ["".join(RAMP[i] for i in row).replace(" ", "\u00a0") for row in idx], cols


def build_svg(rows, cols):
    W = cols * CW
    H = len(rows) * LH
    tw, th = W + 2 * PAD, H + 2 * PAD
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{tw:.0f}" height="{th:.0f}" viewBox="0 0 {tw:.0f} {th:.0f}">',
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
        "<defs>",
    ]
    for i in range(len(rows)):
        t = i * ROW_DELAY
        y = PAD + i * LH
        p.append(
            f'<clipPath id="c{i}"><rect x="{PAD}" y="{y:.2f}" width="0" height="{LH:.2f}">'
            f'<animate attributeName="width" from="0" to="{W:.2f}" dur="{ROW_DUR}s" begin="{t:.2f}s" fill="freeze"/>'
            "</rect></clipPath>"
        )
    p.append("</defs>")
    p.append(
        f'<g font-family="Consolas, Menlo, monospace" font-size="{FONT_SIZE}" fill="{FILL}" xml:space="preserve" style="white-space:pre">'
    )
    for i, row in enumerate(rows):
        t = i * ROW_DELAY
        y = PAD + i * LH
        base = y + FONT_SIZE
        p.append(
            f'<text x="{PAD}" y="{base:.2f}" textLength="{W:.2f}" lengthAdjust="spacing" clip-path="url(#c{i})">{row}</text>'
        )
        p.append(
            f'<rect x="{PAD}" y="{y:.2f}" width="{CW:.2f}" height="{LH:.2f}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{t:.2f}s"/>'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + W:.2f}" dur="{ROW_DUR}s" begin="{t:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{t + ROW_DUR:.2f}s"/>'
            "</rect>"
        )
    p.append("</g></svg>")
    return "\n".join(p)


def main():
    rows, cols = image_to_rows()
    OUT.write_text(build_svg(rows, cols), encoding="utf-8")
    print(f"Saved {OUT} ({cols} x {len(rows)} characters)")


if __name__ == "__main__":
    main()
