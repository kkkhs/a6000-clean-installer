<p align="center">
  <img src="docs/assets/icon.svg" width="96" alt="Sony PMCA App Installer icon">
</p>

<h1 align="center">Sony PMCA App Installer</h1>

<p align="center">
  Install apps on Sony cameras that support PlayMemories Camera Apps.<br>
  <b>21 apps · Offline and online editions · Chinese / English switching</b>
</p>

<p align="center">
  <a href="https://github.com/kkkhs/a6000-clean-installer/releases/latest"><img src="https://img.shields.io/github/v/release/kkkhs/a6000-clean-installer?label=release" alt="Latest release"></a>
  <img src="https://img.shields.io/badge/platform-Windows%20x64-0078D4" alt="Windows x64">
  <img src="https://img.shields.io/badge/languages-Chinese%20%2F%20English-0f766e" alt="Chinese and English">
</p>

<p align="center">
  <a href="https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/A6000-PMCA-Offline-ZH.exe"><b>Download offline edition</b></a> ·
  <a href="https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/A6000-PMCA-Online-ZH.exe"><b>Download online edition</b></a> ·
  <a href="https://github.com/kkkhs/a6000-clean-installer/releases">All releases</a> ·
  <a href="README.md">简体中文</a>
</p>

---

**Contents**

