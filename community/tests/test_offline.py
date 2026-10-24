"""Headless tests: no USB access, network downloads or application launch."""
import ast
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
if 'pmca' not in sys.modules:
    package = types.ModuleType('pmca')
    package.__path__ = [str(ROOT / 'pmca')]
    sys.modules['pmca'] = package
from pmca.i18n import get_language, set_language, tr


def load_module(name, filename):
    name = 'pmca.' + name
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_definitions(filename, names, namespace):
    tree = ast.parse((ROOT / filename).read_text(encoding='utf-8'))
    selected = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names]
    if len(selected) != len(names):
        raise AssertionError('Requested source definitions are missing')
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(ROOT / filename), 'exec'), namespace)
    return namespace


offline = load_module('offline_test_target', 'pmca/offline.py')
friendly = load_module('friendly_test_target', 'pmca/friendly.py')


class OfflineCatalogTests(unittest.TestCase):
    def setUp(self):
        set_language('zh')
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.data = b'PK sample unchanged APK bytes'
        (self.directory / 'sample.apk').write_bytes(self.data)
        self.item = {'package': 'com.example.camera', 'name': 'Example', 'nameZh': '示例',
                     'versionName': '1.0', 'descriptionZh': '示例用途', 'file': 'sample.apk',
                     'sha256': hashlib.sha256(self.data).hexdigest(), 'size': len(self.data),
                     'locales': ['default', 'zh']}
        self.write_catalog()

    def tearDown(self):
        self.temp.cleanup()

    def write_catalog(self, items=None, version=1):
        (self.directory / 'catalog.json').write_text(json.dumps({'version': version, 'apps': items or [self.item]}), encoding='utf-8')

    def test_local_catalog_and_verified_bytes(self):
        app, = offline.load_catalog(str(self.directory))
        self.assertEqual(app.name, '示例')
        self.assertEqual(app.label, '示例 · v1.0')
        with app.open_verified() as source:
            self.assertEqual(source.read(), self.data)
        self.assertIn('实际显示仍需验证', app.details)

    def test_no_chinese_claim_for_default_locale(self):
        self.item['locales'] = ['default']
        self.write_catalog()
        self.assertIn('不会汉化相机内的应用', offline.load_catalog(str(self.directory))[0].details)

    def test_same_size_corruption_rejected(self):
        app = offline.load_catalog(str(self.directory))[0]
        (self.directory / 'sample.apk').write_bytes(b'X' + self.data[1:])
        with self.assertRaises(offline.CatalogError):
            app.open_verified()

    def test_growth_or_truncation_rejected(self):
        app = offline.load_catalog(str(self.directory))[0]
        for data in (self.data + b'X', self.data[:-1]):
            (self.directory / 'sample.apk').write_bytes(data)
            with self.assertRaises(offline.CatalogError):
                app.open_verified()

    def test_missing_apk_rejected_before_install(self):
        app = offline.load_catalog(str(self.directory))[0]
        (self.directory / 'sample.apk').unlink()
        with self.assertRaises(offline.CatalogError):
            app.open_verified()

    def test_missing_catalog_rejected(self):
        (self.directory / 'catalog.json').unlink()
        with self.assertRaises(offline.CatalogError):
            offline.load_catalog(str(self.directory))

    def test_invalid_catalog_fields(self):
        bad_fields = {'file': ['../sample.apk', 'C:\\sample.apk', '/tmp/sample.apk'],
                      'sha256': ['short', 'z' * 64], 'size': [-1, True, 100 * 1024 ** 2],
                      'locales': ['zh', [1]], 'nameZh': ['', None], 'noteZh': [123]}
        original = dict(self.item)
        for field, values in bad_fields.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    self.item = dict(original, **{field: value})
                    self.write_catalog()
                    with self.assertRaises(offline.CatalogError):
                        offline.load_catalog(str(self.directory))

    def test_duplicate_package_rejected(self):
        self.write_catalog([self.item, dict(self.item)])
        with self.assertRaises(offline.CatalogError):
            offline.load_catalog(str(self.directory))

    def test_external_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.directory / 'sample.apk').unlink()
            target = Path(outside) / 'sample.apk'
            target.write_bytes(self.data)
            try:
                (self.directory / 'sample.apk').symlink_to(target)
            except OSError as error:
                self.skipTest('Host does not allow creating a test symlink: %s' % error)
            with self.assertRaises(offline.CatalogError):
                offline.load_catalog(str(self.directory))

    def test_frozen_resource_location(self):
        with patch.object(sys, '_MEIPASS', '/private/bundled', create=True):
            self.assertEqual(offline.catalog_directory(), os.path.join('/private/bundled', 'offline-apps'))

    def test_user_collection_has_21_unique_verified_apks(self):
        apps = offline.load_catalog(str(ROOT / 'offline-apps'))
        self.assertEqual(len(apps), 21)
        self.assertEqual(len({app.package for app in apps}), 21)
        for app in apps:
            with self.subTest(app=app.name), app.open_verified() as source:
                self.assertTrue(source.read(2).startswith(b'PK'))
                self.assertTrue(app.description)


