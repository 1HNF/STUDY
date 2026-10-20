"""Render one abstract 3D sculpture per class with Blender (headless).

Usage: blender -b --factory-startup --python tools/render_objects.py -- <out_dir> [frames]
  frames=1  -> one still per object (<name>.png)
  frames=N  -> an N-frame turntable per object (<name>_00.png ... ), for the spin-to-rotate covers
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
FRAMES = int(argv[1]) if len(argv) > 1 else 1
SIZE = int(argv[2]) if len(argv) > 2 else 640
os.makedirs(OUT, exist_ok=True)


def scene_setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 40 if FRAMES > 1 else 96
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = SIZE
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.03, 0.035, 0.045, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    sc.world = world
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 70
    sc.collection.objects.link(cam)
    cam.location = (0, -8.4, 2.9)
    aim = bpy.data.objects.new("aim", None)
    sc.collection.objects.link(aim)
    aim.location = (0, 0, 0.6)
    tr = cam.constraints.new("TRACK_TO"); tr.target = aim; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
    sc.camera = cam
    for name, loc, energy, size, color in [
        ("key", (3.5, -3, 4.5), 900, 3, (1, 0.97, 0.92)),
        ("rim", (-4, 3, 3), 1200, 2, (0.75, 0.85, 1)),
        ("fill", (-3.5, -4, 0.5), 250, 4, (1, 1, 1)),
        ("top", (0, 0, 6), 500, 5, (1, 1, 1)),
    ]:
        L = bpy.data.lights.new(name, "AREA")
        L.energy, L.size, L.color = energy, size, color
        o = bpy.data.objects.new(name, L)
        o.location = loc
        sc.collection.objects.link(o)
        o.rotation_euler = (Vector(loc) - Vector((0, 0, 0.6))).to_track_quat("Z", "Y").to_euler()
    return sc


def mat(name, base, metal=0.0, rough=0.3, trans=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["IOR"].default_value = 1.45
    return m


def pivot():
    p = bpy.data.objects.new("pivot", None)
    bpy.context.scene.collection.objects.link(p)
    return p  # at the origin: children keep their own coordinates, the pivot only spins them about Z


def add(obj, parent, m):
    obj.data.materials.append(m)
    obj.parent = parent
    bpy.ops.object.shade_smooth() if obj.type == "MESH" and bpy.context.view_layer.objects.active == obj else None
    return obj


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True


# ---------- one sculpture per subject family ----------
def net(p, accent):   # network: a wire lattice sphere with node beads
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.25, location=(0, 0, 0.6))
    s = bpy.context.object
    w = s.modifiers.new("w", "WIREFRAME"); w.thickness = 0.035
    s.modifiers.new("b", "BEVEL").width = 0.01
    add(s, p, mat("chrome", (0.9, 0.9, 0.92), metal=1, rough=0.18)); smooth(s)
    for v in s.data.vertices:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.075, location=s.matrix_world @ v.co, segments=16, ring_count=8)
        b = bpy.context.object; add(b, p, mat("node", accent, rough=0.25, coat=1)); smooth(b)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.62, location=(0, 0, 0.6))
    c = bpy.context.object; add(c, p, mat("glass", (0.95, 0.97, 1), rough=0.08, trans=1)); smooth(c)


def logic(p, accent):   # logic: stacked offset slabs, like gates in a chip
    for i in range(4):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.15 + i * 0.42))
        c = bpy.context.object
        c.scale = (1.7 - i * 0.22, 1.1 - i * 0.1, 0.14)
        c.rotation_euler[2] = math.radians(i * 14)
        bv = c.modifiers.new("b", "BEVEL"); bv.width = 0.05; bv.segments = 4
        m = mat("slab", accent, rough=0.22, coat=1) if i == 3 else mat("glass", (0.92, 0.95, 1), rough=0.06, trans=1) if i % 2 else mat("dark", (0.05, 0.055, 0.06), metal=0.6, rough=0.3)
        add(c, p, m); smooth(c)


def wave(p, accent):    # signals: a twisted ribbon torus
    bpy.ops.mesh.primitive_torus_add(major_radius=1.15, minor_radius=0.22, major_segments=160, minor_segments=24, location=(0, 0, 0.6))
    t = bpy.context.object
    t.scale = (1, 1, 0.35)
    tw = t.modifiers.new("t", "SIMPLE_DEFORM"); tw.deform_method = "TWIST"; tw.angle = math.radians(220); tw.deform_axis = "X"
    add(t, p, mat("chrome", (0.92, 0.92, 0.95), metal=1, rough=0.12)); smooth(t)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.38, location=(0, 0, 0.6), segments=48, ring_count=24)
    s = bpy.context.object; add(s, p, mat("core", accent, rough=0.2, coat=1)); smooth(s)


def shield(p, accent):  # security: nested rotated rounded cubes, a lock-like core
    for i, (sz, m) in enumerate([(1.55, mat("glass", (0.93, 0.96, 1), rough=0.05, trans=1)), (1.05, mat("dark", (0.05, 0.055, 0.06), metal=0.7, rough=0.28)), (0.55, mat("core", accent, rough=0.2, coat=1))]):
        bpy.ops.mesh.primitive_cube_add(size=sz, location=(0, 0, 0.6))
        c = bpy.context.object
        c.rotation_euler = (math.radians(35 + i * 10), math.radians(45), math.radians(i * 20))
        bv = c.modifiers.new("b", "BEVEL"); bv.width = sz * 0.12; bv.segments = 6
        add(c, p, m); smooth(c)


def bars(p, accent):    # statistics: a ring of bars, a distribution in the round
    n = 18
    for i in range(n):
        a = 2 * math.pi * i / n
        h = 0.35 + 1.25 * math.exp(-((i - n / 2) ** 2) / 14)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * 1.1, math.sin(a) * 1.1, -0.1 + h / 2))
        c = bpy.context.object
        c.scale = (0.16, 0.16, h); c.rotation_euler[2] = a
        bv = c.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 3
        add(c, p, mat("bar", accent, rough=0.25, coat=1) if h > 1.2 else mat("chrome", (0.9, 0.9, 0.93), metal=1, rough=0.2)); smooth(c)
    bpy.ops.mesh.primitive_cylinder_add(radius=1.45, depth=0.08, location=(0, 0, -0.14), vertices=96)
    d = bpy.context.object; add(d, p, mat("glass", (0.93, 0.96, 1), rough=0.1, trans=1))


def helix(p, accent):   # biology / chemistry: a double helix of beads with rungs
    n, turns, h, r = 26, 1.6, 2.4, 0.75
    for i in range(n):
        t = i / (n - 1); a = 2 * math.pi * turns * t; z = -0.6 + h * t
        pa = Vector((math.cos(a) * r, math.sin(a) * r, z)); pb = Vector((-math.cos(a) * r, -math.sin(a) * r, z))
        for pt, m in ((pa, mat("chrome", (0.92, 0.92, 0.95), metal=1, rough=0.15)), (pb, mat("bead", accent, rough=0.22, coat=1))):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=pt, segments=24, ring_count=12)
            b = bpy.context.object; add(b, p, m); smooth(b)
        if i % 2 == 0:  # rung between the strands
            mid, d = (pa + pb) / 2, pb - pa
            bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=d.length - 0.2, location=mid, vertices=16)
            c = bpy.context.object; c.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
            add(c, p, mat("glass", (0.93, 0.96, 1), rough=0.08, trans=1))


def gear(p, accent):    # mechanics / engineering: two meshing gears
    for cx, rad, teeth, z, m, rot in ((-0.55, 0.85, 14, 0.6, mat("chrome", (0.9, 0.9, 0.93), metal=1, rough=0.2), 0),
                                      (0.78, 0.55, 9, 0.6, mat("core", accent, rough=0.22, coat=1), 360 / 18)):
        bpy.ops.mesh.primitive_cylinder_add(radius=rad, depth=0.32, location=(cx, 0, z), vertices=96)
        body = bpy.context.object; body.rotation_euler[0] = math.radians(90); add(body, p, m); smooth(body)
        for k in range(teeth):
            a = 2 * math.pi * k / teeth + math.radians(rot)
            bpy.ops.mesh.primitive_cube_add(size=1, location=(cx + math.cos(a) * (rad + 0.1), 0, z + math.sin(a) * (rad + 0.1)))
            t = bpy.context.object; t.scale = (0.22, 0.32, 0.16); t.rotation_euler = (0, -a, 0)
            bv = t.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 3
            add(t, p, m)
        bpy.ops.mesh.primitive_cylinder_add(radius=rad * 0.32, depth=0.4, location=(cx, 0, z), vertices=48)
        hub = bpy.context.object; hub.rotation_euler[0] = math.radians(90); add(hub, p, mat("dark", (0.05, 0.055, 0.06), metal=0.6, rough=0.3)); smooth(hub)


def prism(p, accent):   # optics / physics: a glass prism splitting a beam
    bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=1.5, vertices=3, location=(0, 0, 0.6))
    g = bpy.context.object; g.rotation_euler = (math.radians(90), 0, math.radians(90))
    bv = g.modifiers.new("b", "BEVEL"); bv.width = 0.05; bv.segments = 4
    add(g, p, mat("glass", (0.95, 0.97, 1), rough=0.03, trans=1))
    for k, (c, ang) in enumerate([((0.9, 0.9, 0.93), -14), (accent, 0), ((0.05, 0.055, 0.06), 14)]):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(1.35, 0, 0.6))
        b = bpy.context.object; b.scale = (1.1, 0.06, 0.06); b.rotation_euler[1] = math.radians(ang)
        b.location = (0.35 + 0.55 * math.cos(math.radians(ang)), 0, 0.6 - 0.55 * math.sin(math.radians(ang)))
        add(b, p, mat("beam", c, metal=1 if k == 0 else 0, rough=0.2, coat=1))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.25, 0, 0.6))
    b = bpy.context.object; b.scale = (1.0, 0.06, 0.06); add(b, p, mat("beam", (0.9, 0.9, 0.93), metal=1, rough=0.15))


def orbit(p, accent):   # astronomy / aviation / physics: a planet with a ring and moons
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.72, location=(0, 0, 0.6), segments=64, ring_count=32)
    s = bpy.context.object; add(s, p, mat("dark", (0.05, 0.055, 0.06), metal=0.5, rough=0.25, coat=1)); smooth(s)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.25, minor_radius=0.05, major_segments=128, minor_segments=16, location=(0, 0, 0.6))
    r = bpy.context.object; r.rotation_euler = (math.radians(68), math.radians(12), 0); add(r, p, mat("chrome", (0.92, 0.92, 0.95), metal=1, rough=0.12)); smooth(r)
    for k, (rad, sz) in enumerate([(1.25, 0.13), (1.25, 0.09), (1.6, 0.11)]):
        a = math.radians(40 + k * 130)
        v = Vector((math.cos(a) * rad, math.sin(a) * rad, 0)); v.rotate(r.rotation_euler); v += Vector((0, 0, 0.6))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=sz, location=v, segments=24, ring_count=12)
        m_ = bpy.context.object; add(m_, p, mat("moon", accent, rough=0.2, coat=1)); smooth(m_)


def knot(p, accent):    # mathematics / topology: a (2,3) torus knot tube with a glass core
    cu = bpy.data.curves.new("knot", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.16; cu.bevel_resolution = 6
    sp = cu.splines.new("NURBS"); n = 180; sp.points.add(n - 1)
    for i in range(n):
        t = 2 * math.pi * i / n; rr = 0.75 + 0.35 * math.cos(3 * t)
        sp.points[i].co = (rr * math.cos(2 * t), rr * math.sin(2 * t), 0.6 + 0.35 * math.sin(3 * t), 1)
    sp.use_cyclic_u = True; sp.order_u = 4
    o = bpy.data.objects.new("knot", cu); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat("chrome", (0.92, 0.92, 0.95), metal=1, rough=0.12)); o.parent = p
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.32, location=(0, 0, 0.6))
    c = bpy.context.object; add(c, p, mat("core", accent, rough=0.2, coat=1)); smooth(c)


SHAPES = {"net": net, "logic": logic, "wave": wave, "shield": shield, "bars": bars,
          "helix": helix, "gear": gear, "prism": prism, "orbit": orbit, "knot": knot}
ACCENT = (0.03, 0.16, 1.0)  # electric blue (linear); one accent across every object
ONLY = set(argv[3].split(",")) if len(argv) > 3 else set(SHAPES)  # optional: render just these shapes

for name, fn in SHAPES.items():
    if name not in ONLY:
        continue
    sc = scene_setup()
    p = pivot()
    fn(p, ACCENT)
    for f in range(FRAMES):
        p.rotation_euler[2] = 2 * math.pi * f / FRAMES + math.radians(20)
        sc.render.filepath = os.path.join(OUT, f"{name}.png" if FRAMES == 1 else f"{name}_{f:02d}.png")
        bpy.ops.render.render(write_still=True)
    print("rendered", name)
