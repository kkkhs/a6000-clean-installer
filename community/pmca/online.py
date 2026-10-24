"""Download only selected GitHub Release APKs, verify before touching USB."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .offline import CatalogError, OfflineApp, parse_catalog
from .i18n import tr

MAX_METADATA = 2 * 1024 ** 2


class SafeGitHubRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urlsplit(newurl)
        if parts.scheme != 'https' or parts.port not in (None, 443) or parts.username or parts.password:
            raise CatalogError(tr('redirect_https'))
        if parts.hostname not in ('github.com', 'api.github.com', 'release-assets.githubusercontent.com',
                                  'objects.githubusercontent.com', 'github-releases.githubusercontent.com'):
            raise CatalogError(tr('redirect_host'))
        # Never forward a private-repository token to GitHub's asset CDN.
        redirect = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirect is not None:
            for header in list(redirect.headers):
                if header.lower() == 'authorization':
                    del redirect.headers[header]
        return redirect


def download_response(url, token=None, accept='application/octet-stream'):
    headers = {'User-Agent': 'A6000-PMCA-Online-ZH', 'Accept': accept}
    if token:
        if urlsplit(url).hostname != 'api.github.com':
            raise CatalogError(tr('token_host'))
        headers['Authorization'] = 'Bearer ' + token
    request = Request(url, headers=headers)
    return build_opener(SafeGitHubRedirect()).open(request, timeout=60)


def release_coordinates(url, filename):
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.hostname != 'github.com' or parts.port not in (None, 443)
            or parts.username or parts.password or parts.query or parts.fragment):
        raise CatalogError(tr('release_https'))
    segments = parts.path.strip('/').split('/')
    if len(segments) != 6 or segments[2:4] != ['releases', 'download']:
        raise CatalogError(tr('release_path'))
    owner, repo, _, _, tag, asset = segments
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', owner) or not re.fullmatch(r'[A-Za-z0-9_.-]+', repo):
        raise CatalogError(tr('repo_invalid'))
    if not tag or unquote(asset) != filename:
        raise CatalogError(tr('asset_name'))
    return owner, repo, unquote(tag)


def cache_directory():
    base = os.environ.get('LOCALAPPDATA') if os.name == 'nt' else os.environ.get('XDG_CACHE_HOME')
    base = Path(base) if base else Path.home() / '.cache'
    return base / 'A6000-PMCA' / 'apks'


class OnlineApp(OfflineApp):
    def __init__(self, directory, metadata):
        super().__init__(directory, metadata)
        self.download_url = metadata.get('downloadUrl')
        if not isinstance(self.download_url, str):
            raise CatalogError(tr('url_missing'))
        self.owner, self.repo, self.tag = release_coordinates(self.download_url, self.filename)

    @property
    def details(self):
        return super().details + '\n' + tr('online_source')

    def _asset_url(self, token):
        if not token:
            return self.download_url, None
        endpoint = 'https://api.github.com/repos/%s/%s/releases/tags/%s' % (
            self.owner, self.repo, quote(self.tag, safe=''))
        with download_response(endpoint, token, 'application/vnd.github+json') as response:
            raw = response.read(MAX_METADATA + 1)
        if len(raw) > MAX_METADATA:
            raise CatalogError(tr('metadata_large'))
        release = json.loads(raw.decode('utf-8'))
        for asset in release.get('assets', []):
            if asset.get('name') == self.filename:
                if (type(asset.get('id')) is not int or asset['id'] <= 0
                        or asset.get('size') != self.size):
                    raise CatalogError(tr('asset_mismatch'))
                return 'https://api.github.com/repos/%s/%s/releases/assets/%d' % (
                    self.owner, self.repo, asset['id']), token
        raise CatalogError(tr('asset_missing'))

    def open_verified(self):
        """Download/cache exact bytes; no install is attempted on a bad hash."""
        cache = cache_directory()
        cache.mkdir(parents=True, exist_ok=True)
        target = cache / (self.sha256 + '.apk')
        if target.is_file():
            with target.open('rb') as source:
                data = source.read(self.size + 1)
            if len(data) == self.size and hashlib.sha256(data).hexdigest() == self.sha256:
                print(tr('using_cache', name=self.name))
                return io.BytesIO(data)
        token = os.environ.get('A6000_GITHUB_TOKEN') or None
        temporary = None
        try:
            url, api_token = self._asset_url(token)
            print(tr('downloading', name=self.name, repo=self.owner + '/' + self.repo, tag=self.tag))
            digest = hashlib.sha256()
            total = 0
            with tempfile.NamedTemporaryFile(dir=cache, prefix='.download-', delete=False) as output:
                temporary = Path(output.name)
                with download_response(url, api_token) as response:
                    while True:
                        chunk = response.read(min(64 * 1024, self.size - total + 1))
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > self.size:
                            raise CatalogError(tr('download_large'))
                        output.write(chunk)
                        digest.update(chunk)
            if total != self.size or digest.hexdigest() != self.sha256:
                raise CatalogError(tr('download_integrity'))
            data = temporary.read_bytes()
            # Recheck the bytes actually handed to PMCA, not just the stream hash.
            if len(data) != self.size or hashlib.sha256(data).hexdigest() != self.sha256:
                raise CatalogError(tr('temporary_changed'))
            os.replace(temporary, target)
            print(tr('download_complete', name=self.name))
            return io.BytesIO(data)
        except HTTPError as error:
            raise CatalogError(tr('download_http', code=error.code)) from None
        except (URLError, OSError) as error:
            raise CatalogError(tr('download_io')) from None
        except (ValueError, TypeError, AttributeError) as error:
            if isinstance(error, CatalogError):
                raise
            raise CatalogError(tr('metadata_invalid')) from None
        finally:
            if temporary is not None:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass


def load_online_catalog(directory):
    directory = Path(directory).resolve()
    try:
        with (directory / 'catalog.json').open(encoding='utf-8') as source:
            raw = source.read(MAX_METADATA + 1)
        if len(raw) > MAX_METADATA:
            raise CatalogError(tr('online_catalog_large'))
        catalog = json.loads(raw)
    except (OSError, ValueError) as error:
        raise CatalogError(tr('online_catalog_read')) from error
    return parse_catalog(catalog, str(directory), OnlineApp)
