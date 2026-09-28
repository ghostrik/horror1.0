"""Подсобки, техника, интерактивные предметы (подвижные части — отдельными объектами с правильным пивотом)."""
import math, random
from mathutils import Vector, Matrix
from lib import *


def parented(root, children):
    for c in children:
        c.parent = root
        c.matrix_parent_inverse = root.matrix_world.inverted()
    return [root] + children


# ------------------------------------------------------------------ служебная дверь с коробкой

def staff_door():
    frame_parts = []
    W, H, T = 0.98, 2.46, 0.045
    fw = 0.07
    for sx in (-1, 1):
        frame_parts.append(box("Jamb", (fw, 0.14, H + fw), (sx * (W / 2 + fw / 2), 0, (H + fw) / 2), "M_PaintedMetal", 0.006))
    frame_parts.append(box("Head", (W + 2 * fw, 0.14, fw), (0, 0, H + fw / 2), "M_PaintedMetal", 0.006))
    for sx in (-1, 1):
        frame_parts.append(box("Stop", (0.015, 0.03, H), (sx * (W / 2 - 0.004), 0.03, H / 2), "M_PaintedMetal", 0.002))
    frame = finalize(frame_parts, "DoorFrame")
    # створка: петли слева (x = -W/2), открывается внутрь
    leaf = []
    leaf.append(box("Leaf", (W - 0.01, T, H - 0.01), (0, 0, H / 2), "M_Door", 0.006))
    # окошко с армированным стеклом
    wz = 1.75
    for (sx, sz, x, z) in ((0.34, 0.03, 0, wz + 0.23), (0.34, 0.03, 0, wz - 0.23), (0.03, 0.49, -0.155, wz), (0.03, 0.49, 0.155, wz)):
        for sy in (-1, 1):
            leaf.append(box("WinTrim", (sx, 0.012, sz), (x, sy * (T / 2 + 0.004), z), "M_Chrome", 0.002))
    leaf.append(box("WinGlass", (0.3, T + 0.004, 0.43), (0, 0, wz), "M_GlassDark", 0))
    for i in range(5):
        leaf.append(box("Wire", (0.3, 0.002, 0.002), (0, -T / 2 - 0.003, wz - 0.18 + i * 0.09), "M_Chrome", 0))
        leaf.append(box("Wire", (0.002, 0.002, 0.43), (-0.12 + i * 0.06, -T / 2 - 0.003, wz), "M_Chrome", 0))
    # ручка-скоба и замок
    for sy in (-1, 1):
        rose = cyl("Rose", 0.03, 0.012, (W / 2 - 0.09, sy * (T / 2 + 0.006), 1.05), "M_Chrome", 20, 0.002, rot=(90, 0, 0))
        lever = tube("Lever", smooth_path([(W / 2 - 0.09, sy * (T / 2 + 0.01), 1.05), (W / 2 - 0.09, sy * (T / 2 + 0.06), 1.05), (W / 2 - 0.22, sy * (T / 2 + 0.065), 1.05)], steps=2), 0.01, "M_Chrome", res=10)
        key = cyl("Keyhole", 0.018, 0.01, (W / 2 - 0.09, sy * (T / 2 + 0.005), 0.92), "M_Chrome", 16, 0.002, rot=(90, 0, 0))
        leaf += [rose, lever, key]
        leaf.append(box("KickPlate", (W - 0.08, 0.003, 0.25), (0, sy * (T / 2 + 0.0015), 0.16), "M_Chrome", 0.001))
    for z in (0.25, 1.2, 2.2):
        leaf.append(cyl("Hinge", 0.012, 0.12, (-W / 2 + 0.005, -T / 2 - 0.006, z), "M_Chrome", 12, 0.002))
    leaf.append(box("Closer", (0.3, 0.06, 0.06), (-W / 2 + 0.25, 0.06, H - 0.1), "M_PlasticGrey", 0.01))
    leaf.append(box("CloserArm", (0.3, 0.015, 0.015), (-W / 2 + 0.3, 0.1, H + 0.02), "M_Chrome", 0.002, rot=(0, 0, -20)))
    plate = plane("Plate", 0.3, 0.08, (0, -T / 2 - 0.003, 1.45), (90, 0, 0), "M_SignFuse")
    leaf.append(plate)
    leaf_obj = finalize_group(leaf, "DoorLeaf", (-W / 2, 0, 0))
    return parented(frame, [leaf_obj])


# ------------------------------------------------------------------ раздвижная решётка входа

