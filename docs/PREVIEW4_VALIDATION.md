# Preview 4: official aircraft profile verification

Final ZIP SHA-256: `9d15adfcad105ec1c059f02b8a5a96d6e0376508dda758afbb4c192ce2fda9a6`.

Official S1.50 full archive and S1.51C delta archive were verified against their
release manifests; every used ACF, fuselage OBJ and the baseline XLua init.lua
was hash-checked. S1.51C does not replace init.lua. No official artwork or ACF is
bundled. Fixtures are supplied externally. See OFFICIAL_PROFILE_EVIDENCE.json.
The previous local S1.50A fixture is not the official S1.50 base: both are now
identified separately, alongside S1.51C.

All ten L1/L2 thresholds were independently remeasured on each official set.
Thresholds/service anchors and normalized fuselage attachment transforms remain
unchanged. S1.51C moves the 600/700/800 fuselage from slot23 to22 and changes nominal
CG references. Its 800 L2 leaf has two changed vertices above the sill, without a
threshold change. The official S1.50 900 CG differs from the old S1.50A reference.
Each profile records its own CG, object slot/signature and corresponding OBJ hash.

The runtime selects one profile by exact ACF hash, then checks its paired OBJ and
numeric/object signatures. Standalone uses the same profile set. Modified ACFs or
mixed-release OBJ pairs are rejected, not treated as interchangeable hashes.
MTK still installs declaratively; the runtime gate protects unsupported aircraft.

Verification matrix:
- 19 Python installer/package tests, numeric/hash, own stair validation: PASS.
- Both official releases, all five variants: final ZIP fresh/repeat/verify,
  installed XLua start/lifecycle, uninstall and byte-identical restoration: PASS.
- Preview3 on its old supported fixture, then official aircraft update plus
  Preview4 update: both official releases/all five lifecycles and restoration PASS.
- Modified ACF/mixed OBJ: all five variants rejected by installer before writes
  and suppressed by runtime. No silent relaxation of the geometry contract.
- Actual MTK Core, both official ACF sets/all five variants: install/repeat,
  foreign-owner refusal, Preview3 upgrade, payload parity and native restore PASS.

Native XPLM calls are mocked in lifecycle checks. Actual simulator placement,
terrain, load cases and visual behavior are still unvalidated. No live catalog
activation, simulator deployment or MTK source changes are part of this release.
Local detailed evidence: dist/validation/release-zip-50.log, release-zip-51.log,
profile-rejection.log, mtk-official-matrix.log and the standard check logs.

Independent final source/package review: GO at the ZIP hash above. Reviewer
independently verified all 15 candidate pairs (including retained S1.50A),
attachment signatures, service anchors and CG against local verified inputs,
and checked ZIP/source parity, exact previous-payload allowlist and own-art-only
contents. Tests were reviewed from evidence rather than independently rerun.
