"""Библиотека процедурного моделирования для Blender 5 (bpy): формы, материалы, UV, экспорт, рендер."""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Euler

PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX_DIR = os.path.join(PROJECT, "Assets", "Textures")
C = bpy.context
D = bpy.data


# ============================================================== сцена

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MATS.clear()


def link(obj, parent=None):
    C.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def empty(name, loc=(0, 0, 0), parent=None):
    o = D.objects.new(name, None)
    o.location = loc
    return link(o, parent)


def mesh_obj(name, verts, faces, mat=None, smooth=False, parent=None):
    me = D.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate()
    me.update()
    o = D.objects.new(name, me)
    link(o, parent)
    if mat:
        set_mat(o, mat)
    if smooth:
        shade(o, smooth if isinstance(smooth, (int, float)) and not isinstance(smooth, bool) else 40)
    return o


def shade(o, angle=40):
    """Сглаживание по углу (как Auto Smooth)."""
    me = o.data
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(angle))


def flat(o):
    for p in o.data.polygons:
        p.use_smooth = False


def xform(o, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc
    if rot is not None: o.rotation_euler = [math.radians(a) for a in rot]
    if scale is not None: o.scale = scale if isinstance(scale, (tuple, list)) else (scale,) * 3
    return o


def apply_transform(o):
    """Запечь трансформ объекта в меш (без операторов)."""
    if o.type != "MESH":
        return o
    o.data.transform(o.matrix_basis)
    o.matrix_basis = Matrix.Identity(4)
    return o


def bake(o):
    """Применить все модификаторы (через evaluated mesh)."""
    dg = C.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = D.meshes.new_from_object(ev)
    old = o.data
    o.modifiers.clear()
    o.data = me
    if old.users == 0:
        D.meshes.remove(old)
    return o


def bevel(o, width=0.005, segments=2, angle=35, apply=True, harden=True):
    m = o.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.harden_normals = False
    m.miter_outer = "MITER_ARC"
    if apply:
        bake(o)
        shade(o, 35)
    return o


def subsurf(o, levels=2, apply=True):
    m = o.modifiers.new("Subsurf", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    if apply:
        bake(o)
    return o


def solidify(o, t=0.01, offset=0, apply=True):
    m = o.modifiers.new("Solid", "SOLIDIFY")
    m.thickness = t
    m.offset = offset
    if apply:
        bake(o)
    return o


def join(objs, name=None):
    objs = [o for o in objs if o is not None]
    for o in C.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    C.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = objs[0]
    if name:
        o.name = name
        o.data.name = name
    return o


def copy(o, loc=None, rot=None, scale=None, parent=None, name=None):
    n = o.copy()
    n.data = o.data.copy()
    link(n, parent if parent is not None else o.parent)
    if name: n.name = name
    xform(n, loc, rot, scale)
    return n


def mirror_x(o, name=None):
    n = copy(o, name=name)
    apply_transform(n)
    n.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
    n.data.flip_normals()
    return n


# ============================================================== примитивы

def box(name, size, loc=(0, 0, 0), mat=None, bev=0.004, seg=2, rot=None, parent=None):
    sx, sy, sz = [s / 2 for s in size]
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz), (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    o = mesh_obj(name, v, f, mat, parent=parent)
    if bev > 0:
        bevel(o, min(bev, min(size) * 0.45), seg)
    else:
        flat(o)
    xform(o, loc, rot)
    return o


def cyl(name, r, h, loc=(0, 0, 0), mat=None, n=24, bev=0.003, rot=None, r2=None, cap=True, parent=None, smooth=True):
    """Цилиндр вдоль Z, основание в z=0 локально (центр по Z = h/2)."""
    r2 = r if r2 is None else r2
    verts, faces = [], []
    for i in range(n):
        a = i / n * math.tau
        verts.append((math.cos(a) * r, math.sin(a) * r, -h / 2))
    for i in range(n):
        a = i / n * math.tau
        verts.append((math.cos(a) * r2, math.sin(a) * r2, h / 2))
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    if cap:
        faces.append(tuple(range(n - 1, -1, -1)))
        faces.append(tuple(range(n, 2 * n)))
    o = mesh_obj(name, verts, faces, mat, parent=parent)
    if bev > 0:
        bevel(o, bev, 2, 50)
    if smooth:
        shade(o, 40)
    xform(o, loc, rot)
    return o


def lathe(name, profile, n=48, mat=None, loc=(0, 0, 0), rot=None, parent=None, angle=40):
    """Тело вращения: profile = [(r, z), ...] снизу вверх. r=0 — точка на оси."""
    verts, faces = [], []
    rings = []
    for (r, z) in profile:
        if r <= 1e-6:
            rings.append([len(verts)])
            verts.append((0, 0, z))
        else:
            ring = []
            for i in range(n):
                a = i / n * math.tau
                ring.append(len(verts))
                verts.append((math.cos(a) * r, math.sin(a) * r, z))
            rings.append(ring)
    for a, b in zip(rings[:-1], rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(n):
                faces.append((a[0], b[i], b[(i + 1) % n]))
        elif len(b) == 1:
            for i in range(n):
                faces.append((a[i], b[0], a[(i + 1) % n]))
        else:
            for i in range(n):
                j = (i + 1) % n
                faces.append((a[i], a[j], b[j], b[i]))
    o = mesh_obj(name, verts, faces, mat, parent=parent)
    shade(o, angle)
    xform(o, loc, rot)
    return o


def superellipse_ring(cx, cy, z, rx, ry, n, e=2.0, rot=0.0):
    pts = []
    for i in range(n):
        a = i / n * math.tau
        c, s = math.cos(a), math.sin(a)
        x = math.copysign(abs(c) ** (2 / e), c) * rx
        y = math.copysign(abs(s) ** (2 / e), s) * ry
        xr = x * math.cos(rot) - y * math.sin(rot)
        yr = x * math.sin(rot) + y * math.cos(rot)
        pts.append((cx + xr, cy + yr, z))
    return pts


def loft(name, sections, n=24, mat=None, caps=True, parent=None, smooth=40, sub=0):
    """Лофт по сечениям: [(z, cx, cy, rx, ry, e), ...] (e — степень суперэллипса, 2 = эллипс)."""
    verts, faces = [], []
    for s in sections:
        z, cx, cy, rx, ry = s[:5]
        e = s[5] if len(s) > 5 else 2.0
        verts += superellipse_ring(cx, cy, z, rx, ry, n, e)
    m = len(sections)
    for k in range(m - 1):
        for i in range(n):
            j = (i + 1) % n
            faces.append((k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i))
    if caps:
        faces.append(tuple(range(n - 1, -1, -1)))
        faces.append(tuple(range((m - 1) * n, m * n)))
    o = mesh_obj(name, verts, faces, mat, parent=parent)
    if sub:
        subsurf(o, sub)
    if smooth:
        shade(o, smooth)
    return o


def limb(name, a, b, r_a, r_b, mat=None, n=20, bulge=0.0, flatten=1.0, parent=None, sub=1, sections=6):
    """Сужающийся сегмент конечности от точки a до b (с лёгкой "мышцей" bulge)."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    secs = []
    for k in range(sections + 1):
        t = k / sections
        r = r_a + (r_b - r_a) * t + math.sin(t * math.pi) * bulge
        secs.append((t * L, 0, 0, r, r * flatten, 2.0))
    # скругление концов
    secs.insert(0, (-r_a * 0.35, 0, 0, r_a * 0.6, r_a * 0.6 * flatten, 2.0))
    secs.append((L + r_b * 0.35, 0, 0, r_b * 0.6, r_b * 0.6 * flatten, 2.0))
    o = loft(name, secs, n, mat, True, parent, 40, sub)
    # ориентируем Z -> направление a->b
    d = (b - a).normalized()
    q = Vector((0, 0, 1)).rotation_difference(d)
    o.data.transform(q.to_matrix().to_4x4())
    o.data.transform(Matrix.Translation(a))
    return o


def tube(name, pts, r=0.01, mat=None, closed=False, res=6, parent=None, smooth=True):
    """Труба/проволока по ломаной (кривая с bevel -> меш)."""
    cu = D.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = max(0, res // 2 - 1)
    cu.fill_mode = "FULL"
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (c[0], c[1], c[2], 1)
    sp.use_cyclic_u = closed
    tmp = D.objects.new(name + "_c", cu)
    link(tmp)
    me = D.meshes.new_from_object(tmp.evaluated_get(C.evaluated_depsgraph_get()))
    D.objects.remove(tmp)
    D.curves.remove(cu)
    o = D.objects.new(name, me)
    link(o, parent)
    if mat: set_mat(o, mat)
    if smooth: shade(o, 50)
    return o


def smooth_path(pts, radius=0.03, steps=4):
    """Скругляет углы ломаной (для гнутых труб): простое сглаживание Чайкина."""
    p = [Vector(x) for x in pts]
    for _ in range(steps):
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]):
            q.append(a.lerp(b, 0.25)); q.append(a.lerp(b, 0.75))
        q.append(p[-1])
        p = q
    return [tuple(v) for v in p]


def torus(name, R, r, loc=(0, 0, 0), mat=None, n=32, m=12, rot=None, parent=None):
    verts, faces = [], []
    for i in range(n):
        a = i / n * math.tau
        for j in range(m):
            b = j / m * math.tau
            x = (R + r * math.cos(b)) * math.cos(a)
            y = (R + r * math.cos(b)) * math.sin(a)
            verts.append((x, y, r * math.sin(b)))
    for i in range(n):
        for j in range(m):
            a, b = i * m + j, i * m + (j + 1) % m
            c, d = ((i + 1) % n) * m + (j + 1) % m, ((i + 1) % n) * m + j
            faces.append((a, b, c, d))
    o = mesh_obj(name, verts, faces, mat, parent=parent)
    shade(o, 60)
    xform(o, loc, rot)
    return o


def sphere(name, r, loc=(0, 0, 0), mat=None, seg=24, rings=16, scale=None, parent=None):
    verts, faces = [(0, 0, -r)], []
    for i in range(1, rings):
        th = -math.pi / 2 + i / rings * math.pi
        for j in range(seg):
            ph = j / seg * math.tau
            verts.append((r * math.cos(th) * math.cos(ph), r * math.cos(th) * math.sin(ph), r * math.sin(th)))
    verts.append((0, 0, r))
    top = len(verts) - 1
    for j in range(seg):
        faces.append((0, 1 + (j + 1) % seg, 1 + j))
    for i in range(rings - 2):
        for j in range(seg):
            a = 1 + i * seg + j
            b = 1 + i * seg + (j + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    base = 1 + (rings - 2) * seg
    for j in range(seg):
        faces.append((base + j, base + (j + 1) % seg, top))
    o = mesh_obj(name, verts, faces, mat, parent=parent)
    shade(o, 80)
    xform(o, loc, None, scale)
    return o


def plane(name, w, h, loc=(0, 0, 0), rot=(90, 0, 0), mat=None, parent=None, nx=1, ny=1):
    """Плоскость в XY (после rot=(90,0,0) — вертикальная, лицом в -Y)."""
    verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            verts.append((-w / 2 + w * i / nx, -h / 2 + h * j / ny, 0))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    o = mesh_obj(name, verts, faces, mat, parent=parent)
    uv_front_xy(o, -w / 2, w / 2, -h / 2, h / 2)
    flat(o)
    xform(o, loc, rot)
    return o


def uv_front_xy(o, xmin, xmax, ymin, ymax):
    me = o.data
    name = _uv_layer(me)
    bm = bmesh.new(); bm.from_mesh(me)
    uv = bm.loops.layers.uv[name]
    for f in bm.faces:
        for l in f.loops:
            co = l.vert.co
            l[uv].uv = ((co.x - xmin) / (xmax - xmin), (co.y - ymin) / (ymax - ymin))
    bm.to_mesh(me); bm.free()


def set_origin(o, point):
    """Перенести точку отсчёта объекта в point (мировые координаты), геометрия остаётся на месте."""
    apply_transform(o)
    p = Vector(point)
    o.data.transform(Matrix.Translation(-p))
    o.location = p
    return o


def finalize_group(parts, name, pivot=(0, 0, 0)):
    o = finalize(parts, name)
    set_origin(o, pivot)
    return o


def array(o, count, offset, name=None):
    """Копии объекта со смещением; возвращает список (включая исходный)."""
    out = [o]
    for i in range(1, count):
        n = copy(o, loc=tuple(Vector(o.location) + Vector(offset) * i))
        out.append(n)
    return out


# ============================================================== UV

def _uv_layer(me):
    if "UVMap" not in me.uv_layers:
        me.uv_layers.new(name="UVMap")
    me.uv_layers.active = me.uv_layers["UVMap"]
    return "UVMap"


def uv_box(o, scale=1.0):
    """Кубическая проекция UV по нормали грани (как трипланар)."""
    me = o.data
    name = _uv_layer(me)
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv[name]
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda k: abs(n[k]))
        for l in f.loops:
            co = l.vert.co
            if ax == 0: u, v = co.y * math.copysign(1, n.x), co.z
            elif ax == 1: u, v = -co.x * math.copysign(1, n.y), co.z
            else: u, v = co.x, co.y * math.copysign(1, n.z)
            l[uv].uv = (u * scale, v * scale)
    bm.to_mesh(me)
    bm.free()


def uv_front(o, xmin, xmax, zmin, zmax):
    """Фронтальная проекция XZ -> UV 0..1 (для лиц, экранов, табло)."""
    me = o.data
    name = _uv_layer(me)
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv[name]
    for f in bm.faces:
        for l in f.loops:
            co = l.vert.co
            l[uv].uv = ((co.x - xmin) / (xmax - xmin), (co.z - zmin) / (zmax - zmin))
    bm.to_mesh(me)
    bm.free()


def uv_smart(o, margin=0.02):
    for x in C.view_layer.objects:
        x.select_set(False)
    o.select_set(True)
    C.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=margin)
    bpy.ops.object.mode_set(mode="OBJECT")


# ============================================================== материалы
# Имена совпадают с материалами Unity-проекта (Assets/Materials) — при импорте FBX они подменяются на них.

MATS = {}

# name: (kind, params)
#   kind: "std" (UV-текстура), "tri" (коробочная проекция по объекту), "glow", "decal", "flat"
LIB = {
    "M_Chrome": ("flat", dict(color=(0.75, 0.76, 0.78), metal=1.0, rough=0.18)),
    "M_Metal": ("tri", dict(tex="T_Metal", scale=1.0, metal=0.6, rough=0.45)),
    "M_MetalTri": ("tri", dict(tex="T_Metal", scale=1.0, metal=0.6, rough=0.45)),
    "M_PaintedMetal": ("tri", dict(tex="T_Metal", scale=1.0, metal=0.2, rough=0.5, tint=(0.45, 0.55, 0.5))),
    "M_Plastic": ("tri", dict(tex="T_Plastic", scale=1.6, rough=0.22)),
    "M_PlasticJoint": ("tri", dict(tex="T_Plastic", scale=2.0, rough=0.35, tint=(0.75, 0.7, 0.66))),
    "M_PlasticWhiteTri": ("tri", dict(tex="T_Plastic", scale=1.0, rough=0.4, tint=(0.92, 0.92, 0.9))),
    "M_PlasticYellow": ("flat", dict(color=(0.9, 0.55, 0.0), rough=0.35)),
    "M_PlasticRed": ("flat", dict(color=(0.45, 0.012, 0.01), rough=0.35)),
    "M_PlasticBlue": ("flat", dict(color=(0.05, 0.18, 0.55), rough=0.35)),
    "M_PlasticGrey": ("flat", dict(color=(0.18, 0.19, 0.2), rough=0.45)),
    "M_Uniform": ("tri", dict(tex="T_FabricRed", scale=3.0, rough=0.85)),
    "M_Rubber": ("flat", dict(color=(0.03, 0.03, 0.03), rough=0.7)),
    "M_GlassDark": ("glass", dict(color=(0.02, 0.025, 0.03), rough=0.05)),
    "M_GlassFreezer": ("clear", dict(color=(0.85, 0.92, 1.0), rough=0.03)),
    "M_Black": ("flat", dict(color=(0.01, 0.01, 0.01), rough=0.6)),
    "M_WoodTri": ("tri", dict(tex="T_Wood", scale=1.5, rough=0.55)),
    "M_StoneTri": ("tri", dict(tex="T_FloorMall", scale=0.9, rough=0.3)),
    "M_FountainTiles": ("tri", dict(tex="T_FountainTiles", scale=1.2, rough=0.3)),
    "M_ShutterTri": ("tri", dict(tex="T_Shutter", scale=0.8, metal=0.5, rough=0.45)),
    "M_CardboardTri": ("tri", dict(tex="T_Cardboard", scale=1.8, rough=0.85)),
    "M_FabricTri": ("tri", dict(tex="T_FabricRed", scale=2.0, rough=0.9, tint=(0.5, 0.55, 0.75))),
    "M_Cloth": ("tri", dict(tex="T_FabricRed", scale=2.0, rough=0.95, tint=(0.35, 0.1, 0.25))),
    "M_Door": ("tri", dict(tex="T_Metal", scale=1.0, metal=0.4, rough=0.5, tint=(0.45, 0.52, 0.58))),
    "M_Grate": ("flat", dict(color=(0.18, 0.18, 0.2), metal=0.85, rough=0.45)),
    "M_Fuse": ("flat", dict(color=(0.85, 0.8, 0.6), metal=0.1, rough=0.35)),
    "M_Powerbank": ("flat", dict(color=(0.15, 0.35, 0.2), rough=0.4)),
    "M_Leaves": ("flat", dict(color=(0.26, 0.2, 0.1), rough=0.8)),
    "M_Trunk": ("tri", dict(tex="T_Wood", scale=3.0, rough=0.9, tint=(0.5, 0.4, 0.3))),
    "M_Cup": ("flat", dict(color=(0.85, 0.8, 0.72), rough=0.5)),
    "M_LampOff": ("flat", dict(color=(0.35, 0.36, 0.38), metal=0.2, rough=0.4)),
    "M_Phone": ("flat", dict(color=(0.03, 0.03, 0.035), metal=0.3, rough=0.25)),
    "M_ProductsA": ("tri", dict(tex="T_Products_A", scale=0.9, rough=0.6)),
    "M_ProductsB": ("tri", dict(tex="T_Products_B", scale=0.9, rough=0.6)),
    "M_ProductsC": ("tri", dict(tex="T_Products_C", scale=0.9, rough=0.6)),
    "M_PackRed": ("flat", dict(color=(0.6, 0.06, 0.05), rough=0.5)),
    "M_PackBlue": ("flat", dict(color=(0.08, 0.2, 0.55), rough=0.5)),
    "M_PackYellow": ("flat", dict(color=(0.85, 0.65, 0.08), rough=0.5)),
    "M_PackGreen": ("flat", dict(color=(0.1, 0.4, 0.15), rough=0.5)),
    "M_PackWhite": ("flat", dict(color=(0.8, 0.8, 0.78), rough=0.5)),
    "M_PackOrange": ("flat", dict(color=(0.8, 0.3, 0.05), rough=0.5)),
    "M_Label": ("std", dict(tex="T_PaperScribble", rough=0.6)),
    "M_Receipt": ("std", dict(tex="T_PaperReceipt", rough=0.7)),
    "M_Paper": ("std", dict(tex="T_PaperScribble", rough=0.7)),
    "M_VHS": ("std", dict(tex="T_VHS", rough=0.5)),
    "M_PosterSale": ("std", dict(tex="T_PosterSale", rough=0.6)),
    "M_PosterPromoter": ("std", dict(tex="T_PosterPromoter", rough=0.6)),
    "M_Concrete": ("tri", dict(tex="T_Concrete", scale=0.5, rough=0.8)),
    "M_GlowWarm": ("glow", dict(color=(1, 0.85, 0.62), strength=6)),
    "M_GlowCold": ("glow", dict(color=(0.8, 0.9, 1), strength=6)),
    "M_GlowRed": ("glow", dict(color=(1, 0.1, 0.06), strength=8)),
    "M_GlowGreen": ("glow", dict(color=(0.2, 1, 0.35), strength=5)),
    "M_GlowOrange": ("glow", dict(color=(1, 0.55, 0.2), strength=5)),
    "M_GlowFreezer": ("glow", dict(color=(0.45, 0.7, 1), strength=2.5, tex="T_Products_B")),
    "M_ScreenGlow": ("glow", dict(color=(0.16, 0.2, 0.26), strength=2)),
    "M_Vending": ("glow", dict(color=(0.7, 0.85, 1), strength=1.5)),
    "M_LED": ("glow", dict(color=(1, 0.2, 0.08), strength=10, tex="T_LEDBoard", uvscale=(0.35, 0.25), uvoff=(0, 0.75))),
    "M_Garland": ("glow", dict(color=(1, 0.9, 0.6), strength=6)),
    "M_MannequinFace": ("decal", dict(tex="T_MannequinFace", rough=0.25)),
    "M_SignExit": ("glow", dict(color=(1, 1, 1), strength=3, tex="T_Signs", uvscale=(1, 1 / 16), uvoff=(0, 1 - 5 / 16))),
    "M_SignPhoto": ("glow", dict(color=(1, 1, 1), strength=2, tex="T_Signs", uvscale=(1, 1 / 16), uvoff=(0, 1 - 12 / 16))),
    "M_SignInfo": ("std", dict(tex="T_Signs", rough=0.4, uvscale=(1, 1 / 16), uvoff=(0, 1 - 15 / 16))),
    "M_SignCash": ("std", dict(tex="T_Signs", rough=0.4, uvscale=(1, 1 / 16), uvoff=(0, 1 - 7 / 16))),
    "M_SignFuse": ("std", dict(tex="T_Signs", rough=0.4, uvscale=(1, 1 / 16), uvoff=(0, 1 - 13 / 16))),
}


def _img(name):
    p = os.path.join(TEX_DIR, name + ".png")
    img = D.images.get(name + ".png") or D.images.load(p, check_existing=True)
    return img


def get_mat(name):
    if name in MATS:
        return MATS[name]
    kind, p = LIB[name]
    m = D.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    out = nt.nodes.get("Material Output")
    base = p.get("color", (1, 1, 1))
    bsdf.inputs["Roughness"].default_value = p.get("rough", 0.5)
    bsdf.inputs["Metallic"].default_value = p.get("metal", 0.0)
    tex_node = None
    if "tex" in p:
        tex_node = nt.nodes.new("ShaderNodeTexImage")
        tex_node.image = _img(p["tex"])
        coord = nt.nodes.new("ShaderNodeTexCoord")
        mapn = nt.nodes.new("ShaderNodeMapping")
        if kind == "tri":
            tex_node.projection = "BOX"
            tex_node.projection_blend = 0.25
            nt.links.new(coord.outputs["Object"], mapn.inputs["Vector"])
            s = p.get("scale", 1.0)
            mapn.inputs["Scale"].default_value = (s, s, s)
        else:
            nt.links.new(coord.outputs["UV"], mapn.inputs["Vector"])
            us = p.get("uvscale", (1, 1)); uo = p.get("uvoff", (0, 0))
            mapn.inputs["Scale"].default_value = (us[0], us[1], 1)
            mapn.inputs["Location"].default_value = (uo[0], uo[1], 0)
        nt.links.new(mapn.outputs["Vector"], tex_node.inputs["Vector"])
    if kind in ("std", "tri", "decal"):
        if tex_node:
            if "tint" in p:
                mix = nt.nodes.new("ShaderNodeMix")
                mix.data_type = "RGBA"
                mix.blend_type = "MULTIPLY"
                mix.inputs["Factor"].default_value = 1.0
                nt.links.new(tex_node.outputs["Color"], mix.inputs[6])
                mix.inputs[7].default_value = (*p["tint"], 1)
                nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
            else:
                nt.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
            if kind == "decal":
                nt.links.new(tex_node.outputs["Alpha"], bsdf.inputs["Alpha"])
                m.surface_render_method = "DITHERED" if hasattr(m, "surface_render_method") else None
        else:
            bsdf.inputs["Base Color"].default_value = (*base, 1)
    elif kind == "flat":
        bsdf.inputs["Base Color"].default_value = (*base, 1)
    elif kind == "glass":
        bsdf.inputs["Base Color"].default_value = (*base, 1)
        bsdf.inputs["Coat Weight"].default_value = 1.0
        bsdf.inputs["Specular IOR Level"].default_value = 0.8
    elif kind == "clear":
        bsdf.inputs["Base Color"].default_value = (*base, 1)
        bsdf.inputs["Transmission Weight"].default_value = 1.0
        bsdf.inputs["IOR"].default_value = 1.45
    elif kind == "glow":
        bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = p.get("strength", 5)
        if tex_node:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1
            nt.links.new(tex_node.outputs["Color"], mix.inputs[6])
            mix.inputs[7].default_value = (*base, 1)
            nt.links.new(mix.outputs[2], em.inputs["Color"])
        else:
            em.inputs["Color"].default_value = (*base, 1)
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    MATS[name] = m
    return m


def set_mat(o, name):
    o.data.materials.clear()
    o.data.materials.append(get_mat(name))
    return o


def add_mat(o, name):
    """Добавить слот материала, вернуть его индекс."""
    m = get_mat(name)
    for i, s in enumerate(o.data.materials):
        if s == m:
            return i
    o.data.materials.append(m)
    return len(o.data.materials) - 1


# ============================================================== экспорт

def finalize(objs, name):
    """Склеить всё в один объект с несколькими материалами, UV-развертка, начало в (0,0,0)."""
    objs = [o for o in objs if o is not None and o.type == "MESH"]
    for o in objs:
        o.parent = None
    for o in objs:
        apply_transform(o)
        if not o.data.uv_layers:
            uv_box(o, 1.0)
    obj = join(objs, name)
    return obj


def export_fbx(objs, path, anim=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for o in C.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    kw = dict(filepath=path, use_selection=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
              mesh_smooth_type="FACE", use_mesh_modifiers=True, add_leaf_bones=False, use_tspace=False,
              object_types={"MESH", "ARMATURE", "EMPTY"}, path_mode="STRIP")
    if anim:
        kw.update(bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                  bake_anim_simplify_factor=0.0, bake_space_transform=False, primary_bone_axis="Y", secondary_bone_axis="X")
    else:
        kw.update(bake_anim=False, bake_space_transform=True)
    bpy.ops.export_scene.fbx(**kw)


def stats(o):
    me = o.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    return tris


# ============================================================== рендер-превью

def studio(target_objs, path, res=640, samples=64, cam_dir=(-0.85, -1.25, 0.55), fov_pad=1.18, focal=50, extra_light=None, bg=(0.035, 0.037, 0.045), floor_z=None, lights=True, key_scale=1.0):
    sc = C.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    # мир
    w = D.worlds.new("W"); sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (*bg, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
    # габариты
    mn = Vector((1e9, 1e9, 1e9)); mx = Vector((-1e9, -1e9, -1e9))
    dg = C.evaluated_depsgraph_get()
    for o in target_objs:
        ev = o.evaluated_get(dg)
        for c in ev.bound_box:
            p = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, p)); mx = Vector(map(max, mx, p))
    center = (mn + mx) / 2
    size = (mx - mn)
    radius = size.length / 2
    # фон-подложка (циклорама)
    fl = max(size.x, size.y, size.z) * 6 + 4
    fz = mn.z if floor_z is None else floor_z
    bpy.ops.mesh.primitive_plane_add(size=fl, location=(center.x, center.y, fz))
    floor = C.object
    fm = D.materials.new("Floor"); fm.use_nodes = True
    fb = fm.node_tree.nodes["Principled BSDF"]
    fb.inputs["Base Color"].default_value = (0.05, 0.05, 0.055, 1)
    fb.inputs["Roughness"].default_value = 0.45
    floor.data.materials.append(fm)
    bpy.ops.mesh.primitive_plane_add(size=fl, location=(center.x, center.y + fl * 0.25, fz + fl / 2), rotation=(math.radians(90), 0, 0))
    wall = C.object; wall.data.materials.append(fm)
    # свет
    def area(name, loc, energy, color, size_):
        ld = D.lights.new(name, "AREA"); ld.energy = energy; ld.color = color; ld.size = size_
        lo = D.objects.new(name, ld); link(lo); lo.location = loc
        d = center - Vector(loc)
        lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        return lo
    k = max(radius, 0.3)
    if not lights:
        w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.02
    if lights:
      area("Key", center + Vector((-1.6, -2.0, 2.2)) * k, 380 * k * k, (1, 0.9, 0.8), 1.5 * k)
      area("Fill", center + Vector((2.2, -1.4, 0.8)) * k, 110 * k * k, (0.7, 0.8, 1.0), 2.0 * k)
      area("Rim", center + Vector((0.8, 2.2, 2.0)) * k, 320 * k * k, (0.6, 0.75, 1.0), 1.2 * k)
    if extra_light:
        extra_light(center, k)
    # камера
    cd = D.cameras.new("Cam"); cd.lens = focal
    cam = D.objects.new("Cam", cd); link(cam); sc.camera = cam
    dirv = Vector(cam_dir).normalized()
    fov = 2 * math.atan(36 / 2 / focal)
    dist = radius * fov_pad / math.sin(fov / 2)
    cam.location = center + dirv * dist
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    cd.clip_end = dist * 10
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path
