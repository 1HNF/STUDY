"""Pack Blender turntable frames (<shape>_00.png ... _35.png) into one 6x6 WebP sprite sheet per shape.

Usage: .venv\\Scripts\\python.exe tools\\pack_sprites.py assets\\frames assets
"""
import sys
from pathlib import Path

from PIL import Image

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
COLS = 6
for shape in sorted({p.stem.rsplit("_", 1)[0] for p in src.glob("*_??.png")}):
    frames = sorted(src.glob(f"{shape}_??.png"))
    w, h = Image.open(frames[0]).size
    rows = -(-len(frames) // COLS)
    sheet = Image.new("RGBA", (w * COLS, h * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(Image.open(f).convert("RGBA"), ((i % COLS) * w, (i // COLS) * h))
    out = dst / f"{shape}.webp"
    sheet.save(out, "WEBP", quality=84, method=6)
    assert out.stat().st_size > 0
    print(shape, len(frames), "frames ->", out, out.stat().st_size // 1024, "KB")
