"""Parametric Eiffel Tower — forward 3D rebuild reference artifact.

Rebuilds the Eiffel Tower from its documented elevations as an *editable
parametric* Blender scene: the iron lattice is a CURVE with bevel_depth (one
tube per structural member), platforms are bmesh slabs, arches are swept
curves. Nothing is sculpted by hand and nothing is imported.

Run it two ways (same body):

  Headless (recommended for final artifacts; a separate process that does not
  touch any Blender window you have open):

      blender --background --factory-startup \
              --python build_eiffel_tower.py -- --out ./out

  Live (for iterating): paste the build section through the BlenderMCP socket
  (execute_blender_code) into a running Blender, then screenshot to inspect.

Outputs (into --out, default ./out): EiffelTower.blend, EiffelTower.glb,
preview.png. No machine-specific paths are baked in.
"""

from __future__ import annotations

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector


def parse_out_dir() -> str:
    """Read --out from the args after the Blender `--` separator."""
    argv = sys.argv
    out = "./out"
    if "--" in argv:
        extra = argv[argv.index("--") + 1 :]
        if "--out" in extra:
            out = extra[extra.index("--out") + 1]
    out = os.path.abspath(out)
    os.makedirs(out, exist_ok=True)
    return out


# --- documented elevations (metres) from the SB-AI-001 South Elevation ---
Z1, Z2, Z3, ZT, ZA = 57.63, 115.73, 276.13, 300.65, 330.0


def leg_R(z: float) -> float:
    """Half-distance of a leg centre from the tower axis at height z."""
    f = (1.0 - z / Z2) ** 1.7
    return 8.5 + (52.0 - 8.5) * f


def leg_L(z: float) -> float:
    """Leg box section size at height z."""
    f = (1.0 - z / Z2) ** 1.7
    return 11.0 + (21.0 - 11.0) * f


def tower_w(z: float) -> float:
    """Shaft half-width above the 2nd platform."""
    g = ((ZT - z) / (ZT - Z2)) ** 1.3
    return 4.0 + (14.0 - 4.0) * g


