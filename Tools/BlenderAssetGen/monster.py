"""Мерчандайзер: сегментированный манекен-промоутер с арматурой и анимациями Idle/Walk/Chase/Jumpscare."""
import bpy, math, random
from mathutils import Vector, Matrix, Quaternion, Euler
from lib import *

FPS = 30

# ------------------------------------------------------------------ опорные точки скелета (метры, лицо смотрит в -Y)
J = {
    "hip": Vector((0, 0, 1.2)),
    "waist": Vector((0, 0, 1.38)),
    "chest": Vector((0, 0, 1.64)),
    "neck": Vector((0, 0.01, 1.93)),
    "head": Vector((0, 0.0, 2.07)),
    "headtop": Vector((0, 0.0, 2.47)),
}
SIDE = {}
for s, sx in (("L", 1), ("R", -1)):
    SIDE[s] = {
        "shoulder": Vector((0.25 * sx, 0.01, 1.855)),
        "elbow": Vector((0.3 * sx, 0.04, 1.39)),
        "wrist": Vector((0.32 * sx, 0.0, 0.92)),
        "fingertip": Vector((0.33 * sx, -0.01, 0.62)),
        "hip": Vector((0.1 * sx, 0.0, 1.16)),
        "knee": Vector((0.105 * sx, -0.01, 0.66)),
        "ankle": Vector((0.1 * sx, 0.02, 0.1)),
        "toe": Vector((0.1 * sx, -0.19, 0.03)),
    }

HEAD_C = Vector((0, 0.0, 2.26))
HEAD_R = (0.122, 0.145, 0.205)   # rx, ry(глубина), rz


def head_rx(zn):
    """Ширина головы в зависимости от высоты (сужение к подбородку)."""
    return 1.0 - 0.28 * max(0.0, -zn) ** 1.6


def head_surface(x, z):
    """Точка передней поверхности головы для локальных x,z относительно центра."""
    rx, ry, rz = HEAD_R
    zn = z / rz
    w = rx * head_rx(zn)
    t = 1 - (x / w) ** 2 - zn ** 2
    y = -ry * math.sqrt(max(t, 0.0)) * (1 - 0.18 * max(0.0, -zn) ** 2)
    return Vector((x, y, z))


def split_faces(o, pred, name):
    """Вынести грани, центры которых удовлетворяют pred(center), в отдельный объект."""
    import bmesh
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    sel = [f for f in bm.faces if pred(f.calc_center_median())]
    new_me = D.meshes.new(name)
    bm2 = bm.copy()
    keep_idx = {f.index for f in sel}
    bm2.faces.ensure_lookup_table()
    bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.index not in keep_idx], context="FACES")
    bm2.to_mesh(new_me); bm2.free()
    bmesh.ops.delete(bm, geom=sel, context="FACES")
    bm.to_mesh(me); bm.free()
    no = D.objects.new(name, new_me)
    link(no)
    for m in me.materials:
        new_me.materials.append(m)
    return no


def project_grid(bvh, x0, x1, z0, z1, nx, nz, offset, uv_fn, name, mat):
    from mathutils import Vector as V
    verts, faces, uvs = [], [], []
    for j in range(nz + 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            z = z0 + (z1 - z0) * j / nz
            hit, nrm, idx, dist = bvh.ray_cast(V((x, -1.0, z)), V((0, 1, 0)))
            if hit is None:
                hit, nrm = V((x, HEAD_C.y - 0.01, z)), V((0, -1, 0))
            verts.append(tuple(hit + nrm * offset))
            uvs.append(uv_fn(i / nx, j / nz))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    o = mesh_obj(name, verts, faces, mat)
    uvl = o.data.uv_layers.new(name="UVMap")
    for poly in o.data.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices):
            uvl.data[li].uv = uvs[vi]
    shade(o, 80)
    return o


JAW_CUT = -0.075   # относительно центра головы


