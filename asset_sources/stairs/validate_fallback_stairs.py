#!/usr/bin/env python3
"""Validate generated fallback-stair OBJ8 assets and their fit profiles."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image


def parse_obj8(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    vertices: list[tuple[float, ...]] = []
    indices: list[int] = []
    tris: list[tuple[int, int]] = []
    point_counts: tuple[int, int, int, int] | None = None
    texture: str | None = None
    lods: list[tuple[float, float]] = []
    for line in lines:
        fields = line.split()
        if not fields:
            continue
        command = fields[0]
        if command == "VT":
            vertices.append(tuple(map(float, fields[1:])))
        elif command == "IDX10":
            indices.extend(map(int, fields[1:]))
        elif command == "IDX":
            indices.append(int(fields[1]))
        elif command == "TRIS":
            tris.append((int(fields[1]), int(fields[2])))
        elif command == "POINT_COUNTS":
            point_counts = tuple(map(int, fields[1:5]))
        elif command == "TEXTURE":
            texture = fields[1]
        elif command == "ATTR_LOD":
            lods.append((float(fields[1]), float(fields[2])))
    return {
        "lines": lines,
        "vertices": vertices,
        "indices": indices,
        "tris": tris,
        "point_counts": point_counts,
        "texture": texture,
        "lods": lods,
    }


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(x - y for x, y in zip(a, b))  # type: ignore[return-value]


def validate_obj(path: Path, profile: dict[str, Any]) -> dict[str, Any]:
    data = parse_obj8(path)
    vertices = data["vertices"]
    indices = data["indices"]
    failures: list[str] = []
    if data["lines"][:3] != ["I", "800", "OBJ"]:
        failures.append("invalid OBJ8 header")
    if data["point_counts"] != (len(vertices), 0, 0, len(indices)):
        failures.append("POINT_COUNTS does not match parsed buffers")
    if len(data["tris"]) != 2 or len(data["lods"]) != 2:
        failures.append("expected exactly one draw range for each of two LODs")
    if any(index < 0 or index >= len(vertices) for index in indices):
        failures.append("index outside vertex buffer")
    if any(len(vertex) != 8 for vertex in vertices):
        failures.append("VT row does not have position, normal and UV")
    if any("ANIM_" in line for line in data["lines"]):
        failures.append("static asset contains animation commands")
    if any(
        (fields[0] == "IDX10" and len(fields) != 11) or (fields[0] == "IDX" and len(fields) != 2)
        for line in data["lines"]
        if (fields := line.split()) and fields[0] in ("IDX10", "IDX")
    ):
        failures.append("IDX10/IDX command arity is invalid")
    if any(not (0.0 <= vertex[6] <= 1.0 and 0.0 <= vertex[7] <= 1.0) for vertex in vertices):
        failures.append("UV outside texture bounds")
    for vertex in vertices:
        normal_length = math.sqrt(sum(component * component for component in vertex[3:6]))
        if abs(normal_length - 1.0) > 2e-4:
            failures.append("non-unit normal")
            break
    for first, count in data["tris"]:
        if first % 3 or count % 3 or first < 0 or first + count > len(indices):
            failures.append("invalid TRIS range")
            continue
        for offset in range(first, first + count, 3):
            va, vb, vc = (vertices[indices[offset + item]] for item in range(3))
            geometric = cross(sub(vb[:3], va[:3]), sub(vc[:3], va[:3]))
            if dot(geometric, va[3:6]) <= 1e-10:
                failures.append(f"reversed or degenerate triangle at index {offset}")
                break
    texture_path = path.parent / str(data["texture"])
    if data["texture"] != profile["texture"] or not texture_path.is_file():
        failures.append("texture reference is missing or mismatched")
    else:
        with Image.open(texture_path) as image:
            if image.size != (512, 512) or image.mode not in ("RGB", "RGBA"):
                failures.append("texture must be 512x512 RGB/RGBA")
    height = float(profile["platform_height_m"])
    contact = tuple(profile["contact_point_xyz_m"])
    if contact != (0.0, height, 0.0):
        failures.append("profile contact point violates origin contract")
    if not any(abs(v[0]) < 1e-7 and abs(v[1] - height) < 1e-7 for v in vertices):
        failures.append("door-contact edge is absent from geometry")
    minimum_y = min(vertex[1] for vertex in vertices)
    if abs(minimum_y) > 1e-6:
        failures.append(f"wheel/geometry ground plane is {minimum_y:.6f} m, expected 0")
    for point in profile["wheel_ground_points_xyz_m"]:
        if abs(point[1]) > 1e-9:
            failures.append("profile wheel point is not on ground")
        if not any(
            abs(vertex[0] - point[0]) < 2e-5
            and abs(vertex[1] - point[1]) < 2e-5
            and abs(vertex[2] - point[2]) <= 0.051
            for vertex in vertices
        ):
            failures.append(f"declared wheel ground point not found in mesh: {point}")
    high_triangles = int(profile["high_lod"]["triangles"])
    low_triangles = int(profile["low_lod"]["triangles"])
    if high_triangles > 5000 or low_triangles > 1000:
        failures.append("polygon budget exceeded")
    if data["tris"] and [count // 3 for _, count in data["tris"]] != [high_triangles, low_triangles]:
        failures.append("profile triangle counts differ from OBJ8 draw ranges")
    return {
        "asset": path.name,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "vertices_total": len(vertices),
        "indices_total": len(indices),
        "high_lod_triangles": high_triangles,
        "low_lod_triangles": low_triangles,
        "draw_ranges_per_lod": 1,
        "texture_count": 1,
        "minimum_y_m": minimum_y,
        "platform_contact_xyz_m": list(contact),
    }


def validate_fit(measurement: dict[str, Any], profiles: dict[str, Any]) -> dict[str, Any]:
    model_heights = sorted(float(model["platform_height_m"]) for model in profiles["models"])
    failures: list[str] = []
    cases = 0
    maximum_residual = 0.0
    covered_variants: set[str] = set()
    covered_doors: set[str] = set()
    for variant in measurement["variants"]:
        covered_variants.add(variant["variant"])
        for scenario in variant["scenarios"]:
            for door, fit in scenario["doors"].items():
                cases += 1
                covered_doors.add(door)
                selected = min(model_heights, key=lambda height: abs(height - fit["estimated_sill_height_m"]))
                residual = abs(selected - fit["estimated_sill_height_m"])
                maximum_residual = max(maximum_residual, residual)
                if residual > profiles["family"]["selection_tolerance_m"] + 1e-9:
                    failures.append(f"{variant['variant']} {scenario['id']} {door}: residual {residual:.3f} m")
    if measurement["family_selection"]["lower_bound_model_count"] != len(model_heights):
        failures.append("model count is not the measured continuous-envelope lower bound")
    return {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "case_count": cases,
        "variant_count": len(covered_variants),
        "doors": sorted(covered_doors),
        "maximum_abs_contact_residual_m": maximum_residual,
    }


def report(results: list[dict[str, Any]], fit: dict[str, Any]) -> str:
    lines = [
        "# Fallback stair static validation",
        "",
        "| Asset | OBJ8 | High tris | Low tris | Ground Y | Contact |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for item in results:
        contact = item["platform_contact_xyz_m"]
        lines.append(
            f"| {item['asset']} | {item['status']} | {item['high_lod_triangles']} | {item['low_lod_triangles']} | "
            f"{item['minimum_y_m']:.3f} | {contact[0]:.2f}/{contact[1]:.2f}/{contact[2]:.2f} |"
        )
    lines.extend(
        (
            "",
            "## Coverage",
            "",
            f"{fit['status']}: {fit['case_count']} door/load cases across {fit['variant_count']} variants and doors "
            f"{', '.join(fit['doors'])}; maximum absolute static contact residual {fit['maximum_abs_contact_residual_m']:.3f} m.",
            "",
            "Checks cover OBJ8 structure, triangle/index ranges, unit normals, winding, UV bounds, texture linkage, static-only commands, "
            "origin/contact contract, wheel ground points, LOD draw ranges, polygon budget and the complete static fit matrix.",
            "",
            "Simulator contact, live strut/tire behavior, terrain slope and aircraft reload remain outside this static validation.",
            "",
        )
    )
    failures = [failure for item in results for failure in item["failures"]] + fit["failures"]
    if failures:
        lines.extend(("## Failures", ""))
        lines.extend(f"- {failure}" for failure in failures)
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    base = Path(__file__).resolve().parents[1]
    parser.add_argument("--objects", type=Path, default=base / "generated" / "objects")
    parser.add_argument("--measurements", type=Path, default=base / "measurements" / "levelup_stair_measurements.json")
    parser.add_argument("--output", type=Path, default=base / "validation")
    args = parser.parse_args()
    profiles = json.loads((args.objects / "model_profiles.json").read_text(encoding="utf-8"))
    measurement = json.loads(args.measurements.read_text(encoding="utf-8"))
    results = [validate_obj(args.objects / model["obj8"], model) for model in profiles["models"]]
    fit = validate_fit(measurement, profiles)
    data = {"schema": 1, "assets": results, "fit": fit}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "validation.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    (args.output / "VALIDATION_REPORT.md").write_text(report(results, fit), encoding="utf-8", newline="\n")
    return 0 if all(item["status"] == "PASS" for item in results) and fit["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
