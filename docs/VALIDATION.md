# Release validation

The current regular release is v0.2.2. See [RELEASE_0.2.2_VALIDATION.md](RELEASE_0.2.2_VALIDATION.md)
for its checks, user confirmation and remaining simulator coverage.

The following is historical evidence from the initial development build.

# Build validation — 2026-09-26

Status: SOURCE-READY PREVIEW, not simulator or stable-release approval.

- Python standalone/package: 18 tests passed (fresh/repeat/restore, native retirement,
  changed/unknown files, ownership, corruption, symlinks, offline rejection,
  exception rollback, committed install/uninstall recovery and completion conflicts).
- LuaJIT: known SHA-256 vectors, five variants, 25 stair-height cases, terrain
  slopes, world coordinates, dynamic-model contact curves, misses and range rejection.
- Actual runtime with a mocked SDK and local source inputs: persistent instance,
  fit-failure latch, off/on reset and complete unload passed.
- Original stair validator: all three meshes and all 50 analytical fit cases pass.
- Actual MTK Core schema4 package: load/install/idempotent repeat/foreign-owner
  blocking/restore, plus retirement and byte-identical restoration of a known
  original native GPU in an isolated temporary aircraft directory passed.
- Independent read-only implementation review: see INDEPENDENT_REVIEW.md.

All tests used scratch directories or read-only references. No live aircraft
installation, ACF, W&B, production plugin or MTK source was changed.

Remaining simulator gate: original public LU plugin on all five variants;
light/heavy load, doors/cargo/platform and wheel contact, sloped terrain,
service transitions, aircraft reload and no duplicate rendering. Catering's
minimum reachable local-model contact height must be checked particularly.

Operational limits: MTK and standalone must not run simultaneously. A hard
interruption before a complete standalone journal can require manual recovery;
retain backups. No universal cross-installer or power-loss guarantee is claimed.

Machine-readable evidence and full logs: dist/validation/results.json and *.log.
Package SHA-256: a2e69228abd3f1aee089f4d6f74c0945f0f8328d3af05fa6dbe03c1e25049e67
