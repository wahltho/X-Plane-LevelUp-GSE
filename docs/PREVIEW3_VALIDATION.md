# Preview 3 package verification

Package SHA-256: `1af7d3987ea2174fa24190cdb27593bdc81f85ca826f0bf29ede43efb56d6094`

The XLua loader defect is fixed through four explicit namespace exports;
no runtime geometry or service behavior is otherwise changed. The profile
generator preserves these exports. Prior source-ready assessments did not
cover actual XLua dofile semantics and are superseded for Preview 1/2.

- 19 Python installer/package tests passed.
- Numeric/hash, original stair validation and actual XLua init.lua lifecycle passed.
- Actual final ZIP: fresh install, Preview 1 and Preview 2 upgrade, repeat,
  verification, installed Lua lifecycle and byte-identical full file restoration passed.
- Previous release ZIP checksums and each payload hash were verified before use.
- Actual MTK Core: fresh/repeat/foreign-owner/restore and both previous ZIP upgrades,
  repeat, installed payload parity and native GPU restoration passed.
- Package upgrade metadata now allows the exact hashes of previously published own
  payloads. No MTK source change. Unknown hashes remain outside that allowlist.
- No LR/Zibo art assets are bundled. Only original stairs are included.

The XLua lifecycle test loads the supplied genuine init.lua and installed scripts;
XPLM library calls remain mocked. This is not a simulator validation. All five
variants, load cases, slopes and visual/operational behavior still require testing.
No live catalog activation or simulator deployment was performed.

Reproduction: tools/run_checks.py requires --xlua-init in addition to the other
local reference paths. tests/release_zip.py --help lists the final ZIP and previous
release inputs; tests/mtk/Smoke.csproj accepts package, native GPU, then previous
unpacked packages. Detailed local logs are in dist/validation/.

Independent final review: GO for Preview 3. Reviewer independently compared the
allowlist against both published ZIPs and checked final package/source parity for
manifest, runtime, assets and installer at the SHA above. No remaining concrete
package/loader blockers. Test results were reviewed from logs, not independently
rerun by the reviewer. Simulator validation remains open.
