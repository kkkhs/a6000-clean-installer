<p align="center">
  <a href="README.md"><b>简体中文 README</b></a> · <b>English</b>
</p>

<p align="center">
  <img src="docs/assets/icon.svg" width="96" alt="Sony PMCA App Installer icon">
</p>

<h1 align="center">Sony PMCA App Installer<br>索尼相机应用安装器</h1>

<p align="center">
  A Windows app installer for Sony cameras with PlayMemories Camera Apps support.<br>
  在 Windows 上为具备 PlayMemories Camera Apps 功能的索尼相机安装应用。
</p>

<p align="center">
  <b>21-app catalog · Offline installation / Online downloads · Chinese / English</b><br>
  21 项应用目录 · 离线安装 / 在线下载 · 简体中文 / English
</p>

<p align="center">
  <a href="https://github.com/kkkhs/sony-pmca-app-installer/releases/latest"><img src="https://img.shields.io/github/v/release/kkkhs/sony-pmca-app-installer?label=release" alt="Latest release"></a>
  <img src="https://img.shields.io/badge/platform-Windows%20x64-0078D4" alt="Windows x64">
  <img src="https://img.shields.io/badge/languages-Chinese%20%2F%20English-0f766e" alt="Chinese and English">
</p>

<p align="center">
  <a href="https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.3-community/A6000-PMCA-Offline-ZH.exe"><b>Download offline edition</b></a> ·
  <a href="https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.3-community/A6000-PMCA-Online-ZH.exe"><b>Download online edition</b></a> ·
  <a href="https://github.com/kkkhs/sony-pmca-app-installer/releases">Release history</a>
</p>

---

## Contents

