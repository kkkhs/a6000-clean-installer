# 中文 / English language switching

两个版本共用双语界面，支持且仅支持 `zh`（中文）与 `en`（English）。

- 点击右上角 `English` / `中文`，不重启、不重新下载、不改变选中的应用或本地 APK 文件。
- 标签页、按钮、状态、文件选择提示、应用名称/用途/备注、下载提示和友好错误建议随语言切换。
- 用户语言偏好原子保存到个人配置目录下 `A6000-PMCA/preferences.json`，不写安装器目录。Windows 使用 `LOCALAPPDATA`；Linux 使用 `XDG_CONFIG_HOME` 或 `~/.config`。两种版本共用偏好。
- 默认中文；缺失、损坏或不支持的偏好回退为中文。不需要 GitHub 登录。
- 相机通信期间禁用切换。既有日志不重写，底层 PMCA 原始输出不翻译，便于排错。
- 21 个 APK 没有改动。切换安装器语言不会改变相机内应用或相机设置。

Both installer profiles share one bilingual UI with exactly two languages: Chinese and English.

Click **English / 中文** at the top right to switch without restarting. App names, descriptions, buttons, tabs, status messages and friendly error guidance follow the selected language. Your app selection and local APK path are preserved. The language preference is stored in your user configuration folder, shared by both profiles.

Switching is temporarily disabled during camera communication. Existing logs are not rewritten; raw PMCA diagnostics remain in their original form. Switching this interface does not translate APKs or alter the camera's language.

Older external catalogs without English descriptions remain supported with an explicit English fallback. The maintained 21-app catalogs include both descriptions and notes.

## Product information

The interface uses the display name **Sony PMCA App Installer**. The bilingual About dialog and footer identify **kkkhs** as author/maintainer and credit **ma1co / Sony-PMCA-RE** for the installation backend. Operational hints are concise; compatibility, transfer-safety and log-privacy guidance are retained. Hardware verification details live in release reports rather than being repeated in every app entry.

Repository URLs, EXE filenames and preference paths retain their original A6000-based names for compatibility.

## Verification

Local unit tests check translations, placeholder consistency, preference save/reload and fallback, app metadata language selection, catalog errors and installation regressions. Windows `--self-test` constructs the real GUI without USB/server/background actions, switches Chinese → English → Chinese and checks labels, status, app selection and local APK mode/path preservation. See Release verification reports for the final build result. No A6000 hardware installation has been tested.

## Main changed files

- `pmca/i18n.py`: messages and persisted preference; only Chinese/English.
- `pmca-gui.py`: live UI updates and language-aware status, no installation protocol changes.
- `pmca/{offline,online,catalog,friendly}.py`: language-aware details and messages; download/hash checks unchanged.
- `tools/import_offline_apps.py`, both catalogs: English descriptions and notes, without changing APK names, URLs, sizes, versions or hashes.
- `tests/test_i18n.py`: language and preference tests.