def security_grate():
    parts = []
    W, H = 5.0, 3.0
    parts.append(box("TopTrack", (W + 0.1, 0.08, 0.08), (0, 0, H - 0.04), "M_Grate", 0.006))
    parts.append(box("BottomTrack", (W + 0.1, 0.06, 0.02), (0, 0, 0.01), "M_Grate", 0.004))
    n = 22
    for i in range(n + 1):
        x = -W / 2 + i * W / n
        parts.append(box("Upright", (0.025, 0.035, H - 0.1), (x, 0, H / 2), "M_Grate", 0.004))
    # ножничные планки
    rows = 3
    for i in range(n):
        x0 = -W / 2 + i * W / n
        x1 = x0 + W / n
        for r in range(rows):
            z0 = 0.15 + r * (H - 0.3) / rows
            z1 = z0 + (H - 0.3) / rows
            for (a, b) in (((x0, z0), (x1, z1)), ((x0, z1), (x1, z0))):
                mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
                y = 0.024 if a[1] < b[1] else -0.024
                parts.append(box("Scissor", (L, 0.008, 0.028), (mid[0], y, mid[1]), "M_Grate", 0.002, rot=(0, -ang, 0)))
            parts.append(cyl("Rivet", 0.01, 0.07, ((x0 + x1) / 2, 0, (z0 + z1) / 2), "M_Chrome", 10, 0.002, rot=(90, 0, 0)))
    # замок и цепь
    parts.append(box("LockBody", (0.07, 0.03, 0.09), (0.05, -0.08, 1.1), "M_Chrome", 0.006))
    parts.append(torus("Shackle", 0.028, 0.006, (0.05, -0.08, 1.16), "M_Chrome", 20, 8, rot=(90, 0, 0)))
    for i in range(9):
        ang = 90 if i % 2 else 0
        parts.append(torus("ChainLink", 0.022, 0.005, (-0.14 + i * 0.035, -0.06, 1.2 - abs(i - 4) * 0.012), "M_Chrome", 16, 6, rot=(ang, 90, 0)))
    obj = finalize(parts, "SecurityGrate")
    return [obj]


# ------------------------------------------------------------------ рольставня

def rolling_shutter():
    frame = []
    W, H = 3.0, 2.9
    for sx in (-1, 1):
        frame.append(box("Guide", (0.08, 0.1, H), (sx * (W / 2 + 0.04), 0, H / 2), "M_Grate", 0.006))
    frame.append(box("Housing", (W + 0.2, 0.4, 0.4), (0, 0.1, H + 0.2), "M_ShutterTri", 0.02))
    frame.append(cyl("Motor", 0.09, 0.2, (W / 2 + 0.2, 0.1, H + 0.2), "M_PlasticGrey", 24, 0.006, rot=(0, 90, 0)))
    frame.append(box("Button", (0.1, 0.05, 0.16), (W / 2 + 0.3, -0.05, 1.3), "M_PlasticGrey", 0.008))
    frame.append(cyl("BtnUp", 0.015, 0.01, (W / 2 + 0.3, -0.078, 1.34), "M_GlowGreen", 12, 0, rot=(90, 0, 0)))
    frame.append(cyl("BtnDn", 0.015, 0.01, (W / 2 + 0.3, -0.078, 1.27), "M_GlowRed", 12, 0, rot=(90, 0, 0)))
    frame_obj = finalize(frame, "ShutterFrame")
    # полотно: гофрированные ламели
    slats = []
    prof = [(0.0, 0.0), (-0.012, 0.015), (-0.018, 0.035), (-0.012, 0.055), (0.0, 0.07), (0.006, 0.075)]
    n = int(H / 0.075)
    for i in range(n):
        z0 = i * 0.075
        v, f = [], []
        for (y, z) in prof:
            v.append((-W / 2, y, z0 + z)); v.append((W / 2, y, z0 + z))
        for k in range(len(prof) - 1):
            a = k * 2
            f.append((a, a + 1, a + 3, a + 2))
        s = mesh_obj("Slat", v, f, "M_ShutterTri")
        solidify(s, 0.0025)
        shade(s, 50)
        slats.append(s)
    slats.append(box("BottomBar", (W, 0.05, 0.06), (0, -0.008, 0.03), "M_Grate", 0.006))
    slats.append(box("Handle", (0.2, 0.04, 0.03), (0, -0.05, 0.1), "M_Chrome", 0.006))
    slats.append(box("LockPlate", (0.08, 0.01, 0.08), (0.6, -0.035, 0.12), "M_Chrome", 0.003))
    curtain = finalize(slats, "ShutterCurtain")
    return parented(frame_obj, [curtain])


