# Independent implementation review — Option B

Date: 2026-09-26. Reviewer: independent read-only agent, followed by this report only.
Canonical source: `Zibo Mod/Documentation/levelup_gse_patch`, branch `main`.
Git base checked: `b18a1264c3090fc02c870501849ee016a9075e84`.
Unrelated untracked investigation files were left untouched.

## Verdict

**SOURCE-READY PREVIEW** for the reviewed Option B implementation: unchanged local
Laminar assets plus original static fallback stairs, standalone installer and
existing MTK schema4 packaging. No remaining concrete source blocker identified
in the reviewed owner chains. This verdict does not approve deployment, publication,
or claim simulator fit. It does not reinstate the earlier native-provider/local-copy
schema5 design: the reviewed implementation is explicitly Option B.

## Review scope and corrected findings

- Traced ACF identity/signatures and measured door geometry through body-to-world
  rotation, terrain sampling, model profile selection and XPLM instance publication.
- Ground cross-slope roll sign was reversed in the first snapshot. Corrected
  negative roll now agrees with the actual rotation matrix and support plane.
- Stair instances were destroyed/recreated and heights reselected every frame.
  Model choice now persists through the visible service; failure hides and latches
  until service/reset conditions. Objects remain loaded until aircraft unload.
- Belt/catering used fixed arbitrary animation constants and native origin offsets.
  Current code uses local OBJ8-derived contact curves, physical ACF service XYZ,
  terrain-supported pose and per-instance stationary working parameters. Driver
  shares the same role, visibility and world pose. No global animation writes.
- Equipment now uses terrain plane/support profiles rather than one point plus
  forced zero pitch/roll. Unusable terrain or contact residual suppresses drawing.
- Fixed door contacts now require the measured fuselage OBJ hash and relevant
  aircraft object mapping/transform signature, not only unchanged service anchors.
- SDK uses synchronous object loading, persistent FFI string buffers, compatible
  draw/probe layouts, checked probe return and instance-before-object cleanup.
- Standalone now rejects running X-Plane and supports conservative same-host
  dead-process lock recovery. No process is terminated to clear a lock.
- Committed uninstall cleanup is recoverable via the moved completion archive.
  Cleanup now requires its own committed uninstall journal, verified previous
  package state and absence of unexpected files; path name alone cannot authorize
  recursive deletion. This closes the final data-loss finding.
- Initial concern that a fresh absent `objects/GSE` scope remained absent was
  withdrawn: the actual package contains an owned README copy target creating it.
  The runtime checks known conflicting OBJ paths, so this README does not disable it.

## Verification evidence and independence

The review independently inspected production source and the fixing snapshots.
The implementing agent reports 16 passing Python tests, LuaJIT geometry/hash tests,
a real runtime mock lifecycle using local inputs, and actual MTK package-loader /
install / repeat / foreign-owner-block / restore smoke success. Those runs were
not rerun by this reviewer and are not simulator evidence. Preserve the final run
outputs and package hashes with the build record. Source hashes below bind this
review; later behavioral changes require another scoped review.

## Remaining release gates and practical limits

1. Simulator validation remains mandatory for all five variants: contact/clearance,
   wheel placement, normal light/heavy loading, sloping terrain, service transitions,
   aircraft reload/unload and absence of duplicate equipment. Dry geometry and
   synthetic SDK mocks cannot establish those results.
2. The original stair family is the supplied 2.65/2.85/3.05 m static family, selected
   with the implemented 0.10 m residual limit. The independently measured scenario
   report supports preview coverage, not arbitrary modified ACF or terrain states.
   Out-of-fit roles intentionally disappear rather than change foreign model data.
3. LR catering has a physical lower contact region around 2.71 m in sampled profiles;
   verify heavy-aircraft and sloping-apron cases against the fit gate. Unreachable
   working geometry is a MODEL_FIT condition, not proof of a loading-system defect.
4. Profile SHA restrictions intentionally disable unknown changed model geometry.
   Future LR or LU model revisions require numeric/profile review. Geometry-derived
   support envelopes and selected contacts still need visual simulator confirmation.
5. MTK and standalone must not run simultaneously. This schema4 Option B does not
   add a common inter-installer mutex or generic MTK crash journal. Sequential owner
   rejection is supported; universal concurrent-install safety is not claimed.
6. A hard interruption while creating original backups before a durable journal can
   leave incomplete standalone state requiring conservative manual recovery. Original
   aircraft bytes have not yet been changed at that stage. Do not advertise automatic
   recovery from every instruction boundary or arbitrary filesystem/hardware failure.
7. No deployment, simulator run, commit or publication was performed by this reviewer.

## Reviewed source snapshot

| File | SHA-256 |
|---|---|
| `runtime/geometry.lua` | `5bb7f52d2730f4ee438c23bd2aa20c3679e5196e1b7cb79d250fcc7ed5e26a2d` |
| `runtime/LU_737NG.GSE.lua` | `39f5ad8446deee2c803e9fb9262fa0281089b480f13c682d8a61f2474753fd85` |
| `runtime/sdk.lua` | `5b099d00b22303a1020f7e0f891419d3a99c9461d9cd2d412b813a1683e6c11f` |
| `runtime/sha256.lua` | `3c8a1fd5c3c94cdd2b199f5257780535ab987bbd7975d9637837d3b239ebe9e3` |
| `runtime/profiles.lua` | `159637e42a01bcfb804839b289956e06a36f62a5503f5807dc4dfc679a162cb7` |
| `tools/model_geometry.py` | `8c80639152e61b51e8c4a99c1e93e73b0f28f7c8c985cf8235593d637136a63b` |
| `tools/import_profiles.py` | `5c5f3e9fb2858dba9e5e655e6e1c3b305cfea8c773a19324878d52be9ec05040` |
| `z_Install.py` | `941e0f621830bda1724a3a26759291d364df88d72e32772ca7a7f759538051f4` |
| `packaging/profiles.json` | `045d40802ce76862459afc7e988ffc822cfc044f8eda5838543fc6723630b16a` |
| `assets/stairs/model_profiles.json` | `8e0966e55d60f8634a2a2c0e52f247744f0c41ae8cc84492281ed2f1d0ec38f0` |
