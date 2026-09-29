# Release 0.2.1 validation

ZIP SHA-256: 7bbe77ef2ceb44b58f5e02d37f50491e837a9b93523b37021dcf87c458c4abbe.

Only behavioral change: GSE frame callback is before_physics instead of
after_physics. Geometry, service visibility refs and native-file handling are
unchanged. Stock LU missing native-object log entries do not justify placeholders;
that earlier proposal was withdrawn. No placeholders are included.

- Phase regression against previous callback: expected failure in after_physics.
- Modified callback: all five official S1.51C variants pass XLua lifecycle tests,
  including persistent instances, fit latch, service reset, movement, airborne,
  restart with active instances and unload cleanup. Native SDK is mocked.
- Consolidated checks: 19 Python tests, SDK path boundary, numeric/hash,
  XLua lifecycle, stair assets and actual MTK Core: PASS.
- Actual release ZIP fresh and 0.2.0 upgrade: packaged installer, all five installed
  lifecycles, verify/repeat, payload hashes and byte-identical restoration: PASS.
- Actual MTK Core 0.2.0 upgrade, repeat, payload parity and native restore: PASS.
- Published 0.2.0 payloads checksum-verified and added to upgrade allowlist.

No simulator confirmation of the callback fix yet. A new report of a missing
front stair on -700/-800 is unresolved. Existing supplied log has no GSE fit-error
message. Upstream tablet can suppress external front stairs when using integral
airstairs or a nearby jetway. User clarification is pending; this release does
not claim to resolve that report or the cargo 98-percent report.

Local logs: dist/validation/release-0.2.1-zip.log, release-0.2.1-mtk.log and
results.json. No live installation or MTK catalog changes performed.

## Correction, 2026-09-29
The original fixture did not contain the complete official LU GSE set.
The published package rejects nine S1.51C original hashes. See
`ORIGINAL_GSE_HASH_FIX_2026-09-29.md`; the prior passing results are not
complete-aircraft installation evidence.
