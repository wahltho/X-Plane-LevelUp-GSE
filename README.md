# LevelUp GSE — Option B

**Version 0.2.1.** Install using the standalone Python
installer or an MTK schema-4 compatibility package (MTK 0.19.0 or newer).

A user has confirmed that equipment appears in the simulator after the Preview 5
object-loading fix. Version 0.2.1 retains that fix and the existing geometry, and moves GSE instance
updates to the pre-flightloop phase to resolve the post-flightloop warning.
Detailed positioning checks across all five variants, loads and terrain conditions
remain open; see the limits below. No additional libraries are required.

Upgrade earlier previews using the same installer that currently owns the patch.
Previews 1–4 contain known loading defects and should be replaced.

A standalone, unofficial GSE positioning patch for the LevelUp 737-600, -700,
-800, -900 and -900ER. Uses the user's locally installed Laminar equipment and
three original static stairs (2.65, 2.85 and 3.05 metres). No separate Zibo
installation and no Laminar/Zibo models or textures in the package.

The public release repository is https://github.com/wahltho/X-Plane-LevelUp-GSE.
Local development source remains `Zibo Mod/Documentation/levelup_gse_patch`;
the separate Git publication checkout is an export, not a second source tree.

## What it does

- Uses existing EFB show/hide state without changing service/loading datarefs.
- Positions local Laminar models using variant service stations, model contact
  curves and terrain fits. Working height is chosen when a service appears.
- Selects a fitting original static stair per door and service activation;
  rejects contact/ground mismatch greater than 0.10 m. No static model scaling.
- Verifies aircraft geometry and local model/texture hashes. Unsupported assets
  disable the affected equipment with a log message rather than drawing it wrong.
- Retires known native GSE reversibly to prevent duplicate plugin rendering.
  Unknown files block installation. Original files are restored on uninstall.
- Works through a standalone Python installer or an unchanged schema-4 MTK
  engine (0.19.0 or newer). No local-Zibo-copy capability or new schema required.

## Limits

Verified aircraft profiles cover the official S1.50 base package and S1.51C
update, plus the earlier S1.50A development reference. Each profile binds one
exact ACF hash to its corresponding fuselage object, attachment properties,
remeasured door thresholds and CG reference. Unknown or locally edited aircraft
files are rejected; mixing objects from different releases is not supported.
Local Laminar equipment is still hash-checked and a changed model needs review.

Static fuel/deice equipment does not reproduce Zibo hose/spray/drive-up effects.
All support-point/contact calculations and own stair family still need real
simulator inspection on all five variants, including light/heavy loads and slopes.
A fit failure hides that role until the EFB service is toggled off/on.

Use only the original public LU plugin with XLua/LuaJIT FFI support. Do not combine
with another custom GSE runtime, including the private C++ port. The patch does
not modify ACF, flight model, W&B, or Zibomod binaries.

## Build and checks

`python3 tools/build_package.py` creates a ZIP and checksum under `dist`.
`python3 -m unittest discover -s tests -v` exercises the installer and package.
The consolidated runner requires explicit `--luajit` and `--xlua-init` paths,
plus the local reference paths shown by `python3 tools/run_checks.py --help`.
No third-party XLua source is bundled.
`tools/import_profiles.py` is a developer-only numeric/hash extraction tool;
supply the five explicit local reference paths shown by its --help output.
No extracted mesh vertices or textures are stored in those runtime profiles.

See INSTALLATION.md and docs/VALIDATION.md for installation and release evidence.
No automatic download/update checker.

## Credits and provenance

Laminar Research: local X-Plane default equipment, loaded in place.
Zibo: the original service visibility interface; no Zibo artwork distributed.
BK/RandomUser/JT8D-17: original GSE placement approach and integration discussion.
Thomas: patch implementation, numeric port-derived station data and independently
created fallback stairs. The new runtime is written for Option B rather than
redistributing RandomUser's private asset collection or repository history.
