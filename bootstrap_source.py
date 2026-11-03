"""Unpack Mahwar Focus source archive and generate its branded Windows icon."""
from __future__ import annotations
import base64
import io
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
parts = sorted((ROOT / "bundle").glob("source-*.txt"))
if not parts:
    raise RuntimeError("Missing bundled source parts")
payload = base64.b64decode("".join(p.read_text(encoding="ascii").strip() for p in parts), validate=True)
with tarfile.open(fileobj=io.BytesIO(payload), mode="r:xz") as archive:
    root = ROOT.resolve()
    for member in archive.getmembers():
        destination = (ROOT / member.name).resolve()
        if not destination.is_relative_to(root):
            raise ValueError("Unsafe archive path")
        if member.issym() or member.islnk() or member.isdev():
            raise ValueError("Unsafe archive member")
    archive.extractall(ROOT, filter="data")

from PIL import Image, ImageDraw
factor, size = 4, 256
canvas = Image.new("RGBA", (size * factor, size * factor), (0, 0, 0, 0))
pen = ImageDraw.Draw(canvas)
pen.rounded_rectangle((11*factor,11*factor,245*factor,245*factor),radius=54*factor,fill="#3E8C6F")
pen.ellipse((69*factor,69*factor,187*factor,187*factor),outline="white",width=16*factor)
pen.line([(88*factor,127*factor),(115*factor,153*factor),(169*factor,99*factor)],fill="white",width=18*factor,joint="curve")
for x,y in [(88,127),(115,153),(169,99)]:
    pen.ellipse(((x-9)*factor,(y-9)*factor,(x+9)*factor,(y+9)*factor),fill="white")
canvas=canvas.resize((size,size),Image.Resampling.LANCZOS)
assets=ROOT/"assets"
assets.mkdir(exist_ok=True)
canvas.save(assets/"mahwar.png")
canvas.save(assets/"mahwar.ico",format="ICO",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("Mahwar Focus source and icon prepared")