def build() -> dict:
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    # ---- dense iron lattice: CURVE, one POLY spline per member ----
    verts: list = []
    edges: list = []

    def add_v(co):
        verts.append(co)
        return len(verts) - 1

    def lvl(cx, cy, h, z):
        c = [(cx + h, cy + h, z), (cx - h, cy + h, z), (cx - h, cy - h, z), (cx + h, cy - h, z)]
        ci = [add_v(p) for p in c]
        mi = [
            add_v(((c[k][0] + c[(k + 1) % 4][0]) / 2, (c[k][1] + c[(k + 1) % 4][1]) / 2, z))
            for k in range(4)
        ]
        return {"c": ci, "m": mi}

    def seg(t, b):
        cb, mb, ct, mt = b["c"], b["m"], t["c"], t["m"]
        for k in range(4):
            k1 = (k + 1) % 4
            edges.extend(
                [
                    (cb[k], mb[k]),
                    (mb[k], cb[k1]),  # bottom ring, split at mid
                    (cb[k], ct[k]),  # corner vertical
                    (mb[k], mt[k]),  # mid post
                    (cb[k], mt[k]),
                    (mb[k], ct[k]),  # left X
                    (mb[k], ct[k1]),
                    (cb[k1], mt[k]),  # right X
                ]
            )

    n1 = 12
    for sx, sy in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
        levels = [
            lvl(
                sx * leg_R(Z2 * i / n1),
                sy * leg_R(Z2 * i / n1),
                leg_L(Z2 * i / n1) / 2,
                Z2 * i / n1,
            )
            for i in range(n1 + 1)
        ]
        for i in range(n1):
            seg(levels[i + 1], levels[i])

    n2 = 18
    up = [
        lvl(0, 0, tower_w(Z2 + (ZT - Z2) * i / n2), Z2 + (ZT - Z2) * i / n2) for i in range(n2 + 1)
    ]
    for i in range(n2):
        seg(up[i + 1], up[i])

    ns = 7
    prev = up[-1]
    for i in range(1, ns + 1):
        z = ZT + (ZA - 0.5 - ZT) * i / ns
        cur = lvl(0, 0, 4.0 * (1 - i / ns) + 0.4, z)
        seg(cur, prev)
        prev = cur
    tip = add_v((0, 0, ZA))
    for k in range(4):
        edges.append((prev["c"][k], tip))

    lat = bpy.data.curves.new("EiffelLatticeMesh", "CURVE")
    lat.dimensions = "3D"
    lat.fill_mode = "FULL"
    lat.bevel_depth = 0.5
    lat.bevel_resolution = 1
    lat.resolution_u = 1
    lat.use_fill_caps = True
    for a, b in edges:
        sp = lat.splines.new("POLY")
        sp.points.add(1)
        sp.points[0].co = (*verts[a], 1)
        sp.points[1].co = (*verts[b], 1)
    lat_ob = bpy.data.objects.new("EiffelLattice", lat)
    scene.collection.objects.link(lat_ob)

    # ---- platforms: bmesh slabs at the documented elevations ----
    bm = bmesh.new()
    for z, h, t in [(Z1, 32, 3), (Z2, 17, 2.6), (Z3, 7.5, 2), (ZT, 5.5, 1.8)]:
        corners = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
        vs = [bm.verts.new((sx * h, sy * h, z - t / 2)) for sx, sy in corners]
        vs += [bm.verts.new((sx * h, sy * h, z + t / 2)) for sx, sy in corners]
        bm.faces.new(vs[0:4])
        bm.faces.new(vs[4:8][::-1])
        for k in range(4):
            bm.faces.new([vs[k], vs[(k + 1) % 4], vs[4 + (k + 1) % 4], vs[4 + k]])
    pme = bpy.data.meshes.new("EiffelPlatformsMesh")
    bm.to_mesh(pme)
    bm.free()
    plat_ob = bpy.data.objects.new("EiffelPlatforms", pme)
    scene.collection.objects.link(plat_ob)

    # ---- arches: swept CURVE between the inner leg faces ----
    def inner(z):
        return max(leg_R(z) - leg_L(z) / 2, 6.0)

    arc = [
        (
            42 * math.cos(math.pi * i / 24),
            inner(2 + 38 * math.sin(math.pi * i / 24)),
            2 + 38 * math.sin(math.pi * i / 24),
        )
        for i in range(25)
    ]
    ac = bpy.data.curves.new("EiffelArchesMesh", "CURVE")
    ac.dimensions = "3D"
    ac.fill_mode = "FULL"
    ac.bevel_depth = 0.9
    ac.bevel_resolution = 1
    ac.resolution_u = 2

    def aspl(pts):
        s = ac.splines.new("POLY")
        s.points.add(len(pts) - 1)
        for j, (x, y, z) in enumerate(pts):
            s.points[j].co = (x, y, z, 1)

    aspl([(s, f, z) for s, f, z in arc])
    aspl([(s, -f, z) for s, f, z in arc])
    aspl([(f, s, z) for s, f, z in arc])
    aspl([(-f, s, z) for s, f, z in arc])
    arch_ob = bpy.data.objects.new("EiffelArches", ac)
    scene.collection.objects.link(arch_ob)

    # ---- materials ----
    def principled(mat):
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                return n
        return None

    def set_in(node, key, val):
        if node and key in node.inputs:
            node.inputs[key].default_value = val

    iron = bpy.data.materials.get("EiffelIron") or bpy.data.materials.new("EiffelIron")
    iron.use_nodes = True
    b = principled(iron)
    set_in(b, "Base Color", (0.17, 0.11, 0.065, 1))
    set_in(b, "Metallic", 0.85)
    set_in(b, "Roughness", 0.42)
    for o in (lat_ob, plat_ob, arch_ob):
        o.data.materials.clear()
        o.data.materials.append(iron)

    bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "EiffelGround"
    gm = bpy.data.materials.get("EiffelGround") or bpy.data.materials.new("EiffelGround")
    gm.use_nodes = True
    gb = principled(gm)
    set_in(gb, "Base Color", (0.21, 0.22, 0.19, 1))
    set_in(gb, "Roughness", 0.9)
    ground.data.materials.clear()
    ground.data.materials.append(gm)

    # ---- world / sun / camera ----
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.type == "BACKGROUND":
            n.inputs[0].default_value = (0.55, 0.68, 0.85, 1)
            n.inputs[1].default_value = 1.2

    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 5.0
    sun_data.angle = math.radians(2)
    sun = bpy.data.objects.new("Sun", sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(55), math.radians(12), math.radians(40))

    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    cam.data.lens = 40
    cam.data.clip_start = 1.0
    cam.data.clip_end = 6000.0  # large model -> raise the far clip
    cam.location = (355, -395, 118)
    cam.rotation_euler = (Vector((0, 0, 158)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam

    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"  # current EEVEE id; guarded
    except Exception:
        pass
    scene.render.resolution_x = 950
    scene.render.resolution_y = 1340

    return {"objects": (lat_ob, plat_ob, arch_ob), "edges": len(edges), "verts": len(verts)}


def export(out_dir: str, objs) -> None:
    scene = bpy.context.scene
    blend = os.path.join(out_dir, "EiffelTower.blend")
    glb = os.path.join(out_dir, "EiffelTower.glb")
    preview = os.path.join(out_dir, "preview.png")

    for o in scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]  # active lives on view_layer

    # glTF evaluates the depsgraph: curve+bevel bakes to mesh with export_apply
    bpy.ops.export_scene.gltf(
        filepath=glb, export_format="GLB", use_selection=True, export_apply=True, export_yup=True
    )
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)

    scene.render.filepath = preview
    bpy.ops.render.render(write_still=True)
    print(
        f"BUILT blend={os.path.exists(blend)} "
        f"glb={os.path.exists(glb)} preview={os.path.exists(preview)}"
    )


def main() -> None:
    out_dir = parse_out_dir()
    info = build()
    print(f"lattice members={info['edges']} verts={info['verts']}")
    export(out_dir, info["objects"])


if __name__ == "__main__":
    main()
