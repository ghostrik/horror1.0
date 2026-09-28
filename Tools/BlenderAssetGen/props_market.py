"""Ассеты зоны 2 (гипермаркет «Корзина») и фудкорта: стеллажи, кассы, холодильники, вендинг, киоск."""
import math, random
from mathutils import Vector, Matrix
from lib import *

PACKS = ["M_PackRed", "M_PackBlue", "M_PackYellow", "M_PackGreen", "M_PackWhite", "M_PackOrange"]
PRINTS = ["M_ProductsA", "M_ProductsB", "M_ProductsC"]


# ------------------------------------------------------------------ товары (низкополигональные, но с формой)

def p_box(R, x, y, z, w, d, h, rot=0, mat=None):
    return box("Box", (w, d, h), (x, y, z + h / 2), mat or R.choice(PRINTS), 0.003, 1, rot=(0, 0, rot))


def p_can(R, x, y, z, r=0.033, h=0.12, mat=None):
    body = lathe("Can", [(0, z), (r * 0.85, z), (r, z + 0.008), (r, z + h - 0.012), (r * 0.85, z + h - 0.002), (r * 0.8, z + h), (0, z + h)], 12, mat or R.choice(["M_Chrome", "M_PackRed", "M_PackGreen"]), angle=50)
    body.location = (x, y, 0)
    label = lathe("Label", [(r * 1.004, z + h * 0.2), (r * 1.004, z + h * 0.8)], 12, R.choice(PACKS))
    label.location = (x, y, 0)
    return [body, label]


def p_bottle(R, x, y, z, h=0.28, r=0.038, mat=None):
    prof = [(0, z), (r * 0.9, z), (r, z + 0.01), (r, z + h * 0.55), (r * 0.95, z + h * 0.62), (r * 0.45, z + h * 0.78), (r * 0.36, z + h * 0.92), (r * 0.38, z + h * 0.95), (0, z + h * 0.96)]
    b = lathe("Bottle", prof, 12, mat or R.choice(["M_PackGreen", "M_PackBlue", "M_GlassDark", "M_PackWhite"]), angle=45)
    b.location = (x, y, 0)
    cap = cyl("Cap", r * 0.4, h * 0.06, (x, y, z + h * 0.98), R.choice(["M_PackRed", "M_PackBlue", "M_PackWhite"]), 10, 0)
    label = lathe("Label", [(r * 1.01, z + h * 0.2), (r * 1.01, z + h * 0.5)], 12, R.choice(PACKS))
    label.location = (x, y, 0)
    return [b, cap, label]


def p_carton(R, x, y, z, w=0.07, h=0.2, mat=None):
    m = mat or R.choice(["M_PackWhite", "M_PackBlue", "M_PackRed"])
    body = box("Carton", (w, w, h), (x, y, z + h / 2), m, 0.003, 1)
    # двускатный верх
    v = [(-w / 2, -w / 2, 0), (w / 2, -w / 2, 0), (w / 2, w / 2, 0), (-w / 2, w / 2, 0), (-w / 2, 0, w * 0.45), (w / 2, 0, w * 0.45)]
    f = [(0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4)]
    top = mesh_obj("Gable", v, f, m)
    top.location = (x, y, z + h)
    fin = box("Fin", (w, 0.004, 0.02), (x, y, z + h + w * 0.45 + 0.008), m, 0)
    return [body, top, fin]


def p_jar(R, x, y, z, r=0.04, h=0.11):
    j = lathe("Jar", [(0, z), (r * 0.9, z), (r, z + 0.01), (r, z + h * 0.8), (r * 0.8, z + h * 0.88), (0, z + h * 0.88)], 12, "M_GlassDark", angle=45)
    j.location = (x, y, 0)
    lid = cyl("Lid", r * 0.85, h * 0.14, (x, y, z + h * 0.94), R.choice(["M_PackRed", "M_PackYellow", "M_Chrome"]), 12, 0.002)
    return [j, lid]


def p_bag(R, x, y, z, w=0.16, d=0.08, h=0.24):
    secs = [(0, 0, 0, w * 0.45, d * 0.35, 3), (h * 0.1, 0, 0, w * 0.5, d * 0.5, 3), (h * 0.7, 0, 0, w * 0.5, d * 0.45, 3), (h * 0.95, 0, 0, w * 0.5, d * 0.12, 4), (h, 0, 0, w * 0.5, 0.004, 6)]
    b = loft("Bag", secs, 12, R.choice(PACKS), True, None, 45)
    b.location = (x, y, z)
    b.rotation_euler = (0, 0, R.uniform(-0.1, 0.1))
    return [b]


