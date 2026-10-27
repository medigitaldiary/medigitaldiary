from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

SRC = Path("source-prepped.png")
OUT = Path("ascii-portrait.svg")

MAPPING = "dark"            # "dark" = dark parts of the photo glow (line-art look); "bright" = the reverse
THEME = "dark"              # "dark" = light text on a dark window, "light" = the opposite
COLS = 118                  # characters per row; more = more detail
RAMP = " .`:-=+*cs#%@"      # blank -> light -> dense
FLOOR = 2                   # ("bright" mapping only) darkest part still prints at this level
GAMMA = 1.0                 # below 1 = bolder, above 1 = softer (1.0 looked best)
CROP_X = (0.17, 0.83)       # keep this slice of the width (left, right)
CROP_BOTTOM = 0.74          # keep the top 74% of the height (head + collar)
FONT_SIZE = 5
CW = FONT_SIZE * 0.6        # character width
LH = FONT_SIZE * 1.2        # line height
PAD = 12
BAR = 32                    # title bar height
LINE = "#30363d" if THEME == "dark" else "#d0d7de"
BARBG = "#161b22" if THEME == "dark" else "#eaeef2"
MUTED = "#8b949e" if THEME == "dark" else "#6e7781"
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
    if MAPPING == "bright":  # bright parts of the photo = dense characters
        idx = FLOOR + np.round(n * (len(RAMP) - 1 - FLOOR)).astype(int)
    else:                    # dark parts of the photo = dense characters
        idx = np.round((1 - n) * (len(RAMP) - 1)).astype(int)
    idx = np.where(bg_small, 0, idx)
    # non-breaking spaces so the browser doesn't trim the blank parts
    return ["".join(RAMP[i] for i in row).replace(" ", "\u00a0") for row in idx], cols


def build_svg(rows, cols):
    W = cols * CW
    H = len(rows) * LH
    tw, th = W + 2 * PAD, H + 2 * PAD + BAR
    TOP = PAD + BAR
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{tw:.0f}" height="{th:.0f}" viewBox="0 0 {tw:.0f} {th:.0f}">',
        f'<rect x="0.5" y="0.5" width="{tw-1:.0f}" height="{th-1:.0f}" rx="10" fill="{BG}" stroke="{LINE}"/>',
        f'<path d="M0.5 10 a9.5 9.5 0 0 1 9.5 -9.5 H{tw-10:.0f} a9.5 9.5 0 0 1 9.5 9.5 V{BAR} H0.5 Z" fill="{BARBG}"/>',
        f'<line x1="0.5" y1="{BAR}" x2="{tw-0.5:.0f}" y2="{BAR}" stroke="{LINE}"/>',
        f'<circle cx="18" cy="{BAR/2}" r="5" fill="#ff5f56"/>',
        f'<circle cx="36" cy="{BAR/2}" r="5" fill="#ffbd2e"/>',
        f'<circle cx="54" cy="{BAR/2}" r="5" fill="#27c93f"/>',
        f'<text x="{tw/2:.0f}" y="{BAR/2+4}" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Consolas, Menlo, monospace" font-size="10.5" fill="{MUTED}">megh@github: ~/portrait</text>',
        "<defs>",
    ]
    for i in range(len(rows)):
        t = i * ROW_DELAY
        y = TOP + i * LH
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
        y = TOP + i * LH
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