def build_head(parts_by_bone):
    from mathutils.bvhtree import BVHTree
    rx, ry, rz = HEAD_R
    secs = []
    n = 18
    for i in range(n + 1):
        a = -math.pi / 2 + i / n * math.pi
        zn = math.sin(a)
        r = math.cos(a)
        z = zn * rz
        w = rx * r * head_rx(zn)
        d = ry * r * (1 - 0.2 * max(0.0, -zn) ** 2)
        secs.append((z, 0, 0.012 * zn, max(w, 0.002), max(d, 0.002), 2.0))
    skull = loft("Skull", secs, 36, "M_Plastic", True, None, 60, 1)
    skull.location = HEAD_C
    apply_transform(skull)
    dg = C.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(skull, dg)
    # маска (текстура: лицо-эллипс x 40..472, y 20..502 из 512)
    fx0, fx1, fz0, fz1 = -0.118, 0.118, HEAD_C.z - 0.2, HEAD_C.z + 0.2
    mask = project_grid(bvh, fx0, fx1, fz0, fz1, 26, 30, 0.0025,
                        lambda u, v: ((40 + u * 432) / 512, 1 - (20 + (1 - v) * 482) / 512), "FaceMask", "M_MannequinFace")
    leds = []
    for sx in (-1, 1):
        px0, px1 = (110, 230) if sx < 0 else (282, 402)
        tx = lambda t, a=px0, b=px1: fx0 + (fx1 - fx0) * ((a + (b - a) * t - 40) / 432)
        tz = lambda t: fz0 + (fz1 - fz0) * (1 - ((225 - 55 * t) - 20) / 482)
        led = project_grid(bvh, tx(0), tx(1), tz(0), tz(1), 10, 4, 0.0045, lambda u, v: (u, v), "LED", "M_LED")
        leds.append(led)
        frame = project_grid(bvh, tx(0) - 0.006, tx(1) + 0.006, tz(0) - 0.006, tz(1) + 0.006, 10, 4, 0.0035, lambda u, v: (u, v), "LEDFrame", "M_Black")
        leds.append(frame)
    # челюсть: вырезаем нижнюю-переднюю часть черепа и маски
    cutz = HEAD_C.z + JAW_CUT
    pred = lambda c: c.z < cutz and c.y < HEAD_C.y - 0.03 and abs(c.x) < 0.085
    jaw_skull = split_faces(skull, pred, "JawShell")
    jaw_mask = split_faces(mask, lambda c: c.z < cutz and abs(c.x) < 0.085, "JawMask")
    # полость рта и зубы (видны только при открытой челюсти)
    cavity = sphere("MouthCavity", 0.075, HEAD_C + Vector((0, -0.03, -0.1)), "M_Black", 20, 12, scale=(1.0, 0.9, 0.7))
    apply_transform(cavity)
    teeth = []
    for i in range(8):
        x = -0.049 + i * 0.014
        yy = HEAD_C.y - 0.104 + abs(x) * 0.45
        teeth.append(box("Tooth", (0.01, 0.012, 0.02), (x, yy, cutz - 0.004), "M_Cup", 0.002))
    lower = []
    for i in range(7):
        x = -0.042 + i * 0.014
        yy = HEAD_C.y - 0.098 + abs(x) * 0.45
        lower.append(box("LowerTooth", (0.01, 0.012, 0.016), (x, yy, cutz - 0.022), "M_Cup", 0.002))
    ears = [sphere("EarJoint", 0.022, HEAD_C + Vector((sx * rx * 0.95, 0.02, -0.07)), "M_PlasticJoint", 16, 10) for sx in (-1, 1)]
    parts_by_bone["Head"] += [skull, mask, cavity] + ears + leds + teeth
    parts_by_bone["Jaw"] += [jaw_skull, jaw_mask] + lower