PRODUCT_TYPES = {
    "box": (lambda R, x, y, z: [p_box(R, x, y, z, 0.18, 0.07, 0.27, R.uniform(-3, 3))], 0.19, 0.075),
    "smallbox": (lambda R, x, y, z: [p_box(R, x, y, z, 0.11, 0.06, 0.16, R.uniform(-3, 3))], 0.12, 0.065),
    "can": (lambda R, x, y, z: p_can(R, x, y, z), 0.072, 0.072),
    "bottle": (lambda R, x, y, z: p_bottle(R, x, y, z), 0.085, 0.085),
    "carton": (lambda R, x, y, z: p_carton(R, x, y, z), 0.08, 0.08),
    "jar": (lambda R, x, y, z: p_jar(R, x, y, z), 0.09, 0.09),
    "bag": (lambda R, x, y, z: p_bag(R, x, y, z), 0.17, 0.09),
}


def fill_shelf(R, parts, x0, x1, y_front, depth, z, max_h, sparse, face_dir=-1):
    """Заполняет полку товарами одного типа (фронт полки у y_front, глубина уходит в -face_dir)."""
    kind = R.choice(list(PRODUCT_TYPES))
    fn, w, d = PRODUCT_TYPES[kind]
    x = x0 + w / 2 + 0.01
    rows = max(1, int(depth / (d + 0.01)))
    while x < x1 - w / 2:
        if R.random() < sparse:  # пустое место
            x += w + 0.01
            continue
        n = rows if R.random() > sparse * 0.5 else R.randint(1, rows)
        for k in range(n):
            y = y_front - face_dir * (d / 2 + 0.015 + k * (d + 0.008))
            parts += fn(R, x + R.uniform(-0.004, 0.004), y, z)
        x += w + 0.008
    # иногда упавший товар
    if R.random() < sparse:
        fx = R.uniform(x0 + 0.1, x1 - 0.1)
        if kind in ("box", "smallbox"):
            b = p_box(R, fx, y_front - face_dir * 0.1, z, 0.18, 0.07, 0.27)
            b.rotation_euler = (math.radians(90 * face_dir), 0, math.radians(R.uniform(-30, 30)))
            b.location.z = z + 0.035
            parts.append(b)


def gondola(sparse=0.0, seed=11, name="ShelfGondola"):
    R = random.Random(seed)
    parts = []
    W, D, H = 1.25, 1.0, 2.1
    # цоколь
    parts.append(box("Plinth", (W, D * 0.96, 0.12), (0, 0, 0.06), "M_PaintedMetal", 0.004))
    for s in (-1, 1):
        parts.append(box("Kick", (W, 0.01, 0.1), (0, s * D * 0.48, 0.06), "M_PlasticGrey", 0.002))
        parts.append(box("BaseDeck", (W - 0.02, 0.45, 0.02), (0, s * 0.26, 0.14), "M_PaintedMetal", 0.003))
    # хребет и стойки
    parts.append(box("Spine", (W, 0.04, H - 0.14), (0, 0, 0.14 + (H - 0.14) / 2), "M_PlasticWhiteTri", 0.004))
    for sx in (-1, 1):
        post = box("Upright", (0.05, 0.08, H), (sx * (W / 2 - 0.025), 0, H / 2), "M_PaintedMetal", 0.004)
        parts.append(post)
        for s in (-1, 1):
            for i in range(28):
                parts.append(box("Slot", (0.012, 0.002, 0.03), (sx * (W / 2 - 0.025), s * 0.041, 0.25 + i * 0.066), "M_Black", 0))
    parts.append(box("TopCap", (W + 0.01, 0.1, 0.03), (0, 0, H + 0.015), "M_PaintedMetal", 0.004))
    # полки с обеих сторон
    levels = [0.15, 0.55, 0.95, 1.35, 1.72]
    for s in (-1, 1):
        for li, z in enumerate(levels):
            depth = 0.44 if li == 0 else 0.4 - li * 0.02
            yf = s * (0.03 + depth)
            if li > 0:
                shelf = box("Shelf", (W - 0.06, depth, 0.02), (0, s * (0.03 + depth / 2), z), "M_PaintedMetal", 0.003, rot=(s * -3, 0, 0))
                parts.append(shelf)
                for sx in (-1, 1):
                    br = mesh_obj("Bracket", [(0, 0, 0), (0, depth * 0.9, 0), (0, 0, -0.12)], [(0, 1, 2)], "M_PaintedMetal")
                    xform(br, (sx * (W / 2 - 0.06), s * 0.03, z - 0.01), (0, 0, 0 if s > 0 else 180))
                    solidify(br, 0.004)
                    parts.append(br)
            rail = box("PriceRail", (W - 0.06, 0.012, 0.04), (0, yf + s * 0.006, z - 0.005), "M_PlasticWhiteTri", 0.002)
            parts.append(rail)
            for t in range(R.randint(2, 4)):
                tx = -W / 2 + 0.12 + R.random() * (W - 0.3)
                tag = box("PriceTag", (0.07, 0.003, 0.032), (tx, yf + s * 0.013, z - 0.005), "M_PlasticYellow" if R.random() < 0.6 else "M_Label", 0)
                parts.append(tag)
            top_z = z + 0.01
            max_h = (levels[li + 1] - z - 0.06) if li + 1 < len(levels) else 0.35
            fill_shelf(R, parts, -W / 2 + 0.05, W / 2 - 0.05, yf, depth - 0.03, top_z, max_h, sparse, face_dir=s)
    # табличка-шапка
    parts.append(box("HeaderHolder", (0.02, 0.02, 0.25), (0, 0, H + 0.14), "M_Chrome", 0.003))
    parts.append(box("Header", (0.9, 0.02, 0.18), (0, 0, H + 0.33), "M_PlasticRed", 0.006))
    return [finalize(parts, name)]


