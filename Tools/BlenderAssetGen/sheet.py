import sys, os, glob, json
from PIL import Image, ImageDraw, ImageFont
files = sys.argv[2:]
out = sys.argv[1]
th = 400; cols = min(4, len(files)); rows = (len(files) + cols - 1) // cols
stats = json.load(open("renders/stats.json"))
sheet = Image.new("RGB", (cols * th, rows * (th + 30)), (14, 14, 16))
d = ImageDraw.Draw(sheet); f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
for i, p in enumerate(files):
    im = Image.open(p).convert("RGB").resize((th, th))
    x, y = (i % cols) * th, (i // cols) * (th + 30)
    sheet.paste(im, (x, y))
    key = os.path.basename(p)[:-4].replace("_", "/", 1)
    s = stats.get(key, {})
    base = key.split("/")[-1]
    if "tris" in s:
        label = f"{base}  ·  {s['tris']:,} tris".replace(",", " ")
    else:
        label = base.replace("Merchandiser_", "Merchandiser · ")
    d.text((x + 8, y + th + 6), label, fill=(220, 220, 220), font=f)
sheet.save(out)
