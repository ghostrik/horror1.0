"""Сборка ассетов.

  pip install bpy==5.0.1        (или запуск внутри Blender 5: blender -b -P run.py -- <module>)
  python3 run.py props_mall     # все ассеты модуля
  python3 run.py monster Characters/Merchandiser

Результат: FBX -> Assets/Models, исходники .blend -> Art/Blender, превью -> Tools/BlenderAssetGen/renders.
"""
import sys, os, json, time, importlib
sys.path.insert(0, os.path.dirname(__file__))
import lib

MODELS = os.path.join(lib.PROJECT, "Assets", "Models")
RENDERS = os.path.join(os.path.dirname(__file__), "renders")
os.makedirs(RENDERS, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
mod = importlib.import_module(argv[0])
names = argv[1:] or list(mod.ASSETS.keys())
stats_path = os.path.join(RENDERS, "stats.json")
stats = json.load(open(stats_path)) if os.path.exists(stats_path) else {}

for key in names:
    fn = mod.ASSETS[key]
    t0 = time.time()
    lib.reset()
    res = fn()
    objs = res if isinstance(res, list) else res["objects"]
    opts = {} if isinstance(res, list) else res
    anim = opts.get("anim", False)
    path = os.path.join(MODELS, key + ".fbx")
    lib.export_fbx(objs, path, anim=anim)
    blend = os.path.join(lib.PROJECT, "Art", "Blender", key + ".blend")
    os.makedirs(os.path.dirname(blend), exist_ok=True)
    import bpy
    bpy.ops.wm.save_as_mainfile(filepath=blend, relative_remap=True, compress=True, copy=True)
    tris = sum(lib.stats(o) for o in objs if o.type == "MESH")
    mats = sorted({m.name for o in objs if o.type == "MESH" for m in o.data.materials})
    render = os.path.join(RENDERS, key.replace("/", "_") + ".png")
    ropt = getattr(mod, "RENDER_OPTS", {}).get(key, {})
    opts = {**ropt, **opts}
    if opts.get("pose_for_render"):
        opts["pose_for_render"](objs)
    if opts.get("render_rot"):
        import math as _m
        from mathutils import Matrix as _M
        for o in objs:
            if o.parent is None:
                o.matrix_world = _M.Rotation(_m.radians(opts["render_rot"][0]), 4, "X") @ o.matrix_world
    lib.studio([o for o in objs if o.type == "MESH"], render, samples=opts.get("samples", 64), cam_dir=opts.get("cam_dir", (-0.85, -1.25, 0.55)),
               fov_pad=opts.get("pad", 1.12))
    if opts.get("extra"):
        opts["extra"](objs, RENDERS)
    stats[key] = {"tris": tris, "materials": mats, "anim": anim, "actions": opts.get("actions", [])}
    json.dump(stats, open(stats_path, "w"), indent=1, ensure_ascii=False)
    print(f"[{key}] tris={tris} mats={len(mats)} {time.time() - t0:.1f}s", flush=True)