def gondola_full():
    return gondola(0.0, 11, "ShelfGondola_Full")


def gondola_looted():
    return gondola(0.45, 23, "ShelfGondola_Looted")


# ------------------------------------------------------------------ касса

def checkout():
    R = random.Random(5)
    parts = []
    L, Wd, Hh = 2.4, 0.8, 0.88
    body = loft("Body", [(0, 0, 0, L / 2, Wd / 2, 8), (0.05, 0, 0, L / 2, Wd / 2, 8), (Hh - 0.05, 0, 0, L / 2, Wd / 2, 8), (Hh, 0, 0, L / 2 - 0.01, Wd / 2 - 0.01, 8)], 48, "M_PlasticWhiteTri", True, None, 30)
    parts.append(body)
    parts.append(box("KickBand", (L - 0.04, Wd + 0.004, 0.08), (0, 0, 0.04), "M_PlasticGrey", 0.004))
    parts.append(box("ColorBand", (L - 0.02, Wd + 0.006, 0.05), (0, 0, 0.7), "M_PlasticRed", 0.004))
    # лента транспортёра
    parts.append(box("BeltBed", (1.5, 0.5, 0.03), (-0.35, 0, Hh + 0.015), "M_Chrome", 0.004))
    belt = box("Belt", (1.44, 0.44, 0.012), (-0.35, 0, Hh + 0.034), "M_Rubber", 0.004)
    parts.append(belt)
    for x in (-1.1, 0.4):
        parts.append(cyl("Roller", 0.022, 0.44, (x, 0, Hh + 0.028), "M_Chrome", 16, 0.002, rot=(90, 0, 0)))
    for s in (-1, 1):
        parts.append(box("BeltTrim", (1.5, 0.02, 0.05), (-0.35, s * 0.26, Hh + 0.03), "M_Chrome", 0.004))
    parts.append(box("Divider", (0.35, 0.03, 0.05), (-0.6, 0.05, Hh + 0.066), "M_PlasticRed", 0.01, rot=(0, 0, 90)))
    # сканер-весы
    parts.append(box("ScannerPlate", (0.35, 0.4, 0.015), (0.62, 0, Hh + 0.008), "M_Chrome", 0.003))
    parts.append(box("ScannerGlass", (0.28, 0.2, 0.004), (0.62, 0, Hh + 0.017), "M_GlassDark", 0.001))
    parts.append(box("ScannerTower", (0.3, 0.1, 0.18), (0.62, 0.22, Hh + 0.09), "M_PlasticGrey", 0.01))
    parts.append(box("TowerGlass", (0.2, 0.004, 0.1), (0.62, 0.169, Hh + 0.1), "M_GlowRed", 0))
    # кассовое место
    parts.append(box("Drawer", (0.42, 0.42, 0.13), (0.95, 0.12, Hh + 0.065), "M_PlasticGrey", 0.01))
    parts.append(cyl("MonArm", 0.018, 0.32, (0.95, 0.25, Hh + 0.29), "M_PlasticGrey", 12, 0.003))
    mon = box("Monitor", (0.34, 0.04, 0.26), (0.95, 0.24, Hh + 0.48), "M_PlasticGrey", 0.01, rot=(-10, 0, 180))
    scr = plane("Screen", 0.3, 0.2, (0.95, 0.218, Hh + 0.48), (80, 0, 180), "M_ScreenGlow")
    parts += [mon, scr]
    parts.append(box("Keyboard", (0.36, 0.14, 0.025), (0.95, 0.0, Hh + 0.14), "M_Black", 0.004, rot=(8, 0, 0)))
    parts.append(box("Printer", (0.14, 0.18, 0.12), (1.12, -0.18, Hh + 0.06), "M_PlasticGrey", 0.01))
    receipt = box("ReceiptTail", (0.06, 0.002, 0.25), (1.12, -0.28, Hh + 0.02), "M_Receipt", 0, rot=(35, 0, 0))
    parts.append(receipt)
    # терминал на ножке
    parts.append(cyl("TermPole", 0.012, 0.2, (0.95, -0.3, Hh + 0.1), "M_Chrome", 10, 0.002))
    parts.append(box("Terminal", (0.09, 0.05, 0.16), (0.95, -0.3, Hh + 0.26), "M_Black", 0.008, rot=(-25, 0, 0)))
    parts.append(box("TermScreen", (0.065, 0.004, 0.05), (0.95, -0.325, Hh + 0.29), "M_ScreenGlow", 0, rot=(-25, 0, 0)))
    # стойка с номером кассы
    parts.append(cyl("LanePole", 0.025, 1.4, (1.15, 0.33, Hh + 0.7), "M_Chrome", 16, 0.003))
    lamp = cyl("LaneLamp", 0.12, 0.2, (1.15, 0.33, Hh + 1.5), "M_PlasticGrey", 24, 0.01)
    lens = cyl("LaneLens", 0.105, 0.15, (1.15, 0.33, Hh + 1.5), "M_GlowWarm", 24, 0)
    parts += [lamp, lens]
    # пакеты на крючке
    for i in range(3):
        parts.append(box("Bags", (0.2, 0.02, 0.3), (-1.18, 0.0 + i * 0.02, 0.6), "M_PackWhite", 0.004, rot=(0, 90, 0)))
    # стул кассира
    parts.append(cyl("ChairBase", 0.25, 0.03, (0.95, 0.75, 0.015), "M_PlasticGrey", 20, 0.005))
    parts.append(cyl("ChairPole", 0.025, 0.5, (0.95, 0.75, 0.28), "M_Chrome", 12, 0.002))
    parts.append(loft("ChairSeat", [(0, 0, 0, 0.21, 0.2, 3), (0.07, 0, 0, 0.22, 0.21, 3), (0.08, 0, 0, 0.2, 0.19, 3)], 24, "M_Cloth", True, None, 40))
    parts[-1].location = (0.95, 0.75, 0.53)
    # жвачка-стойка
    parts.append(box("CandyRack", (0.5, 0.2, 1.1), (-1.0, -0.52, 0.55), "M_PaintedMetal", 0.006))
    for i in range(4):
        for j in range(4):
            parts.append(box("Candy", (0.1, 0.04, 0.14), (-1.18 + j * 0.12, -0.63, 0.25 + i * 0.25), R.choice(PACKS), 0.004))
    return [finalize(parts, "CheckoutCounter")]


