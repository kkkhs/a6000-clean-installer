"""Localized summaries accompany, rather than hide or alter, raw PMCA errors."""
from .i18n import tr


def error_hint(error):
    text = str(error).lower()
    rules = [
        (('no devices found or too many sony devices',), 'hint_unique'),
        (('no devices found',), 'hint_missing'),
        (('too many sony devices',), 'hint_multiple'),
        (('timed out', 'timeout'), 'hint_timeout'),
        (('unknown location',), 'hint_location'),
        (('10048', 'address already in use'), 'hint_port'),
        (('10061', 'connection refused'), 'hint_connection'),
        (('ssl', 'tls', 'certificate'), 'hint_tls'),
        (('win32', 'no module named'), 'hint_dependencies'),
        (('sendcommand', 'usb', 'access denied'), 'hint_usb'),
        (('does not support apps',), 'hint_unsupported'),
        (('cannot use camera in this mode',), 'hint_mode'),
    ]
    for needles, key in rules:
        if any(needle in text for needle in needles):
            return tr(key)
    return tr('hint_generic')