# ------------------------------------------------------------------ шкафчик для персонала (2 дверцы)

def locker_door(name, w, h, x, hinge_x, number, R):
    parts = [box("Panel", (w - 0.006, 0.018, h), (x, -0.009, 0), "M_PaintedMetal", 0.004)]
    # жалюзи-выштамповки
    for i in range(6):
        z = h / 2 - 0.06 - i * 0.03
        s = box("Louver", (w * 0.6, 0.012, 0.012), (x, -0.02, z), "M_PaintedMetal", 0.002, rot=(-35, 0, 0))
        parts.append(s)
        parts.append(box("LouverHole", (w * 0.58, 0.002, 0.008), (x, -0.0185, z + 0.004), "M_Black", 0))
    for i in range(6):
        z = -h / 2 + 0.2 + i * 0.03
        parts.append(box("Louver", (w * 0.6, 0.012, 0.012), (x, -0.02, z), "M_PaintedMetal", 0.002, rot=(-35, 0, 0)))
    hx = x + (w / 2 - 0.05) * (1 if hinge_x < x else -1)
    parts.append(box("Handle", (0.03, 0.03, 0.12), (hx, -0.028, 0.02), "M_Chrome", 0.006))
    parts.append(torus("Hasp", 0.015, 0.004, (hx, -0.035, -0.07), "M_Chrome", 16, 6, rot=(90, 0, 0)))
    parts.append(box("NumPlate", (0.08, 0.004, 0.05), (x, -0.02, h / 2 - 0.28), "M_Chrome", 0.002))
    o = finalize_group(parts, name, (hinge_x, 0, 0))
    return o


def locker():
    R = random.Random(8)
    W, D, H = 0.8, 0.5, 1.95
    body = []
    body.append(box("Back", (W, 0.02, H), (0, D - 0.01, H / 2 + 0.1), "M_PaintedMetal", 0.004))
    for sx in (-1, 1):
        body.append(box("Side", (0.02, D, H), (sx * (W / 2 - 0.01), D / 2, H / 2 + 0.1), "M_PaintedMetal", 0.004))
    body.append(box("Mid", (0.02, D, H), (0, D / 2, H / 2 + 0.1), "M_PaintedMetal", 0.004))
    body.append(box("Top", (W, D, 0.02), (0, D / 2, H + 0.09), "M_PaintedMetal", 0.004))
    body.append(box("Bottom", (W, D, 0.02), (0, D / 2, 0.11), "M_PaintedMetal", 0.004))
    body.append(box("Plinth", (W, D - 0.04, 0.1), (0, D / 2, 0.05), "M_Black", 0.004))
    for sx in (-0.2, 0.2):
        body.append(box("Shelf", (W / 2 - 0.04, D - 0.04, 0.015), (sx, D / 2, 1.7), "M_PaintedMetal", 0.002))
        body.append(cyl("HangRod", 0.008, W / 2 - 0.04, (sx, D / 2, 1.6), "M_Chrome", 10, 0, rot=(0, 90, 0)))
    # немного вещей внутри
    body.append(box("Bag", (0.25, 0.2, 0.3), (-0.2, 0.3, 0.27), "M_Cloth", 0.03))
    body.append(box("Vest", (0.3, 0.05, 0.55), (0.2, 0.3, 1.3), "M_Uniform", 0.02))
    body_obj = finalize(body, "LockerBody")
    dl = locker_door("DoorL", W / 2 - 0.02, H - 0.04, -W / 4, -W / 2 + 0.01, 1, R)
    dr = locker_door("DoorR", W / 2 - 0.02, H - 0.04, W / 4, W / 2 - 0.01, 2, R)
    for d in (dl, dr):
        d.location.z += H / 2 + 0.1
    return parented(body_obj, [dl, dr])


def janitor_cabinet():
    R = random.Random(9)
    W, D, H = 0.9, 0.6, 2.0
    body = [box("Back", (W, 0.02, H), (0, D - 0.01, H / 2), "M_PaintedMetal", 0.004)]
    for sx in (-1, 1):
        body.append(box("Side", (0.02, D, H), (sx * (W / 2 - 0.01), D / 2, H / 2), "M_PaintedMetal", 0.004))
    body.append(box("Top", (W, D, 0.02), (0, D / 2, H - 0.01), "M_PaintedMetal", 0.004))
    body.append(box("Bottom", (W, D, 0.04), (0, D / 2, 0.02), "M_PaintedMetal", 0.004))
    body.append(box("Shelf", (W - 0.04, D - 0.04, 0.015), (0, D / 2, 1.6), "M_PaintedMetal", 0.002))
    for i in range(3):
        body += [cyl("Bottle", 0.04, 0.25, (-0.25 + i * 0.12, 0.3, 1.73), R.choice(["M_PackBlue", "M_PackYellow", "M_PackGreen"]), 16, 0.005)]
    body_obj = finalize(body, "CabinetBody")
    door = locker_door("Door", W - 0.02, H - 0.04, 0, -W / 2 + 0.01, 0, R)
    door.location.z += H / 2
    return parented(body_obj, [door])