# ------------------------------------------------------------------ холодильник со стеклянными дверями

def freezer():
    R = random.Random(9)
    parts = []
    W, D, H = 2.4, 0.8, 2.1
    shell_parts = []
    parts.append(box("Back", (W, 0.05, H), (0, D / 2 - 0.025, H / 2), "M_PlasticWhiteTri", 0.006))
    for sx in (-1, 1):
        parts.append(box("Side", (0.05, D, H), (sx * (W / 2 - 0.025), 0, H / 2), "M_PlasticWhiteTri", 0.006))
    parts.append(box("Top", (W, D, 0.22), (0, 0, H - 0.11), "M_PlasticWhiteTri", 0.006))
    parts.append(box("Bottom", (W, D, 0.18), (0, 0, 0.09), "M_PlasticGrey", 0.006))
    parts.append(box("Grille", (W - 0.1, 0.01, 0.1), (0, -D / 2 - 0.004, 0.09), "M_Black", 0.002))
    for i in range(20):
        parts.append(box("Vent", (0.06, 0.004, 0.08), (-W / 2 + 0.15 + i * 0.11, -D / 2 - 0.01, 0.09), "M_PlasticGrey", 0))
    parts.append(box("HeaderGlow", (W - 0.1, 0.01, 0.12), (0, -D / 2 - 0.006, H - 0.11), "M_GlowCold", 0))
    parts.append(box("InnerGlow", (W - 0.12, 0.01, H - 0.45), (0, D / 2 - 0.055, (H - 0.4) / 2 + 0.18), "M_GlowFreezer", 0))
    # полки и товар внутри
    for z in (0.3, 0.72, 1.14, 1.56):
        parts.append(box("WireShelf", (W - 0.12, D - 0.2, 0.012), (0, 0.05, z), "M_Chrome", 0.002))
        x = -W / 2 + 0.12
        while x < W / 2 - 0.12:
            if R.random() < 0.25:
                x += 0.1; continue
            k = R.random()
            if k < 0.4:
                parts += p_bottle(R, x, -0.1, z + 0.006, 0.3, 0.036)
                x += 0.085
            elif k < 0.7:
                parts += p_carton(R, x, -0.1, z + 0.006)
                x += 0.085
            else:
                parts.append(p_box(R, x, -0.05, z + 0.006, 0.2, 0.14, 0.12, R.uniform(-5, 5), R.choice(PACKS)))
                x += 0.22
    # двери: рама + стекло + ручка
    for i in range(3):
        cx = -W / 2 + W / 6 + i * W / 3
        dw = W / 3 - 0.02
        z0, z1 = 0.2, H - 0.24
        fr = []
        for (a, b) in (((cx - dw / 2, z0), (cx + dw / 2, z0)), ((cx - dw / 2, z1), (cx + dw / 2, z1))):
            fr.append(box("DoorRailH", (dw, 0.04, 0.04), (cx, -D / 2 - 0.02, a[1]), "M_Chrome", 0.004))
        for x in (cx - dw / 2, cx + dw / 2):
            fr.append(box("DoorRailV", (0.04, 0.04, z1 - z0), (x, -D / 2 - 0.02, (z0 + z1) / 2), "M_Chrome", 0.004))
        glass = box("Glass", (dw - 0.04, 0.008, z1 - z0 - 0.04), (cx, -D / 2 - 0.02, (z0 + z1) / 2), "M_GlassFreezer", 0)
        handle = cyl("Handle", 0.012, 0.7, (cx + dw / 2 - 0.06, -D / 2 - 0.07, 1.1), "M_Chrome", 12, 0.003)
        for hz in (0.78, 1.42):
            fr.append(box("HandleMount", (0.02, 0.05, 0.02), (cx + dw / 2 - 0.06, -D / 2 - 0.045, hz), "M_Chrome", 0.003))
        sticker = plane("Sticker", 0.16, 0.24, (cx - 0.12, -D / 2 - 0.026, 1.5), (90, 0, 0), "M_PosterSale")
        parts += fr + [glass, handle, sticker]
    return [finalize(parts, "FreezerGlassDoors")]


