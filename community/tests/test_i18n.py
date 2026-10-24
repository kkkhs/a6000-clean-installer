"""Language tests are local-only; no GUI, network or camera is opened."""
import ast
import hashlib
import json
from pathlib import Path
import string
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pmca import i18n
from pmca.offline import CatalogError, OfflineApp, parse_catalog
from pmca.friendly import error_hint


class TranslationTests(unittest.TestCase):
    def tearDown(self):
        i18n.set_language('zh')

    def test_only_two_languages(self):
        self.assertEqual(i18n.LANGUAGES, ('zh', 'en'))
        with self.assertRaises(ValueError):
            i18n.set_language('ja')

    def test_all_messages_have_both_translations_and_matching_fields(self):
        formatter = string.Formatter()
        for key, values in i18n.MESSAGES.items():
            with self.subTest(key=key):
                self.assertEqual(len(values), 2)
                self.assertTrue(all(isinstance(value, str) and value.strip() for value in values))
                fields = [{field for _, field, _, _ in formatter.parse(value) if field} for value in values]
                self.assertEqual(fields[0], fields[1])

    def test_literal_message_keys_exist(self):
        for path in (ROOT / 'pmca').glob('*.py'):
            self.check_keys(path)
        self.check_keys(ROOT / 'pmca-gui.py')

    def check_keys(self, path):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'tr'
                    and node.args and isinstance(node.args[0], ast.Constant)):
                self.assertIn(node.args[0].value, i18n.MESSAGES, str(path))

    def test_switch_changes_ui_and_error_hints(self):
        i18n.set_language('zh')
        self.assertEqual(i18n.tr('install_selected'), '安装选中的应用')
        i18n.set_language('en')
        self.assertEqual(i18n.tr('install_selected'), 'Install selected app')
        self.assertIn('timed out', error_hint(RuntimeError('Operation timed out')))
        self.assertIn('do not disable the firewall', error_hint(OSError('10061')))

    def test_preference_saved_and_reloaded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings' / 'preferences.json'
            i18n.set_language('en', persist=True, path=path)
            i18n.set_language('zh')
            self.assertEqual(i18n.load_language(path), 'en')
            self.assertEqual(json.loads(path.read_text()), {'language': 'en'})
            self.assertEqual(list(path.parent.iterdir()), [path])
            i18n.set_language('zh', persist=True, path=path)
            self.assertEqual(i18n.load_language(path), 'zh')

    def test_missing_corrupt_or_unsupported_preferences_default_to_chinese(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'preferences.json'
            self.assertEqual(i18n.load_language(path), 'zh')
            for text in ('{broken', '[]', '{"language":"ja"}', '{"language":false}'):
                path.write_text(text)
                i18n.set_language('en')
                self.assertEqual(i18n.load_language(path), 'zh')

    def test_switch_without_persistence_creates_no_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'preferences.json'
            i18n.set_language('en', path=path)
            self.assertFalse(path.exists())
            self.assertEqual(i18n.get_language(), 'en')

    def test_app_names_and_details_switch_without_changing_metadata(self):
        metadata = {'name': 'Original App', 'nameZh': '原应用', 'descriptionZh': '中文用途',
                    'descriptionEn': 'English description.', 'noteZh': '名称待确认',
                    'noteEn': 'Name remains unverified.', 'package': 'com.example.app',
                    'versionName': '1.0', 'locales': ['default'], 'file': 'app.apk',
                    'size': 3, 'sha256': hashlib.sha256(b'APK').hexdigest()}
        before = json.dumps(metadata, sort_keys=True)
        app = OfflineApp('/local', metadata)
        i18n.set_language('zh')
        self.assertEqual(app.name, '原应用')
        i18n.set_language('en')
        self.assertEqual(app.name, 'Original App')
        self.assertEqual(app.label, 'Original App · v1.0')
        self.assertIn('English description.', app.details)
        self.assertIn('Name remains unverified.', app.details)
        self.assertIn('app interface language is determined by the APK', app.details)
        self.assertNotIn('中文用途', app.details)
        self.assertEqual(json.dumps(metadata, sort_keys=True), before)

    def test_older_catalog_without_english_description_remains_supported(self):
        metadata = {'name': 'Original', 'nameZh': '原名', 'descriptionZh': '原说明',
                    'noteZh': '备注', 'package': 'com.example.app', 'versionName': '1.0',
                    'locales': ['zh'], 'file': 'app.apk', 'size': 3, 'sha256': 'a' * 64}
        with tempfile.TemporaryDirectory() as directory:
            app, = parse_catalog({'version': 1, 'apps': [metadata]}, directory)
        i18n.set_language('en')
        self.assertIn('Refer to the app documentation', app.description)
        self.assertIn('only provides a Chinese note', app.details)

    def test_product_copy_is_concise_and_keeps_attribution(self):
        for language in ('zh', 'en'):
            i18n.set_language(language)
            self.assertIn('kkkhs', i18n.tr('author'))
            notice = i18n.tr('about_body', version='v0.2.2')
            self.assertIn('kkkhs', notice)
            self.assertIn('ma1co', notice)
            self.assertIn('MIT', notice)
            self.assertIn('v0.2.2', notice)
            self.assertIn('https://github.com/kkkhs/sony-pmca-app-installer', notice)
            self.assertIn('序列号' if language == 'zh' else 'serial numbers', i18n.tr('log_privacy'))
            startup = i18n.tr('startup', source=i18n.tr('offline'))
            for status in ('没测试', '尚未', '正在测试', 'not yet tested', 'untested'):
                self.assertNotIn(status, startup)
            self.assertEqual(i18n.tr('save_log'), '导出诊断日志' if language == 'zh' else 'Export diagnostic log')

    def test_complete_21_app_translation_coverage_in_both_catalogs(self):
        for mode in ('offline', 'online'):
            catalog = json.loads((ROOT / (mode + '-apps') / 'catalog.json').read_text(encoding='utf-8'))
            self.assertEqual(len(catalog['apps']), 21)
            for item in catalog['apps']:
                with self.subTest(mode=mode, app=item['id']):
                    self.assertTrue(item.get('descriptionEn'))
                    self.assertIsInstance(item.get('noteEn'), str)
                    self.assertTrue(item['name'])
                    self.assertTrue(item['nameZh'])


if __name__ == '__main__':
    unittest.main()
