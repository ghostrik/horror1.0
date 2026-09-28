"""Ассеты зоны 1 (атриум/фудкорт) и общие для ТЦ."""
import math, random
from mathutils import Vector
from lib import *


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# ------------------------------------------------------------------ тележка

def shopping_cart():
    R = random.Random(1)
    wire, rim = 0.0028, 0.0055
    parts = []
    # углы корзины (фронт по -Y, ручка по +Y)
    tb, tf = 0.99, 0.93          # высота верхнего края сзади/спереди
    zb_b, zb_f = 0.52, 0.47      # дно сзади/спереди
    top = {"bl": (-0.28, 0.44, tb), "br": (0.28, 0.44, tb), "fr": (0.25, -0.46, tf), "fl": (-0.25, -0.46, tf)}
    bot = {"bl": (-0.25, 0.36, zb_b), "br": (0.25, 0.36, zb_b), "fr": (0.2, -0.32, zb_f), "fl": (-0.2, -0.32, zb_f)}
    # верхний обод и нижняя рамка
    parts.append(tube("Rim", [top["bl"], top["br"], top["fr"], top["fl"]], rim, "M_Chrome", closed=True))
    parts.append(tube("BottomFrame", [bot["bl"], bot["br"], bot["fr"], bot["fl"]], rim * 0.8, "M_Chrome", closed=True))
    # боковые стенки: наклонные прутья + горизонтальные
    for side in ("l", "r"):
        tb_, tf_ = top["b" + side], top["f" + side]
        bb_, bf_ = bot["b" + side], bot["f" + side]
        n = 16
        for i in range(1, n):
            t = i / n
            parts.append(tube("SideV", [lerp(bb_, bf_, t), lerp(tb_, tf_, t)], wire, "M_Chrome", res=4))
        for k in range(1, 6):
            h = k / 6
            parts.append(tube("SideH", [lerp(bb_, tb_, h), lerp(bf_, tf_, h)], wire, "M_Chrome", res=4))
        parts.append(tube("SideFront", [bf_, tf_], rim * 0.8, "M_Chrome"))
    # передняя стенка
    for i in range(1, 12):
        t = i / 12
        parts.append(tube("FrontV", [lerp(bot["fl"], bot["fr"], t), lerp(top["fl"], top["fr"], t)], wire, "M_Chrome", res=4))
    for k in range(1, 6):
        h = k / 6
        parts.append(tube("FrontH", [lerp(bot["fl"], top["fl"], h), lerp(bot["fr"], top["fr"], h)], wire, "M_Chrome", res=4))
    # дно-решётка
    for i in range(1, 10):
        t = i / 10
        parts.append(tube("BotL", [lerp(bot["bl"], bot["br"], t), lerp(bot["fl"], bot["fr"], t)], wire, "M_Chrome", res=4))
    for k in range(1, 12):
        t = k / 12
        parts.append(tube("BotW", [lerp(bot["bl"], bot["fl"], t), lerp(bot["br"], bot["fr"], t)], wire, "M_Chrome", res=4))
    # задняя откидная стенка (сиденье для ребёнка)
    gate_bot_l, gate_bot_r = (-0.25, 0.4, 0.62), (0.25, 0.4, 0.62)
    parts.append(tube("GateFrame", [gate_bot_l, top["bl"], top["br"], gate_bot_r], rim * 0.8, "M_Chrome", closed=True))
    for i in range(1, 14):
        t = i / 14
        parts.append(tube("GateV", [lerp(gate_bot_l, gate_bot_r, t), lerp(top["bl"], top["br"], t)], wire, "M_Chrome", res=4))
    seat = box("SeatFlap", (0.46, 0.012, 0.2), (0, 0.405, 0.8), "M_PlasticRed", 0.004, rot=(-8, 0, 0))
    parts.append(seat)
    # шасси
    for sx in (-1, 1):
        leg = smooth_path([(0.25 * sx, 0.36, 0.52), (0.27 * sx, 0.44, 0.3), (0.27 * sx, 0.46, 0.13)], steps=3)
        parts.append(tube("RearLeg", leg, 0.011, "M_Chrome", res=8))
        rail = [(0.27 * sx, 0.46, 0.13), (0.2 * sx, -0.38, 0.13), (0.19 * sx, -0.44, 0.13)]
        parts.append(tube("BaseRail", rail, 0.011, "M_Chrome", res=8))
        parts.append(tube("Strut", [(0.2 * sx, -0.3, 0.47), (0.2 * sx, -0.36, 0.13)], 0.008, "M_Chrome", res=8))
        # ручка
        h = smooth_path([top["b" + ("l" if sx < 0 else "r")], (0.28 * sx, 0.5, 1.0), (0.28 * sx, 0.56, 1.04)], steps=3)
        parts.append(tube("HandleArm", h, 0.009, "M_Chrome", res=8))
    parts.append(tube("RearCross", [(-0.27, 0.46, 0.13), (0.27, 0.46, 0.13)], 0.011, "M_Chrome", res=8))
    # нижняя полка
    tray_c = [(-0.24, 0.4, 0.2), (0.24, 0.4, 0.2), (0.17, -0.35, 0.2), (-0.17, -0.35, 0.2)]
    parts.append(tube("TrayFrame", tray_c, 0.005, "M_Chrome", closed=True))
    for i in range(1, 8):
        t = i / 8
        parts.append(tube("TrayW", [lerp(tray_c[0], tray_c[1], t), lerp(tray_c[3], tray_c[2], t)], wire, "M_Chrome", res=4))
    # поручень с пластиковой накладкой
    parts.append(tube("HandleBar", [(-0.28, 0.56, 1.04), (0.28, 0.56, 1.04)], 0.009, "M_Chrome", res=8))
    grip = cyl("Grip", 0.017, 0.46, (0, 0.56, 1.04), "M_PlasticRed", 20, 0.004, rot=(0, 90, 0))
    parts.append(grip)
    for sx in (-0.23, 0.23):
        parts.append(cyl("GripCap", 0.02, 0.02, (sx, 0.56, 1.04), "M_PlasticGrey", 20, 0.003, rot=(0, 90, 0)))
    # колёса
    for (x, y) in ((-0.26, 0.44), (0.26, 0.44), (-0.19, -0.42), (0.19, -0.42)):
        yaw = R.uniform(-30, 30)
        plate = cyl("CasterPlate", 0.03, 0.01, (x, y, 0.125), "M_Chrome", 16, 0.002)
        parts.append(plate)
        for fx in (-0.022, 0.022):
            fork = box("Fork", (0.004, 0.03, 0.08), (x + fx, y + 0.012, 0.08), "M_Chrome", 0.001)
            parts.append(fork)
        tire = torus("Tire", 0.048, 0.014, (x, y + 0.02, 0.062), "M_Rubber", 28, 10, rot=(0, 90, 0))
        tire.scale = (1.3, 1, 1)
        apply_transform(tire)
        hub = cyl("Hub", 0.036, 0.03, (x, y + 0.02, 0.062), "M_PlasticGrey", 20, 0.003, rot=(0, 90, 0))
        parts += [tire, hub]
    # рекламная табличка на передней стенке
    sign = box("AdPlate", (0.32, 0.006, 0.12), (0, -0.465, 0.8), "M_PlasticRed", 0.003, rot=(-10, 0, 0))
    parts.append(sign)
    obj = finalize(parts, "ShoppingCart")
    return [obj]


