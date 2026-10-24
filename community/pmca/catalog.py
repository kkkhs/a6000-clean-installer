"""Two build profiles share one GUI and the upstream installation backend."""
import os
import sys

from .offline import load_catalog
from .online import load_online_catalog


def build_mode():
    if getattr(sys, 'frozen', False):
        from build_profile import mode
    else:
        mode = 'online' if '--online' in sys.argv else 'offline'
    if mode not in ('offline', 'online'):
        raise ValueError('Unknown catalog build profile')
    return mode


def load_app_list():
    if build_mode() == 'offline':
        return load_catalog()
    root = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(__file__)))
    # An explicit sidecar allows release metadata updates without rebuilding EXE.
    # Replacing it replaces the trust source, including all hashes and URLs.
    if getattr(sys, 'frozen', False):
        sidecar = os.path.join(os.path.dirname(sys.executable), 'online-apps')
        if os.path.isfile(os.path.join(sidecar, 'catalog.json')):
            print('读取 EXE 同目录的在线清单；请确认它来自可信维护者。')
            return load_online_catalog(sidecar)
    return load_online_catalog(os.path.join(root, 'online-apps'))
