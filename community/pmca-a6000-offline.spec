# Application-only personal build. Run PyInstaller on Windows, not by cross-build.
# Verify and copy the authorized APK collection before invoking this spec.
from pathlib import Path
import hashlib
import json
import sys

root = Path(SPECPATH)
catalog_dir = root / 'offline-apps'
catalog = json.loads((catalog_dir / 'catalog.json').read_text(encoding='utf-8'))
apps = catalog['apps']
if (catalog.get('version') != 1 or len(apps) != 21
        or len({app['package'] for app in apps}) != 21):
    raise ValueError('The personal build requires the complete 21-app catalog')
for app in apps:
    filename = app['file']
    path = (catalog_dir / filename).resolve()
    if path.parent != catalog_dir.resolve() or path.suffix != '.apk':
        raise ValueError('APK must be inside offline-apps')
    data = path.read_bytes()
    if len(data) != app['size'] or hashlib.sha256(data).hexdigest() != app['sha256']:
        raise ValueError('Missing or changed APK: ' + filename)

hiddenimports = ['pmca.catalog', 'pmca.offline', 'pmca.online', 'tlslite', 'axmlparserpy.axmlprinter', 'asn1crypto.cms',
                 'Cryptodome']
if sys.platform == 'win32':
    from PyInstaller.utils.hooks import collect_submodules
    generated = collect_submodules('comtypes.gen')
    assert 'comtypes.gen.PortableDeviceApiLib' in generated
    assert 'comtypes.gen.PortableDeviceTypesLib' in generated
    hiddenimports += generated
    hiddenimports += ['win32file', 'win32event', 'win32con', 'pywintypes', 'comtypes',
                      'pmca.usb.driver.windows.msc', 'pmca.usb.driver.windows.wpd',
                      'pmca.usb.driver.windows.driverless']

# This GUI retains the upstream packaged-version import without creating a
# temporary frozenversion.py in the working tree.
block_cipher = None
runtime_version = root / 'packaging' / 'frozenversion.py'
a = Analysis(
    [str(root / 'pmca-gui.py')],
    pathex=[str(root), str(runtime_version.parent), str(root / 'packaging' / 'offline')],
    binaries=[],
    datas=[(str(catalog_dir / 'catalog.json'), 'offline-apps'),
           (str(root / 'certs' / 'localtest.me.pem'), 'certs')]
          + [(str(catalog_dir / app['file']), 'offline-apps') for app in apps],
    hiddenimports=hiddenimports + ['frozenversion', 'build_profile'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['pmca.usb.driver.generic.libusb', 'usb'] if sys.platform == 'win32' else [],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='A6000-PMCA-Offline-ZH', debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False,
)