def mop_bucket():
    parts = []
    parts.append(loft("Bucket", [(0.1, 0, 0, 0.2, 0.15, 3), (0.42, 0, 0, 0.23, 0.18, 3), (0.44, 0, 0, 0.24, 0.19, 3), (0.44, 0, 0, 0.22, 0.17, 3), (0.14, 0, 0, 0.19, 0.14, 3)], 32, "M_PlasticYellow", True, None, 40))
    parts.append(loft("Water", [(0.34, 0, 0, 0.215, 0.165, 3), (0.341, 0, 0, 0.215, 0.165, 3)], 32, "M_GlassDark", True, None, 40))
    wr = loft("Wringer", [(0, 0, 0, 0.06, 0.12, 5), (0.2, 0, 0, 0.1, 0.16, 5), (0.22, 0, 0, 0.11, 0.17, 5)], 24, "M_PlasticGrey", True, None, 40)
    wr.location = (0.12, 0, 0.42)
    parts.append(wr)
    for i in range(6):
        parts.append(box("WringerSlot", (0.012, 0.25, 0.004), (0.06 + i * 0.024, 0, 0.641), "M_Black", 0))
    parts.append(box("PressPlate", (0.03, 0.28, 0.16), (0.2, 0, 0.56), "M_PlasticGrey", 0.01, rot=(0, -15, 0)))
    parts.append(tube("WringerHandle", smooth_path([(0.2, 0, 0.62), (0.3, 0, 0.9), (0.33, 0, 1.0)], steps=2), 0.012, "M_PlasticGrey", res=8))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl("Caster", 0.03, 0.03, (sx * 0.17, sy * 0.12, 0.04), "M_Rubber", 12, 0.004, rot=(90, 0, 0)))
            parts.append(box("CasterMount", (0.03, 0.03, 0.06), (sx * 0.17, sy * 0.12, 0.08), "M_PlasticGrey", 0.004))
    # швабра
    mop = []
    mop.append(cyl("Stick", 0.012, 1.35, (-0.05, 0, 0.95), "M_Chrome", 12, 0.002, rot=(0, 12, 0)))
    for i in range(30):
        a = i / 30 * math.tau
        pts = smooth_path([(-0.12 + math.cos(a) * 0.03, math.sin(a) * 0.03, 0.3), (-0.12 + math.cos(a) * 0.08, math.sin(a) * 0.08, 0.16), (-0.12 + math.cos(a) * 0.1, math.sin(a) * 0.1, 0.12)], steps=2)
        mop.append(tube("Strand", pts, 0.008, "M_Cup", res=4))
    parts += mop
    parts.append(plane("Label", 0.12, 0.08, (0, -0.19, 0.3), (90, 0, 0), "M_Label"))
    return [finalize(parts, "MopBucket")]


# ------------------------------------------------------------------ щиток с рубильником + предохранитель

def fuse_item(name="Fuse", loc=(0, 0, 0)):
    parts = []
    parts.append(cyl("Body", 0.022, 0.09, (0, 0, 0), "M_Fuse", 24, 0.003))
    for s in (-1, 1):
        parts.append(cyl("Cap", 0.025, 0.018, (0, 0, s * 0.052), "M_Chrome", 24, 0.003))
        parts.append(cyl("Blade", 0.008, 0.02, (0, 0, s * 0.07), "M_Chrome", 12, 0.002))
    parts.append(cyl("Band", 0.0225, 0.03, (0, 0, 0), "M_PackRed", 24, 0))
    o = finalize(parts, name)
    o.location = loc
    return o


def fuse_asset():
    o = fuse_item()
    o.rotation_euler = (0, math.radians(90), 0)
    o.location = (0, 0, 0.025)
    apply_transform(o)
    return [o]