- [What it is](#what-it-is)
- [Which download to choose](#which-download-to-choose)
- [Compatibility](#compatibility)
- [Installing an app](#installing-an-app)
- [Switching languages](#switching-languages)
- [The apps](#the-apps)
- [What it changes](#what-it-changes)
- [Troubleshooting](#troubleshooting)
- [For developers](#for-developers)
- [Author, credits and licensing](#author-credits-and-licensing)

## What it is

This installer runs on your **Windows computer** and targets Sony cameras with PlayMemories Camera Apps (PMCA) support. The A6000 is one primary use case, not the only platform target. It is not an app that runs on the camera, and it is not a firmware-flashing tool.

Built on [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE), it presents 21 camera APKs in one list with Chinese and English descriptions. Connect the camera, choose an app and click Install. There is no Sony Market login, and no need to find each APK separately.

Both editions include their runtime: **you do not need to install Python**. Installation uses USB and installs only the selected app, not all 21 at once.

The display name is Sony PMCA App Installer. The repository URL (`a6000-clean-installer`) and EXE filenames remain unchanged to preserve existing download links.

> **Compatibility:** the camera must support PMCA. Each app also has model, firmware, lens and existing-app requirements. Inclusion in the catalog is not a claim that every app works on every model.

## Which download to choose

| Edition | Download | Choose it when… |
| --- | --- | --- |
| **Offline** | [EXE · 49.8 MB](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/A6000-PMCA-Offline-ZH.exe) | You want all 21 APKs included in one download, with no further app downloads. **Start here if unsure.** |
| **Online** | [EXE · 16.4 MB](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/A6000-PMCA-Online-ZH.exe) | You prefer a smaller installer that downloads the selected APK from this repository's Release assets. |

**Both editions include both languages.** The filenames retain `-ZH.exe` for continuity; English is available inside either program.

Public Release downloads require **no GitHub account or token**. The online edition checks the downloaded size and SHA-256 and can reuse a verified cache. A failed integrity check stops installation before accessing the camera.

- [Release notes and verification reports](https://github.com/kkkhs/a6000-clean-installer/releases/tag/v0.2.1-community)
- [EXE SHA-256 checksums](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/SHA256SUMS.txt)
- [The 21 original APKs, separately](https://github.com/kkkhs/a6000-clean-installer/releases/tag/apk-set-v1)

The EXEs are not code-signed. Windows SmartScreen may identify an unknown publisher. Check the download source and SHA-256; **do not disable security software**.

## Compatibility

| Item | Current scope |
| --- | --- |
| Computer | The published executables are for **Windows x64**. This fork does not publish macOS or Linux packages. |
| Camera | Targets **Sony cameras with PlayMemories Camera Apps support**, using the Sony-PMCA-RE installation channel. |
| Model examples | PMCA-capable models such as the A6000, A6300, A6500 and A7 II. Installer compatibility and each APK's requirements must be checked separately. |
| Model and app requirements | Consult the [upstream camera documentation](https://openmemories.readthedocs.io/devices.html) and each app's documentation. These examples are not a list of hardware-tested models for this project. |
| Installation result | Verify the app in the camera's Application List and check its operation. Build and startup checks do not establish model compatibility. |

Check for `MENU → Application` on the camera. An installer cannot add app support to a body that does not have it. A similar model name is not evidence of compatibility.

Successes and failures are welcome in [Issues](https://github.com/kkkhs/a6000-clean-installer/issues). Include the model, firmware, app and full log.

## Installing an app

**1. Download and open an installer.** Choose the offline or online EXE above. No Python installation or GitHub token is needed.

**2. Prepare the camera.**

- Charge the battery and turn the camera on normally.
- Connect it directly to the computer with a USB cable that transfers data.
- Set **USB Connection to MTP**, the connection mode used in this version's instructions.
- Close other PMCA instances, photo-import tools and remote-control software that might hold the device.

**3. Select an app.** In the Install apps tab, choose an entry and read its description, original name, version and language notes. Open APK lets you choose another local APK instead.

The Camera info tab can check the current connection. **Reading camera information successfully does not prove that installation will work.**

**4. Click Install selected app.** The offline edition reads its bundled APK; the online edition downloads it first. Both verify the file before calling the community PMCA backend. Wait for completion and do not unplug USB during a transfer.

**5. Check the camera.** After the task finishes, confirm the app name and version under `MENU → Application → Application List`. A success message reflects the camera task result; verify the app on the camera itself.

If it fails, save the log and note what the camera screen shows. Use the troubleshooting table rather than repeatedly retrying.

## Switching languages

Click **English / 中文** at the top right. The switch is immediate and does not require a restart.

- Buttons, tabs, app names and descriptions, status, download messages and friendly error guidance follow the selected language.
- Your selected app, local APK path and installation mode are preserved.
- The preference is remembered and shared by both editions.
- Switching is temporarily disabled during camera communication. Existing logs are not rewritten; raw PMCA diagnostics stay in their original form.

**Changing the installer language does not translate the APKs or change the camera's language.** [More about language preferences →](community/README-BILINGUAL.md)

## The apps

The collection contains 21 APKs. Chinese names are descriptive translations, not necessarily Sony's official product names. Some names and descriptions were inferred from resource strings; the list retains these caveats.

| Category | Apps |
| --- | --- |
| Time and motion | Time-lapse, Timelapse add-on, Stop Motion, Motion Shot, Star Trail |
| Light and composites | Smooth Reflection, Light Graffiti, Light effects, Multiple Exposure, Graduated Filter, Digital Filter |
| Portraits and editing | Beauty Effect, Photo Retouch, Portrait Lighting, Effect Master |
| Color and recipes | LVG preset app (name unverified), [Recipe Lab](https://github.com/voxivoid/recipe-lab-sony-pmca) |
| Shooting tools | Bracket tools, Optical Compensation, Touchless Shutter, Smart Remote Control |

**[All 21 apps, original names and versions →](docs/APPS.md)**

19 APKs declare `zh` resources; Touchless Shutter and Recipe Lab do not. This is resource metadata, not a guarantee that every in-camera screen is translated.

The Timelapse add-on may have dependencies; do not use it as the first installation test. The included Recipe Lab is **v1.9.0**, not necessarily the latest upstream version.

## What it changes

Compared with the selected community upstream source, this fork:

- Uses its own 21-app catalog with bundled APKs or GitHub Release downloads.
- Adds Chinese/English UI, descriptions, integrity checks and log saving.
- Makes missing-device, wrong-mode and timeout failures explicit, and fixes Windows COM packaging compatibility.

**It does not modify or re-sign APKs, or rewrite Sony USB commands, APK transfer formats or the camera installation protocol.** It does not automatically flash firmware, unlock languages or change the camera region. Service-mode controls are not exposed in the application GUI. The behavior of an installed app is determined by that app.

The repository's earlier `v0.1.x` browser shell is retained for historical reference. Current downloads use the `v0.2.x` community installer. [File-by-file changes (Chinese) →](community/README-TWO-VERSIONS-ZH.md#逐文件说明)

## Troubleshooting

| What you see | What to check first |
| --- | --- |
| `No devices found` | Camera on, USB set to MTP, data-capable cable, no other camera software holding it. Try a different cable or USB port. |
| `Waiting for camera to switch...` or a timeout | Save the log. Wait until transfers have stopped and the normal camera screen returns before reconnecting. Do not unplug during an active transfer. |
| `Unknown location` | The camera rejected an installation URL. Save the full log and camera-screen message; this does not mean the app list is wrong. |
| Download error, 404 or network failure | Check access to this repository's Releases. Use the offline edition if network access is inconvenient. Public downloads need no token. |
| Size or SHA-256 mismatch | Do not bypass verification. Check the file and catalog and obtain the file again from its original Release. |
| TLS/certificate error or a busy local port | Close other installer instances and save the error. Check security-software logs; do not disable the firewall or global certificate validation. |
| Success reported, but no app on the camera | Check the camera's Application List. Report the app, firmware, program log and camera-screen message. |
| Anything else | Click Export diagnostic log, redact it and [open an Issue](https://github.com/kkkhs/a6000-clean-installer/issues/new). |

Include the **installer edition/version, Windows version, camera model and firmware, app name/version, full log and camera-screen message**. Logs may contain a camera serial number and personal paths; remove them before posting publicly.

Do not respond to an installation failure by resetting the camera, flashing firmware or replacing the system MTP driver with Zadig.

## For developers

Ordinary users can use the EXEs directly. Developer details live separately.

The verification reports distinguish automated checks from hardware results: Windows builds, startup, language switching and file integrity are covered; no camera installation result has been recorded for this modified installer.


- [Two editions and file-by-file changes (Chinese)](community/README-TWO-VERSIONS-ZH.md)
- [APK import, tests and Windows builds (Chinese)](community/README-A6000-ZH.md#windows-开发构建)
- [Bilingual UI and language preference](community/README-BILINGUAL.md)
- [Static findings in the earlier browser shell (Chinese)](community/ANALYSIS-A6000.md)
- [Windows build workflow](https://github.com/kkkhs/a6000-clean-installer/actions/workflows/community-windows.yml)
- [v0.2.1 verification report](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/BUILD-VERIFICATION.json)

## Author, credits and licensing

**Author / maintainer: [kkkhs](https://github.com/kkkhs)** · [Project repository](https://github.com/kkkhs/a6000-clean-installer)

Maintains the installer interface, bilingual app catalog, offline/online editions and releases. Camera installation uses the community backend credited below.

**Thanks to [ma1co](https://github.com/ma1co)** for [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE) and the work on Sony's camera platform. This project uses that installation backend rather than reimplementing camera communication.

**Thanks to [André Domingues (voxivoid)](https://github.com/voxivoid)** for [Recipe Lab](https://github.com/voxivoid/recipe-lab-sony-pmca). Its README also inspired this user-oriented organization of setup, compatibility boundaries and troubleshooting.

Installer source: [MIT](LICENSE). The upstream PMCA license is preserved in [community/LICENSE.txt](community/LICENSE.txt). Each APK retains its own rights and license; the installer's MIT license does not replace those terms. The maintainer has confirmed authorization to publish this collection.

**Camera installation relies on community reverse engineering and carries compatibility and device-operation risks. Hardware results take precedence over automated checks.**