def build_torso(parts_by_bone):
    # таз
    pel = loft("Pelvis", [(1.08, 0, 0.0, 0.1, 0.08, 2.6), (1.14, 0, 0, 0.145, 0.1, 2.6), (1.24, 0, 0, 0.16, 0.105, 2.6), (1.33, 0, 0, 0.14, 0.095, 2.5), (1.37, 0, 0, 0.125, 0.088, 2.4)], 32, "M_Plastic", True, None, 50, 1)
    parts_by_bone["Hips"].append(pel)
    parts_by_bone["Hips"].append(torus("WaistSeam", 0.122, 0.012, (0, 0, 1.375), "M_PlasticJoint", 40, 8))
    parts_by_bone["Hips"][-1].scale = (1, 0.72, 1)
    apply_transform(parts_by_bone["Hips"][-1])
    # грудь/торс
    secs = [(1.37, 0, 0, 0.12, 0.085, 2.4), (1.45, 0, 0, 0.123, 0.085, 2.4), (1.55, 0, 0.0, 0.138, 0.094, 2.4), (1.65, 0, -0.004, 0.152, 0.104, 2.5),
            (1.74, 0, -0.004, 0.163, 0.106, 2.6), (1.82, 0, 0.0, 0.172, 0.097, 2.8), (1.88, 0, 0.01, 0.15, 0.08, 2.6), (1.92, 0, 0.012, 0.08, 0.055, 2.2)]
    torso = loft("Chest", secs, 36, "M_Plastic", True, None, 50, 1)
    parts_by_bone["Chest"].append(torso)
    # жилет промоутера
    vsecs = [(z, cx, cy - 0.002, rx * 1.075 + 0.004, ry * 1.09 + 0.004, e) for (z, cx, cy, rx, ry, e) in secs[1:7]]
    vest = loft("Vest", vsecs, 36, "M_Uniform", False, None, 50, 1)
    solidify(vest, 0.008)
    parts_by_bone["Chest"].append(vest)
    hem = torus("VestHem", 1.0, 0.006, (0, -0.002, vsecs[0][0]), "M_PlasticWhiteTri", 48, 6)
    hem.scale = (vsecs[0][3] + 0.01, vsecs[0][4] + 0.01, 1)
    apply_transform(hem)
    parts_by_bone["Chest"].append(hem)
    # воротник
    for sx in (-1, 1):
        col = mesh_obj("Collar", [(0, -0.06, 1.9), (sx * 0.1, -0.045, 1.9), (sx * 0.07, -0.1, 1.84), (sx * 0.015, -0.11, 1.83)], [(0, 1, 2, 3)], "M_PlasticWhiteTri")
        solidify(col, 0.004)
        parts_by_bone["Chest"].append(col)
    # пуговицы и бейдж
    for i in range(4):
        z = 1.5 + i * 0.09
        y = -0.1 - 0.006 * math.sin(i)
        parts_by_bone["Chest"].append(cyl("Button", 0.009, 0.006, (0, y - 0.012, z), "M_Chrome", 12, 0.001, rot=(90, 0, 0)))
    badge = plane("Badge", 0.07, 0.035, (0.08, -0.125, 1.76), (80, 0, 12), "M_Receipt")
    parts_by_bone["Chest"].append(badge)
    parts_by_bone["Chest"].append(box("BadgeClip", (0.02, 0.004, 0.01), (0.08, -0.124, 1.782), "M_Chrome", 0))
    # шея
    neck = limb("Neck", J["neck"] + Vector((0, 0, -0.02)), J["head"] + Vector((0, 0, 0.05)), 0.042, 0.038, "M_Plastic", 20, 0, 0.9, None, 1)
    parts_by_bone["Neck"].append(neck)
    parts_by_bone["Neck"].append(sphere("NeckJoint", 0.048, J["neck"] + Vector((0, 0, 0.005)), "M_PlasticJoint", 20, 12))


def build_hand(side, parts):
    s = SIDE[side]
    sx = 1 if side == "L" else -1
    w = s["wrist"]
    palm = loft("Palm", [(0, 0, 0, 0.028, 0.012, 2.6), (0.05, 0, 0, 0.036, 0.013, 2.6), (0.095, 0, 0, 0.038, 0.011, 3.0)], 16, "M_Plastic", True, None, 50, 1)
    palm.data.transform(Matrix.Rotation(math.pi, 4, "X"))   # вниз
    palm.location = w + Vector((0, 0, -0.025))
    apply_transform(palm)
    parts.append(palm)
    base = w + Vector((0, 0, -0.12))
    for fi in range(4):
        fx = (-0.027 + fi * 0.018) * sx
        L = [0.075, 0.085, 0.08, 0.065][fi] * 1.25
        p0 = base + Vector((fx, 0, 0))
        curl = 0.25 + fi * 0.05
        p1 = p0 + Vector((0, -math.sin(curl * 0.5) * L * 0.4, -L * 0.45))
        p2 = p1 + Vector((0, -math.sin(curl) * L * 0.35, -L * 0.33))
        p3 = p2 + Vector((0, -math.sin(curl * 1.6) * L * 0.3, -L * 0.25))
        for a, b, r in ((p0, p1, 0.0085), (p1, p2, 0.0075), (p2, p3, 0.0065)):
            parts.append(limb("Finger", a, b, r, r * 0.92, "M_Plastic", 10, 0, 1.0, None, 0, 3))
    th0 = w + Vector((-0.03 * sx, -0.015, -0.04))
    th1 = th0 + Vector((-0.02 * sx, -0.03, -0.045))
    th2 = th1 + Vector((-0.005 * sx, -0.025, -0.035))
    parts.append(limb("Thumb", th0, th1, 0.011, 0.0095, "M_Plastic", 10, 0, 1.0, None, 0, 3))
    parts.append(limb("Thumb", th1, th2, 0.0095, 0.008, "M_Plastic", 10, 0, 1.0, None, 0, 3))


