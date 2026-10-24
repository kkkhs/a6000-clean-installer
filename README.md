<p align="center">
  <b>简体中文</b> · <a href="README.en.md"><b>English README</b></a>
</p>

<p align="center">
  <img src="docs/assets/icon.svg" width="96" alt="Sony PMCA App Installer 图标">
</p>

<h1 align="center">索尼相机应用安装器<br>Sony PMCA App Installer</h1>

<p align="center">
  在 Windows 上为具备 PlayMemories Camera Apps 功能的索尼相机安装应用。<br>
  A Windows app installer for Sony cameras with PlayMemories Camera Apps support.
</p>

<p align="center">
  <b>21 项应用目录 · 离线安装 / 在线下载 · 简体中文 / English</b><br>
  21-app catalog · Offline installation / Online downloads · Chinese / English
</p>

<p align="center">
  <a href="https://github.com/kkkhs/sony-pmca-app-installer/releases/latest"><img src="https://img.shields.io/github/v/release/kkkhs/sony-pmca-app-installer?label=release" alt="最新版本"></a>
  <img src="https://img.shields.io/badge/platform-Windows%20x64-0078D4" alt="Windows x64">
  <img src="https://img.shields.io/badge/languages-中文%20%2F%20English-0f766e" alt="简体中文和英文">
</p>

<p align="center">
  <a href="https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.2-community/A6000-PMCA-Offline-ZH.exe"><b>下载离线版</b></a> ·
  <a href="https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.2-community/A6000-PMCA-Online-ZH.exe"><b>下载在线版</b></a> ·
  <a href="https://github.com/kkkhs/sony-pmca-app-installer/releases">版本记录</a>
</p>

---

## 目录

