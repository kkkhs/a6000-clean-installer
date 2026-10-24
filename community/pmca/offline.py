"""Local-only application catalog. Loading it never contacts an app store."""
import hashlib
import io
import json
import os
import re
import sys

from .i18n import get_language, tr


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
        self.english_name = metadata['name']
        self.version = metadata['versionName']
        self.locales = metadata['locales']
        self.filename = metadata['file']
        self.size = metadata['size']
        self.sha256 = metadata['sha256']

    @property
    def name(self):
        return self.metadata['nameZh'] if get_language() == 'zh' else self.english_name

    @property
    def description(self):
        if get_language() == 'zh':
            return self.metadata['descriptionZh']
        return self.metadata.get('descriptionEn') or tr('description_unknown')

    @property
    def label(self):
        return '%s · v%s' % (self.name, self.version)

    @property
    def details(self):
        notes = [self.description, tr('original_name', name=self.english_name),
                 tr('version_size', version=self.version, size=self.size / 1024 ** 2),
                 tr('package', package=self.package),
                 tr('locale_yes' if 'zh' in self.locales else 'locale_no')]
        note = self.metadata.get('noteZh' if get_language() == 'zh' else 'noteEn')
        if note:
            notes.append(note)
        elif get_language() == 'en' and self.metadata.get('noteZh'):
            notes.append(tr('legacy_note'))
        notes.append(tr('app_caution'))
        return '\n'.join(notes)

    def open_verified(self):
        """Hash the exact bytes passed to PMCA, not a subsequently reopened file."""
        path = os.path.join(self.directory, self.filename)
        try:
            with open(path, 'rb') as source:
                data = source.read(self.size + 1)
        except OSError as error:
            raise CatalogError(tr('apk_read', file=self.filename)) from error
        if len(data) != self.size or hashlib.sha256(data).hexdigest() != self.sha256:
            raise CatalogError(tr('apk_integrity', name=self.name))
        return io.BytesIO(data)


def load_catalog(directory=None):
    directory = os.path.realpath(directory or catalog_directory())
    try:
        with open(os.path.join(directory, 'catalog.json'), encoding='utf-8') as source:
            catalog = json.load(source)
    except (OSError, ValueError) as error:
        raise CatalogError(tr('catalog_read')) from error
    return parse_catalog(catalog, directory)


def parse_catalog(catalog, directory, app_type=OfflineApp):
    """Shared metadata validation for bundled and GitHub-backed catalogs."""
    directory = os.path.realpath(directory)
    if not isinstance(catalog, dict) or catalog.get('version') != 1 or not isinstance(catalog.get('apps'), list):
        raise CatalogError(tr('catalog_format'))
    apps = []
    packages = set()
    filenames = set()
    for item in catalog['apps']:
        if not isinstance(item, dict):
            raise CatalogError(tr('entry_object'))
        for field in ('package', 'name', 'nameZh', 'versionName', 'descriptionZh', 'file', 'sha256'):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise CatalogError(tr('entry_field', field=field))
        filename = item['file']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.apk', filename):
            raise CatalogError(tr('filename_invalid'))
        path = os.path.realpath(os.path.join(directory, filename))
        if os.path.dirname(path) != directory:
            raise CatalogError(tr('path_invalid'))
        if item['package'] in packages or filename in filenames:
            raise CatalogError(tr('duplicate'))
        if not re.fullmatch(r'[a-f0-9]{64}', item['sha256']):
            raise CatalogError(tr('hash_invalid'))
        if type(item.get('size')) is not int or not 0 < item['size'] <= 64 * 1024 ** 2:
            raise CatalogError(tr('size_invalid'))
        if not isinstance(item.get('locales'), list) or not all(isinstance(locale, str) for locale in item['locales']):
            raise CatalogError(tr('locales_invalid'))
        if not all(isinstance(item.get(field, ''), str) for field in ('noteZh', 'noteEn', 'descriptionEn')):
            raise CatalogError(tr('note_invalid'))
        packages.add(item['package'])
        filenames.add(filename)
        apps.append(app_type(directory, item))
    return apps