def build_limbs(parts_by_bone):
    for side in ("L", "R"):
        s = SIDE[side]
        sx = 1 if side == "L" else -1
        # рука
        parts_by_bone[f"UpperArm.{side}"] += [sphere("ShoulderJoint", 0.058, s["shoulder"], "M_PlasticJoint", 20, 12),
                                               limb("UpperArm", s["shoulder"], s["elbow"], 0.047, 0.034, "M_Plastic", 20, 0.006, 0.92)]
        parts_by_bone[f"ForeArm.{side}"] += [sphere("ElbowJoint", 0.04, s["elbow"], "M_PlasticJoint", 18, 10),
                                              limb("ForeArm", s["elbow"], s["wrist"], 0.036, 0.024, "M_Plastic", 20, 0.004, 0.85)]
        parts_by_bone[f"Hand.{side}"].append(sphere("WristJoint", 0.027, s["wrist"], "M_PlasticJoint", 16, 10))
        build_hand(side, parts_by_bone[f"Hand.{side}"])
        # нога
        parts_by_bone[f"Thigh.{side}"] += [sphere("HipJoint", 0.068, s["hip"] + Vector((0, 0, 0.01)), "M_PlasticJoint", 20, 12),
                                            limb("Thigh", s["hip"], s["knee"], 0.078, 0.05, "M_Plastic", 22, 0.01, 0.95)]
        parts_by_bone[f"Shin.{side}"] += [sphere("KneeJoint", 0.052, s["knee"], "M_PlasticJoint", 18, 10),
                                           limb("Shin", s["knee"], s["ankle"], 0.05, 0.031, "M_Plastic", 20, 0.008, 0.95)]
        fsecs = [(0.0, 0, 0.0, 0.03, 0.03, 2.2), (0.03, 0, 0.004, 0.038, 0.042, 2.4), (0.09, 0, 0.0, 0.043, 0.04, 2.6), (0.16, 0, -0.012, 0.043, 0.028, 2.8),
                 (0.22, 0, -0.02, 0.036, 0.018, 2.6), (0.25, 0, -0.022, 0.026, 0.011, 2.2), (0.262, 0, -0.022, 0.012, 0.006, 2.0)]
        foot = loft("Foot", fsecs, 18, "M_Plastic", True, None, 50, 1)
        foot.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))   # ось лофта Z -> -Y (носок вперёд)
        foot.location = s["ankle"] + Vector((0, 0.06, -0.055))
        apply_transform(foot)
        parts_by_bone[f"Foot.{side}"] += [sphere("AnkleJoint", 0.03, s["ankle"], "M_PlasticJoint", 16, 10), foot]
    # обломок стойки-штыря, торчащий из правой икры
    parts_by_bone["Shin.R"].append(cyl("BrokenRod", 0.009, 0.28, tuple(SIDE["R"]["knee"] + Vector((0.02, 0.06, -0.3))), "M_Chrome", 12, 0.002, rot=(-35, 10, 0)))
    parts_by_bone["Shin.R"].append(cyl("RodCollar", 0.02, 0.02, tuple(SIDE["R"]["knee"] + Vector((0.005, 0.035, -0.23))), "M_Chrome", 16, 0.002, rot=(-35, 10, 0)))


