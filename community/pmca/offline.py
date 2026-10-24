"""Local-only application catalog. Loading it never contacts an app store."""
import hashlib
import io
import json
import os
import re
import sys


def catalog_directory():
    # PyInstaller extracts bundled data here; source runs use the project root.
    root = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(root, 'offline-apps')


class CatalogError(ValueError):
    pass


class OfflineApp:
    def __init__(self, directory, metadata):
        self.directory = directory
        self.metadata = metadata
        self.package = metadata['package']
        self.name = metadata['nameZh']
        self.english_name = metadata['name']
        self.version = metadata['versionName']
        self.description = metadata['descriptionZh']
        self.locales = metadata['locales']
        self.filename = metadata['file']
        self.size = metadata['size']
        self.sha256 = metadata['sha256']

    @property
    def label(self):
        return '%s · v%s' % (self.name, self.version)

    @property
    def details(self):
        locale_note = ('APK 声明了中文资源；相机内实际显示仍需验证。'
                       if 'zh' in self.locales else
                       'APK 未声明中文资源；本软件的中文说明不会汉化相机内的应用。')
        notes = [self.description, '英文名称：' + self.english_name,
                 '版本：%s  |  大小：%.2f MB' % (self.version, self.size / 1024 ** 2),
                 '包名：' + self.package, locale_note]
        if self.metadata.get('noteZh'):
            notes.append(self.metadata['noteZh'])
        notes.append('兼容性提示：列入清单不代表已通过 A6000 真机安装测试。')
        return '\n'.join(notes)

    def open_verified(self):
        """Hash the exact bytes passed to PMCA, not a subsequently reopened file."""
        path = os.path.join(self.directory, self.filename)
        try:
            with open(path, 'rb') as source:
                data = source.read(self.size + 1)
        except OSError as error:
            raise CatalogError('无法读取离线 APK：%s。请检查应用文件是否完整。' % self.filename) from error
        if len(data) != self.size or hashlib.sha256(data).hexdigest() != self.sha256:
            raise CatalogError('APK 完整性校验失败：%s。已停止安装，请从原始副本重新复制。' % self.name)
        return io.BytesIO(data)


def load_catalog(directory=None):
    directory = os.path.realpath(directory or catalog_directory())
    try:
        with open(os.path.join(directory, 'catalog.json'), encoding='utf-8') as source:
            catalog = json.load(source)
    except (OSError, ValueError) as error:
        raise CatalogError('无法读取离线应用清单，请确认 offline-apps 文件夹完整。') from error
    return parse_catalog(catalog, directory)


def parse_catalog(catalog, directory, app_type=OfflineApp):
    """Shared metadata validation for bundled and GitHub-backed catalogs."""
    directory = os.path.realpath(directory)
    if not isinstance(catalog, dict) or catalog.get('version') != 1 or not isinstance(catalog.get('apps'), list):
        raise CatalogError('不支持的应用清单格式。')
    apps = []
    packages = set()
    filenames = set()
    for item in catalog['apps']:
        if not isinstance(item, dict):
            raise CatalogError('应用条目必须是对象。')
        for field in ('package', 'name', 'nameZh', 'versionName', 'descriptionZh', 'file', 'sha256'):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise CatalogError('应用条目缺少有效字段：' + field)
        filename = item['file']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.apk', filename):
            raise CatalogError('APK 文件名必须是本目录内的文件名。')
        path = os.path.realpath(os.path.join(directory, filename))
        if os.path.dirname(path) != directory:
            raise CatalogError('APK 路径不能指向应用目录之外。')
        if item['package'] in packages or filename in filenames:
            raise CatalogError('清单中存在重复的应用或文件。')
        if not re.fullmatch(r'[a-f0-9]{64}', item['sha256']):
            raise CatalogError('SHA-256 格式无效。')
        if type(item.get('size')) is not int or not 0 < item['size'] <= 64 * 1024 ** 2:
            raise CatalogError('APK 大小无效。')
        if not isinstance(item.get('locales'), list) or not all(isinstance(locale, str) for locale in item['locales']):
            raise CatalogError('语言资源声明无效。')
        if not isinstance(item.get('noteZh', ''), str):
            raise CatalogError('应用备注必须是文本。')
        packages.add(item['package'])
        filenames.add(filename)
        apps.append(app_type(directory, item))
    return apps