# ------------------------------------------------------------------ паллета + коробки

def pallet():
    parts = []
    for i in range(5):
        x = -0.55 + i * 0.275
        parts.append(box("TopBoard", (0.1 if i % 2 else 0.14, 0.8, 0.022), (x, 0, 0.133), "M_WoodTri", 0.003))
    for x in (-0.55, 0, 0.55):
        for y in (-0.34, 0, 0.34):
            parts.append(box("Block", (0.14, 0.12 if y else 0.1, 0.078), (x, y, 0.083), "M_WoodTri", 0.004))
        parts.append(box("Stringer", (0.145, 0.8, 0.022), (x, 0, 0.033), "M_WoodTri", 0.003))
    for y in (-0.34, 0, 0.34):
        parts.append(box("BottomBoard", (1.2, 0.1, 0.022), (0, y, 0.011), "M_WoodTri", 0.003))
    return [finalize(parts, "Pallet")]


def cardboard_box(w, d, h, open_=False, crushed=False, name="Box", seed=0):
    R = random.Random(seed)
    parts = []
    b = box("Body", (w, d, h), (0, 0, h / 2), "M_CardboardTri", 0.006, 2)
    if crushed:
        for v in b.data.vertices:
            if v.co.z > 0:
                v.co.z -= 0.25 * h * (0.5 + 0.5 * math.sin(v.co.x * 20))
                v.co.x += R.uniform(-0.01, 0.01)
    parts.append(b)
    if open_:
        for (ax, sgn, L) in (("x", -1, d), ("x", 1, d), ("y", -1, w), ("y", 1, w)):
            fw = (w if ax == "y" else d) / 2
            flap = box("Flap", (L if ax == "y" else 0.004, 0.004 if ax == "y" else L, fw), (0, 0, 0), "M_CardboardTri", 0)
            ang = R.uniform(100, 150)
            if ax == "y":
                flap.location = (0, sgn * (d / 2 + math.sin(math.radians(ang - 90)) * fw / 2), h + math.cos(math.radians(ang - 90)) * fw / 2)
                flap.rotation_euler = (math.radians(-sgn * (ang - 90)), 0, 0)
            else:
                flap.location = (sgn * (w / 2 + math.sin(math.radians(ang - 90)) * fw / 2), 0, h + math.cos(math.radians(ang - 90)) * fw / 2)
                flap.rotation_euler = (0, math.radians(sgn * (ang - 90)), 0)
            parts.append(flap)
        parts.append(box("Inside", (w - 0.01, d - 0.01, 0.004), (0, 0, h * 0.4), "M_Black", 0))
    else:
        parts.append(box("Tape", (0.06, d + 0.002, 0.002), (0, 0, h + 0.001), "M_PlasticGrey", 0))
        parts.append(box("TapeSide", (0.06, 0.002, 0.12), (0, -d / 2 - 0.001, h - 0.06), "M_PlasticGrey", 0))
    parts.append(plane("Label", 0.1, 0.07, (w * 0.2, -d / 2 - 0.002, h * 0.45), (90, 0, 0), "M_Label"))
    return finalize(parts, name)