BONES = [
    # имя, голова, хвост, родитель
    ("Root", Vector((0, 0, 0)), Vector((0, 0, 0.25)), None),
    ("Hips", J["hip"], J["waist"], "Root"),
    ("Spine", J["waist"], J["chest"], "Hips"),
    ("Chest", J["chest"], J["neck"], "Spine"),
    ("Neck", J["neck"], J["head"], "Chest"),
    ("Head", J["head"], J["headtop"], "Neck"),
    ("Jaw", HEAD_C + Vector((0, 0.02, -0.07)), HEAD_C + Vector((0, -0.12, -0.14)), "Head"),
]
for sd in ("L", "R"):
    s = SIDE[sd]
    BONES += [
        (f"UpperArm.{sd}", s["shoulder"], s["elbow"], "Chest"),
        (f"ForeArm.{sd}", s["elbow"], s["wrist"], f"UpperArm.{sd}"),
        (f"Hand.{sd}", s["wrist"], s["fingertip"], f"ForeArm.{sd}"),
        (f"Thigh.{sd}", s["hip"], s["knee"], "Hips"),
        (f"Shin.{sd}", s["knee"], s["ankle"], f"Thigh.{sd}"),
        (f"Foot.{sd}", s["ankle"], s["toe"], f"Shin.{sd}"),
    ]


def build_armature():
    ad = D.armatures.new("MerchandiserRig")
    arm = D.objects.new("MerchandiserRig", ad)
    link(arm)
    C.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for name, h, t, par in BONES:
        b = ad.edit_bones.new(name)
        b.head, b.tail = h, t
        b.roll = 0
        if par:
            b.parent = eb[par]
            b.use_connect = False
        eb[name] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


# ------------------------------------------------------------------ анимация: вращения задаём в мировых осях покоя

def set_rot(arm, bone, rx=0, ry=0, rz=0):
    """Поворот кости: углы (градусы) вокруг МИРОВЫХ осей X,Y,Z в позе покоя."""
    b = arm.data.bones[bone]
    M = b.matrix_local.to_3x3()
    Rw = (Matrix.Rotation(math.radians(rz), 3, "Z") @ Matrix.Rotation(math.radians(ry), 3, "Y") @ Matrix.Rotation(math.radians(rx), 3, "X"))
    Rl = M.inverted() @ Rw @ M
    pb = arm.pose.bones[bone]
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = Rl.to_quaternion()


def key_pose(arm, frame, pose, root_z=0.0, root_y=0.0, interp=None):
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = Quaternion()
        pb.location = (0, 0, 0)
    for bone, r in pose.items():
        set_rot(arm, bone, *r)
    arm.pose.bones["Root"].location = (0, root_z, -root_y)  # оси кости Root: локальная Y = мировая Z, локальная Z = мировая -Y
    for pb in arm.pose.bones:
        pb.keyframe_insert("rotation_quaternion", frame=frame)
    arm.pose.bones["Root"].keyframe_insert("location", frame=frame)


def set_interp(action, mode):
    try:
        curves = action.fcurves
    except AttributeError:
        curves = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = mode


def make_action(arm, name, keys, interp="BEZIER"):
    act = D.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    for frame, pose, rz, ry in keys:
        key_pose(arm, frame, pose, rz, ry)
    set_interp(act, interp)
    return act


def walk_pose(t, amp=1.0, lean=4, arms_reach=0.0, arm_amp=1.0):
    """Поза цикла ходьбы, t в [0,1)."""
    ph = t * math.tau
    s = math.sin(ph)
    c = math.cos(ph)
    leg = 30 * amp
    pose = {
        "Thigh.L": (-s * leg, 0, 0), "Thigh.R": (s * leg, 0, 0),
        "Shin.L": (max(0, c) * 45 * amp, 0, 0), "Shin.R": (max(0, -c) * 45 * amp, 0, 0),
        "Foot.L": (-s * 10 * amp, 0, 0), "Foot.R": (s * 10 * amp, 0, 0),
        "Hips": (0, s * 4 * amp, s * 6 * amp),
        "Spine": (lean * 0.5, -s * 3 * amp, -s * 5 * amp),
        "Chest": (lean * 0.5, 0, -s * 4 * amp),
        "Neck": (-lean * 0.3, 0, 0),
        "Head": (-lean * 0.25 + math.sin(ph * 2) * 3, s * 5, 0),
    }
    reach = arms_reach
    for sd, sg in (("L", 1), ("R", -1)):
        swing = sg * s * 22 * amp * arm_amp
        pose[f"UpperArm.{sd}"] = (swing * (1 - reach) - 78 * reach + (sg * s * 8 * reach), 0, sg * 6)
        pose[f"ForeArm.{sd}"] = (-12 - 10 * reach - abs(s) * 6, 0, 0)
        pose[f"Hand.{sd}"] = (-8 - 10 * reach, 0, 0)
    return pose


