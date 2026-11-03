"""Generate the Mahwar Focus green checkmark icon in PNG and ICO formats."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
S, D = 256, 4
canvas = Image.new("RGBA", (S*D, S*D), (0,0,0,0))
draw = ImageDraw.Draw(canvas)
draw.rounded_rectangle((11*D,11*D,245*D,245*D),radius=54*D,fill="#3E8C6F")
draw.ellipse((69*D,69*D,187*D,187*D),outline="white",width=16*D)
draw.line([(88*D,127*D),(115*D,153*D),(169*D,99*D)],fill="white",width=18*D,joint="curve")
for x,y in [(88,127),(115,153),(169,99)]:
    draw.ellipse(((x-9)*D,(y-9)*D,(x+9)*D,(y+9)*D),fill="white")
canvas = canvas.resize((S,S),Image.Resampling.LANCZOS)
assets=ROOT/"assets"
assets.mkdir(parents=True,exist_ok=True)
canvas.save(assets/"mahwar.png")
canvas.save(assets/"mahwar.ico",format="ICO",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("Mahwar Focus icon generated.")
