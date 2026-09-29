# Official LU GSE original hash correction — 2026-09-29

## Finding and correction
Published v0.2.1 ZIP SHA256:
`7bbe77ef2ceb44b58f5e02d37f50491e837a9b93523b37021dcf87c458c4abbe`.
The standalone check fails on `objects/GSE/737misc2.dds` from the
S1.51C Git tag. Nine of twelve original GSE files were absent from the
allowlist; S1.50C has eight missing hashes. The importer used Zibo and legacy
renamed GSE sources only. Earlier ZIP tests constructed an aircraft fixture
with one known Zibo GPU, so they did not cover the complete official LU GSE set.
The earlier release validation must not be read as full-aircraft coverage.

`packaging/official_lu_gse.json` records repository, exact tag commits and all
12 path hashes per source. `retired.json` adds only these verified hashes;
existing verified Zibo/legacy originals remain accepted. `import_profiles.py`
merges this contract during regeneration. Installer/runtime behavior is unchanged.

## Scope and evidence
Sources are complete Git archives from `petrolpram/737NG-Series`:
- S1.50C: `5ab6c3ae3096428abc3503211e13f6b9076c7fa7` (3645 files).
- S1.51C: `478d6ce164045aa5e7059de755ed5cab6a97b445` (3229 files).
These are tagged source snapshots, NOT independently downloaded release ZIPs.

The test package was built in `/private/tmp/gse-originals-fix-validation/source`.
It retains the old version string solely for local testing; it must never be
published as a replacement v0.2.1. Public artifacts were not overwritten.

- 20 package tests pass, including the new official-original contract check.
- Complete S1.51C: check, install, verify, repeat, uninstall, complete file-hash
  restoration pass. Modified texture/ASU/GPU and unknown OBJ block check and
  install without file changes.
- All five isolated S1.51C ACF variants pass check/install/verify/repeat/full restore.
  Logs are retained in `docs/investigations/original_gse_hash_fix_2026-09-29/`.
- Actual MTK Core: complete 12-file GSE sets from BOTH source tags pass
  install, repeat, byte-identical restore and modified-original rejection.
  This checks the MTK package transaction, not aircraft runtime acceptance.
- S1.50C standalone full-aircraft check still rejects its ACF as unsupported.
  This is a separate pre-existing exact-profile boundary, deliberately unchanged.
  Full S1.50C standalone install/restore is NOT claimed as passing.

Reproducible standalone regression: `tests/full_aircraft_install.py` requires
an expendable complete supported aircraft export and a built package.
MTK regression: set `GSE_TEST_ORIGINAL_GSE` to the full original GSE directory
when running `tests/mtk/Smoke.csproj`.

No simulator validation, commit, push or public release in this correction.
Release gate: assign new version, perform normal final-package release checks;
resolve intended S1.50C support separately before claiming that compatibility.

## Completed distribution check
The official downloads contain no native GSE files. See RELEASE_0.2.2_VALIDATION.md
for verified archives and complete released-aircraft tests. The correction is
for separately present original files, not a general release-install failure.
