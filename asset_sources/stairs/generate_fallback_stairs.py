#!/usr/bin/env python3
"""Generate the original LevelUp fallback stair OBJ8 family and texture.

The geometry in this file is built from independent design dimensions only.
It does not import, trace, transform, or copy any third-party mesh or texture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont


HEIGHTS_M = (2.65, 2.85, 3.05)
MODEL_PREFIX = "LU_fallback_stairs"
TEXTURE_NAME = "LU_fallback_stairs.png"

PLATFORM_LENGTH_M = 1.25
PLATFORM_WIDTH_M = 1.20
STAIR_CLEAR_WIDTH_M = 1.10
TREAD_DEPTH_M = 0.28
TREAD_THICKNESS_M = 0.045
MAX_RISER_M = 0.19
RAIL_HEIGHT_M = 1.00
WHEEL_RADIUS_M = 0.18
WHEEL_WIDTH_M = 0.10

UV = {
    # UV origin is bottom-left while Pillow authors the atlas top-down.
    "paint": (0.035, 0.035, 0.465, 0.465),
    "yellow": (0.535, 0.035, 0.965, 0.465),
    "metal": (0.035, 0.535, 0.465, 0.965),
    "rubber": (0.535, 0.535, 0.965, 0.965),
}

Vec3 = tuple[float, float, float]


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def length(a: Vec3) -> float:
    return math.sqrt(dot(a, a))


def unit(a: Vec3) -> Vec3:
    size = length(a)
    if size <= 1e-12:
        raise ValueError("zero-length vector")
    return mul(a, 1.0 / size)


@dataclass
class Mesh:
    vertices: list[tuple[float, float, float, float, float, float, float, float]] = field(default_factory=list)
    indices: list[int] = field(default_factory=list)

    def polygon(self, points: Sequence[Vec3], normal: Vec3, region: str) -> None:
        if len(points) not in (3, 4):
            raise ValueError("only triangles and quads are supported")
        n = unit(normal)
        pts = list(points)
        if dot(cross(sub(pts[1], pts[0]), sub(pts[2], pts[0])), n) < 0.0:
            pts.reverse()
        u0, v0, u1, v1 = UV[region]
        tex = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        start = len(self.vertices)
        for i, point in enumerate(pts):
            u, v = tex[i]
            self.vertices.append((*point, *n, u, v))
        if len(pts) == 3:
            self.indices.extend((start, start + 1, start + 2))
        else:
            self.indices.extend((start, start + 1, start + 2, start, start + 2, start + 3))

    def box(self, minimum: Vec3, maximum: Vec3, region: str) -> None:
        x0, y0, z0 = minimum
        x1, y1, z1 = maximum
        self.polygon(((x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)), (-1, 0, 0), region)
        self.polygon(((x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)), (1, 0, 0), region)
        self.polygon(((x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)), (0, -1, 0), region)
        self.polygon(((x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)), (0, 1, 0), region)
        self.polygon(((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)), (0, 0, -1), region)
        self.polygon(((x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)), (0, 0, 1), region)

    def cylinder(self, start: Vec3, end: Vec3, radius: float, segments: int, region: str) -> None:
        axis = unit(sub(end, start))
        reference = (0.0, 1.0, 0.0) if abs(axis[1]) < 0.9 else (1.0, 0.0, 0.0)
        u = unit(cross(axis, reference))
        v = cross(axis, u)
        for i in range(segments):
            a0 = 2.0 * math.pi * i / segments
            a1 = 2.0 * math.pi * (i + 1) / segments
            r0 = add(mul(u, math.cos(a0) * radius), mul(v, math.sin(a0) * radius))
            r1 = add(mul(u, math.cos(a1) * radius), mul(v, math.sin(a1) * radius))
            self.polygon((add(start, r0), add(end, r0), add(end, r1), add(start, r1)), unit(add(r0, r1)), region)
            self.polygon((start, add(start, r1), add(start, r0)), mul(axis, -1.0), region)
            self.polygon((end, add(end, r0), add(end, r1)), axis, region)

    def prism_z(self, profile: Sequence[tuple[float, float]], z0: float, z1: float, region: str) -> None:
        for i in range(1, len(profile) - 1):
            a = profile[0]
            b = profile[i]
            c = profile[i + 1]
            self.polygon(((a[0], a[1], z0), (c[0], c[1], z0), (b[0], b[1], z0)), (0, 0, -1), region)
            self.polygon(((a[0], a[1], z1), (b[0], b[1], z1), (c[0], c[1], z1)), (0, 0, 1), region)
        for i, a in enumerate(profile):
            b = profile[(i + 1) % len(profile)]
            edge = (b[0] - a[0], b[1] - a[1], 0.0)
            normal = unit((edge[1], -edge[0], 0.0))
            self.polygon(((a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)), normal, region)


def add_wheel(mesh: Mesh, x: float, z: float, detailed: bool) -> None:
    segments = 12 if detailed else 8
    half = WHEEL_WIDTH_M / 2.0
    mesh.cylinder((x, WHEEL_RADIUS_M, z - half), (x, WHEEL_RADIUS_M, z + half), WHEEL_RADIUS_M, segments, "rubber")
    mesh.cylinder((x, WHEEL_RADIUS_M, z - half - 0.006), (x, WHEEL_RADIUS_M, z + half + 0.006), 0.070, segments, "metal")


def build_high(height: float) -> tuple[Mesh, dict[str, object]]:
    mesh = Mesh()
    risers = math.ceil(height / MAX_RISER_M)
    rise = height / risers
    stair_end = -PLATFORM_LENGTH_M - risers * TREAD_DEPTH_M

    mesh.box((-PLATFORM_LENGTH_M, height - 0.10, -PLATFORM_WIDTH_M / 2), (0.0, height, PLATFORM_WIDTH_M / 2), "paint")
    mesh.box((-0.045, height - 0.18, -0.50), (0.0, height + 0.06, 0.50), "rubber")
    mesh.box((-PLATFORM_LENGTH_M, height, -PLATFORM_WIDTH_M / 2), (-PLATFORM_LENGTH_M + 0.055, height + 0.025, PLATFORM_WIDTH_M / 2), "yellow")

    for j in range(risers):
        x0 = -PLATFORM_LENGTH_M - (risers - j) * TREAD_DEPTH_M
        x1 = x0 + TREAD_DEPTH_M
        top = (j + 1) * rise
        mesh.box((x0, top - TREAD_THICKNESS_M, -STAIR_CLEAR_WIDTH_M / 2), (x1, top, STAIR_CLEAR_WIDTH_M / 2), "paint")
        mesh.box((x0, top - TREAD_THICKNESS_M, -STAIR_CLEAR_WIDTH_M / 2), (x0 + 0.045, top + 0.015, STAIR_CLEAR_WIDTH_M / 2), "yellow")
        lower = j * rise
        mesh.box((x0, lower, -STAIR_CLEAR_WIDTH_M / 2), (x0 + 0.035, top, STAIR_CLEAR_WIDTH_M / 2), "paint")

    # Main support frame and under-platform bracing.
    for z in (-0.49, 0.49):
        mesh.cylinder((stair_end + 0.48, 0.22, z), (-PLATFORM_LENGTH_M + 0.05, height - 0.16, z), 0.055, 8, "metal")
        mesh.cylinder((-0.62, 0.22, z), (-0.12, height - 0.14, z), 0.055, 8, "metal")
        mesh.cylinder((-0.62, 0.22, z), (-PLATFORM_LENGTH_M + 0.08, height - 0.16, z), 0.055, 8, "metal")
        mesh.cylinder((-PLATFORM_LENGTH_M + 0.08, height - 0.16, z), (-0.10, height - 0.16, z), 0.050, 8, "metal")
    mesh.cylinder((-0.62, 0.22, -0.58), (-0.62, 0.22, 0.58), 0.050, 8, "metal")
    mesh.cylinder((stair_end + 0.48, 0.22, -0.58), (stair_end + 0.48, 0.22, 0.58), 0.050, 8, "metal")

    # Platform guardrails. The door-facing side remains open.
    for z in (-0.58, 0.58):
        for x in (-PLATFORM_LENGTH_M + 0.08, -0.10):
            mesh.cylinder((x, height, z), (x, height + RAIL_HEIGHT_M, z), 0.035, 8, "metal")
        mesh.cylinder((-PLATFORM_LENGTH_M + 0.08, height + RAIL_HEIGHT_M, z), (-0.10, height + RAIL_HEIGHT_M, z), 0.035, 8, "metal")
        mesh.cylinder((-PLATFORM_LENGTH_M + 0.08, height + 0.52, z), (-0.10, height + 0.52, z), 0.028, 8, "metal")

    # Stair handrails and intermediate posts.
    post_indices = sorted(set((0, risers // 4, risers // 2, 3 * risers // 4, risers - 1)))
    for z in (-0.58, 0.58):
        tops: list[Vec3] = []
        for j in post_indices:
            x = -PLATFORM_LENGTH_M - (risers - j - 0.5) * TREAD_DEPTH_M
            y = (j + 1) * rise
            top = (x, y + RAIL_HEIGHT_M, z)
            mesh.cylinder((x, y, z), top, 0.032, 8, "metal")
            tops.append(top)
        for a, b in zip(tops, tops[1:]):
            mesh.cylinder(a, b, 0.035, 8, "metal")

    wheel_x = (-0.62, stair_end + 0.48)
    wheel_z = (-0.64, 0.64)
    for x in wheel_x:
        for z in wheel_z:
            add_wheel(mesh, x, z, detailed=True)

    metadata = {
        "platform_height_m": height,
        "riser_count": risers,
        "riser_height_m": rise,
        "tread_depth_m": TREAD_DEPTH_M,
        "contact_point_xyz_m": [0.0, height, 0.0],
        "wheel_ground_points_xyz_m": [[x, 0.0, z] for x in wheel_x for z in wheel_z],
        "origin": "ground projection of the platform door-contact centre",
        "axes": "+X aircraft right, +Y up, +Z aircraft aft; stair run extends along -X",
        "nominal_heading_deg": 0.0,
    }
    return mesh, metadata


def build_low(height: float) -> Mesh:
    mesh = Mesh()
    risers = math.ceil(height / MAX_RISER_M)
    stair_end = -PLATFORM_LENGTH_M - risers * TREAD_DEPTH_M
    mesh.box((-PLATFORM_LENGTH_M, height - 0.10, -0.60), (0.0, height, 0.60), "paint")
    profile = ((stair_end, 0.08), (stair_end, 0.22), (-PLATFORM_LENGTH_M, height), (-PLATFORM_LENGTH_M, height - 0.12))
    mesh.prism_z(profile, -0.55, 0.55, "paint")
    mesh.box((stair_end, 0.18, -0.50), (-0.08, 0.28, 0.50), "metal")
    for x in (-0.62, stair_end + 0.48):
        for z in (-0.64, 0.64):
            add_wheel(mesh, x, z, detailed=False)
    return mesh


def bounds(vertices: Iterable[Sequence[float]]) -> list[list[float]]:
    xyz = [tuple(row[:3]) for row in vertices]
    return [[min(p[i] for p in xyz), max(p[i] for p in xyz)] for i in range(3)]


def write_obj8(path: Path, high: Mesh, low: Mesh) -> None:
    vertices = high.vertices + low.vertices
    low_offset = len(high.vertices)
    indices = high.indices + [index + low_offset for index in low.indices]
    lines = [
        "I",
        "800",
        "OBJ",
        "",
        "# Independently generated LevelUp fallback passenger stairs.",
        "# Source: fallback_stairs/source/generate_fallback_stairs.py",
        f"TEXTURE {TEXTURE_NAME}",
        "GLOBAL_specular 0.35",
        "ATTR_cull",
        f"POINT_COUNTS {len(vertices)} 0 0 {len(indices)}",
        "",
    ]
    for row in vertices:
        lines.append("VT " + " ".join(f"{value:.6f}" for value in row))
    lines.append("")
    full_groups_end = len(indices) - (len(indices) % 10)
    for start in range(0, full_groups_end, 10):
        lines.append("IDX10 " + " ".join(str(index) for index in indices[start : start + 10]))
    for index in indices[full_groups_end:]:
        lines.append(f"IDX {index}")
    lines.extend(
        (
            "",
            "ATTR_LOD 0 220",
            f"TRIS 0 {len(high.indices)}",
            "ATTR_LOD 220 1500",
            f"TRIS {len(high.indices)} {len(low.indices)}",
            "",
        )
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def make_texture(path: Path) -> None:
    size = 512
    image = Image.new("RGB", (size, size), (96, 100, 103))
    draw = ImageDraw.Draw(image)
    # Four authored atlas tiles: metal, rubber, painted structure, safety yellow.
    draw.rectangle((0, 0, 255, 255), fill=(72, 78, 82))
    for y in range(0, 256, 8):
        shade = 66 + (y // 8) % 3 * 5
        draw.line((0, y, 255, y), fill=(shade, shade + 5, shade + 8))
    draw.rectangle((256, 0, 511, 255), fill=(31, 33, 34))
    for x in range(260, 512, 16):
        draw.line((x, 0, x - 64, 255), fill=(42, 44, 45), width=3)
    draw.rectangle((0, 256, 255, 511), fill=(220, 224, 224))
    for y in range(270, 512, 18):
        draw.line((0, y, 255, y), fill=(210, 214, 214))
    draw.rectangle((256, 256, 511, 511), fill=(244, 184, 24))
    for x in range(260, 512, 48):
        draw.polygon(((x, 512), (x + 18, 512), (x + 100, 256), (x + 82, 256)), fill=(223, 151, 9))
    font = ImageFont.load_default()
    draw.rectangle((16, 466, 240, 500), fill=(35, 47, 55))
    draw.text((26, 477), "LEVELUP 737NG  |  FALLBACK GSE", fill=(245, 247, 247), font=font)
    image.save(path, optimize=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "generated" / "objects")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    texture = output / TEXTURE_NAME
    make_texture(texture)

    profiles: list[dict[str, object]] = []
    for height in HEIGHTS_M:
        high, metadata = build_high(height)
        low = build_low(height)
        code = f"{round(height * 100):03d}"
        obj = output / f"{MODEL_PREFIX}_{code}.obj"
        write_obj8(obj, high, low)
        metadata.update(
            {
                "id": f"stairs_{code}",
                "obj8": obj.name,
                "texture": TEXTURE_NAME,
                "assigned_levelup_variants": ["737-600", "737-700", "737-800", "737-900", "737-900ER"],
                "assigned_doors": ["L1", "L2"],
                "assignment_rule": "select only when this is the nearest platform height and absolute live contact residual is <= 0.10 m",
                "high_lod": {"vertices": len(high.vertices), "triangles": len(high.indices) // 3, "range_m": [0, 220]},
                "low_lod": {"vertices": len(low.vertices), "triangles": len(low.indices) // 3, "range_m": [220, 1500]},
                "bounds_xyz_m": bounds(high.vertices),
                "sha256": sha256(obj),
            }
        )
        profiles.append(metadata)

    manifest = {
        "schema": 1,
        "provenance": {
            "geometry": "independent procedural primitives authored in this repository",
            "texture": "independent deterministic PIL drawing authored in this repository",
            "third_party_geometry_or_texture_used": False,
            "generator": str(Path(__file__).resolve().relative_to(Path(__file__).resolve().parents[2])),
            "generator_sha256": sha256(Path(__file__).resolve()),
        },
        "family": {
            "selection_tolerance_m": 0.10,
            "available_platform_heights_m": list(HEIGHTS_M),
            "common_texture": {"path": TEXTURE_NAME, "size_px": [512, 512], "sha256": sha256(texture)},
        },
        "models": profiles,
    }
    (output / "model_profiles.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
