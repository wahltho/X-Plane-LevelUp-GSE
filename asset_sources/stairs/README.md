# Original static stairs

The source scripts are preserved from the separately reviewed original stair
asset task. They accept explicit output paths; their default paths reflect the
original task layout. To rebuild into this patch from its root:

```
python3 asset_sources/stairs/generate_fallback_stairs.py --output assets/stairs
python3 asset_sources/stairs/validate_fallback_stairs.py --objects assets/stairs --measurements docs/levelup_stair_measurements.json --output dist/stair-validation
```

The generator needs Pillow; validation is standard-library Python. Rebuilding
also updates provenance metadata. Then regenerate runtime numeric profiles and
rebuild the package. Do not copy any third-party model/texture source into this
repository. The measurements are derived numeric fit evidence, not a copy of
an aircraft mesh, and are not a substitute for in-simulator tests.
