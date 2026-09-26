# Fallback stair asset handoff

## Decision

The minimum justified family is three static heights: 2.65 m, 2.85 m and 3.05 m. The measured continuous static envelope is 2.573-3.106 m. A static model accepted only within +/-0.10 m covers at most 0.20 m, so two models cannot cover the 0.533 m envelope; the selected three cover all 50 measured variant/door/load cases with a worst residual of 0.097 m.

The five variants share the same L1 and L2 threshold cross-sections; their longitudinal door stations shift with fuselage length. Height variation is driven more by aircraft attitude, strut compression, load and door station than by a unique fuselage type. Separate forward/aft or per-variant meshes would therefore add files without improving the bounded selection contract.

## Common model profile

Every model is independently generated from primitives: 1.10 m clear stair width, 0.28 m tread depth, <=0.19 m equal risers, 1.25 x 1.20 m top platform, tubular guardrails, paired stringer/platform frame and four 0.18 m radius wheels. The single original texture atlas supplies painted structure, safety yellow, dark metal and rubber regions through explicit UVs.

Origin is `(0,0,0)` on the ground below the door-facing platform-edge centre. Model contact is `(0,H,0)`. Stair run is -X; +X is aircraft right, +Y up and +Z aft. Nominal heading is 0 degrees. Exact wheel points, bounds, riser count, hashes and LOD counts are in `generated/objects/model_profiles.json`.

| Model | Platform | Risers | High/low triangles | Assigned use |
|---|---:|---:|---:|---|
| `LU_fallback_stairs_265.obj` | 2.65 m | 14 | 2076 / 292 | nearest-fit L1/L2, all five variants |
| `LU_fallback_stairs_285.obj` | 2.85 m | 15 | 2112 / 292 | nearest-fit L1/L2, all five variants |
| `LU_fallback_stairs_305.obj` | 3.05 m | 17 | 2184 / 292 | nearest-fit L1/L2, all five variants |

The models use one 512 x 512 texture, one indexed draw range per LOD, no animation commands and LOD ranges 0-220 m and 220-1500 m.

## Aircraft contacts and integration

Use the threshold points in `measurements/levelup_stair_measurements.json`, transformed by the current aircraft pose. Do not reuse the existing native-stair `EquipmentSpec` origin offsets: those offsets belong to the Zibo asset origins, not these contact-centred models.

Relative to the current LevelUp door service anchors in `gse_geometry.inc`, the measured fallback contact is approximately +0.558 m aft and 0.281 m farther left for L1, and +0.520 m aft and 0.208 m inboard for L2. Store exact per-variant threshold XYZ from the measurement JSON, not rounded prose values.

For a later runtime implementation:

1. Transform the selected door threshold to world coordinates using live aircraft position, pitch and roll.
2. Determine a valid local ground plane from at least three non-collinear terrain samples covering the four declared wheel points.
3. Compute required platform height from the door contact to that plane, select the nearest of the three heights, and reject residuals above 0.10 m.
4. Place the model origin on the ground plane so local contact `(0,H,0)` coincides with the door threshold; nominal model heading is aircraft heading with no native 2/-5 degree stair correction.
5. Recheck all four transformed wheel points against the ground plane. Hide on terrain miss or residual above 0.10 m; do not scale or vertically float a static model.

## Validation status and limitations

Static validation passes OBJ8 structure, counts, indices, winding, unit normals, UV bounds, texture link, static-only contract, origins, contact points, wheel ground points, LODs, polygon budget and all 50 fit cases. The Blender preview was inspected for disconnected structure, inverted faces, floating components and atlas errors after correcting the first render; the final image is `validation/fallback_stairs_family.png`.

No simulator validation is claimed. The local productive X-Plane installation contains only two of the five aircraft variants and no authorized standalone fallback runtime integration; it was deliberately not modified. Live X-Plane strut/tire deformation, sloped terrain, reload behavior and actual door contact remain mandatory later-patch/runtime checks. The ACF load model is analytical and flags curve extrapolation; it is not simulator physics output.

No ACF, flight model, W&B, installer, MTK, existing GSE asset, production aircraft installation, release, commit or push was changed by this asset work.
