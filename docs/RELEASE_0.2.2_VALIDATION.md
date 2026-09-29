# Release 0.2.2 validation

Compatibility update for separately present verified original LU GSE files.
Normal official LU downloads contain no native GSE and were not affected by
the v0.2.1 rejection. No runtime/geometry change or expanded ACF acceptance.

## Official distribution verification
Downloaded from petrolpram/737NG-Updates:
- S1.50 full archive SHA256: b62f01c3446bd5a311c8a7b7aa596c117ed29c2f602e5c694dd5aed77556f7af
- S1.51C delta SHA256: 7dba2a5b0ab8f1ad1d9f262aa28609a62908a04dacb21106b7b737a93229d4dc
Both match GitHub release asset digests. All 3615 base manifest entries and
66 delta entries were checked against their file hashes. The delta was applied
including its deleted paths. Neither download contains native GSE objects.
All five variants from BOTH complete released aircraft stands pass standalone
check/install/verify/repeat and full file-hash restoration. Unknown GSE rejects
without writes. The tagged S1.50C source ACF remains separately unsupported;
it must not be confused with the released S1.50 base.

## Additional native originals
Nine additional path/hash pairs from the official S1.50C/S1.51C Git tags;
provenance in packaging/official_lu_gse.json. All 68 managed retirement paths
are unchanged; original accepted hashes are preserved. Importer regeneration
retains the official contract. Complete source-tag S1.51C aircraft (all five
variants) passes standalone installation/repeat/restore. Modified texture/ASU/GPU
and unknown files reject without writes. Actual MTK transactions tested the
complete 12-file native GSE sets of both tags, including byte-identical restore.

## Automated checks
20 Python package tests; SDK path tests; numeric/hash tests; mocked XLua
lifecycle; own stair validator; actual MTK Core checks pass. A concurrent
scratch-fixture read initially hit a temporarily removed ACF; rerunning after
the fixture mutation test completed passes. This was test scheduling, not a
production defect.
Final ZIP check covers fresh install and upgrades from 0.2.0/0.2.1 with all-five
installed XLua lifecycle, repeat, payload hashes and exact restoration.
Actual MTK upgrades from both public ZIPs, repeat and restore pass, plus the
complete S1.51C original GSE set and modified-file rejection.

MTK live catalog already selects levelup-gse-*.zip from this repository;
no catalog change required. Simulator position validation remains open.

Package SHA256: 574c342614ba799e2e7a8001c08e43f9b6baa9b2137b6f959251cfc02e48f715
