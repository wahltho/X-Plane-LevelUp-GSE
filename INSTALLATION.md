# Installation

Version 0.2.2 supports verified official S1.50 and S1.51C aircraft files.
Download the release ZIP; do not copy individual files or the modules folder into
the aircraft. Earlier previews can be updated using the same installer owner.

Close X-Plane before installing or restoring. Use one installer owner at a time.
Back up your aircraft before installation. Extract the release ZIP outside
the aircraft folder. Python 3.10+ is required for the standalone installer.

```
python3 z_Install.py check --aircraft-root "/path/to/737NG Series"
python3 z_Install.py install --aircraft-root "/path/to/737NG Series"
python3 z_Install.py verify --aircraft-root "/path/to/737NG Series"
python3 z_Install.py uninstall --aircraft-root "/path/to/737NG Series"
```

For MTK use the same package through its compatibility-package installation
path. The package is optional. Availability in MTK depends on its catalog; publishing
this ZIP does not automatically add or enable a maintenance-group entry.

Known native files in objects/GSE are backed up then retired. Unknown files,
modified installed files, links and unexpected managed-folder content block the
operation before aircraft writes. The local Laminar files are read only and are
never copied into the release. Our own stairs are installed under objects/LU_GSE_stairs.

Switching owner: uninstall with the owner that installed the patch first. The
standalone marker in the script scope intentionally blocks MTK takeover; an
MTK/manual script installation likewise blocks fresh standalone installation.
Do not run installers concurrently. An MTK run does not use the standalone lock.

Retain .levelup-gse-patch until standalone uninstall completes: it contains your
originals. After an interrupted standalone operation, use `recover` instead of
install. Recovery rolls the operation back only when file hashes and scope
contents still match its journal; it does not overwrite conflicting user edits.
The recover command can reclaim a recorded lock from a terminated process on
the same host. Incomplete or foreign-host locks require manual resolution after
confirming no installer/X-Plane is running. If the journal is incomplete,
retain all backups for manual recovery; do not delete the state to force install.

An aircraft update that recreates original native GSE requires uninstall/reinstall
or resolution through the owning toolkit. Runtime reports conflicts and refuses
its own GSE rather than allowing duplicate objects. Log.txt messages use [LU GSE].

No live simulator installation is part of the development build process.
