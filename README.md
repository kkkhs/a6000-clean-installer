<p align="center">
  <img src="docs/assets/icon.svg" width="96" alt="Sony PMCA App Installer 图标">
</p>

<h1 align="center">Sony PMCA App Installer</h1>

<p align="center">
  为支持 PlayMemories Camera Apps 的 Sony 相机安装应用。<br>
  <b>21 个应用 · 离线 / 在线两个版本 · 中文 / English 随时切换</b>
</p>

<p align="center">
  <a href="https://github.com/kkkhs/a6000-clean-installer/releases/latest"><img src="https://img.shields.io/github/v/release/kkkhs/a6000-clean-installer?label=release" alt="最新版本"></a>
  <img src="https://img.shields.io/badge/platform-Windows%20x64-0078D4" alt="Windows x64">
  <img src="https://img.shields.io/badge/languages-中文%20%2F%20English-0f766e" alt="中文和英文">
</p>

<p align="center">
  <a href="https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/A6000-PMCA-Offline-ZH.exe"><b>下载离线完整版</b></a> ·
  <a href="https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/A6000-PMCA-Online-ZH.exe"><b>下载在线版</b></a> ·
  <a href="https://github.com/kkkhs/a6000-clean-installer/releases">所有版本</a> ·
  <a href="README.en.md">English</a>
</p>

---

**目录**