# ------------------------------------------------------------------ скамья

def bench():
    parts = []
    L = 2.0
    # чугунные боковины
    for sx in (-0.85, 0.85):
        prof = [(0.26, 0.0), (0.22, 0.05), (0.2, 0.38), (0.24, 0.44), (0.16, 0.46), (-0.2, 0.46), (-0.24, 0.43), (-0.22, 0.38), (-0.2, 0.05), (-0.26, 0.0)]
        verts = [(sx - 0.03, y, z) for y, z in prof] + [(sx + 0.03, y, z) for y, z in prof]
        n = len(prof)
        faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
        for i in range(n):
            j = (i + 1) % n
            faces.append((i, n + i, n + j, j))
        side = mesh_obj("Side", verts, faces, "M_Grate")
        bevel(side, 0.006, 2)
        parts.append(side)
        # спинка-стойка
        back = tube("BackPost", smooth_path([(sx, 0.18, 0.44), (sx, 0.22, 0.6), (sx, 0.3, 0.88)], steps=3), 0.022, "M_Grate", res=10)
        parts.append(back)
    # рейки сиденья
    for i in range(6):
        y = -0.2 + i * 0.075
        parts.append(box("SeatSlat", (L, 0.062, 0.035), (0, y, 0.48), "M_WoodTri", 0.008))
    for i in range(3):
        z = 0.62 + i * 0.1
        y = 0.22 + i * 0.03
        parts.append(box("BackSlat", (L, 0.035, 0.08), (0, y, z), "M_WoodTri", 0.008, rot=(-18, 0, 0)))
    for sx in (-0.5, 0.0, 0.5):
        parts.append(box("Brace", (0.04, 0.44, 0.03), (sx, -0.01, 0.445), "M_Grate", 0.004))
    # болты
    for sx in (-0.85, 0.85):
        for i in range(6):
            parts.append(cyl("Bolt", 0.007, 0.006, (sx, -0.2 + i * 0.075, 0.5), "M_Chrome", 10, 0.001))
    return [finalize(parts, "Bench")]


