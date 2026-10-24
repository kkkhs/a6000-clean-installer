"""Online-download tests use fake responses, never contact GitHub or USB."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
from urllib.request import Request

ROOT = Path(__file__).resolve().parents[1]

# Import only the standard-library catalog modules, not USB/TLS/UI dependencies.
if 'pmca' not in sys.modules:
    package = types.ModuleType('pmca')
    package.__path__ = [str(ROOT / 'pmca')]
    sys.modules['pmca'] = package


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


online = load_module('pmca.online', 'pmca/online.py')


class OnlineCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = b'PK private authorized APK'
        self.item = {'package': 'com.example.camera', 'name': 'Example', 'nameZh': '示例',
                     'versionName': '1.0', 'descriptionZh': '示例用途', 'file': 'sample.apk',
                     'sha256': hashlib.sha256(self.data).hexdigest(), 'size': len(self.data),
                     'locales': ['default'],
                     'downloadUrl': 'https://github.com/owner/repo/releases/download/apk-set-v1/sample.apk'}
        self.app = online.OnlineApp(str(self.root), self.item)

    def tearDown(self):
        self.temp.cleanup()

    def test_catalog_needs_no_network_or_apk_files(self):
        (self.root / 'catalog.json').write_text(json.dumps({'version': 1, 'apps': [self.item]}), encoding='utf-8')
        with patch.object(online, 'download_response') as request:
            app, = online.load_online_catalog(self.root)
        request.assert_not_called()
        self.assertEqual(app.name, '示例')
        self.assertIn('GitHub Release', app.details)
        self.assertFalse((self.root / 'sample.apk').exists())

    def test_public_download_is_verified_and_cached(self):
        cache = self.root / 'cache'
        response = io.BytesIO(self.data)
        with patch.object(online, 'cache_directory', return_value=cache), \
                patch.object(online, 'download_response', return_value=response) as request, \
                patch.dict(online.os.environ, {}, clear=True):
            with self.app.open_verified() as source:
                self.assertEqual(source.read(), self.data)
        request.assert_called_once_with(self.item['downloadUrl'], None)
        self.assertEqual((cache / (self.item['sha256'] + '.apk')).read_bytes(), self.data)

    def test_verified_cache_works_without_network(self):
        target = self.root / (self.item['sha256'] + '.apk')
        target.write_bytes(self.data)
        with patch.object(online, 'cache_directory', return_value=self.root), \
                patch.object(online, 'download_response') as request:
            with self.app.open_verified() as source:
                self.assertEqual(source.read(), self.data)
        request.assert_not_called()

    def test_bad_digest_never_becomes_cache(self):
        with patch.object(online, 'cache_directory', return_value=self.root), \
                patch.object(online, 'download_response', return_value=io.BytesIO(b'X' + self.data[1:])), \
                patch.dict(online.os.environ, {}, clear=True):
            with self.assertRaises(online.CatalogError):
                self.app.open_verified()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_oversized_or_truncated_download_rejected(self):
        for data in (self.data + b'X', self.data[:-1]):
            with self.subTest(data=data), \
                    patch.object(online, 'cache_directory', return_value=self.root), \
                    patch.object(online, 'download_response', return_value=io.BytesIO(data)), \
                    patch.dict(online.os.environ, {}, clear=True):
                with self.assertRaises(online.CatalogError):
                    self.app.open_verified()
            self.assertEqual(list(self.root.iterdir()), [])

    def test_private_download_uses_api_asset_id(self):
        metadata = {'assets': [{'id': 123, 'name': 'sample.apk', 'size': len(self.data)}]}
        responses = [io.BytesIO(json.dumps(metadata).encode()), io.BytesIO(self.data)]
        with patch.object(online, 'cache_directory', return_value=self.root), \
                patch.object(online, 'download_response', side_effect=responses) as request, \
                patch.dict(online.os.environ, {'A6000_GITHUB_TOKEN': 'test-token-not-real'}, clear=True):
            with self.app.open_verified() as source:
                self.assertEqual(source.read(), self.data)
        self.assertEqual(request.call_args_list[0][0],
                         ('https://api.github.com/repos/owner/repo/releases/tags/apk-set-v1',
                          'test-token-not-real', 'application/vnd.github+json'))
        self.assertEqual(request.call_args_list[1][0],
                         ('https://api.github.com/repos/owner/repo/releases/assets/123', 'test-token-not-real'))

    def test_token_not_forwarded_to_cdn(self):
        original = Request('https://api.github.com/repos/o/r/releases/assets/123',
                           headers={'Authorization': 'Bearer secret', 'User-Agent': 'test'})
        redirect = online.SafeGitHubRedirect().redirect_request(
            original, None, 302, 'Found', {}, 'https://release-assets.githubusercontent.com/asset.apk')
        self.assertNotIn('Authorization', redirect.headers)

    def test_unknown_or_insecure_redirect_rejected(self):
        original = Request('https://github.com/o/r/releases/download/v1/sample.apk')
        for url in ('http://github.com/file', 'https://example.com/file',
                    'https://127.0.0.1/file', 'https://github.com:8443/file'):
            with self.subTest(url=url), self.assertRaises(online.CatalogError):
                online.SafeGitHubRedirect().redirect_request(original, None, 302, 'Found', {}, url)

    def test_release_url_must_match_fixed_asset(self):
        for url in ('https://example.com/sample.apk',
                    'https://github.com/o/r/releases/latest/download/sample.apk',
                    'https://github.com/o/r/releases/download/v1/other.apk',
                    'https://user:secret@github.com/o/r/releases/download/v1/sample.apk',
                    'https://github.com/o/r/releases/download/v1/sample.apk?token=secret'):
            with self.subTest(url=url), self.assertRaises(online.CatalogError):
                online.OnlineApp(str(self.root), dict(self.item, downloadUrl=url))


if __name__ == '__main__':
    unittest.main()
