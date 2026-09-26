# Fallback stair static validation

| Asset | OBJ8 | High tris | Low tris | Ground Y | Contact |
|---|---|---:|---:|---:|---:|
| LU_fallback_stairs_265.obj | PASS | 2076 | 292 | 0.000 | 0.00/2.65/0.00 |
| LU_fallback_stairs_285.obj | PASS | 2112 | 292 | 0.000 | 0.00/2.85/0.00 |
| LU_fallback_stairs_305.obj | PASS | 2184 | 292 | 0.000 | 0.00/3.05/0.00 |

## Coverage

PASS: 50 door/load cases across 5 variants and doors L1, L2; maximum absolute static contact residual 0.097 m.

Checks cover OBJ8 structure, triangle/index ranges, unit normals, winding, UV bounds, texture linkage, static-only commands, origin/contact contract, wheel ground points, LOD draw ranges, polygon budget and the complete static fit matrix.

Simulator contact, live strut/tire behavior, terrain slope and aircraft reload remain outside this static validation.
