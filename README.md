# A6000 应用安装器 · 社区 PMCA 中文 / English

基于 [ma1co/Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE) 的个人双语改造：同一套安装后端，两种 APK 获取方式，均包含 **21 项应用列表和中文 / English 切换**。

> **v0.2.1-community 双语版已发布：两个安装器均支持中文 / English，Windows 构建和实际界面切换检查通过。** 21 个原始 APK 保持不变，独立发布在 `apk-set-v1`。
> 这不是 Sony 或 ma1co 官方发布的安装器。尚未完成这次改造的 A6000 真机安装验证，不能保证所有 APK 在每台相机、固件及已有应用版本上均可安装。
> 仓库原 `v0.1.x` Go 网页外壳保留供参考；它存在依赖和成功判断问题，不是下面的新社区版本。

## 两个版本

| 版本 | APK 从哪里来 | 是否需要网络或 GitHub 令牌 |
| --- | --- | --- |
| **[下载离线完整版](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/A6000-PMCA-Offline-ZH.exe)**（49.8 MB） | 21 个 APK 原样打包在 EXE 内，选中一个直接安装 | 获取 APK 不需要网络，不需要令牌 |
| **[下载在线下载版](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/A6000-PMCA-Online-ZH.exe)**（16.4 MB） | EXE 内置相同 21 项清单，选中后从本仓库公开 Release 下载 | 首次下载需要网络；公开 Release 不需要令牌；校验正确的缓存可复用 |

两个 Windows x64 EXE 都随 PyInstaller 包含运行时，普通用户不需要另外安装 Python。两者均通过 USB 由社区 PMCA 安装，不刷固件、不自动安装全部 21 个应用、不登录 Sony Market。

