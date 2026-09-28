# Preview 5: SDK object-loading path correction

ZIP SHA-256: `6207560d55597edecd9ffb437d9ae1b270583c23700661ec6fdafc4de7dd0a56`.

The reported Windows log shows repeated OBJ load failures with `C//Program Files
(x86)/Steam/...` paths, affecting both local Laminar models and original stairs.
File/hash validation had already succeeded. The SDK contract requires paths
relative to the X-Plane root: https://developer.x-plane.com/sdk/XPLMLoadObject/.

Only runtime/sdk.lua changes runtime behavior: normalize separators, verify the
root boundary, remove that root and submit a relative path to XPLMLoadObject.
Windows comparison tolerates case differences and UNC roots. Outside-root,
traversal, empty, colon and NUL paths are rejected before the SDK call. Absolute
paths remain in filesystem/hash checks; no shared XLua feature setting is changed.
Geometry, ACF contracts, service visibility, fit checks and asset hashes are unchanged.
The log's MODEL_FIT messages with unloaded stair assets are not evidence of actual
physical stair-fit failure; no placement tuning is justified by this report.

Validation on the final ZIP/source:
- 19 Python installer/package tests: PASS.
- Real SDK adapter with only native C calls mocked: Windows drive and UNC,
  macOS and Linux; both LR and own-stair paths, invalid-path refusal: PASS.
- Same regression against published Preview 4: expected FAIL on absolute SDK path.
- Numeric/hash, actual XLua init/lifecycle and original stair asset checks: PASS.
- Final ZIP fresh installation and upgrades from published Preview 3 and 4:
  official S1.51C aircraft, all five installed XLua lifecycles, payload hashes,
  repeat install, verify, uninstall and byte-identical original restoration: PASS.
- Actual MTK Core: install/repeat, foreign-owner refusal, native retirement/restore,
  upgrades from Preview 3 and 4, payload parity and repeat/restore: PASS.
- Preview 4 upgrade hashes obtained from the checksum-verified published archive.
  Only two previously absent payload hashes were added to the existing allowlist.
- Independent SDK source/test review: GO; reviewer independently ran the boundary test.
- Independent final ZIP/release review: GO; source/publication/payload parity,
  exact Preview 1-4 allowlist, own-art-only payloads and release wording confirmed.

Lifecycle tests mock native SDK functions. Boundary tests inspect the actual
adapter's submitted path, not a replacement S.load function. No real simulator
loading, placement, terrain or animation result is claimed. No live deployment,
MTK source/catalog change or third-party art redistribution is included.
