import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps
from rembg import remove

HEAD_CROP = 0.62   # keep the top 62% of the subject (head + shoulders); 1.0 = no crop
MARGIN = 0.04      # white margin around the subject, as a fraction of its width


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <photo>")
        sys.exit(1)

    src = Path(sys.argv[1])
    out = Path("source-prepped.png")

    # 1. Load the photo and fix phone rotation
    img = ImageOps.exif_transpose(Image.open(src)).convert("RGBA")

    # 2. Remove the background only if the photo doesn't already have one removed
    alpha = np.array(img)[:, :, 3]
    if (alpha < 10).mean() < 0.05:
        print("Removing background...")
        flat = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = remove(Image.alpha_composite(flat, img).convert("RGB")).convert("RGBA")
    else:
        print("Background already transparent, skipping removal.")

    arr = np.array(img)
    a = arr[:, :, 3] / 255.0

    # 3. Crop to head and shoulders
    ys, xs = np.where(a > 0.5)
    top, bottom, left, right = ys.min(), ys.max(), xs.min(), xs.max()
    bottom = int(top + (bottom - top) * HEAD_CROP)
    m = int((right - left) * MARGIN)
    y0, y1 = max(0, top - m), min(arr.shape[0], bottom + m)
    x0, x1 = max(0, left - m), min(arr.shape[1], right + m)
    arr, a = arr[y0:y1, x0:x1], a[y0:y1, x0:x1]

    # 4. Make transparent areas white, then boost local contrast (CLAHE)
    rgb = np.where(a[..., None] > 0.5, arr[:, :, :3], 255).astype(np.uint8)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)

    # 5. Put the subject on pure white
    comp = gray * a + 255 * (1 - a)
    Image.fromarray(comp.astype(np.uint8)).save(out)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