- [安装器 Release：v0.2.1-community（已发布）](https://github.com/kkkhs/a6000-clean-installer/releases/tag/v0.2.1-community)
- [EXE SHA-256 校验文件](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/SHA256SUMS.txt)
- [构建和资源验证报告](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/BUILD-VERIFICATION.json)
- [21 个原始 APK 与在线清单：apk-set-v1（已发布，可匿名下载）](https://github.com/kkkhs/a6000-clean-installer/releases/tag/apk-set-v1)
- [完整变更与两种版本设计](community/README-TWO-VERSIONS-ZH.md)
- [离线版开发和验证说明](community/README-A6000-ZH.md)

## 中文 / English 切换

点击窗口右上角 **English / 中文**，无需重启。按钮、标签页、应用名称/用途/备注、状态、下载提示和友好错误建议随语言切换，保留当前选中的应用、本地 APK 路径及模式。

默认中文，记住上次语言选择；偏好保存在当前用户配置目录 `A6000-PMCA/preferences.json`（Windows 的 `LOCALAPPDATA`），不写入 EXE 目录。两种版本共用偏好。相机通信期间暂时禁用语言切换，既有日志和底层 PMCA 原始输出不事后翻译。

Both installer profiles support **Chinese and English**. Click **English / 中文** at the top right to switch without restarting. Your language preference, selected app and local APK path are preserved. No GitHub login or token is required to download from this public repository. Interface translation does not translate APKs or change camera settings.

详见 [双语界面说明 / Language guide](community/README-BILINGUAL.md)。文件名保留 `-ZH.exe` 以兼容既有命名，两个 EXE 都包含中英文，不是两个不同语言的安装包。

## 使用方法

1. 下载并启动需要的 Windows 版本；无需登录 GitHub，不用配置令牌。
2. 相机电量充足，正常开机，用支持数据传输的 USB 线直连电脑；USB 连接设为 **MTP**。
3. 关闭其他 PMCA、相机遥控或照片导入程序。可以先在“相机信息”页读取信息；**读取成功不代表安装链路一定成功**。
4. 在应用列表中选择一个应用，查看中文用途、英文名、版本和语言说明，点击“安装选中的应用”。
5. 离线版校验内置 APK；在线版下载所选 APK 并校验大小和 SHA-256。校验失败不会开始相机安装。
6. 等任务结束后，在相机应用列表里确认应用名称和版本。失败时保存完整日志，并记录相机屏幕提示。

不要在相机传输过程中拔线。不要因安装失败就恢复出厂设置、刷固件、关闭防火墙、改全局证书安全设置或用 Zadig 替换系统 MTP 驱动。

EXE 没有 Authenticode 代码签名，Windows SmartScreen 可能提示未知发布者。请先核对仓库来源和 SHA-256，不关闭系统安全软件。

日志可能含相机序列号、个人路径或账户字段，对外发送前请先脱敏。该程序的安装服务仅监听电脑回环地址，不对外发布。

## 21 项应用列表

中文名称是友好的说明，不保证都是 Sony 官方中文名称。部分用途源自原资源字符串推断，界面保留不确定性；**列入清单不代表已通过 A6000 真机验证**。

| 编号 | 中文显示名称 | 英文名 | 版本 |
| --- | --- | --- | --- |
| 01 | 延时摄影扩展 | Timelapse add-on | 1.00 |
| 02 | 延时摄影 | Time-lapse | 3.40 |
| 03 | 平滑反射 | Smooth Photo / Smooth Reflection | 1.10 |
| 04 | 实时色彩预设（名称待确认） | LVG preset app | 1.20 |
| 05 | 光绘 | Light Graffiti | 1.00 |
| 06 | 专业包围拍摄 | Bracket tools | 1.40 |
| 07 | 人像美化 | Beauty Effect | 1.30 |
| 08 | 定格动画 | Stop Motion | 1.00 |
| 09 | 照片润饰 | Photo Retouch / EZ Edit | 1.30 |
| 10 | 渐变滤镜 | Graduated Filter | 1.00 |
| 11 | 手动镜头补偿 | Optical Compensation | 2.40 |
| 12 | 增强图片效果 | Effect Master | 1.30 |
| 13 | 非接触快门 | Touchless Shutter | 1.00 |
| 14 | 光线效果 | Light effects | 1.20 |
| 15 | 多重曝光 | Multiple Exposure | 1.20 |
| 16 | 智能遥控 | Smart Remote Control | 4.30 |
| 17 | 运动轨迹 | Motion Shot | 1.40 |
| 18 | 星轨 | Star Trail | 1.50 |
| 19 | 数码滤镜 | Digital Filter | 1.00 |
| 20 | 人像光效 | Portrait Lighting | 1.10 |
| 21 | 影像配方实验室 | Recipe Lab | 1.9.0 |

19 个 APK 声明了 `zh` 资源；非接触快门和 Recipe Lab 没有声明。**安装器中文说明不会修改 APK、汉化相机内应用或解锁相机语言。** 延时摄影扩展可能有依赖，不建议作为第一个安装测试。

## 在线文件如何管理

本仓库现在是公开的，公开 Release APK 可匿名下载，不需要普通用户提供 GitHub 令牌。

- `apk-set-v1`：21 个原始 APK 独立 assets，外加包含名称、版本、大小、完整 SHA-256 和固定下载地址的 `catalog.json`。
- `v0.2.1-community`：离线 EXE、在线 EXE、SHA256SUMS 和构建验证报告。
- 更新 APK 时使用新的固定内容 tag，更新清单，不静默替换固定版本文件。
- 在线版可将可信的新清单放在 EXE 同目录的 `online-apps/catalog.json`，无需重打 EXE 更新列表。程序目前不自动追踪最新远程清单。
- 维护者上传用的 GitHub 凭据不打包进任何 EXE/清单。保留的私有仓库支持仅在自行部署私有 Release 时需要用户自己的 `A6000_GITHUB_TOKEN`。

SHA-256 检查文件一致性，不代表清单或 APK 来源可信；只使用可信维护者提供的清单。

## 源码与构建

```text
community/                        社区中文改造源码
  pmca-gui.py                     共用中文 GUI
  pmca/{catalog,offline,online}.py 两种应用来源
  tools/                          21 APK 导入及在线清单生成
  pmca-a6000-{offline,online}.spec  两个打包入口
payload/apps/                     原始 21 个 APK 和 manifest
.github/workflows/                 Windows 构建、模拟测试和冻结启动检查
main.go + payload/pmca/            原 v0.1.x 外壳（历史参考）
```

上游源码基线：`a82f5baaa8e9c3d9f28f94699e860fb2e48cc8e0`。46 项 Python 3.11 模拟和语言测试、Windows x64 构建通过。两个冻结 EXE 均通过 COM/WPD、TLS 证书解析、AES 依赖及实际 GUI 中文→英文→中文切换检查，确认应用选择、本地 APK 路径/模式与状态保留。语言偏好保存、恢复和无效配置回退也有单元测试覆盖。APK 的包名、版本和证书结构已解析；离线包中的 21 个 APK 逐一核对大小与 SHA-256，在线包不含 APK。实际在线下载路径已验证一个 APK 可匿名下载并校验。

没有连接或修改相机。GUI 自动化检查不等于完整人工界面测试，也不能证明相机 USB/TLS 握手或应用安装成功。详细结果附在安装器 Release。

Windows 构建状态见 [GitHub Actions](https://github.com/kkkhs/a6000-clean-installer/actions/workflows/community-windows.yml)。维护者上传和构建凭据不会写入安装器；普通用户下载公开 Release 不需要 GitHub 令牌。

模拟测试、APK 校验或 GUI 启动都不能代替相机实际安装。

## 许可和风险

上游 PMCA 和本项目源码采用 MIT 许可，保留上游许可证。APK 的权利归各自权利人，源码许可证不替代 APK 的许可；本仓库维护者已确认这批文件的发布授权。

相机通信基于社区逆向工程成果，存在兼容性和硬件操作风险。遇到失败先分析日志，不承诺安装成功率。原外壳的静态问题见 [分析记录](community/ANALYSIS-A6000.md)。
