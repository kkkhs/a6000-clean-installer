# Metadata-only online build; never bundle offline-apps or any APK assets.
from pathlib import Path
import json
import sys
from urllib.parse import unquote, urlsplit

root = Path(SPECPATH)
catalog_file = root / 'online-apps' / 'catalog.json'
catalog = json.loads(catalog_file.read_text(encoding='utf-8'))
apps = catalog['apps']
if (catalog.get('version') != 1 or len(apps) != 21
        or len({app['package'] for app in apps}) != 21):
    raise ValueError('The online build requires 21 unique application entries')
for app in apps:
    parts = urlsplit(app.get('downloadUrl', ''))
    segments = parts.path.strip('/').split('/')
    if (parts.scheme != 'https' or parts.hostname != 'github.com'
            or parts.port not in (None, 443) or parts.username or parts.password
            or parts.query or parts.fragment or len(segments) != 6
            or segments[2:4] != ['releases', 'download']
            or unquote(segments[-1]) != app['file']):
        raise ValueError('Every entry must point to its fixed GitHub Release APK')

hiddenimports = ['pmca.catalog', 'pmca.offline', 'pmca.online', 'tlslite',
                 'axmlparserpy.axmlprinter', 'asn1crypto.cms', 'Cryptodome',
                 'frozenversion', 'build_profile']
if sys.platform == 'win32':
    from PyInstaller.utils.hooks import collect_submodules
    generated = collect_submodules('comtypes.gen')
    assert 'comtypes.gen.PortableDeviceApiLib' in generated
    assert 'comtypes.gen.PortableDeviceTypesLib' in generated
    hiddenimports += generated
    hiddenimports += ['win32file', 'win32event', 'win32con', 'pywintypes', 'comtypes',
                      'pmca.usb.driver.windows.msc', 'pmca.usb.driver.windows.wpd',
                      'pmca.usb.driver.windows.driverless']
a = Analysis(
    [str(root / 'pmca-gui.py')],
    pathex=[str(root), str(root / 'packaging'), str(root / 'packaging' / 'online')],
    binaries=[],
    # Explicit files prevent accidental inclusion of private APKs/tokens.
    datas=[(str(catalog_file), 'online-apps'),
           (str(root / 'certs' / 'localtest.me.pem'), 'certs')],
    hiddenimports=hiddenimports,
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['pmca.usb.driver.generic.libusb', 'usb'] if sys.platform == 'win32' else [], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='A6000-PMCA-Online-ZH', debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False,
)