def build_actions(arm):
    arm.animation_data_create()
    acts = []
    # Idle: дыхание + механические рывки головы (ступенчатая интерполяция по отдельным ключам)
    keys = []
    R = random.Random(4)
    heads = [(0, 0, 0), (0, 0, 0), (12, 0, 25), (12, 0, 25), (-5, 20, -10), (-5, 20, -10), (0, 0, 35), (0, 0, 0)]
    for i in range(9):
        f = 1 + i * 12
        br = math.sin(i / 8 * math.tau)
        hp = heads[i % len(heads)]
        pose = {"Spine": (br * 1.5, 0, 0), "Chest": (br * 2, 0, 0), "Head": hp, "Neck": (3, 0, 0),
                "UpperArm.L": (-2 + br * 2, 0, 8), "UpperArm.R": (-2 - br * 2, 0, -8),
                "ForeArm.L": (-10, 0, 0), "ForeArm.R": (-14, 0, 0), "Hand.L": (-10, 0, 0), "Hand.R": (-6, 0, 0),
                "Jaw": (6 + (10 if i in (3, 6) else 0), 0, 0)}
        keys.append((f, pose, br * 0.004, 0))
    acts.append(make_action(arm, "Idle", keys, "CONSTANT"))
    # Walk: механическая ходьба, 32 кадра
    keys = [(1 + int(i * 4), walk_pose(i / 8, 1.0, 5), abs(math.sin(i / 8 * math.tau)) * 0.03, 0) for i in range(9)]
    acts.append(make_action(arm, "Walk", keys, "BEZIER"))
    # Chase: рывковый бег с протянутыми руками, 20 кадров
    keys = []
    for i in range(9):
        t = i / 8
        p = walk_pose(t, 1.5, 26, arms_reach=1.0, arm_amp=0.3)
        p["Jaw"] = (22 + 10 * math.sin(t * math.tau * 2), 0, 0)
        p["Head"] = (-18 + math.sin(t * math.tau * 2) * 6, math.sin(t * math.tau) * 12, math.sin(t * math.tau * 3) * 15)
        keys.append((1 + int(round(i * 2.5)), p, abs(math.sin(t * math.tau)) * 0.06 - 0.03, 0))
    acts.append(make_action(arm, "Chase", keys, "BEZIER"))
    # Jumpscare: рывок, руки вверх и в стороны, челюсть отпадает, голова трясётся
    keys = []
    for i, f in enumerate((1, 4, 7, 9, 11, 13, 15, 17, 20, 24)):
        k = min(1.0, i / 2)
        shake = (R.uniform(-25, 25), R.uniform(-20, 20), R.uniform(-35, 35)) if i >= 2 else (0, 0, 0)
        pose = {"Spine": (12 * k, 0, 0), "Chest": (10 * k, 0, 0), "Neck": (-6 * k, 0, 0), "Head": (-12 * k + shake[0], shake[1], shake[2]),
                "Jaw": (48 * k, 0, 0),
                "UpperArm.L": (-150 * k, 0, 35 * k), "UpperArm.R": (-150 * k, 0, -35 * k),
                "ForeArm.L": (-35 * k, 0, 0), "ForeArm.R": (-35 * k, 0, 0), "Hand.L": (-30 * k, 0, 0), "Hand.R": (-30 * k, 0, 0),
                "Thigh.L": (-20 * k, 0, 0), "Shin.L": (25 * k, 0, 0), "Thigh.R": (10 * k, 0, 0), "Shin.R": (15 * k, 0, 0)}
        keys.append((f, pose, -0.05 * k, -0.25 * k))
    acts.append(make_action(arm, "Jumpscare", keys, "LINEAR"))
    arm.animation_data.action = acts[0]
    return acts


# ------------------------------------------------------------------ сборка