def fuse_box():
    W, H, D = 0.9, 1.2, 0.3
    body = []
    body.append(box("Back", (W, 0.02, H), (0, D - 0.01, 0), "M_Door", 0.004))
    for sx in (-1, 1):
        body.append(box("Side", (0.02, D, H), (sx * (W / 2 - 0.01), D / 2, 0), "M_Door", 0.004))
    for sz in (-1, 1):
        body.append(box("TopBot", (W, D, 0.02), (0, D / 2, sz * (H / 2 - 0.01)), "M_Door", 0.004))
    body.append(box("Inner", (W - 0.04, 0.01, H - 0.04), (0, D - 0.03, 0), "M_PlasticGrey", 0))
    # DIN-рейка с автоматами
    body.append(box("DinRail", (W - 0.1, 0.01, 0.035), (0, D - 0.05, 0.38), "M_Chrome", 0.002))
    for i in range(12):
        x = -0.36 + i * 0.065
        body.append(box("Breaker", (0.06, 0.07, 0.09), (x, D - 0.09, 0.38), "M_PackWhite", 0.004))
        body.append(box("Toggle", (0.015, 0.02, 0.025), (x, D - 0.13, 0.38 + (0.012 if i % 3 else -0.012)), "M_Black", 0.002))
    # гнёзда предохранителей
    for i in range(3):
        x = -0.25 + i * 0.25
        body.append(box("FuseHolder", (0.12, 0.05, 0.2), (x, D - 0.06, 0.05), "M_Black", 0.006))
        for s in (-1, 1):
            body.append(box("Clip", (0.04, 0.02, 0.02), (x, D - 0.09, 0.05 + s * 0.07), "M_Chrome", 0.002))
    body.append(box("LeverBase", (0.16, 0.06, 0.22), (0.25, D - 0.07, -0.32), "M_PlasticGrey", 0.01))
    # кабели
    for i, x in enumerate((-0.3, -0.15, 0.0, 0.15)):
        body.append(tube("Cable", smooth_path([(x, D - 0.05, H / 2 - 0.02), (x, D - 0.05, H / 2 + 0.4), (x * 0.5, D - 0.05, H / 2 + 1.0)], steps=2), 0.015, "M_Rubber", res=8))
    body.append(box("Warning", (0.14, 0.004, 0.12), (-0.25, -0.012, 0.42), "M_PlasticYellow", 0))
    body_obj = finalize(body, "FuseBoxBody")
    # дверца (петли слева)
    door = [box("DoorPanel", (W - 0.01, 0.02, H - 0.01), (0, -0.01, 0), "M_Door", 0.006)]
    door.append(box("DoorLatch", (0.03, 0.03, 0.1), (W / 2 - 0.06, -0.035, 0), "M_Chrome", 0.006))
    tri = mesh_obj("Bolt", [(-0.07, 0, -0.06), (0.07, 0, -0.06), (0, 0, 0.07)], [(0, 1, 2)], "M_PlasticYellow")
    tri.location = (0, -0.022, 0.3)
    door.append(tri)
    door.append(box("BoltMark", (0.02, 0.003, 0.08), (0, -0.024, 0.3), "M_Black", 0, rot=(0, 25, 0)))
    door_obj = finalize_group(door, "FuseBoxDoor", (-W / 2, 0, 0))
    # рубильник (вращается вокруг X)
    lev = [box("Arm", (0.03, 0.03, 0.22), (0, 0, 0.11), "M_Chrome", 0.006),
           cyl("Grip", 0.022, 0.1, (0, -0.04, 0.22), "M_GlowRed", 16, 0.004, rot=(90, 0, 0)),
           cyl("Pivot", 0.025, 0.1, (0, 0, 0), "M_Chrome", 16, 0.004, rot=(0, 90, 0))]
    lever = finalize_group(lev, "Lever", (0, 0, 0))
    lever.location = (0.25, D - 0.11, -0.32)
    fuses = []
    for i in range(3):
        f = fuse_item(f"FuseInSlot_{i}", (-0.25 + i * 0.25, D - 0.1, 0.05))
        fuses.append(f)
    return parented(body_obj, [door_obj, lever] + fuses)


def powerbank():
    parts = [box("Body", (0.07, 0.14, 0.018), (0, 0, 0.009), "M_Powerbank", 0.006, 3)]
    for i in range(4):
        parts.append(box("LED", (0.006, 0.003, 0.003), (-0.015 + i * 0.01, -0.07, 0.012), "M_GlowGreen" if i < 2 else "M_Black", 0))
    parts.append(box("USB", (0.014, 0.004, 0.006), (0.02, -0.0705, 0.008), "M_Black", 0))
    parts.append(tube("Cable", smooth_path([(0.02, -0.075, 0.008), (0.03, -0.12, 0.005), (-0.02, -0.16, 0.005), (-0.05, -0.12, 0.005)], steps=3), 0.0025, "M_PackWhite", res=6))
    return [finalize(parts, "Powerbank")]


