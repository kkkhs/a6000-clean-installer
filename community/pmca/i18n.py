"""Two-language UI messages and a per-user language preference; no network."""
import json
import os
from pathlib import Path
import tempfile

LANGUAGES = ('zh', 'en')
_language = 'zh'

# Keep both translations together so missing keys can be tested without Tk.
MESSAGES = {
    'title': ('A6000 应用安装 · 社区 PMCA {source}', 'A6000 App Installer · Community PMCA {source}'),
    'offline': ('离线版', 'Offline'),
    'online': ('在线下载版', 'Online'),
    'tab_offline': ('安装应用（离线）', 'Install apps (offline)'),
    'tab_online': ('安装应用（在线）', 'Install apps (online)'),
    'tab_info': ('相机信息', 'Camera info'),
    'compatibility': ('查看社区机型兼容性说明', 'Camera compatibility (community docs)'),
    'save_log': ('保存完整日志（可能含序列号，请先脱敏）', 'Save full log (may contain serial numbers; redact before sharing)'),
    'startup': ('社区安装后端 · {source}；不是官方版本，尚未完成 A6000 真机验证。', 'Community installation backend · {source}; unofficial build, not yet tested on an A6000 camera.'),
    'info_note': ('读取信息只能确认当前连接；不能保证后续应用安装成功。', 'Reading camera info confirms the current connection, not that an app installation will succeed.'),
    'read_info': ('读取相机信息（不安装应用）', 'Read camera info (no app installation)'),
    'connect_note': ('先开机，用数据线直连电脑，将 USB 连接设为 MTP。\n只安装一个选定应用，不会批量安装或刷固件。', 'Turn on the camera, connect it directly with a USB data cable, and select MTP.\nOnly the selected app is installed; no batch installation or firmware flashing.'),
    'list_offline': ('从 21 个离线应用中选择（不联网）', 'Choose from 21 bundled apps (no download)'),
    'list_online': ('从 21 个应用中选择（GitHub Release 下载）', 'Choose from 21 apps (GitHub Release download)'),
    'refresh': ('重新读取列表', 'Reload app list'),
    'other_apk': ('可选：安装其他本地 APK', 'Optional: install another local APK'),
    'open_apk': ('打开 APK…', 'Open APK…'),
    'install_selected': ('安装选中的应用', 'Install selected app'),
    'idle': ('请选择一个应用；界面翻译不会改动 APK 本身。', 'Select an app; changing the interface language does not modify the APK.'),
    'choose_app': ('请选择应用…', 'Select an app…'),
    'choose_details': ('请选择应用查看用途、英文名、版本和语言说明。', 'Select an app to view its description, original name, version and language notes.'),
    'list_not_loaded': ('列表尚未加载。请检查应用清单文件夹或下方日志。', 'The list has not loaded. Check the catalog folder and the log below.'),
    'install_running': ('正在安装，请勿关闭程序或断开相机。', 'Installation in progress. Do not close the app or disconnect the camera.'),
    'failure_title': ('安装未完成', 'Installation did not complete'),
    'full_error': ('完整错误保留在下方日志中。', 'The complete error is retained in the log below.'),
    'busy_title': ('正在与相机通信', 'Camera communication in progress'),
    'busy_warning': ('请等待任务结束后再关闭程序，不要在传输时断开 USB。', 'Wait for the task to finish before closing the app. Do not unplug USB during a transfer.'),
    'text_log': ('文本日志', 'Text log'),
    'android_app': ('Android 应用', 'Android app'),
    'all_files': ('所有文件', 'All files'),
    'save_failed': ('日志保存失败', 'Could not save log'),
    'settings_failed': ('语言已切换，但无法保存偏好：{error}', 'Language changed, but the preference could not be saved: {error}'),
    'loaded': ('已加载 {count} 个应用 · {source}。', 'Loaded {count} apps · {source}.'),
    'load_failed': ('应用清单加载失败：{error}', 'Could not load the app catalog: {error}'),
    'reading_info': ('正在读取相机信息；这一步不会安装 APK。', 'Reading camera info; this step does not install an APK.'),
    'info_caution': ('能够读取信息不代表 APK 安装链路一定可用。', 'Reading camera info successfully does not prove that APK installation will work.'),
    'info_failed': ('读取相机信息失败：{error}\n建议：{hint}', 'Could not read camera info: {error}\nSuggestion: {hint}'),
    'checking_app': ('正在校验并安装：{name}（{original}）', 'Verifying and installing: {name} ({original})'),
    'select_required': ('请先从列表选择一个应用，或打开一个 APK 文件。', 'Select an app from the list or open an APK file first.'),
    'install_success': ('相机已返回安装任务成功，请在相机内确认。', 'The camera reported task success. Confirm the app in the camera app list.'),
    'install_failed': ('安装未完成：{error}\n建议：{hint}', 'Installation did not complete: {error}\nSuggestion: {hint}'),
    'locale_yes': ('APK 声明了中文资源；相机内实际显示仍需验证。', 'The APK declares Chinese resources; the actual in-camera display still needs verification.'),
    'locale_no': ('APK 未声明中文资源；本软件的中文说明不会汉化相机内的应用。', 'The APK does not declare Chinese resources. This interface translation does not translate the in-camera app.'),
    'original_name': ('英文名称：{name}', 'Original name: {name}'),
    'version_size': ('版本：{version}  |  大小：{size:.2f} MB', 'Version: {version}  |  Size: {size:.2f} MB'),
    'package': ('包名：{package}', 'Package: {package}'),
    'app_caution': ('兼容性提示：列入清单不代表已通过 A6000 真机安装测试。', 'Compatibility: inclusion in this list does not mean the app has passed an A6000 hardware installation test.'),
    'online_source': ('来源：GitHub Release；首次安装需下载，已校验缓存可复用。', 'Source: GitHub Release; the first installation needs a download. Verified cached APKs can be reused.'),
    'description_unknown': ('具体功能请以应用自身说明为准。', 'Refer to the app documentation for its features.'),
    'legacy_note': ('此清单只有中文备注；请查看中文版本。', 'This catalog only provides a Chinese note; switch to Chinese to read it.'),
    'apk_read': ('无法读取离线 APK：{file}。请检查应用文件是否完整。', 'Cannot read bundled APK: {file}. Check that the app files are complete.'),
    'apk_integrity': ('APK 完整性校验失败：{name}。已停止安装，请从原始副本重新复制。', 'APK integrity check failed: {name}. Installation stopped; copy the file again from the original source.'),
    'catalog_read': ('无法读取离线应用清单，请确认 offline-apps 文件夹完整。', 'Cannot read the offline catalog. Check that the offline-apps folder is complete.'),
    'catalog_format': ('不支持的应用清单格式。', 'Unsupported app catalog format.'),
    'entry_object': ('应用条目必须是对象。', 'Each app entry must be an object.'),
    'entry_field': ('应用条目缺少有效字段：{field}', 'An app entry is missing a valid field: {field}'),
    'filename_invalid': ('APK 文件名必须是本目录内的文件名。', 'The APK filename must be a filename within the app directory.'),
    'path_invalid': ('APK 路径不能指向应用目录之外。', 'An APK path cannot point outside the app directory.'),
    'duplicate': ('清单中存在重复的应用或文件。', 'The catalog contains a duplicate app or file.'),
    'hash_invalid': ('SHA-256 格式无效。', 'Invalid SHA-256 format.'),
    'size_invalid': ('APK 大小无效。', 'Invalid APK size.'),
    'locales_invalid': ('语言资源声明无效。', 'Invalid language-resource declaration.'),
    'note_invalid': ('应用备注必须是文本。', 'App notes and translations must be text.'),
    'redirect_https': ('下载重定向必须使用 HTTPS，且不能包含凭据。', 'Download redirects must use HTTPS and must not contain credentials.'),
    'redirect_host': ('拒绝跳转到未知的下载主机。', 'Refusing a redirect to an unknown download host.'),
    'token_host': ('仓库访问令牌只能发送到 GitHub API。', 'Repository access tokens may only be sent to the GitHub API.'),
    'release_https': ('下载地址必须是 GitHub Release 的固定版本 HTTPS 地址。', 'The download URL must be a fixed-version GitHub Release HTTPS URL.'),
    'release_path': ('下载地址必须指向 /OWNER/REPO/releases/download/TAG/FILE。', 'The download URL must point to /OWNER/REPO/releases/download/TAG/FILE.'),
    'repo_invalid': ('GitHub 仓库名称无效。', 'Invalid GitHub repository name.'),
    'asset_name': ('下载地址的文件名必须与清单一致。', 'The download URL filename must match the catalog.'),
    'url_missing': ('在线应用缺少 downloadUrl。', 'An online app is missing downloadUrl.'),
    'metadata_large': ('GitHub Release 元数据过大。', 'GitHub Release metadata is too large.'),
    'asset_mismatch': ('Release 文件大小或资产编号与清单不匹配。', 'The Release asset size or ID does not match the catalog.'),
    'asset_missing': ('该 GitHub Release 没有清单指定的 APK。', 'This GitHub Release does not contain the APK named in the catalog.'),
    'using_cache': ('使用已校验的下载缓存：{name}', 'Using verified cached APK: {name}'),
    'downloading': ('从 GitHub Release 下载：{name}（{repo}，{tag}）', 'Downloading from GitHub Release: {name} ({repo}, {tag})'),
    'download_large': ('下载超过清单指定的大小，已停止。', 'The download exceeded the catalog size limit and was stopped.'),
    'download_integrity': ('下载文件的大小或 SHA-256 不匹配，已停止安装。', 'Downloaded size or SHA-256 does not match. Installation stopped.'),
    'temporary_changed': ('下载临时文件发生变化，已停止安装。', 'The temporary download file changed. Installation stopped.'),
    'download_complete': ('下载完成，SHA-256 校验通过：{name}', 'Download complete, SHA-256 verified: {name}'),
    'download_http': ('GitHub 下载失败（HTTP {code}）。请检查 Release、网络和仓库权限；私有仓库需 A6000_GITHUB_TOKEN。', 'GitHub download failed (HTTP {code}). Check the Release, network and repository permissions; private repositories need A6000_GITHUB_TOKEN.'),
    'download_io': ('GitHub 下载或缓存写入失败，请检查网络与本地磁盘权限。', 'GitHub download or cache write failed. Check the network and local disk permissions.'),
    'metadata_invalid': ('GitHub Release 元数据无效，已停止安装。', 'Invalid GitHub Release metadata. Installation stopped.'),
    'online_catalog_large': ('在线应用清单过大。', 'The online app catalog is too large.'),
    'online_catalog_read': ('无法读取在线应用列表，请确认 online-apps/catalog.json 完整且配置了 Release 地址。', 'Cannot read the online app catalog. Check online-apps/catalog.json and its Release URLs.'),
    'sidecar': ('读取 EXE 同目录的在线清单；请确认它来自可信维护者。', 'Reading the online catalog beside the EXE; make sure it comes from a trusted maintainer.'),
    'hint_unique': ('未找到唯一可用的相机。请只连接一台相机，确认相机已开机、数据线可传输数据、USB 模式为 MTP；具体设备数量请查看完整日志。', 'No single usable camera was found. Connect only one camera, turn it on, use a data cable and select MTP. Check the full log for device counts.'),
    'hint_missing': ('没有找到相机。请确认相机已开机，用可传输数据的 USB 线直连电脑，并将 USB 连接设为 MTP。关闭可能占用相机的照片导入或遥控软件后再试。', 'No camera found. Turn it on, connect it directly with a USB data cable and select MTP. Close photo-import or remote-control apps that may be using it.'),
    'hint_multiple': ('同时发现多台索尼设备。请只保留需要安装的这一台相机连接。', 'Multiple Sony devices were found. Connect only the camera you want to install to.'),
    'hint_timeout': ('相机切换或通信超时。请等待相机恢复正常画面，再重新连接；不要在仍传输数据时拔线。', 'Camera switching or communication timed out. Wait for the normal camera screen before reconnecting; do not unplug during a transfer.'),
    'hint_location': ('相机拒绝了安装任务中的地址。这不是 APK 列表的问题。请保留完整日志，以便检查相机的安装协议与本地服务。', 'The camera rejected the task URL. This is not an APK list issue. Save the full log to investigate the installation protocol and local service.'),
    'hint_port': ('本地安装端口被占用。请关闭其他 PMCA/安装器实例后再试。', 'The local installation port is busy. Close other PMCA or installer instances before retrying.'),
    'hint_connection': ('无法连接本机安装服务。请先关闭其他安装器，并检查系统或公司安全软件的拦截记录；不要直接关闭防火墙。', 'Cannot connect to the local installation service. Close other installers and check system or company security logs; do not disable the firewall.'),
    'hint_tls': ('本地安装服务的 TLS/证书通信失败。请保留完整错误和运行版本；不要修改全局 TLS 设置或关闭证书校验。', 'Local TLS/certificate communication failed. Save the full error and version; do not change global TLS settings or disable certificate validation.'),
    'hint_dependencies': ('运行依赖缺失。Windows 原生 USB 后端需要 pywin32 和 comtypes；建议在独立虚拟环境按项目依赖文件安装，不要反复重试相机。', 'A runtime dependency is missing. Windows native USB needs pywin32 and comtypes. For source runs, install the project dependencies in a virtual environment rather than repeatedly retrying the camera.'),
    'hint_usb': ('USB 通信失败或设备被占用。请关闭其他相机程序，检查数据线和 USB 模式。应用安装通常不需要用 Zadig 替换系统 MTP 驱动。', 'USB communication failed or the device is busy. Close other camera apps and check the cable and USB mode. App installation normally does not require replacing the MTP driver with Zadig.'),
    'hint_unsupported': ('相机未接受应用安装模式。请记录机型、固件版本及完整日志；本工具不会自动刷固件或修改相机设置。', 'The camera did not accept app-installation mode. Record the model, firmware and full log; this tool does not automatically flash firmware or alter camera settings.'),
    'hint_mode': ('当前 USB 模式不能安装应用。请退出服务/升级模式，恢复正常开机后将 USB 连接设为 MTP。', 'This USB mode cannot install apps. Exit service/update mode, start the camera normally and select MTP.'),
    'hint_generic': ('这次安装没有完成。请先保留完整日志，检查相机屏幕的提示，再决定下一步；不建议盲目反复重试。', 'The installation did not complete. Save the full log and check the camera screen before deciding what to do next; avoid blind retries.'),
}


def get_language():
    return _language


def tr(key, **values):
    return MESSAGES[key][LANGUAGES.index(_language)].format(**values)


def preference_path():
    base = os.environ.get('LOCALAPPDATA') if os.name == 'nt' else os.environ.get('XDG_CONFIG_HOME')
    base = Path(base) if base else Path.home() / '.config'
    return base / 'A6000-PMCA' / 'preferences.json'


def load_language(path=None):
    """Invalid or unreadable preferences use Chinese; never execute config data."""
    global _language
    try:
        raw = json.loads(Path(path or preference_path()).read_text(encoding='utf-8'))
        language = raw.get('language') if isinstance(raw, dict) else None
    except (OSError, ValueError):
        language = None
    _language = language if language in LANGUAGES else 'zh'
    return _language


def set_language(language, persist=False, path=None):
    global _language
    if language not in LANGUAGES:
        raise ValueError('Language must be zh or en')
    _language = language
    if persist:
        target = Path(path or preference_path())
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent,
                                             prefix='.preferences-', delete=False) as output:
                temporary = Path(output.name)
                json.dump({'language': language}, output)
                output.write('\n')
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass
