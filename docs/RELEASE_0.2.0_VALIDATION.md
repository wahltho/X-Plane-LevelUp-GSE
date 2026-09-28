# Regular release 0.2.0

ZIP SHA-256: `9f9376e0b993189b3de63c327e8b6803a490c51dc3a353824ae85abd0d61d4bd`.

This is the first non-prerelease distribution, promoted at the maintainer's
explicit request. A user reported that all equipment now displays following the
Preview 5 path correction. This is evidence of successful display in that user's
installation, not a completed five-variant positioning or terrain acceptance test.

Runtime behavior and geometry are unchanged from Preview 5. The only Lua change
is the startup log text. Package version, description, current installation and
release documentation no longer identify the current distribution as a preview.
The Preview 5 SDK hash was added from the verified public ZIP to the existing
upgrade allowlist; all prior preview hashes remain available.

Release checks:
- 19 Python installer/package tests, SDK path boundary tests, numeric/hash tests,
  actual XLua-init lifecycle and own-stair geometry checks: PASS.
- Final packaged CLI: fresh installation and upgrades from Preview 3, 4 and 5,
  repeat/verify, all five official S1.51C aircraft lifecycles, payload hashes,
  uninstall and byte-identical restoration: PASS.
- Actual MTK Core: schema-4 install/repeat, foreign-owner rejection, native GSE
  retirement/restoration, Preview 3/4/5 updates, payload parity and restore: PASS.
- Independent source/ZIP review: GO. Exact published Preview 1-5 allowlist union,
  payload/source/documentation parity and unchanged installation scopes verified.

MTK package ID remains jt8d17.levelup-737ng.gse, module gse, optional and disabled
by default. The same release ZIP supports standalone installation and the MTK
schema-4 engine. Live catalog activation is separate and was not performed here.
No MTK code, aircraft ACF, W&B, flight model or plugin binary changes are included.
No third-party asset content is distributed.

Automated lifecycle tests mock native SDK calls; path tests exercise the actual
SDK adapter with its native C boundary mocked. Detailed simulator positioning,
all five variants, light/heavy loads, slopes, service transitions and reloads
remain open. Compatibility profile coverage remains official S1.50/S1.51C plus
the retained S1.50A development reference; no guards were relaxed.

Local evidence: dist/validation/results.json, release-0.2.0-zip.log and
release-0.2.0-mtk.log. Historical preview evidence is retained separately.
