#!/usr/bin/env python3
"""Reproduce the LevelUp door-sill and static landing-gear fit analysis.

Third-party ACF/OBJ files are read only to measure aircraft contact geometry.
No source vertex, texture, or component is copied into the generated stair assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


FT_TO_M = 0.3048
MODEL_HEIGHTS_M = (2.65, 2.85, 3.05)
FIT_TOLERANCE_M = 0.10
VARIANTS = (
    ("737-600", "737_60NG"),
    ("737-700", "737_70NG"),
    ("737-800", "737_80NG"),
    ("737-900", "737_90NG"),
    ("737-900ER", "737_9ENG"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_acf(path: Path) -> dict[str, float]:
    values: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("P "):
            continue
        fields = line.split(maxsplit=2)
        if len(fields) != 3:
            continue
        try:
            values[fields[1]] = float(fields[2])
        except ValueError:
            continue
    return values


def parse_obj8(path: Path) -> tuple[list[tuple[float, float, float]], list[int], list[str]]:
    vertices: list[tuple[float, float, float]] = []
    indices: list[int] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines:
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "VT":
            vertices.append(tuple(map(float, fields[1:4])))
        elif fields[0] == "IDX10":
            indices.extend(map(int, fields[1:]))
        elif fields[0] == "IDX":
            indices.append(int(fields[1]))
    return vertices, indices, lines


def door_threshold(vertices: list[tuple[float, float, float]], indices: list[int], lines: list[str], door: str) -> dict[str, Any]:
    ranges: list[tuple[int, int]] = []
    needle = f"doors/{door}"
    for line_number, line in enumerate(lines):
        if needle not in line or not line.startswith("ANIM_"):
            continue
        for candidate in lines[line_number : line_number + 28]:
            fields = candidate.split()
            if fields and fields[0] == "TRIS":
                item = (int(fields[1]), int(fields[2]))
                if item not in ranges:
                    ranges.append(item)
                break
    if not ranges:
        raise ValueError(f"no {door} animated geometry range found")
    first, count = max(ranges, key=lambda item: item[1])
    points = {vertices[index] for index in indices[first : first + count]}
    minimum_y = min(point[1] for point in points)
    threshold = [point for point in points if abs(point[1] - minimum_y) <= 1e-7]
    if len(threshold) < 2:
        raise ValueError(f"insufficient {door} threshold vertices")
    return {
        "xyz_m": [
            sum(point[0] for point in threshold) / len(threshold),
            minimum_y,
            (min(point[2] for point in threshold) + max(point[2] for point in threshold)) / 2.0,
        ],
        "source_vertex_count": len(threshold),
        "source_tris_range": [first, count],
        "method": "midpoint of the lowest edge of the largest animated door-leaf mesh",
    }


def gear(values: dict[str, float], index: int) -> dict[str, float]:
    names = (
        "_gear_y",
        "_gear_z",
        "_leg_len",
        "_tire_radius",
        "_strut_preload_def",
        "_strut_preload_frc",
        "_strut_max_wgt_def",
        "_strut_max_wgt_frc",
    )
    return {name: values[f"_gear/{index}/{name}"] for name in names}


def strut_deflection_ft(force_lbf: float, item: dict[str, float]) -> tuple[float, str]:
    preload_def = item["_strut_preload_def"]
    preload_force = item["_strut_preload_frc"]
    maximum_def = item["_strut_max_wgt_def"]
    maximum_force = item["_strut_max_wgt_frc"]
    if force_lbf <= preload_force:
        return preload_def * force_lbf / preload_force, "below-preload linear estimate"
    value = preload_def + (maximum_def - preload_def) * (force_lbf - preload_force) / (maximum_force - preload_force)
    mode = "declared curve interpolation" if force_lbf <= maximum_force else "declared curve linear extrapolation"
    return value, mode


def wheel_ground_point(item: dict[str, float], deflection_ft: float) -> tuple[float, float]:
    z = item["_gear_z"] * FT_TO_M
    y = (item["_gear_y"] - item["_leg_len"] + deflection_ft - item["_tire_radius"]) * FT_TO_M
    return z, y


def height_above_gear_plane(point: list[float], nose: tuple[float, float], main: tuple[float, float]) -> float:
    z, y = point[2], point[1]
    z1, y1 = nose
    z2, y2 = main
    return ((z2 - z1) * (y - y1) - (y2 - y1) * (z - z1)) / math.hypot(z2 - z1, y2 - y1)


def select_model(height: float) -> tuple[float, float]:
    selected = min(MODEL_HEIGHTS_M, key=lambda candidate: abs(candidate - height))
    return selected, selected - height


def scenarios(values: dict[str, float]) -> list[tuple[str, float, float]]:
    empty = values["acf/_m_empty"]
    maximum = values["acf/_m_max"]
    nominal_cg = values["acf/_cgZ"]
    return [
        ("operating-empty", empty, nominal_cg),
        ("mid-load", (empty + maximum) / 2.0, nominal_cg),
        ("maximum-nominal-cg", maximum, nominal_cg),
        ("maximum-forward-cg", maximum, values["acf/_cgZ_fwd"]),
        ("maximum-aft-cg", maximum, values["acf/_cgZ_aft"]),
    ]


def analyze(root: Path, geometry_source: Path) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    all_heights: list[float] = []
    for display_name, stem in VARIANTS:
        acf_path = root / f"{stem}.acf"
        obj_path = root / "objects" / stem / f"{stem}_fuselage.obj"
        values = parse_acf(acf_path)
        vertices, indices, lines = parse_obj8(obj_path)
        thresholds = {door: door_threshold(vertices, indices, lines, door) for door in ("L1", "L2")}
        nose_gear = gear(values, 0)
        main_gear = gear(values, 1)
        case_rows: list[dict[str, Any]] = []
        for label, weight, cg_z in scenarios(values):
            nose_force = weight * (main_gear["_gear_z"] - cg_z) / (main_gear["_gear_z"] - nose_gear["_gear_z"])
            main_force_each = (weight - nose_force) / 2.0
            nose_deflection, nose_mode = strut_deflection_ft(nose_force, nose_gear)
            main_deflection, main_mode = strut_deflection_ft(main_force_each, main_gear)
            nose_ground = wheel_ground_point(nose_gear, nose_deflection)
            main_ground = wheel_ground_point(main_gear, main_deflection)
            door_rows: dict[str, Any] = {}
            for door, threshold in thresholds.items():
                measured_height = height_above_gear_plane(threshold["xyz_m"], nose_ground, main_ground)
                selected, residual = select_model(measured_height)
                all_heights.append(measured_height)
                door_rows[door] = {
                    "estimated_sill_height_m": measured_height,
                    "selected_platform_height_m": selected,
                    "signed_contact_residual_m": residual,
                    "within_tolerance": abs(residual) <= FIT_TOLERANCE_M + 1e-9,
                }
            case_rows.append(
                {
                    "id": label,
                    "weight_lb": weight,
                    "cg_z_ft": cg_z,
                    "gear_reaction_lbf": {"nose": nose_force, "main_each": main_force_each},
                    "strut_deflection_ft": {"nose": nose_deflection, "main": main_deflection},
                    "strut_estimate_mode": {"nose": nose_mode, "main": main_mode},
                    "doors": door_rows,
                }
            )
        results.append(
            {
                "variant": display_name,
                "acf": {"path": str(acf_path), "sha256": sha256(acf_path)},
                "fuselage_obj": {"path": str(obj_path), "sha256": sha256(obj_path)},
                "door_thresholds": thresholds,
                "scenarios": case_rows,
            }
        )

    minimum = min(all_heights)
    maximum = max(all_heights)
    span = maximum - minimum
    minimum_count = math.ceil((span - 1e-12) / (2.0 * FIT_TOLERANCE_M))
    return {
        "schema": 1,
        "method": {
            "door": "read-only geometric measurement of the animated LevelUp fuselage door leaf; coordinates are not reused in asset geometry",
            "attitude": "flat-ground line through estimated nose/main tire contact points after ACF strut-curve deflection",
            "loading": "operating empty, midpoint mass, maximum nominal CG, and maximum at declared forward/aft CG limits",
            "limitations": [
                "ACF spring-curve calculation is a static analytical estimate, not simulator physics output",
                "forces beyond the declared max-weight force use linear curve extrapolation and are flagged per row",
                "tire deformation and uneven terrain are not estimated",
            ],
            "gse_geometry_source": {"path": str(geometry_source), "sha256": sha256(geometry_source)},
        },
        "family_selection": {
            "fit_tolerance_m": FIT_TOLERANCE_M,
            "measured_height_range_m": [minimum, maximum],
            "continuous_span_m": span,
            "lower_bound_model_count": minimum_count,
            "selected_platform_heights_m": list(MODEL_HEIGHTS_M),
            "all_cases_covered": all(
                door["within_tolerance"]
                for variant in results
                for case in variant["scenarios"]
                for door in case["doors"].values()
            ),
        },
        "variants": results,
    }


def markdown(data: dict[str, Any]) -> str:
    family = data["family_selection"]
    rows = [
        "# LevelUp fallback-stair measurement",
        "",
        "This is a read-only aircraft-fit analysis. No third-party geometry or texture is included in the generated assets.",
        "",
        "## Model-family result",
        "",
        f"Estimated sill-height envelope: {family['measured_height_range_m'][0]:.3f}-{family['measured_height_range_m'][1]:.3f} m.",
        f"At +/-{family['fit_tolerance_m']:.2f} m contact tolerance the continuous-envelope lower bound is {family['lower_bound_model_count']} models.",
        "The selected family is 2.65 m, 2.85 m and 3.05 m.",
        "",
        "## Door contacts",
        "",
        "| Variant | Door | Aircraft-local contact X/Y/Z (m) |",
        "|---|---|---:|",
    ]
    for variant in data["variants"]:
        for door, threshold in variant["door_thresholds"].items():
            point = threshold["xyz_m"]
            rows.append(f"| {variant['variant']} | {door} | {point[0]:.3f} / {point[1]:.3f} / {point[2]:.3f} |")
    rows.extend(("", "## Static loading matrix", "", "| Variant | State | Door | Sill (m) | Model (m) | Residual (m) |", "|---|---|---|---:|---:|---:|"))
    for variant in data["variants"]:
        for case in variant["scenarios"]:
            for door, fit in case["doors"].items():
                rows.append(
                    f"| {variant['variant']} | {case['id']} | {door} | {fit['estimated_sill_height_m']:.3f} | "
                    f"{fit['selected_platform_height_m']:.2f} | {fit['signed_contact_residual_m']:+.3f} |"
                )
    rows.extend(
        (
            "",
            "## Evidence boundary",
            "",
            "The matrix validates static source geometry and an ACF-based loading sensitivity model. It is not simulator proof. "
            "Actual X-Plane strut compression, tire deformation, terrain slope and live door-to-platform contact remain runtime checks.",
            "",
        )
    )
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--levelup-root", type=Path, required=True)
    parser.add_argument("--geometry-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "measurements")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    data = analyze(args.levelup_root.resolve(), args.geometry_source.resolve())
    (output / "levelup_stair_measurements.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    (output / "MEASUREMENT_REPORT.md").write_text(markdown(data), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