def phone():
    parts = [box("Body", (0.074, 0.008, 0.155), (0, 0, 0), "M_Phone", 0.004, 3)]
    parts.append(box("Screen", (0.068, 0.001, 0.148), (0, -0.0045, 0), "M_ScreenGlow", 0))
    parts.append(box("Bump", (0.03, 0.003, 0.034), (-0.018, 0.005, 0.055), "M_Phone", 0.004))
    for (x, z) in ((-0.025, 0.063), (-0.011, 0.063), (-0.025, 0.048)):
        parts.append(cyl("Lens", 0.0055, 0.003, (x, 0.0068, z), "M_GlassDark", 16, 0.0005, rot=(90, 0, 0)))
        parts.append(cyl("LensRing", 0.0065, 0.002, (x, 0.0062, z), "M_Chrome", 16, 0.0005, rot=(90, 0, 0)))
    parts.append(cyl("Flash", 0.003, 0.002, (-0.011, 0.0068, 0.048), "M_GlowWarm", 12, 0, rot=(90, 0, 0)))
    for z in (0.03, 0.05):
        parts.append(box("VolBtn", (0.002, 0.004, 0.012), (-0.038, 0, z), "M_Phone", 0.001))
    parts.append(box("PwrBtn", (0.002, 0.004, 0.018), (0.038, 0, 0.035), "M_Phone", 0.001))
    return [finalize(parts, "Phone")]


# ------------------------------------------------------------------ свет и техника на потолке/стенах

def ceiling_lamp(broken=False):
    parts = []
    L, W = 1.25, 0.3
    parts.append(box("Housing", (W, L, 0.08), (0, 0, -0.04), "M_PlasticWhiteTri", 0.008))
    parts.append(box("Reflector", (W - 0.04, L - 0.04, 0.005), (0, 0, -0.078), "M_Chrome", 0))
    tubes = []
    for x in (-0.06, 0.06):
        t = cyl("Tube", 0.013, L - 0.1, (x, 0, -0.1), "M_GlowCold", 16, 0, rot=(90, 0, 0))
        tubes.append(t)
        for s in (-1, 1):
            parts.append(box("Socket", (0.035, 0.03, 0.035), (x, s * (L / 2 - 0.04), -0.095), "M_PlasticWhiteTri", 0.004))
    if broken:
        tubes[1].rotation_euler = (math.radians(90), math.radians(25), 0)
        tubes[1].location = (0.1, 0.1, -0.25)
    parts += tubes
    grid = []
    for i in range(9):
        grid.append(box("Louver", (W - 0.03, 0.004, 0.035), (0, -L / 2 + 0.07 + i * (L - 0.14) / 8, -0.1), "M_Chrome", 0))
    grid.append(box("Rail", (0.004, L - 0.04, 0.035), (-W / 2 + 0.02, 0, -0.1), "M_Chrome", 0))
    grid.append(box("Rail", (0.004, L - 0.04, 0.035), (W / 2 - 0.02, 0, -0.1), "M_Chrome", 0))
    if broken:
        g = finalize(grid, "LouverGrid")
        g.rotation_euler = (math.radians(-38), 0, 0)
        g.location = (0, -L / 2 + 0.02, 0)
        # повисла на проводе
        for v in g.data.vertices:
            v.co.y += L / 2 - 0.02
        parts.append(g)
        parts.append(tube("Wire", [(0.0, L / 2 - 0.1, -0.08), (0.02, L / 2 - 0.2, -0.4), (0.0, 0.2, -0.75)], 0.004, "M_Rubber", res=6))
    else:
        parts += grid
    parts.append(tube("Cable", [(0, 0, 0), (0, 0, 0.4)], 0.005, "M_Rubber", res=6))
    return [finalize(parts, "CeilingLamp_Broken" if broken else "CeilingLamp")]


def ceiling_lamp_ok():
    return ceiling_lamp(False)


def ceiling_lamp_broken():
    return ceiling_lamp(True)


def emergency_beacon():
    parts = [cyl("Base", 0.08, 0.05, (0, 0, 0.025), "M_PlasticGrey", 32, 0.006)]
    dome = lathe("Dome", [(0.065, 0.05), (0.065, 0.12), (0.055, 0.17), (0.03, 0.195), (0, 0.2)], 32, "M_GlowRed")
    parts.append(dome)
    parts.append(cyl("Reflector", 0.02, 0.1, (0, 0, 0.11), "M_Chrome", 12, 0))
    for i in range(6):
        a = i / 6 * math.tau
        parts.append(tube("Cage", smooth_path([(math.cos(a) * 0.075, math.sin(a) * 0.075, 0.05), (math.cos(a) * 0.075, math.sin(a) * 0.075, 0.14), (math.cos(a) * 0.04, math.sin(a) * 0.04, 0.2), (0, 0, 0.215)], steps=2), 0.003, "M_Chrome", res=6))
    parts.append(torus("CageRing", 0.075, 0.003, (0, 0, 0.1), "M_Chrome", 32, 6))
    return [finalize(parts, "EmergencyBeacon")]