- [Overview](#overview)
- [Downloads](#downloads)
- [Compatibility](#compatibility)
- [Installation](#installation)
- [Language settings](#language-settings)
- [App catalog](#app-catalog)
- [Technical details](#technical-details)
- [Troubleshooting](#troubleshooting)
- [Developer documentation](#developer-documentation)
- [Author and acknowledgments](#author-and-acknowledgments)
- [License and disclaimer](#license-and-disclaimer)

## Overview

Sony PMCA App Installer uses [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE) to install apps over USB on Sony cameras with PlayMemories Camera Apps (PMCA) support. It provides a unified 21-app catalog, bilingual descriptions, and offline and online editions.

### Features

- **Offline installation:** all 21 APKs are included in the installer.
- **Online downloads:** retrieve the selected APK from public GitHub Releases and reuse verified cached files.
- **Bilingual interface:** switch between Chinese and English, with saved preferences and preserved selection.
- **Integrity verification:** catalog APKs are checked against file size and SHA-256 before installation.
- **Diagnostics:** retain raw PMCA output and provide error guidance and log export.
- **Standalone executable:** Windows packages include their runtime; no separate Python installation or Sony Market login is required.

The software runs on the computer, not on the camera, and is not a firmware updater. The A6000 is a primary use case, but not the only platform target.

## Downloads

Current release: **[v0.2.3-community](https://github.com/kkkhs/sony-pmca-app-installer/releases/tag/v0.2.3-community)**.

v0.2.3 fixes the frozen TLS AES initialization exception behind the matching `SSL error / Communication error 201` log. Download the updated EXE if an older release produces this error; camera and system security settings do not need to be changed.

| Edition | Download | Contents and use case |
| --- | --- | --- |
| **Offline** | [Windows x64 EXE · 50.1 MB](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.3-community/A6000-PMCA-Offline-ZH.exe) | Includes all 21 APKs. Suitable for offline use or a complete local app collection. |
| **Online** | [Windows x64 EXE · 16.6 MB](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.3-community/A6000-PMCA-Online-ZH.exe) | Includes the catalog only and downloads the selected APK during installation. Suitable for on-demand downloads. |

Both editions include Chinese and English. The retained filenames, `A6000-PMCA-*-ZH.exe`, do not indicate A6000-only support or a Chinese-only interface. The executables include their runtime and do not require Python installation.

Public Release downloads require no GitHub account or access token. The online edition invokes the installation backend only after file verification; a failed check stops that installation.

- [SHA-256 checksums](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.3-community/SHA256SUMS.txt)
- [Build and verification report](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.3-community/BUILD-VERIFICATION.json)
- [Original APK collection](https://github.com/kkkhs/sony-pmca-app-installer/releases/tag/apk-set-v1)

> The executables are not Authenticode-signed. Windows SmartScreen may report an unknown publisher. Verify the download source and checksums; do not disable system security protections to run the software.

## Compatibility

| Item | Requirements and scope |
| --- | --- |
| Operating system | Windows x64. This modified installer does not currently publish macOS or Linux packages. |
| Camera platform | Requires PlayMemories Camera Apps support and uses the Sony-PMCA-RE installation channel. |
| Model examples | Sony A6000, A6300, A6500 and A7 II are examples of PMCA-capable models, not a hardware-tested list for this project. |
| App requirements | Each APK may have model, firmware, lens and existing-app requirements. Consult its documentation. |

The camera menu entry `MENU → Application` provides an initial indication of app support. This installer cannot add PMCA support to a camera that lacks it. Refer to the [upstream device documentation](https://openmemories.readthedocs.io/devices.html) for platform information.

## Installation

### 1. Prepare the devices

- Charge the camera battery and turn the camera on normally.
- Connect the camera directly to the computer using a USB data cable.
- Set **USB Connection to MTP**.
- Close other PMCA instances, photo-import tools and camera remote-control applications to avoid device contention.

### 2. Select an app

Select an entry in the Install apps tab and review its description, version and language resources. Open APK allows installation from another local APK file.

The Camera info tab reads model, firmware and connection information. Reading device information and installing an app are separate operations; success of the first does not establish that the second will complete.

### 3. Start installation

Click Install selected app. The offline edition reads a bundled file; the online edition downloads the selected file. After verification of a catalog APK, the community PMCA backend performs installation. Each operation installs one selected app. Do not disconnect USB during a transfer.

### 4. Verify the result

After completion, check the app name and version under `MENU → Application → Application List`. The installer completion message reflects the camera task result; confirm app operation on the camera.

If installation fails, export the diagnostic log, record the camera-screen message, and follow [Troubleshooting](#troubleshooting).

## Language settings

Use the **English / 中文** button at the top right to switch interface languages without restarting.

- Buttons, tabs, app descriptions, status and error guidance use the selected language.
- The selected app, local APK path and installation mode are preserved.
- The language preference is stored in the user configuration directory and shared by both editions.
- Switching is temporarily disabled during camera communication. Existing logs are not rewritten; raw PMCA output is preserved.

This setting does not change the camera language or APK resources. See the [bilingual interface documentation](community/README-BILINGUAL.md).

## App catalog

The collection contains 21 APKs:

| Category | Apps |
| --- | --- |
| Time and motion | Time-lapse, Timelapse add-on, Stop Motion, Motion Shot, Star Trail |
| Light and composites | Smooth Reflection, Light Graffiti, Light effects, Multiple Exposure, Graduated Filter, Digital Filter |
| Portraits and editing | Beauty Effect, Photo Retouch, Portrait Lighting, Effect Master |
| Color and recipes | LVG preset app (name unverified), [Recipe Lab](https://github.com/voxivoid/recipe-lab-sony-pmca) |
| Shooting tools | Bracket tools, Optical Compensation, Touchless Shutter, Smart Remote Control |

The [app catalog documentation](docs/APPS.md) lists names, versions, descriptions and notes. Chinese names are descriptive translations. Some names and descriptions were inferred from resource strings and are not claims of official Sony names or complete functionality.

19 APKs declare `zh` resources; Touchless Shutter and Recipe Lab do not. A resource declaration does not guarantee translation of every screen. The Timelapse add-on may have dependencies. The included Recipe Lab is **v1.9.0**, not necessarily the latest upstream release.

## Technical details

This project retains the upstream Sony USB commands, APK transfer format and camera installation protocol. Its extensions cover app sources, bilingual UI, integrity verification, diagnostic guidance and Windows COM packaging compatibility. APKs are unchanged and are not re-signed.

The installer does not automatically update firmware, unlock languages or alter the camera region. The app GUI does not expose service-mode controls. Installed applications determine their own behavior.

The repository has been renamed from `a6000-clean-installer` to **`sony-pmca-app-installer`**. Existing repository and Release links redirect; EXE filenames and user configuration paths remain unchanged. v0.2.3 uses the new repository URL. Earlier published EXEs have not been replaced; their embedded URLs continue to work through redirects. The historical `v0.1.x` browser shell is retained for reference; current releases use the `v0.2.x` community installer.

The online edition pins APK content to the `apk-set-v1` Release. Its catalog can be updated using `online-apps/catalog.json` beside the EXE; use only a catalog supplied by a trusted maintainer. SHA-256 establishes file consistency, not catalog or publisher trust.

## Troubleshooting

| Error or symptom | Recommended checks |
| --- | --- |
| `No devices found` | Check camera power, MTP mode and the USB data cable. Close applications holding the device and test another cable or USB port. |
| `Waiting for camera to switch...` or a timeout | Save the log. Reconnect only after transfers stop and the camera returns to its normal state; do not unplug during a transfer. |
| `Unknown location` | The camera rejected the installation task URL. Retain the complete log and camera-screen message to investigate the protocol or local service. |
| Download failure, HTTP 404 or network error | Check access to the repository Releases. Use the offline edition on restricted networks. Public downloads require no token. |
| File size or SHA-256 mismatch | Stop installation; do not bypass verification. Check file/catalog versions and retrieve the file from the corresponding Release. |
| `SSL error` / `Communication error 201` | 201 is a generic camera TLS failure. If the log also contains `python_aes.py`, `deprecations.py` and the `NoneType` exception, it matches the confirmed frozen-package defect; see the [SSL 201 analysis](docs/TLS-201.md). Do not disable the firewall or certificate validation. |
| Local port contention or connection refused | Close other installer instances, retain the full error and inspect security-software blocking records. Do not disable the firewall. |
| Task completed but the app is absent | Check the camera Application List and record the app, firmware, installation log and camera message. |

Issue reports should include installer version and edition, Windows version, camera model and firmware, app name/version, complete log and camera-screen information. Logs may contain device serial numbers and personal paths; redact them before public submission. [Submit an Issue](https://github.com/kkkhs/sony-pmca-app-installer/issues/new)

Factory resets, firmware flashing and replacing the system MTP driver with Zadig are not routine installation troubleshooting steps.

## Developer documentation

- [Edition design and file-by-file changes (Chinese)](community/README-TWO-VERSIONS-ZH.md)
- [APK import, tests and Windows builds (Chinese)](community/README-A6000-ZH.md#windows-开发构建)
- [Bilingual UI and language preferences](community/README-BILINGUAL.md)
- [Historical browser-shell analysis (Chinese)](community/ANALYSIS-A6000.md)
- [Windows build workflow](https://github.com/kkkhs/sony-pmca-app-installer/actions/workflows/community-windows.yml)
- [v0.2.3 verification report](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.3-community/BUILD-VERIFICATION.json)

v0.2.3 passed 51 automated tests, Windows builds and UI/TLS/HTTP/SPK checks inside both final executables. It fixes the frozen Python AES exception exposed by A6000 installation feedback; see the [SSL 201 analysis](docs/TLS-201.md) for the cause and regression scope. Successful hardware installation remains unverified; automated results are not proof of camera installation success.

## Author and acknowledgments

**Author / maintainer: [kkkhs](https://github.com/kkkhs)** — installer interface, bilingual app catalog, editions and release maintenance.

- [ma1co](https://github.com/ma1co): [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE) and Sony camera-platform research, providing the installation backend used here.
- [André Domingues (voxivoid)](https://github.com/voxivoid): [Recipe Lab](https://github.com/voxivoid/recipe-lab-sony-pmca); its documentation structure informed this project's README.

## License and disclaimer

Installer source is [MIT-licensed](LICENSE), and the upstream PMCA license is preserved in [community/LICENSE.txt](community/LICENSE.txt). Each APK retains its own authorship, rights and license. The installer license does not replace app licenses; the maintainer has confirmed authorization to publish this collection.

This project is not affiliated with Sony and is not official Sony software. Camera communication relies on community reverse engineering and carries compatibility and device-operation risks. Follow the camera and application requirements.