def boxes_set():
    a = cardboard_box(0.6, 0.4, 0.4, False, False, "Box_Closed", 1)
    b = cardboard_box(0.5, 0.35, 0.35, True, False, "Box_Open", 2)
    c = cardboard_box(0.45, 0.35, 0.3, False, True, "Box_Crushed", 3)
    a.location = (-0.7, 0, 0); b.location = (0.05, 0.1, 0); c.location = (0.7, -0.05, 0)
    c.rotation_euler = (0, 0, math.radians(25))
    return [a, b, c]


# ------------------------------------------------------------------ антикражная рамка

def antitheft_gate():
    parts = []
    parts.append(box("Base", (0.5, 0.12, 0.08), (0, 0, 0.04), "M_PlasticGrey", 0.02))
    frame = []
    pts = smooth_path([(-0.2, 0, 0.08), (-0.2, 0, 1.45), (0.2, 0, 1.55), (0.2, 0, 0.08)], steps=3)
    parts.append(tube("Frame", pts, 0.03, "M_PlasticWhiteTri", res=10))
    panel = box("Acrylic", (0.36, 0.02, 1.36), (0, 0, 0.8), "M_GlassDark", 0.004)
    parts.append(panel)
    parts.append(box("LED", (0.3, 0.025, 0.02), (0, 0, 1.45), "M_GlowRed", 0))
    parts.append(plane("Logo", 0.25, 0.25, (0, -0.012, 1.05), (90, 0, 0), "M_PosterSale"))
    return [finalize(parts, "AntiTheftGate")]


# ------------------------------------------------------------------ вендинг-автомат

