#!/usr/bin/env python3
"""Render derived previews of the generated OBJ8 files with Blender.

Run with: blender --background --python render_fallback_previews.py -- [objects] [output]
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_obj8(path: Path) -> tuple[list[tuple[float, ...]], list[int], tuple[int, int], str]:
    vertices: list[tuple[float, ...]] = []
    indices: list[int] = []
    tris: list[tuple[int, int]] = []
    texture = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "VT":
            vertices.append(tuple(map(float, fields[1:])))
        elif fields[0] == "IDX10":
            indices.extend(map(int, fields[1:]))
        elif fields[0] == "IDX":
            indices.append(int(fields[1]))
        elif fields[0] == "TRIS":
            tris.append((int(fields[1]), int(fields[2])))
        elif fields[0] == "TEXTURE":
            texture = fields[1]
    return vertices, indices, tris[0], texture


def material_for(texture_path: Path) -> bpy.types.Material:
    material = bpy.data.materials.new("Fallback stair atlas")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    shader = nodes.get("Principled BSDF")
    image_node = nodes.new("ShaderNodeTexImage")
    image_node.image = bpy.data.images.load(str(texture_path))
    material.node_tree.links.new(image_node.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.58
    shader.inputs["Metallic"].default_value = 0.08
    return material


def import_obj8(path: Path, offset_y: float, material: bpy.types.Material) -> bpy.types.Object:
    vertices, indices, draw_range, _texture = parse_obj8(path)
    first, count = draw_range
    positions = [(row[0], row[2] + offset_y, row[1]) for row in vertices]
    faces = [tuple(indices[i : i + 3]) for i in range(first, first + count, 3)]
    mesh = bpy.data.meshes.new(path.stem)
    mesh.from_pydata(positions, [], faces)
    mesh.materials.append(material)
    uv_layer = mesh.uv_layers.new(name="OBJ8 UV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = (vertices[vertex_index][6], vertices[vertex_index][7])
        polygon.use_smooth = False
    mesh.update()
    obj = bpy.data.objects.new(path.stem, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def point_camera(camera: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render_scene(objects_dir: Path, output: Path) -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.035, 0.045, 0.055)

    material = material_for(objects_dir / "LU_fallback_stairs.png")
    obj_paths = sorted(objects_dir.glob("LU_fallback_stairs_*.obj"))
    spacing = 3.0
    offsets = [spacing * (i - (len(obj_paths) - 1) / 2.0) for i in range(len(obj_paths))]
    for path, offset in zip(obj_paths, offsets):
        import_obj8(path, offset, material)

    bpy.ops.mesh.primitive_plane_add(size=30, location=(-2.4, 0.0, -0.012))
    ground = bpy.context.object
    ground_material = bpy.data.materials.new("Ground")
    ground_material.diffuse_color = (0.09, 0.11, 0.12, 1.0)
    ground.data.materials.append(ground_material)

    bpy.ops.object.light_add(type="AREA", location=(2.5, -3.5, 9.0))
    key = bpy.context.object
    key.data.energy = 1700
    key.data.shape = "DISK"
    key.data.size = 7.0
    bpy.ops.object.light_add(type="AREA", location=(-6.0, 5.0, 5.0))
    fill = bpy.context.object
    fill.data.energy = 900
    fill.data.size = 5.0

    bpy.ops.object.camera_add(location=(8.8, -9.5, 7.2))
    camera = bpy.context.object
    camera.data.lens = 52
    point_camera(camera, (-2.2, 0.0, 1.45))
    scene.camera = camera
    output.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)


def main() -> int:
    separator = sys.argv.index("--") if "--" in sys.argv else len(sys.argv)
    args = sys.argv[separator + 1 :]
    base = Path(__file__).resolve().parents[1]
    objects = Path(args[0]).resolve() if args else base / "generated" / "objects"
    output = Path(args[1]).resolve() if len(args) > 1 else base / "validation" / "fallback_stairs_family.png"
    render_scene(objects, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
