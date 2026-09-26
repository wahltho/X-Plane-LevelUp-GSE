# XLua dofile integration review — 2026-09-26

The published Preview 1/2 runtime has a confirmed loader defect. XLua's
namespace-specific dofile executes a chunk but discards its return values.
The four assigned imports therefore become nil; flight_start fails on S.paths.
The prior lifecycle fixture returned ordinary Lua results and missed this.
This finding supersedes the earlier no-source-blocker assessment for those releases.

## Comparison and correction

W&B and flight-control lockout modules publish named exports before their adapter
consumes them. The tablet performance patch uses the same approach. GSE now loads
each helper and reads a named LU_GSE_* namespace export. Table exports use
real_table to preserve raw tables; SHA-256 exports a function. Ordinary Lua return
values remain available for standalone numeric tests. The profile generator writes
the same export contract, so regeneration cannot undo the correction.

The installed folder and entrypoint both use LU_737NG.GSE; XLua discovers this
independent module directly. Unlike W&B/tablet performance, no injected hook in an
existing Tablet/FMS script is required. XLua resolves dofile against the module
folder. A full XLua reload destroys its interpreter; flight_start only resets
resources and does not rerun FFI declarations.

## Verification

- Baseline reproduced with actual MTK XLua r1.3.7r4 init.lua: nil S at flight_start.
- Corrected lifecycle passed with that init.lua and the original LU S1.50A init.lua.
- Test executes the actual namespace/dofile logic, actual SDK declarations/export
  with native-library access mocked, all helper exports and raw profile assertions.
- Persistent instances, fit-failure latch, service reset and repeated flight
  start/unload release checks passed. Numeric/hash regression checks passed.
- Python compile checks for importer and check runner passed.
- Independent read-only final diff review: loader root cause closed; no remaining
  concrete blocker within the loader scope. Reviewer did not rerun the tests.

Run tests/lifecycle.lua with root, LU reference, X-Plane root, and actual XLua
init.lua as four arguments. tools/run_checks.py now also requires --xlua-init.
No third-party init.lua is bundled.

Follow-up: Preview 3 packages this correction. Preview 1/2 remain affected and
are publicly marked accordingly. See PREVIEW3_VALIDATION.md for package evidence.
Simulator validation remains open; mocked native calls do not establish it.