def vending_machine():
    R = random.Random(4)
    parts = []
    W, D, H = 0.95, 0.85, 1.9
    z0 = 0.05
    parts.append(box("Back", (W, 0.04, H), (0, D / 2 - 0.02, z0 + H / 2), "M_PlasticRed", 0.01))
    for sx in (-1, 1):
        parts.append(box("Side", (0.04, D, H), (sx * (W / 2 - 0.02), 0, z0 + H / 2), "M_PlasticRed", 0.015))
    parts.append(box("Top", (W, D, 0.06), (0, 0, z0 + H - 0.03), "M_PlasticRed", 0.015))
    parts.append(box("Bottom", (W, D, 0.5), (0, 0, z0 + 0.25), "M_PlasticRed", 0.015))
    # передняя рама вокруг витрины (окно x -0.42..0.18, z 0.55..1.85)
    parts.append(box("FrontRight", (0.29, 0.04, H - 0.5), (0.315, -D / 2 + 0.02, z0 + 0.5 + (H - 0.5) / 2), "M_PlasticRed", 0.01))
    parts.append(box("FrontLeftStrip", (0.06, 0.04, H - 0.5), (-0.445, -D / 2 + 0.02, z0 + 0.5 + (H - 0.5) / 2), "M_PlasticRed", 0.01))
    parts.append(box("FrontTop", (0.6, 0.04, 0.08), (-0.12, -D / 2 + 0.02, 1.88), "M_PlasticRed", 0.01))
    parts.append(box("FrontSill", (0.6, 0.04, 0.06), (-0.12, -D / 2 + 0.02, 0.53), "M_PlasticRed", 0.01))
    parts.append(box("Divider", (0.02, D - 0.1, H - 0.55), (0.17, 0, z0 + 0.5 + (H - 0.5) / 2), "M_Black", 0))
    parts.append(box("Window", (0.6, 0.01, 1.3), (-0.12, -D / 2 + 0.005, 1.2), "M_GlassFreezer", 0))
    parts.append(box("BackLight", (0.58, 0.01, 1.3), (-0.12, -D / 2 + 0.3, 1.2), "M_Vending", 0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl("Foot", 0.03, 0.05, (sx * 0.4, sy * 0.35, 0.025), "M_Rubber", 12, 0.004))
    for row in range(5):
        z = 0.7 + row * 0.24
        parts.append(box("Tray", (0.56, 0.2, 0.01), (-0.12, -D / 2 + 0.14, z), "M_Chrome", 0.002))
        for col in range(5):
            x = -0.36 + col * 0.12
            # спираль
            pts = []
            for k in range(40):
                t = k / 39
                a = t * math.tau * 4
                pts.append((x + math.cos(a) * 0.035, -D / 2 + 0.05 + t * 0.2, z + 0.04 + math.sin(a) * 0.035))
            parts.append(tube("Coil", pts, 0.003, "M_Chrome", res=4))
            if R.random() > 0.3:
                for k in range(3):
                    parts.append(box("Snack", (0.09, 0.035, 0.13), (x, -D / 2 + 0.08 + k * 0.06, z + 0.075), R.choice(PACKS + PRINTS), 0.006))
    # панель управления
    parts.append(box("Panel", (0.22, 0.02, 0.9), (0.33, -D / 2 - 0.005, 1.25), "M_PlasticGrey", 0.006))
    parts.append(box("Display", (0.16, 0.006, 0.06), (0.33, -D / 2 - 0.016, 1.58), "M_GlowGreen", 0))
    for i in range(4):
        for j in range(3):
            parts.append(box("Key", (0.035, 0.012, 0.03), (0.29 + j * 0.042, -D / 2 - 0.018, 1.46 - i * 0.042), "M_Chrome", 0.003))
    parts.append(box("CoinSlot", (0.04, 0.012, 0.012), (0.33, -D / 2 - 0.018, 1.22), "M_Black", 0.002))
    parts.append(box("CardReader", (0.12, 0.03, 0.08), (0.33, -D / 2 - 0.02, 1.08), "M_Black", 0.006))
    # лоток выдачи
    parts.append(box("Hatch", (0.6, 0.03, 0.22), (-0.12, -D / 2 - 0.01, 0.35), "M_Black", 0.01))
    parts.append(box("Flap", (0.52, 0.02, 0.14), (-0.12, -D / 2 - 0.02, 0.36), "M_PlasticGrey", 0.006, rot=(8, 0, 0)))
    # шапка с подсветкой
    parts.append(box("Header", (W - 0.06, 0.02, 0.18), (0, -D / 2 - 0.004, 1.95 - 0.02), "M_GlowWarm", 0.004))
    parts.append(plane("Promo", 0.26, 0.4, (0.33, -D / 2 - 0.018, 0.65), (90, 0, 0), "M_PosterPromoter"))
    return [finalize(parts, "VendingMachine")]


# ------------------------------------------------------------------ киоск кофейни + кофемашина

def espresso_machine():
    parts = []
    parts.append(box("Body", (0.75, 0.5, 0.42), (0, 0, 0.26), "M_Chrome", 0.03, 3))
    parts.append(box("Base", (0.78, 0.52, 0.05), (0, 0, 0.025), "M_Black", 0.01))
    parts.append(box("DripTray", (0.6, 0.18, 0.02), (0, -0.28, 0.06), "M_Chrome", 0.004))
    for i in range(12):
        parts.append(box("TraySlot", (0.004, 0.14, 0.021), (-0.27 + i * 0.05, -0.28, 0.061), "M_Black", 0))
    parts.append(box("TopRail", (0.7, 0.45, 0.03), (0, 0, 0.5), "M_Chrome", 0.01))
    for i in range(4):
        parts.append(cyl("CupOnTop", 0.035, 0.06, (-0.25 + i * 0.16, 0.05, 0.545), "M_Cup", 16, 0.003))
    for sx in (-0.18, 0.18):
        parts.append(cyl("GroupHead", 0.045, 0.06, (sx, -0.26, 0.33), "M_Chrome", 20, 0.004))
        parts.append(cyl("Portafilter", 0.04, 0.03, (sx, -0.27, 0.285), "M_Chrome", 20, 0.004))
        parts.append(tube("PFHandle", [(sx, -0.3, 0.285), (sx, -0.45, 0.27)], 0.012, "M_Black", res=8))
        parts.append(box("Button", (0.05, 0.01, 0.03), (sx, -0.255, 0.42), "M_GlowGreen", 0.003))
    parts.append(tube("SteamWand", smooth_path([(0.33, -0.2, 0.35), (0.36, -0.28, 0.32), (0.36, -0.3, 0.18)], steps=2), 0.006, "M_Chrome", res=8))
    parts.append(cyl("Gauge", 0.035, 0.01, (0, -0.255, 0.42), "M_PackWhite", 20, 0.002, rot=(90, 0, 0)))
    return finalize(parts, "EspressoMachine")


def kiosk_counter():
    R = random.Random(12)
    parts = []
    L, Dp, H = 2.2, 0.7, 1.08
    parts.append(box("Front", (L, 0.05, H - 0.06), (0, -Dp / 2 + 0.025, (H - 0.06) / 2), "M_WoodTri", 0.006))
    for sx in (-1, 1):
        parts.append(box("Side", (0.05, Dp, H - 0.06), (sx * (L / 2 - 0.025), 0, (H - 0.06) / 2), "M_WoodTri", 0.006))
    parts.append(box("Plinth", (L - 0.02, Dp - 0.04, 0.1), (0, 0.02, 0.05), "M_Black", 0.004))
    parts.append(box("Top", (L + 0.08, Dp + 0.1, 0.05), (0, 0.0, H - 0.025), "M_StoneTri", 0.01))
    for i in range(7):
        parts.append(box("Panel", (0.26, 0.012, 0.7), (-L / 2 + 0.2 + i * 0.3, -Dp / 2 - 0.004, 0.5), "M_WoodTri", 0.004))
    parts.append(box("LEDStrip", (L - 0.1, 0.01, 0.015), (0, -Dp / 2 - 0.01, 0.9), "M_GlowWarm", 0))
    # защитный экран
    for sx in (-0.9, 0.9):
        parts.append(cyl("GuardPost", 0.012, 0.4, (sx, -0.2, H + 0.2), "M_Chrome", 12, 0.002))
    parts.append(box("Guard", (1.9, 0.008, 0.36), (0, -0.2, H + 0.22), "M_GlassDark", 0.002))
    em = espresso_machine()
    em.location = (0.5, 0.1, H)
    parts.append(em)
    # стопки стаканов, сиропы
    for i in range(3):
        for k in range(8):
            c = lathe("Cup", [(0, 0), (0.032, 0), (0.042, 0.11), (0.043, 0.115), (0.0, 0.115)], 16, "M_Cup")
            c.location = (-0.8 + i * 0.1, 0.1, H + k * 0.012)
            parts.append(c)
    for i in range(5):
        parts += p_bottle(R, -0.35 + i * 0.08, 0.2, H, 0.3, 0.03, R.choice(["M_PackRed", "M_PackOrange", "M_PackYellow", "M_GlassDark"]))
    parts.append(box("Register", (0.3, 0.3, 0.12), (-0.15, -0.05, H + 0.06), "M_PlasticGrey", 0.01))
    parts.append(box("RegScreen", (0.25, 0.02, 0.16), (-0.15, 0.08, H + 0.2), "M_ScreenGlow", 0.004, rot=(-15, 0, 0)))
    parts.append(box("TipJar", (0.1, 0.1, 0.14), (-0.55, -0.2, H + 0.07), "M_GlassDark", 0.01))
    return [finalize(parts, "KioskCoffeeCounter")]


ASSETS = {
    "Props/ShelfGondola_Full": gondola_full,
    "Props/ShelfGondola_Looted": gondola_looted,
    "Props/CheckoutCounter": checkout,
    "Props/FreezerGlassDoors": freezer,
    "Props/Pallet": pallet,
    "Props/CardboardBoxes": boxes_set,
    "Props/AntiTheftGate": antitheft_gate,
    "Props/VendingMachine": vending_machine,
    "Props/KioskCoffeeCounter": kiosk_counter,
}