- [这是什么](#这是什么)
- [下载哪个版本](#下载哪个版本)
- [兼容性](#兼容性)
- [开始安装](#开始安装)
- [切换语言](#切换语言)
- [有哪些应用](#有哪些应用)
- [它改了什么](#它改了什么)
- [遇到问题](#遇到问题)
- [开发与文档](#开发与文档)
- [作者、致谢与许可](#作者致谢与许可)

## 这是什么

这是一个运行在 **Windows 电脑上** 的 Sony 相机应用安装器，面向具备 PlayMemories Camera Apps（PMCA）功能的机型。A6000 是主要使用场景之一，不是唯一的平台目标。它不是装在相机里的应用，也不是固件刷机工具。

它基于社区项目 [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE)，把 21 个相机 APK 整理成带中文和英文说明的列表。连接相机、选择应用、点击安装，不必逐个寻找 APK，也不用登录 Sony Market。

两个版本都带运行时，普通用户 **不需要另外安装 Python**。应用安装通过 USB 完成，一次只安装你选中的一个应用。

项目展示名使用 Sony PMCA App Installer；仓库地址 `a6000-clean-installer` 和 EXE 文件名保持不变，兼容既有下载链接。

> **兼容性提示：** 相机必须具备 PMCA 功能；每个应用的适用范围还取决于机型、固件、镜头和已有应用。请查看应用说明，不要把列表收录等同于全部机型可用。

## 下载哪个版本

| 版本 | 下载 | 适合你，如果…… |
| --- | --- | --- |
| **离线完整版** | [EXE · 49.8 MB](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/A6000-PMCA-Offline-ZH.exe) | 希望一次下载后，自带全部 21 个 APK，安装时不再下载应用。**不确定就先选这个。** |
| **在线版** | [EXE · 16.4 MB](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/A6000-PMCA-Online-ZH.exe) | 希望安装器更小，选择应用后再从本仓库 Release 下载对应 APK。 |

**两个版本都支持中英文，不是各一个语言版本。** 文件名保留 `-ZH.exe`，但界面可以切换 English。

在线版下载公开 Release **不需要 GitHub 账号或令牌**，下载后会校验大小和 SHA-256，正确的缓存可以复用。校验失败不会开始相机安装。

- [完整 Release 与验证报告](https://github.com/kkkhs/a6000-clean-installer/releases/tag/v0.2.1-community)
- [EXE 的 SHA-256 校验文件](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/SHA256SUMS.txt)
- [单独下载 21 个原始 APK](https://github.com/kkkhs/a6000-clean-installer/releases/tag/apk-set-v1)

EXE 没有代码签名证书，Windows SmartScreen 可能显示“未知发布者”。请核对下载来源和 SHA-256，**不要关闭系统安全软件**。

## 兼容性

| 项目 | 当前范围 |
| --- | --- |
| 电脑 | 发布的安装器为 **Windows x64**；没有发布此改造版的 macOS / Linux 安装包。 |
| 相机 | 面向 **具备 PlayMemories Camera Apps 功能的 Sony 相机**，沿用 Sony-PMCA-RE 安装通道。 |
| 机型示例 | A6000、A6300、A6500、A7 II 等具备 PMCA 功能的机型；安装器和每个 APK 的具体适用范围仍需分别确认。 |
| 机型与应用适配 | 请查阅 [上游机型说明](https://openmemories.readthedocs.io/devices.html)及应用自身文档；这里的机型示例不是本项目真机验证名单。 |
| 安装结果 | 以相机应用列表和应用实际运行为准；构建与启动检查不能替代机型适配。 |

请在相机里检查 `MENU → 应用程序（Application）`。没有应用功能的机型，不能因为使用这个安装器就获得应用支持。不要仅凭名称相近就把 A6000 的适用范围推及其他机型。

成功与失败的记录都欢迎提交到 [Issues](https://github.com/kkkhs/a6000-clean-installer/issues)，并注明机型、固件、应用及完整日志。

## 开始安装

**1. 下载并打开安装器。**

选择上面的离线版或在线版 EXE。无需安装 Python，不用填写 GitHub 令牌。

**2. 准备相机。**

- 电量充足，正常开机。
- 使用能传输数据的 USB 线，直接连接电脑。
- 相机菜单的 **USB 连接设为 MTP**，这是本版本说明采用的连接方式。
- 关闭其他 PMCA、照片导入和相机遥控程序，避免占用设备。

**3. 选择一个应用。**

打开“安装应用”页，在列表里选择应用，查看用途、英文原名、版本和语言说明。也可以使用“打开 APK…”选择自己的本地文件。

“相机信息”页可读取当前连接信息；**读取信息成功不代表后续安装一定成功**。

**4. 点击“安装选中的应用”。**

离线版读取内置 APK；在线版先下载所选 APK。两者都先校验文件，再调用社区 PMCA 安装后端。等待任务结束，传输中不要拔 USB 线。

**5. 在相机内确认。**

任务结束后，检查 `MENU → 应用程序 → 应用程序列表` 中的应用名称和版本。程序显示成功是相机任务返回成功，最终仍应到相机里核实。

若失败，保存日志、记录相机屏幕提示，按下面的故障表排查，别直接连续重试。

## 切换语言

点击窗口右上角 **English / 中文**，立即切换，无需重启。

- 按钮、标签页、应用名称与说明、状态、下载提示和错误建议随语言切换。
- 保留当前选中的应用、本地 APK 路径及模式。
- 记住上次选择，离线版和在线版共用语言偏好。
- 相机通信期间暂时禁用切换；已有日志不会事后重写，底层 PMCA 输出保留原文。

**安装器的语言不会改变相机语言，也不会汉化 APK 本身。** [详细说明 →](community/README-BILINGUAL.md)

## 有哪些应用

共 21 个 APK，列表中的名称是便于理解的译名，不保证都是 Sony 官方中文名称。部分名称和用途由资源字符串推断，界面保留了相关备注。

| 类别 | 应用 |
| --- | --- |
| 时间与运动 | 延时摄影、延时摄影扩展、定格动画、运动轨迹、星轨 |
| 光线与合成 | 平滑反射、光绘、光线效果、多重曝光、渐变滤镜、数码滤镜 |
| 人像与编辑 | 人像美化、照片润饰、人像光效、增强图片效果 |
| 色彩与配方 | 实时色彩预设（名称待确认）、[Recipe Lab](https://github.com/voxivoid/recipe-lab-sony-pmca) |
| 拍摄辅助 | 专业包围拍摄、手动镜头补偿、非接触快门、智能遥控 |

**[完整 21 项列表、英文名和版本 →](docs/APPS.md)**

19 个 APK 声明了 `zh` 资源；非接触快门（Touchless Shutter）和 Recipe Lab 没有声明。这只是资源信息，不能保证应用内所有页面都有中文。

延时摄影扩展可能依赖其他应用，不建议把它作为第一个安装测试。Recipe Lab 随附版本为 **1.9.0**；不代表它的上游最新版本。

## 它改了什么

相较于所选的社区上游源码：

- 换成自己的 21 项列表，支持自带 APK 和 GitHub Release 下载。
- 加入中英界面、用途说明、文件校验和日志保存。
- 改善无设备、模式错误和超时等失败反馈，修正 Windows COM 打包兼容问题。

**没有修改或重新签名 APK，没有重写底层 Sony USB 指令、APK 传输格式或相机安装协议。** 安装器不会自动刷固件、解锁语言或修改相机区域，也不提供服务模式入口。安装进去的应用会做什么，仍取决于各应用自身。

原仓库的 `v0.1.x` 网页外壳保留作历史参考；当前下载的是 `v0.2.x` 社区版本。[逐文件改动 →](community/README-TWO-VERSIONS-ZH.md#逐文件说明)

## 遇到问题

| 看到什么 | 先做什么 |
| --- | --- |
| `No devices found` / 没找到相机 | 确认相机开机、USB 设为 MTP、线能传数据；关闭其他相机程序，换数据线或 USB 口检查。 |
| `Waiting for camera to switch...` / 超时 | 保存日志，等相机退出传输并恢复正常画面后再重新连接；不要在仍传输时拔线。 |
| `Unknown location` | 相机拒绝了安装地址。保存完整日志和相机屏幕提示；这不等于 APK 列表有问题。 |
| 下载失败、404 或网络错误 | 确认能访问本仓库 Release；网络不便时使用离线版。公开下载不需要令牌。 |
| 大小或 SHA-256 不匹配 | 不要绕过校验。检查是否使用了正确文件和清单，从原 Release 重新取得文件。 |
| TLS / 证书错误，或本地端口被占用 | 关闭其他安装器实例，保存完整错误；检查安全软件记录，不关闭防火墙或全局证书校验。 |
| 程序说成功，但相机里没有应用 | 不只看提示，在相机应用列表核实；提交应用名称、固件、程序日志和相机提示。 |
| 其他问题 | 点击“导出诊断日志”，脱敏后提交 [Issue](https://github.com/kkkhs/a6000-clean-installer/issues/new)。 |

报告时请附：**离线/在线版本、Windows 版本、相机型号与固件、应用名称与版本、完整日志及相机提示**。日志可能包含相机序列号和个人路径，公开提交前先删去这些信息。

不要因为安装失败就恢复出厂设置、刷固件或用 Zadig 替换系统 MTP 驱动。

## 开发与文档

普通用户直接下载 EXE 即可。开发资料独立放在以下文档，不需要为了安装应用阅读构建过程。

验证报告区分了自动化检查与相机实测：当前提供 Windows 构建、启动、双语切换及文件完整性结果，尚无本改造版的相机安装实测记录。

- [两种版本的实现与逐文件修改](community/README-TWO-VERSIONS-ZH.md)
- [本地导入 APK、测试与 Windows 构建](community/README-A6000-ZH.md#windows-开发构建)
- [双语界面与语言偏好](community/README-BILINGUAL.md)
- [原网页外壳的静态问题记录](community/ANALYSIS-A6000.md)
- [Windows 构建工作流](https://github.com/kkkhs/a6000-clean-installer/actions/workflows/community-windows.yml)
- [v0.2.1 验证报告](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/BUILD-VERIFICATION.json)

## 作者、致谢与许可

**作者 / 维护者：[kkkhs](https://github.com/kkkhs)** · [项目主页](https://github.com/kkkhs/a6000-clean-installer)

负责安装器界面、双语应用目录、离线 / 在线版本及发布维护。相机安装后端来自下述社区项目。

**感谢 [ma1co](https://github.com/ma1co)** 的 [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE) 及 Sony 相机平台逆向工作。本项目沿用其安装后端，不是从零实现相机通信。

**感谢 [André Domingues（voxivoid）](https://github.com/voxivoid)** 的 [Recipe Lab](https://github.com/voxivoid/recipe-lab-sony-pmca)。这里也借鉴了它 README 以用户操作、兼容性边界和故障排查为中心的组织方式。

安装器源码：[MIT](LICENSE)。上游 PMCA 许可证保留在 [community/LICENSE.txt](community/LICENSE.txt)。各 APK 的权利和许可证归各自作者/权利人，安装器的 MIT 许可不替代应用许可；维护者已确认本集合的发布授权。

**相机安装依赖社区逆向工程，存在兼容性和设备操作风险。请以实际相机结果为准，不把自动化测试等同于安装成功。**