- [项目简介](#项目简介)
- [下载安装](#下载安装)
- [兼容性](#兼容性)
- [安装流程](#安装流程)
- [语言设置](#语言设置)
- [应用目录](#应用目录)
- [技术说明](#技术说明)
- [故障排查](#故障排查)
- [开发文档](#开发文档)
- [作者与致谢](#作者与致谢)
- [许可与声明](#许可与声明)

## 项目简介

Sony PMCA App Installer 基于 [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE)，通过 USB 为具备 PlayMemories Camera Apps（PMCA）功能的索尼相机安装应用。项目提供统一的 21 项应用目录、双语说明，以及离线安装和在线下载两种发行版本。

### 主要功能

- **离线安装**：安装器内置全部 21 个 APK，无需额外下载应用。
- **在线下载**：按需从公开 GitHub Release 获取选定 APK，并复用已校验缓存。
- **双语界面**：支持简体中文与英文切换，保存语言偏好并保留当前选择。
- **文件校验**：目录内的 APK 在安装前校验文件大小和 SHA-256。
- **诊断日志**：保留原始 PMCA 输出，提供错误提示及日志导出。
- **独立运行**：Windows 发行包包含运行时，无需另行安装 Python 或登录 Sony Market。

本软件运行于电脑端，不是相机端应用或固件更新工具。A6000 是主要使用场景之一，项目范围不限于该型号。

## 下载安装

当前版本：**[v0.2.2-community](https://github.com/kkkhs/sony-pmca-app-installer/releases/tag/v0.2.2-community)**。

| 发行版本 | 下载 | 内容与适用场景 |
| --- | --- | --- |
| **离线版** | [Windows x64 EXE · 49.8 MB](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.2-community/A6000-PMCA-Offline-ZH.exe) | 内置全部 21 个 APK，适用于离线环境或需要完整应用集合的用户。 |
| **在线版** | [Windows x64 EXE · 16.4 MB](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.2-community/A6000-PMCA-Online-ZH.exe) | 仅内置应用目录，安装时下载选定 APK，适用于按需获取应用的场景。 |

两个版本均包含简体中文和英文界面。文件名沿用 `A6000-PMCA-*-ZH.exe`，不表示仅支持 A6000 或仅提供中文界面。下载 EXE 后可直接运行，无需安装 Python。

公开 Release 下载不需要 GitHub 账号或访问令牌。在线版在文件校验通过后调用安装后端；校验失败时终止该次安装。

- [SHA-256 校验文件](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.2-community/SHA256SUMS.txt)
- [构建与验证报告](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.2-community/BUILD-VERIFICATION.json)
- [原始 APK 集合](https://github.com/kkkhs/sony-pmca-app-installer/releases/tag/apk-set-v1)

> 发行包未使用 Authenticode 签名，Windows SmartScreen 可能显示“未知发布者”。请核对下载来源与校验值，不应为运行本软件而关闭系统安全保护。

## 兼容性

| 项目 | 要求与范围 |
| --- | --- |
| 操作系统 | Windows x64。当前不提供此改造版本的 macOS 或 Linux 发行包。 |
| 相机平台 | 相机须具备 PlayMemories Camera Apps 功能，安装通道沿用 Sony-PMCA-RE。 |
| 机型示例 | Sony A6000、A6300、A6500、A7 II 等 PMCA 机型。示例仅说明平台范围，不构成本项目的真机验证名单。 |
| 应用适配 | 具体 APK 的支持范围取决于机型、固件、镜头及已有应用；应查阅应用自身文档。 |

相机菜单中的 `MENU → 应用程序（Application）` 可作为初步判断依据。没有 PMCA 功能的相机，不能通过本安装器获得应用支持。完整平台信息请查阅 [上游机型文档](https://openmemories.readthedocs.io/devices.html)。

## 安装流程

### 1. 准备设备

- 确保相机电量充足并正常开机。
- 使用支持数据传输的 USB 线，将相机直接连接至电脑。
- 将相机的 **USB 连接模式设置为 MTP**。
- 关闭其他 PMCA、照片导入或相机遥控程序，避免设备占用。

### 2. 选择应用

在“安装应用”页选择目录中的应用，查阅功能简介、版本及语言资源。使用“打开 APK…”可选择其他本地 APK 文件。

“相机信息”页用于读取设备型号、固件等连接信息。设备信息读取与应用安装属于不同操作，前者成功不能证明后者可完成。

### 3. 执行安装

点击“安装选中的应用”。离线版读取内置文件，在线版下载选定文件；目录内的 APK 校验通过后，由社区 PMCA 后端执行安装。每次操作仅安装一个选定应用。传输过程中不得断开 USB 连接。

### 4. 确认结果

任务结束后，在 `MENU → 应用程序 → 应用程序列表` 中确认应用名称与版本。安装器的完成提示对应相机任务返回结果，应用是否可正常使用仍需在相机端确认。

安装失败时，应导出诊断日志并记录相机屏幕提示，按照[故障排查](#故障排查)处理。

## 语言设置

使用窗口右上角的 **English / 中文** 按钮切换界面语言，无需重启。

- 按钮、标签页、应用说明、状态及错误建议使用所选语言。
- 切换时保留应用选择、本地 APK 路径和安装模式。
- 语言偏好保存在用户配置目录，两个发行版本共用该配置。
- 相机通信期间暂时禁用语言切换。已有日志不重写，底层 PMCA 输出保留原文。

安装器语言设置不改变相机语言，也不修改 APK 内部资源。详细信息见[双语界面文档](community/README-BILINGUAL.md)。

## 应用目录

应用集合共包含 21 个 APK：

| 类别 | 应用 |
| --- | --- |
| 时间与运动 | 延时摄影、延时摄影扩展、定格动画、运动轨迹、星轨 |
| 光线与合成 | 平滑反射、光绘、光线效果、多重曝光、渐变滤镜、数码滤镜 |
| 人像与编辑 | 人像美化、照片润饰、人像光效、增强图片效果 |
| 色彩与配方 | 实时色彩预设（名称待确认）、[Recipe Lab](https://github.com/voxivoid/recipe-lab-sony-pmca) |
| 拍摄辅助 | 专业包围拍摄、手动镜头补偿、非接触快门、智能遥控 |

完整名称、版本、用途和备注见[应用目录文档](docs/APPS.md)。中文名称为说明性译名，部分名称和用途依据资源字符串推断，不作为 Sony 官方名称或完整功能声明。

19 个 APK 声明了 `zh` 资源；Touchless Shutter 和 Recipe Lab 未声明。资源声明不保证每个页面均提供中文。延时摄影扩展可能依赖其他应用；集合中的 Recipe Lab 为 **1.9.0**，不代表其上游最新版本。

## 技术说明

本项目保留上游 Sony USB 指令、APK 传输格式和相机安装协议，主要扩展内容为应用来源、双语界面、完整性校验、诊断提示及 Windows COM 打包兼容修正。APK 保持原样，不修改或重新签名。

安装器不自动更新固件、解锁语言或改变相机区域，应用界面不提供服务模式入口。安装后的应用行为由各应用自身决定。

仓库已由 `a6000-clean-installer` 更名为 **`sony-pmca-app-installer`**。旧仓库及发行包链接仍可跳转，EXE 文件名和用户配置路径保持不变。已发布的 EXE 未重新构建，其内置旧地址通过跳转继续使用；后续构建采用新仓库地址。历史 `v0.1.x` 网页外壳保留供参考，当前发行版本采用 `v0.2.x` 社区安装器。

在线版将 APK 内容固定于 `apk-set-v1` Release。更新应用目录可使用 EXE 同目录的 `online-apps/catalog.json`；仅应使用可信维护者提供的清单。SHA-256 用于核验文件一致性，不能证明清单或应用发布者的可信性。

## 故障排查

| 错误或现象 | 排查建议 |
| --- | --- |
| `No devices found` / 未检测到相机 | 检查开机状态、MTP 模式及 USB 数据线；关闭设备占用程序，检查其他数据线或 USB 端口。 |
| `Waiting for camera to switch...` / 切换超时 | 保存日志；确认传输已结束、相机恢复正常状态后再重新连接，不得在传输期间拔线。 |
| `Unknown location` | 相机拒绝了安装任务地址。保留完整日志和相机屏幕信息，以定位协议或本地服务问题。 |
| 下载失败、HTTP 404 或网络错误 | 检查本仓库 Release 的可访问性；受限网络环境可使用离线版。公开下载无需访问令牌。 |
| 文件大小或 SHA-256 不匹配 | 终止安装，不绕过校验；核对文件与清单版本，并从对应 Release 重新获取文件。 |
| `SSL error` / `Communication error 201` | 201 为相机的通用 TLS 失败结果。如果日志同时出现 `python_aes.py`、`deprecations.py` 和 `NoneType` 异常，对应已定位的冻结包兼容性问题；参阅 [SSL 201 分析](docs/TLS-201.md)。不得通过关闭防火墙或证书校验处理。 |
| 本地端口占用或连接被拒绝 | 关闭其他安装器实例，记录完整错误并检查安全软件拦截记录；不得直接关闭防火墙。 |
| 任务完成但应用未显示 | 检查相机应用列表；记录应用名称、固件版本、安装日志和相机提示。 |

提交问题时，请提供安装器版本与类型、Windows 版本、相机型号与固件、应用名称与版本、完整日志及相机屏幕信息。日志可能包含设备序列号和个人路径，公开提交前应脱敏。[提交 Issue](https://github.com/kkkhs/sony-pmca-app-installer/issues/new)

不应将恢复出厂设置、刷写固件或使用 Zadig 替换系统 MTP 驱动作为常规安装故障处理步骤。

## 开发文档

- [发行版本设计与逐文件修改](community/README-TWO-VERSIONS-ZH.md)
- [APK 导入、测试及 Windows 构建](community/README-A6000-ZH.md#windows-开发构建)
- [双语界面与语言偏好](community/README-BILINGUAL.md)
- [历史网页外壳分析记录](community/ANALYSIS-A6000.md)
- [Windows 构建工作流](https://github.com/kkkhs/sony-pmca-app-installer/actions/workflows/community-windows.yml)
- [v0.2.2 验证报告](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.2-community/BUILD-VERIFICATION.json)

v0.2.2 的 47 项自动化测试、Windows 构建和界面检查已通过，但未覆盖 TLS 的纯 Python AES 冻结运行路径。后续 A6000 安装反馈暴露了该打包异常，完整原因与回归范围见 [SSL 201 分析](docs/TLS-201.md)。自动化结果与真机安装结果分别记录，不将前者作为后者的证明。

## 作者与致谢

**作者 / 维护者：[kkkhs](https://github.com/kkkhs)**，负责安装器界面、双语应用目录、发行版本及发布维护。

- [ma1co](https://github.com/ma1co)：[Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE) 及 Sony 相机平台研究，提供本项目沿用的安装后端。
- [André Domingues（voxivoid）](https://github.com/voxivoid)：[Recipe Lab](https://github.com/voxivoid/recipe-lab-sony-pmca)；其文档组织方式为本项目 README 提供参考。

## 许可与声明

安装器源码采用 [MIT 许可](LICENSE)，上游 PMCA 许可证保留于 [community/LICENSE.txt](community/LICENSE.txt)。各 APK 的权利、署名和许可证归各自作者或权利人所有，安装器许可不替代应用许可；维护者已确认本集合的发布授权。

本项目不隶属于 Sony，也不是 Sony 官方软件。相机通信依赖社区逆向工程成果，存在兼容性和设备操作风险，实际使用应遵循相机及应用的适用要求。
