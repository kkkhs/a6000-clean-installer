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

MAX_METADATA = 2 * 1024 ** 2


class SafeGitHubRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urlsplit(newurl)
        if parts.scheme != 'https' or parts.port not in (None, 443) or parts.username or parts.password:
            raise CatalogError('下载重定向必须使用 HTTPS，且不能包含凭据。')
        if parts.hostname not in ('github.com', 'api.github.com', 'release-assets.githubusercontent.com',
                                  'objects.githubusercontent.com', 'github-releases.githubusercontent.com'):
            raise CatalogError('拒绝跳转到未知的下载主机。')
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
            raise CatalogError('仓库访问令牌只能发送到 GitHub API。')
        headers['Authorization'] = 'Bearer ' + token
    request = Request(url, headers=headers)
    return build_opener(SafeGitHubRedirect()).open(request, timeout=60)


def release_coordinates(url, filename):
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.hostname != 'github.com' or parts.port not in (None, 443)
            or parts.username or parts.password or parts.query or parts.fragment):
        raise CatalogError('下载地址必须是 GitHub Release 的固定版本 HTTPS 地址。')
    segments = parts.path.strip('/').split('/')
    if len(segments) != 6 or segments[2:4] != ['releases', 'download']:
        raise CatalogError('下载地址必须指向 /OWNER/REPO/releases/download/TAG/FILE。')
    owner, repo, _, _, tag, asset = segments
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', owner) or not re.fullmatch(r'[A-Za-z0-9_.-]+', repo):
        raise CatalogError('GitHub 仓库名称无效。')
    if not tag or unquote(asset) != filename:
        raise CatalogError('下载地址的文件名必须与清单一致。')
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
            raise CatalogError('在线应用缺少 downloadUrl。')
        self.owner, self.repo, self.tag = release_coordinates(self.download_url, self.filename)

    @property
    def details(self):
        return super().details + '\n来源：GitHub Release；首次安装需下载，已校验缓存可复用。'

    def _asset_url(self, token):
        if not token:
            return self.download_url, None
        endpoint = 'https://api.github.com/repos/%s/%s/releases/tags/%s' % (
            self.owner, self.repo, quote(self.tag, safe=''))
        with download_response(endpoint, token, 'application/vnd.github+json') as response:
            raw = response.read(MAX_METADATA + 1)
        if len(raw) > MAX_METADATA:
            raise CatalogError('GitHub Release 元数据过大。')
        release = json.loads(raw.decode('utf-8'))
        for asset in release.get('assets', []):
            if asset.get('name') == self.filename:
                if (type(asset.get('id')) is not int or asset['id'] <= 0
                        or asset.get('size') != self.size):
                    raise CatalogError('Release 文件大小或资产编号与清单不匹配。')
                return 'https://api.github.com/repos/%s/%s/releases/assets/%d' % (
                    self.owner, self.repo, asset['id']), token
        raise CatalogError('该 GitHub Release 没有清单指定的 APK。')

    def open_verified(self):
        """Download/cache exact bytes; no install is attempted on a bad hash."""
        cache = cache_directory()
        cache.mkdir(parents=True, exist_ok=True)
        target = cache / (self.sha256 + '.apk')
        if target.is_file():
            with target.open('rb') as source:
                data = source.read(self.size + 1)
            if len(data) == self.size and hashlib.sha256(data).hexdigest() == self.sha256:
                print('使用已校验的下载缓存：' + self.name)
                return io.BytesIO(data)
        token = os.environ.get('A6000_GITHUB_TOKEN') or None
        temporary = None
        try:
            url, api_token = self._asset_url(token)
            print('从 GitHub Release 下载：%s（%s/%s，%s）' % (self.name, self.owner, self.repo, self.tag))
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
                            raise CatalogError('下载超过清单指定的大小，已停止。')
                        output.write(chunk)
                        digest.update(chunk)
            if total != self.size or digest.hexdigest() != self.sha256:
                raise CatalogError('下载文件的大小或 SHA-256 不匹配，已停止安装。')
            data = temporary.read_bytes()
            # Recheck the bytes actually handed to PMCA, not just the stream hash.
            if len(data) != self.size or hashlib.sha256(data).hexdigest() != self.sha256:
                raise CatalogError('下载临时文件发生变化，已停止安装。')
            os.replace(temporary, target)
            print('下载完成，SHA-256 校验通过：' + self.name)
            return io.BytesIO(data)
        except HTTPError as error:
            raise CatalogError('GitHub 下载失败（HTTP %d）。请检查 Release 是否存在、网络和仓库权限；私有仓库需 A6000_GITHUB_TOKEN。' % error.code) from None
        except (URLError, OSError) as error:
            raise CatalogError('GitHub 下载或缓存写入失败，请检查网络与本地磁盘权限。') from None
        except (ValueError, TypeError, AttributeError) as error:
            if isinstance(error, CatalogError):
                raise
            raise CatalogError('GitHub Release 元数据无效，已停止安装。') from None
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
            raise CatalogError('在线应用清单过大。')
        catalog = json.loads(raw)
    except (OSError, ValueError) as error:
        raise CatalogError('无法读取在线应用列表，请确认 online-apps/catalog.json 完整且配置了 Release 地址。') from error
    return parse_catalog(catalog, str(directory), OnlineApp)