def merchandiser():
    bones = [b[0] for b in BONES]
    parts_by_bone = {b: [] for b in bones}
    build_head(parts_by_bone)
    build_torso(parts_by_bone)
    build_limbs(parts_by_bone)
    # собираем по костям, назначаем жёсткие веса
    pieces = []
    for bone, parts in parts_by_bone.items():
        if not parts:
            continue
        for p in parts:
            apply_transform(p)
            if not p.data.uv_layers:
                uv_box(p, 2.0)
        o = join(parts, "Part_" + bone)
        vg = o.vertex_groups.new(name=bone)
        vg.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
        pieces.append(o)
    body = join(pieces, "Merchandiser")
    arm = build_armature()
    body.parent = arm
    mod = body.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    acts = build_actions(arm)
    set_pose(arm, None, 0)
    return {"objects": [arm, body], "anim": True, "actions": [a.name for a in acts],
            "cam_dir": (-0.55, -1.35, 0.3), "pad": 1.02, "extra": extra_renders}


def set_pose(arm, action_name, frame):
    if action_name is None:
        arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0)
    else:
        arm.animation_data.action = D.actions[action_name]
        try:
            arm.animation_data.action_slot = arm.animation_data.action.slots[0]
        except Exception:
            pass
    C.scene.frame_set(frame)
    C.view_layer.update()


def _cleanup(keep):
    for o in list(D.objects):
        if o not in keep:
            D.objects.remove(o, do_unlink=True)


def extra_renders(objs, out_dir):
    import os
    arm, body = objs
    shots = [("Idle", "Idle", 30, (-0.3, -1.4, 0.25)), ("Walk", "Walk", 9, (-1.2, -0.9, 0.3)),
             ("Chase", "Chase", 6, (-0.9, -1.2, 0.25)), ("Jumpscare", "Jumpscare", 13, (-0.25, -1.4, 0.05))]
    def red(center, k):
        ld = D.lights.new("Under", "POINT"); ld.energy = 60 * k * k; ld.color = (1, 0.15, 0.08)
        lo = D.objects.new("Under", ld); link(lo); lo.location = center + Vector((0, -0.8, -0.6)) * k
    for label, act, frame, cam in shots:
        _cleanup([arm, body])
        set_pose(arm, act, frame)
        studio([body], os.path.join(out_dir, f"Characters_Merchandiser_{label}.png"), samples=64, cam_dir=cam, fov_pad=1.0, extra_light=red)
    # крупный план головы
    _cleanup([arm, body])
    set_pose(arm, "Idle", 30)
    hb = box("HeadTarget", (0.34, 0.34, 0.5), tuple(HEAD_C + Vector((0, -0.02, -0.02))), "M_Black", 0)
    hb.hide_render = True
    studio([hb], os.path.join(out_dir, "Characters_Merchandiser_Head.png"), samples=96, cam_dir=(-0.35, -1.3, 0.12), fov_pad=0.95, focal=85, extra_light=red)
    _cleanup([arm, body])
    set_pose(arm, "Jumpscare", 20)
    hp = arm.matrix_world @ arm.pose.bones["Head"].head
    hb = box("HeadTarget", (0.34, 0.34, 0.5), tuple(hp + Vector((0, -0.05, 0.18))), "M_Black", 0)
    hb.hide_render = True
    studio([hb], os.path.join(out_dir, "Characters_Merchandiser_HeadScream.png"), samples=96, cam_dir=(0.25, -1.3, 0.05), fov_pad=1.6, focal=85, extra_light=red, floor_z=0.0)
    # "игровой" кадр: темнота, луч фонарика телефона, отражение на полу
    _cleanup([arm, body])
    set_pose(arm, "Chase", 11)
    def flashlight(center, k):
        cam = C.scene.camera
        ld = D.lights.new("Phone", "SPOT"); ld.energy = 900; ld.spot_size = math.radians(38); ld.spot_blend = 0.6
        ld.color = (1, 0.95, 0.88); ld.shadow_soft_size = 0.02
        lo = D.objects.new("Phone", ld); link(lo)
        lo.location = center + Vector((0.35, -3.4, 0.05))
        lo.rotation_euler = (center + Vector((0, 0, 0.25)) - lo.location).to_track_quat("-Z", "Y").to_euler()
        red(center, k)
    studio([body], os.path.join(out_dir, "Characters_Merchandiser_Hero.png"), samples=128, cam_dir=(0.12, -1.4, 0.02), fov_pad=0.95, focal=35,
           extra_light=flashlight, bg=(0.004, 0.004, 0.006), lights=False)


ASSETS = {"Characters/Merchandiser": merchandiser}
