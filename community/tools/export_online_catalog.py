"""Prepare a 21-app GitHub Release catalog; never create/upload a release."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote


def export_catalog(source, destination, repository, tag):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Repository must be OWNER/REPO')
    if not tag or tag in ('.', '..') or '/' in tag or '\\' in tag:
        raise ValueError('Use an explicit fixed release tag, without path separators')
    source, destination = Path(source).resolve(), Path(destination).resolve()
    catalog = json.loads((source / 'catalog.json').read_text(encoding='utf-8'))
    apps = catalog.get('apps')
    if catalog.get('version') != 1 or not isinstance(apps, list) or len(apps) != 21:
        raise ValueError('Import the complete 21-app offline catalog first')
    if len({app['package'] for app in apps}) != 21:
        raise ValueError('Duplicate app package in catalog')
    exported = []
    for app in apps:
        filename = app['file']
        path = (source / filename).resolve()
        if (path.parent != source or not re.fullmatch(r'[A-Za-z0-9_.-]+\.apk', filename)):
            raise ValueError('APK must be an ordinary local filename')
        data = path.read_bytes()
        if len(data) != app['size'] or hashlib.sha256(data).hexdigest() != app['sha256']:
            raise ValueError('APK has changed or is incomplete: ' + filename)
        entry = dict(app)
        entry['downloadUrl'] = 'https://github.com/%s/releases/download/%s/%s' % (
            repository, quote(tag, safe=''), quote(filename, safe=''))
        exported.append(entry)
    result = {'version': 1, 'repository': repository, 'releaseTag': tag,
              'source': 'Maintainer-controlled GitHub Release. Verify redistribution rights before uploading.',
              'apps': exported}
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / 'catalog.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return target


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=str(root / 'offline-apps'))
    parser.add_argument('--output', default=str(root / 'online-apps'))
    parser.add_argument('--repo', required=True, help='GitHub OWNER/REPO that will hold the authorized APK assets')
    parser.add_argument('--tag', required=True, help='Fixed APK release tag, for example apk-set-v1')
    args = parser.parse_args()
    output = export_catalog(args.source, args.output, args.repo, args.tag)
    print('Prepared 21 online entries at %s; no release was created and no file was uploaded.' % output)