class InstallOutcomeTests(unittest.TestCase):
    class ExtDevice:
        pass

    class InstallDevice:
        pass

    def setUp(self):
        self.driver = Mock()
        self.driver.__enter__ = Mock(return_value=self.driver)
        self.driver.__exit__ = Mock(return_value=False)
        self.namespace = {'importDriver': Mock(return_value=self.driver), 'getDevice': Mock(),
                          'SonyExtCmdDevice': self.ExtDevice, 'SonyAppInstallDevice': self.InstallDevice,
                          'SonyExtCmdCamera': Mock(), 'InvalidCommandException': ValueError,
                          'time': types.SimpleNamespace(sleep=Mock()), 'listDevices': Mock(),
                          'installApp': Mock(return_value={'confirmed': True})}
        load_definitions('pmca/commands/usb.py', {'installCommand'}, self.namespace)
        self.install = self.namespace['installCommand']

    def test_no_device_is_failure_not_success(self):
        self.namespace['getDevice'].return_value = None
        with self.assertRaises(RuntimeError):
            self.install(apkFile=io.BytesIO(b'apk'))
        self.namespace['installApp'].assert_not_called()

    def test_wrong_mode_is_failure(self):
        self.namespace['getDevice'].return_value = object()
        with self.assertRaisesRegex(RuntimeError, 'Cannot use camera'):
            self.install()

    def test_switch_timeout_is_failure(self):
        self.namespace['getDevice'].return_value = self.ExtDevice()
        self.namespace['listDevices'].return_value = []
        with self.assertRaisesRegex(RuntimeError, 'timed out'):
            self.install()
        self.namespace['installApp'].assert_not_called()

    def test_unsupported_camera_is_failure(self):
        self.namespace['getDevice'].return_value = self.ExtDevice()
        self.namespace['SonyExtCmdCamera'].return_value.switchToAppInstaller.side_effect = ValueError('unsupported')
        with self.assertRaisesRegex(RuntimeError, 'does not support apps'):
            self.install()

    def test_accepted_result_is_returned(self):
        device = self.InstallDevice()
        self.namespace['getDevice'].return_value = device
        source = io.BytesIO(b'apk')
        self.assertEqual(self.install(apkFile=source), {'confirmed': True})
        self.namespace['installApp'].assert_called_once_with(device, source, None, None)

    def test_camera_rejection_propagates(self):
        self.namespace['getDevice'].return_value = self.InstallDevice()
        self.namespace['installApp'].side_effect = RuntimeError('camera rejected task')
        with self.assertRaisesRegex(RuntimeError, 'camera rejected task'):
            self.install()

    def test_switch_success_uses_install_device(self):
        self.namespace['getDevice'].return_value = self.ExtDevice()
        device = self.InstallDevice()
        self.namespace['listDevices'].return_value = [device]
        self.assertEqual(self.install(), {'confirmed': True})


class GuiInstallTests(unittest.TestCase):
    def setUp(self):
        class FakeTask:
            def __init__(self, ui):
                self.ui = ui
        set_language('zh')
        self.install = Mock()
        self.namespace = {'BackgroundTask': FakeTask, 'installCommand': self.install, 'sys': sys, 'tr': tr,
                          'error_hint': friendly.error_hint, 'traceback': types.SimpleNamespace(print_exc=Mock()),
                          'showerror': Mock()}
        load_definitions('pmca-gui.py', {'InstallTask'}, self.namespace)
        self.ui = Mock()
        self.ui.MODE_APP, self.ui.MODE_APK = 0, 1
        self.task = self.namespace['InstallTask'](self.ui)

    def test_no_selection_does_not_touch_camera(self):
        success, message = self.task.do((0, '', None))
        self.assertFalse(success)
        self.install.assert_not_called()

    def test_catalog_bytes_not_remote_package_are_installed(self):
        app = Mock(name='app')
        app.name, app.english_name = '示例', 'Example'
        source = io.BytesIO(b'PK verified')
        app.open_verified.return_value = source
        self.assertTrue(self.task.do((0, '', app))[0])
        self.install.assert_called_once_with(driverName='native' if sys.platform == 'win32' else None, apkFile=source)
        self.assertTrue(source.closed)

    def test_verification_failure_does_not_touch_camera(self):
        app = Mock()
        app.name, app.english_name = '示例', 'Example'
        app.open_verified.side_effect = offline.CatalogError('bad hash')
        self.assertFalse(self.task.do((0, '', app))[0])
        self.install.assert_not_called()

    def test_usb_failure_is_not_reported_as_success(self):
        app = Mock()
        app.name, app.english_name = '示例', 'Example'
        app.open_verified.return_value = io.BytesIO(b'apk')
        self.install.side_effect = RuntimeError('Operation timed out')
        success, message = self.task.do((0, '', app))
        self.assertFalse(success)
        self.assertIn('超时', friendly.error_hint(message))

    def test_error_dialog_and_unlock(self):
        self.task.doAfter((False, '没有完成'))
        self.ui.master.setBusy.assert_called_once_with(False)
        self.namespace['showerror'].assert_called_once()

    def test_success_has_no_error_dialog(self):
        self.task.doAfter((True, 'install_success'))
        self.namespace['showerror'].assert_not_called()

    def test_console_free_flush_does_not_crash(self):
        ns = load_definitions('pmca-gui.py', {'PrintRedirector'}, {})
        ns['PrintRedirector'](Mock(), None).flush()


class FriendlyHintTests(unittest.TestCase):
    def setUp(self):
        set_language('zh')

    def test_firewall_advice_does_not_disable_security(self):
        self.assertIn('不要直接关闭防火墙', friendly.error_hint(OSError('WinError 10061')))

    def test_tls_advice_does_not_disable_global_validation(self):
        self.assertIn('不要修改全局 TLS', friendly.error_hint(RuntimeError('SSL certificate')))


if __name__ == '__main__':
    unittest.main()
