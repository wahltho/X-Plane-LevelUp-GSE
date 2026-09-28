"""Exercise actual ZIP payloads and packaged installers in scratch aircraft only."""
import argparse, hashlib, json, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
for name in ('zip', 'previous-dir', 'lu-reference', 'xplane-root', 'luajit', 'xlua-init', 'native-gpu', 'previous-aircraft'):
    p.add_argument('--'+name, required=True, type=Path)
a = p.parse_args()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def extract(archive, target):
    expected = archive.with_suffix('.zip.sha256').read_text().split()[0]
    assert sha(archive) == expected, archive
    with zipfile.ZipFile(archive) as z: z.extractall(target)
    m = json.loads((target/'package-manifest.json').read_text())
    for item in m['modules'][0]['payloads']:
        path = target/'modules/gse'/item['path']
        assert sha(path) == item['sha256'] and path.stat().st_size == item['size']
    return m
with tempfile.TemporaryDirectory(prefix='gse-zip-') as tmp:
    base = Path(tmp).resolve(); latest = base/'latest'
    manifest = extract(a.zip, latest)
    assert manifest['packageVersion'] == '0.2.0-preview.5'
    packages = {}
    for version in ('3', '4'):
        old = base/('old'+version)
        extract(a.previous_dir/('levelup-gse-0.2.0-preview.'+version+'.zip'), old)
        packages[version] = old
    subprocess.run([str(a.luajit), str(ROOT/'tests/sdk_paths.lua'),
                    str(latest/'modules/gse/plugins/xlua/scripts/LU_737NG.GSE/sdk.lua')], check=True)
    profiles = json.loads((latest/'profiles.json').read_text())
    for version in ('fresh', '3', '4'):
        aircraft = base/('aircraft-'+version); aircraft.mkdir()
        (aircraft/'plugins/xlua/scripts').mkdir(parents=True)
        for name, profile in profiles['variants'].items():
            shutil.copy2(a.lu_reference/name, aircraft/name)
            obj = profile['door_object']['path']; dst = aircraft/obj
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(a.lu_reference/obj, dst)
        native = aircraft/'objects/GSE/gpu.obj'; native.parent.mkdir(parents=True)
        shutil.copy2(a.native_gpu, native)
        (aircraft/'unrelated-user.txt').write_text('must survive')
        before = {str(f.relative_to(aircraft)): sha(f) for f in aircraft.rglob('*') if f.is_file()}
        def run(package, command):
            r = subprocess.run([sys.executable, str(package/'z_Install.py'), command,
                                '--aircraft-root', str(aircraft)], text=True, capture_output=True)
            assert r.returncode == 0, r.stdout+r.stderr
            return r.stdout
        if version != 'fresh':
            # Previously installed preview on its supported reference, followed by
            # official aircraft update; patch then updates against the new aircraft.
            for name, profile in profiles['variants'].items():
                shutil.copy2(a.previous_aircraft/name, aircraft/name)
                shutil.copy2(a.previous_aircraft/profile['door_object']['path'], aircraft/profile['door_object']['path'])
            run(packages[version], 'install')
            for name, profile in profiles['variants'].items():
                shutil.copy2(a.lu_reference/name, aircraft/name)
                shutil.copy2(a.lu_reference/profile['door_object']['path'], aircraft/profile['door_object']['path'])
        run(latest, 'check'); run(latest, 'install'); run(latest, 'verify')
        assert 'Already installed' in run(latest, 'install')
        assert not native.exists()
        for item in manifest['modules'][0]['payloads']:
            assert sha(aircraft/item['path']) == item['sha256']
        for name in profiles['variants']:
            r = subprocess.run([str(a.luajit), str(ROOT/'tests/lifecycle.lua'), str(ROOT),
                                str(aircraft), str(a.xplane_root), str(a.xlua_init),
                                str(aircraft/'plugins/xlua/scripts/LU_737NG.GSE'),
                                str(aircraft/'objects/LU_GSE_stairs'), name], text=True, capture_output=True)
            assert r.returncode == 0, r.stdout+r.stderr
        run(latest, 'uninstall')
        after = {str(f.relative_to(aircraft)): sha(f) for f in aircraft.rglob('*') if f.is_file()}
        assert before == after, 'restore mismatch '+version
        print(version+': packaged CLI install/update/repeat, installed XLua lifecycle, hashes and byte-identical restore PASS')
print('Release ZIP integration PASS: '+sha(a.zip))