def pa_speaker():
    parts = [lathe("Rim", [(0.13, 0.0), (0.14, -0.005), (0.14, -0.015), (0.12, -0.02), (0.11, -0.02)], 48, "M_PlasticWhiteTri")]
    parts.append(cyl("Grill", 0.11, 0.004, (0, 0, -0.018), "M_Chrome", 48, 0))
    for r in (0.03, 0.05, 0.07, 0.09):
        parts.append(torus("GrillRing", r, 0.0025, (0, 0, -0.021), "M_Black", 48, 6))
    parts.append(cyl("Can", 0.1, 0.12, (0, 0, 0.06), "M_PlasticGrey", 32, 0.006))
    return [finalize(parts, "PASpeaker")]


def cctv_camera():
    parts = [box("WallPlate", (0.1, 0.02, 0.14), (0, 0.01, 0), "M_PlasticWhiteTri", 0.006)]
    parts.append(tube("Arm", smooth_path([(0, 0, 0), (0, -0.12, 0.02), (0, -0.2, 0.08)], steps=2), 0.015, "M_PlasticWhiteTri", res=10))
    body = loft("Housing", [(0, 0, 0, 0.05, 0.045, 4), (0.26, 0, 0, 0.055, 0.05, 4), (0.3, 0, 0, 0.055, 0.05, 4)], 24, "M_PlasticWhiteTri", True, None, 40)
    body.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    body.location = (0, -0.1, 0.12)
    body.rotation_euler = (math.radians(18), 0, 0)
    parts.append(body)
    parts.append(box("Hood", (0.13, 0.32, 0.01), (0, -0.261, 0.185), "M_PlasticWhiteTri", 0.003, rot=(18, 0, 0)))
    parts.append(cyl("LensRing", 0.042, 0.02, (0, -0.39, 0.03), "M_PlasticGrey", 24, 0.003, rot=(108, 0, 0)))
    parts.append(cyl("Lens", 0.03, 0.02, (0, -0.398, 0.027), "M_GlassDark", 24, 0.003, rot=(108, 0, 0)))
    parts.append(cyl("LED", 0.005, 0.004, (0.03, -0.39, 0.072), "M_GlowRed", 10, 0, rot=(108, 0, 0)))
    return [finalize(parts, "CCTVCamera")]


def exit_sign():
    parts = [box("Box", (0.4, 0.06, 0.16), (0, 0, 0), "M_PlasticWhiteTri", 0.01)]
    for s in (-1, 1):
        f = plane("Face", 0.36, 0.0225 * 5, (0, s * 0.031, 0), (90, 0, 0 if s < 0 else 180), "M_SignExit")
        parts.append(f)
    parts.append(box("Mount", (0.06, 0.06, 0.12), (0, 0, 0.14), "M_PlasticWhiteTri", 0.006))
    return [finalize(parts, "ExitSign")]


# ------------------------------------------------------------------ фотобудка