# ------------------------------------------------------------------ столик + стул фудкорта

def food_table():
    parts = []
    top = lathe("Top", [(0, 0.735), (0.44, 0.735), (0.455, 0.742), (0.46, 0.755), (0.455, 0.768), (0.44, 0.772), (0, 0.772)], 64, "M_WoodTri")
    edge = lathe("Edge", [(0.452, 0.738), (0.462, 0.745), (0.463, 0.765), (0.452, 0.772)], 64, "M_PlasticGrey")
    col = lathe("Column", [(0.05, 0.02), (0.045, 0.1), (0.04, 0.68), (0.07, 0.72), (0.07, 0.735)], 32, "M_Chrome")
    base = lathe("Base", [(0, 0.0), (0.27, 0.0), (0.28, 0.008), (0.26, 0.02), (0.08, 0.035), (0.05, 0.05), (0, 0.05)], 48, "M_Grate")
    parts += [top, edge, col, base]
    # след от стакана и мусор
    parts.append(cyl("CupRing", 0.042, 0.001, (0.12, -0.1, 0.7725), "M_Black", 32, 0))
    return [finalize(parts, "FoodCourtTable")]


def food_chair():
    parts = []
    # литое сиденье-оболочка: чуть вогнутое, передний край загнут вниз
    sv, sf = [], []
    nx, ny = 14, 12
    for j in range(ny + 1):
        for i in range(nx + 1):
            u, v = i / nx - 0.5, j / ny - 0.5
            x, y = u * 0.43, v * 0.41
            z = 0.455 + (u * u) * 0.06 - (0.02 if v > 0.3 else 0) * 0
            if v < -0.35:
                z -= ((v + 0.35) ** 2) * 2.2
            if v > 0.42:
                z += ((v - 0.42) ** 2) * 3
            sv.append((x, y, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            sf.append((a, a + 1, a + nx + 2, a + nx + 1))
    seat = mesh_obj("Seat", sv, sf, "M_PlasticWhiteTri")
    solidify(seat, 0.014, 0)
    bevel(seat, 0.005, 2, 50)
    parts.append(seat)
    # спинка — изогнутая оболочка
    bverts, bfaces = [], []
    nx, nz = 12, 8
    for j in range(nz + 1):
        for i in range(nx + 1):
            u = i / nx - 0.5
            v = j / nz
            x = u * 0.42 * (1 - 0.1 * v)
            y = 0.2 + v * 0.1 + (u * u) * 0.12
            z = 0.52 + v * 0.36
            bverts.append((x, y, z))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            bfaces.append((a, a + 1, a + nx + 2, a + nx + 1))
    back = mesh_obj("Back", bverts, bfaces, "M_PlasticWhiteTri")
    solidify(back, 0.012, 0)
    bevel(back, 0.004, 2, 50)
    parts.append(back)
    # ножки
    for sx in (-1, 1):
        for sy in (-1, 1):
            leg = smooth_path([(0.17 * sx, 0.16 * sy, 0.44), (0.19 * sx, 0.19 * sy, 0.2), (0.2 * sx, 0.2 * sy, 0.01)], steps=2)
            parts.append(tube("Leg", leg, 0.011, "M_Chrome", res=8))
            parts.append(cyl("Foot", 0.013, 0.012, (0.2 * sx, 0.2 * sy, 0.006), "M_Rubber", 12, 0.002))
    for sx in (-1, 1):
        parts.append(tube("BackPost", smooth_path([(0.17 * sx, 0.16, 0.45), (0.18 * sx, 0.2, 0.55), (0.18 * sx, 0.24, 0.7)], steps=2), 0.009, "M_Chrome", res=8))
    parts.append(tube("Cross", [(-0.19, -0.19, 0.18), (0.19, -0.19, 0.18)], 0.008, "M_Chrome", res=8))
    parts.append(tube("Cross", [(-0.19, 0.19, 0.18), (0.19, 0.19, 0.18)], 0.008, "M_Chrome", res=8))
    return [finalize(parts, "FoodCourtChair")]


# ------------------------------------------------------------------ кадка с засохшей пальмой

def planter_palm():
    R = random.Random(7)
    parts = []
    pot = loft("Pot", [(0, 0, 0, 0.5, 0.5, 6), (0.7, 0, 0, 0.56, 0.56, 6), (0.74, 0, 0, 0.6, 0.6, 6), (0.8, 0, 0, 0.6, 0.6, 6), (0.8, 0, 0, 0.53, 0.53, 6), (0.74, 0, 0, 0.53, 0.53, 6)], 48, "M_StoneTri", True, None, 30)
    parts.append(pot)
    soil = loft("Soil", [(0.66, 0, 0, 0.54, 0.54, 6), (0.7, 0, 0, 0.53, 0.53, 6)], 48, "M_Leaves", True)
    parts.append(soil)
    # ствол с кольцами
    prof = []
    H = 2.4
    for i in range(40):
        t = i / 39
        z = 0.68 + t * H
        r = 0.12 - 0.04 * t + (0.012 if i % 3 == 0 else 0)
        prof.append((r, z))
    prof.append((0, 0.68 + H + 0.02))
    trunk = lathe("Trunk", prof, 16, "M_Trunk", angle=60)
    # изгиб ствола
    for v in trunk.data.vertices:
        t = (v.co.z - 0.68) / H
        v.co.x += math.sin(t * 1.5) * 0.18 * t
    parts.append(trunk)
    tip = Vector((math.sin(1.5) * 0.18, 0, 0.68 + H))
    # мёртвые листья: стебель + листочки
    for k in range(11):
        yaw = k / 11 * math.tau + R.uniform(-0.2, 0.2)
        droop = R.uniform(0.6, 1.4)
        L = R.uniform(1.0, 1.6)
        pts = []
        for i in range(12):
            t = i / 11
            d = t * L
            h = math.sin(t * 1.4) * 0.35 - (t ** 2) * droop
            pts.append(tip + Vector((math.cos(yaw) * d, math.sin(yaw) * d, h)))
        parts.append(tube("Stem", [tuple(p) for p in pts], 0.008, "M_Leaves", res=4))
        # листочки
        lv, lf = [], []
        for i in range(2, 11):
            p = pts[i]
            nxt = pts[i + 1]
            fwd = (nxt - p).normalized()
            side = fwd.cross(Vector((0, 0, 1))).normalized()
            for s in (-1, 1):
                ll = 0.28 * math.sin(i / 11 * math.pi) + 0.05
                hang = Vector((0, 0, -ll * R.uniform(0.4, 1.0)))
                a = p
                b = p + side * s * ll * 0.8 + hang + fwd * 0.05
                c = p + fwd * 0.06
                base = len(lv)
                lv += [tuple(a), tuple(b), tuple(c)]
                lf.append((base, base + 1, base + 2))
        leaves = mesh_obj("Leaflets", lv, lf, "M_Leaves")
        solidify(leaves, 0.003)
        parts.append(leaves)
    # опавшие листья на земле
    for i in range(6):
        a = R.uniform(0, math.tau)
        parts.append(box("Fallen", (0.3, 0.05, 0.004), (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.705), "M_Leaves", 0, rot=(0, 0, math.degrees(a))))
    return [finalize(parts, "PlanterDeadPalm")]


# ------------------------------------------------------------------ фонтан

def fountain():
    parts = []
    # чаша бассейна с бортом (полая)
    rim = lathe("Basin", [(0, 0.05), (2.9, 0.05), (2.9, 0.12), (2.95, 0.12), (2.98, 0.5), (3.05, 0.58), (3.25, 0.58), (3.3, 0.52), (3.28, 0.06), (3.34, 0.0), (0, 0.0)], 96, "M_StoneTri", angle=30)
    parts.append(rim)
    tiles = lathe("BasinTiles", [(0, 0.121), (2.92, 0.121)], 96, "M_FountainTiles")
    parts.append(tiles)
    # центральная колонна с ярусами
    col = lathe("Column", [(0.0, 0.12), (0.62, 0.12), (0.62, 0.22), (0.5, 0.3), (0.42, 0.34), (0.38, 1.0), (0.42, 1.1), (0.5, 1.16),
                           (0.5, 1.2), (0.0, 1.2)], 64, "M_StoneTri", angle=30)
    bowl1 = lathe("Bowl1", [(0.0, 1.2), (0.3, 1.22), (0.8, 1.35), (1.25, 1.58), (1.32, 1.66), (1.28, 1.7), (1.18, 1.66), (0.7, 1.52), (0.3, 1.46), (0.0, 1.46)], 64, "M_StoneTri", angle=30)
    stem2 = lathe("Stem2", [(0.0, 1.46), (0.18, 1.46), (0.14, 1.6), (0.13, 2.05), (0.2, 2.12), (0.0, 2.12)], 48, "M_StoneTri", angle=30)
    bowl2 = lathe("Bowl2", [(0.0, 2.1), (0.2, 2.12), (0.55, 2.22), (0.72, 2.36), (0.76, 2.42), (0.72, 2.45), (0.62, 2.41), (0.2, 2.32), (0.0, 2.32)], 48, "M_StoneTri", angle=30)
    finial = lathe("Finial", [(0.0, 2.32), (0.08, 2.33), (0.06, 2.45), (0.12, 2.55), (0.13, 2.62), (0.09, 2.7), (0.03, 2.8), (0.0, 2.84)], 32, "M_StoneTri", angle=40)
    parts += [col, bowl1, stem2, bowl2, finial]
    # насадки-сопла
    for i in range(8):
        a = i / 8 * math.tau
        parts.append(cyl("Nozzle", 0.02, 0.06, (math.cos(a) * 1.22, math.sin(a) * 1.22, 1.69), "M_Chrome", 12, 0.003))
    # мусор и монеты на дне
    R = random.Random(3)
    for i in range(40):
        a = R.uniform(0, math.tau); r = R.uniform(0.8, 2.8)
        parts.append(cyl("Coin", 0.012, 0.002, (math.cos(a) * r, math.sin(a) * r, 0.123), "M_Fuse", 12, 0))
    for i in range(5):
        a = R.uniform(0, math.tau); r = R.uniform(1, 2.6)
        c = cyl("Can", 0.033, 0.12, (math.cos(a) * r, math.sin(a) * r, 0.155), "M_Chrome", 16, 0.003, rot=(90, 0, math.degrees(a)))
        parts.append(c)
    for i in range(8):
        a = R.uniform(0, math.tau); r = R.uniform(1, 2.7)
        parts.append(box("Leaf", (0.12, 0.05, 0.002), (math.cos(a) * r, math.sin(a) * r, 0.123), "M_Leaves", 0, rot=(0, 0, R.uniform(0, 180))))
    return [finalize(parts, "Fountain")]


# ------------------------------------------------------------------ урна

def trash_bin():
    parts = []
    body = lathe("Body", [(0, 0.0), (0.2, 0.0), (0.21, 0.02), (0.22, 0.75), (0.235, 0.78), (0.235, 0.8), (0.2, 0.8), (0.2, 0.05), (0, 0.05)], 48, "M_Grate", angle=30)
    parts.append(body)
    # вертикальные рёбра
    for i in range(24):
        a = i / 24 * math.tau
        parts.append(box("Slat", (0.018, 0.012, 0.7), (math.cos(a) * 0.222, math.sin(a) * 0.222, 0.4), "M_Grate", 0.003, rot=(0, 0, math.degrees(a))))
    lid = lathe("Lid", [(0.24, 0.8), (0.245, 0.82), (0.22, 0.9), (0.12, 0.97), (0.0, 0.98)], 48, "M_Grate", angle=30)
    parts.append(lid)
    hole = cyl("Hole", 0.08, 0.005, (0, -0.19, 0.86), "M_Black", 24, 0, rot=(60, 0, 0))
    parts.append(hole)
    # торчащий мусор
    parts.append(box("Cup", (0.07, 0.07, 0.12), (0.05, 0.02, 0.97), "M_Cup", 0.01, rot=(20, 10, 0)))
    return [finalize(parts, "TrashBin")]


# ------------------------------------------------------------------ знак "Осторожно, мокрый пол"

def wet_floor_sign():
    parts = []
    for s in (-1, 1):
        panel = box("Panel", (0.3, 0.012, 0.62), (0, s * 0.055, 0.31), "M_PlasticYellow", 0.006, rot=(s * 10, 0, 0))
        parts.append(panel)
        # предупреждающий треугольник
        tri = mesh_obj("Warn", [(-0.09, 0, 0), (0.09, 0, 0), (0, 0, 0.16)], [(0, 1, 2)], "M_Black")
        xform(tri, (0, s * 0.064, 0.34), (s * 10, 0, 0 if s < 0 else 180))
        parts.append(tri)
    parts.append(cyl("Hinge", 0.012, 0.3, (0, 0, 0.62), "M_PlasticYellow", 16, 0.003, rot=(0, 90, 0)))
    parts.append(box("Handle", (0.14, 0.02, 0.05), (0, 0, 0.66), "M_PlasticYellow", 0.008))
    return [finalize(parts, "WetFloorSign")]


# ------------------------------------------------------------------ стойка информации

def info_desk():
    parts = []
    desk = lathe("Desk", [(0.0, 0.0), (0.85, 0.0), (0.88, 0.05), (0.9, 1.05), (0.0, 1.05)], 72, "M_WoodTri", angle=30)
    top = lathe("Top", [(0.0, 1.05), (0.97, 1.05), (0.99, 1.07), (0.97, 1.09), (0.0, 1.09)], 72, "M_StoneTri", angle=30)
    band = lathe("Band", [(0.905, 0.12), (0.905, 0.16)], 72, "M_Chrome")
    parts += [desk, top, band]
    parts.append(cyl("Pole", 0.035, 2.1, (0, 0, 2.14), "M_Chrome", 20, 0.004))
    sign = box("SignBox", (1.4, 0.12, 0.3), (0, 0, 3.2), "M_PlasticBlue", 0.02)
    parts.append(sign)
    for s in (-1, 1):
        face = plane("SignFace", 1.32, 0.0825, (0, s * 0.062, 3.2), (90, 0, 0 if s < 0 else 180), "M_SignInfo")
        parts.append(face)
    # монитор
    parts.append(box("Monitor", (0.45, 0.04, 0.3), (0.2, 0.3, 1.3), "M_Black", 0.01, rot=(0, 0, 20)))
    parts.append(cyl("MonStand", 0.02, 0.12, (0.2, 0.32, 1.15), "M_PlasticGrey", 12, 0.002))
    return [finalize(parts, "InfoDesk")]


ASSETS = {
    "Props/ShoppingCart": shopping_cart,
    "Props/Bench": bench,
    "Props/FoodCourtTable": food_table,
    "Props/FoodCourtChair": food_chair,
    "Props/PlanterDeadPalm": planter_palm,
    "Props/Fountain": fountain,
    "Props/TrashBin": trash_bin,
    "Props/WetFloorSign": wet_floor_sign,
    "Props/InfoDesk": info_desk,
}