def photo_booth():
    R = random.Random(21)
    parts = []
    W, D, H = 1.3, 1.3, 2.25
    parts.append(box("Back", (W, 0.05, H), (0, D / 2 - 0.025, H / 2), "M_PlasticRed", 0.02))
    for sx in (-1, 1):
        parts.append(box("Side", (0.05, D, H), (sx * (W / 2 - 0.025), 0, H / 2), "M_PlasticRed", 0.02))
    parts.append(box("Roof", (W + 0.04, D + 0.04, 0.08), (0, 0, H + 0.04), "M_PlasticRed", 0.02))
    parts.append(box("Header", (W + 0.04, 0.08, 0.3), (0, -D / 2 - 0.02, H + 0.15), "M_PlasticWhiteTri", 0.02))
    parts.append(plane("HeaderSign", W - 0.1, (W - 0.1) / 16 * 2.2, (0, -D / 2 - 0.063, H + 0.15), (90, 0, 0), "M_SignPhoto"))
    parts.append(box("Base", (W + 0.02, D + 0.02, 0.06), (0, 0, 0.03), "M_Black", 0.01))
    # внутри
    parts.append(box("CameraPanel", (0.6, 0.04, 0.5), (0, D / 2 - 0.07, 1.4), "M_Black", 0.01))
    parts.append(plane("CameraScreen", 0.3, 0.2, (0, D / 2 - 0.092, 1.45), (90, 0, 0), "M_ScreenGlow"))
    parts.append(cyl("Lens", 0.03, 0.02, (0, D / 2 - 0.1, 1.62), "M_GlassDark", 20, 0.003, rot=(90, 0, 0)))
    parts.append(box("FlashPanel", (0.5, 0.03, 0.12), (0, D / 2 - 0.06, 1.85), "M_GlowWarm", 0.006))
    parts.append(cyl("StoolSeat", 0.2, 0.05, (0, 0.05, 0.55), "M_Cloth", 24, 0.01))
    parts.append(cyl("StoolPole", 0.025, 0.5, (0, 0.05, 0.28), "M_Chrome", 12, 0.002))
    parts.append(cyl("StoolBase", 0.18, 0.02, (0, 0.05, 0.01), "M_Chrome", 24, 0.003))
    # штора со складками (оставлена щель)
    cv, cf = [], []
    nx, nz = 40, 10
    cw, ch = W * 0.75, H - 0.35
    for j in range(nz + 1):
        for i in range(nx + 1):
            u = i / nx
            x = -W / 2 + 0.05 + u * cw
            z = 0.25 + j / nz * ch
            y = -D / 2 + 0.02 + math.sin(u * math.pi * 9) * 0.03 * (0.6 + 0.4 * (1 - j / nz))
            cv.append((x, y, z))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            cf.append((a, a + 1, a + nx + 2, a + nx + 1))
    curtain = mesh_obj("Curtain", cv, cf, "M_Cloth")
    solidify(curtain, 0.006)
    shade(curtain, 70)
    parts.append(curtain)
    parts.append(cyl("CurtainRod", 0.012, W - 0.1, (0, -D / 2 + 0.02, H - 0.08), "M_Chrome", 12, 0.002, rot=(0, 90, 0)))
    # боковая панель с образцами фото и приёмником монет
    for i in range(4):
        parts.append(plane("PhotoSample", 0.16, 0.22, (W / 2 + 0.002, -0.35 + i * 0.2, 1.55), (90, 0, 90), "M_PosterPromoter"))
    parts.append(box("CoinBox", (0.03, 0.2, 0.3), (W / 2 + 0.015, 0.3, 1.1), "M_Chrome", 0.006))
    parts.append(box("PhotoSlot", (0.03, 0.18, 0.02), (W / 2 + 0.015, 0.3, 0.8), "M_Black", 0.003))
    parts.append(plane("PhotoStrip", 0.05, 0.18, (W / 2 + 0.035, 0.3, 0.72), (60, 0, 90), "M_PosterSale"))
    return [finalize(parts, "PhotoBooth")]


def _open_fusebox(objs):
    for o in objs:
        if o.name == "FuseBoxDoor":
            o.rotation_euler = (0, 0, math.radians(-115))


RENDER_OPTS = {
    "Props/CeilingLamp": {"render_rot": (180,), "cam_dir": (-0.8, -1.2, 0.7)},
    "Props/CeilingLamp_Broken": {"render_rot": (180,)},
    "Props/PASpeaker": {"render_rot": (180,)},
    "Props/FuseBox": {"pose_for_render": _open_fusebox},
    "Items/Phone": {"cam_dir": (0.9, 1.1, 0.6)},
    "Props/Locker": {"pose_for_render": lambda objs: [setattr(o, "rotation_euler", (0, 0, math.radians(-100))) for o in objs if o.name == "DoorR"]},
}

ASSETS = {
    "Props/StaffDoor": staff_door,
    "Props/SecurityGrate": security_grate,
    "Props/RollingShutter": rolling_shutter,
    "Props/Locker": locker,
    "Props/JanitorCabinet": janitor_cabinet,
    "Props/MopBucket": mop_bucket,
    "Props/FuseBox": fuse_box,
    "Items/Fuse": fuse_asset,
    "Items/Powerbank": powerbank,
    "Items/Phone": phone,
    "Props/CeilingLamp": ceiling_lamp_ok,
    "Props/CeilingLamp_Broken": ceiling_lamp_broken,
    "Props/EmergencyBeacon": emergency_beacon,
    "Props/PASpeaker": pa_speaker,
    "Props/CCTVCamera": cctv_camera,
    "Props/ExitSign": exit_sign,
    "Props/PhotoBooth": photo_booth,
}
