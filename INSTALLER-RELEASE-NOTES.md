# A6000 社区 PMCA 中文版 v0.2.0

同一套社区 PMCA 安装后端，两种 Windows x64 安装器：

- **[A6000-PMCA-Offline-ZH.exe](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.0-community/A6000-PMCA-Offline-ZH.exe)**（49.8 MB）：自带 21 个原始 APK 和中文应用列表，获取 APK 不需要联网。
- **[A6000-PMCA-Online-ZH.exe](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.0-community/A6000-PMCA-Online-ZH.exe)**（16.3 MB）：自带相同中文列表，从本仓库公开 `apk-set-v1` Release 下载所选 APK；不需要普通用户提供 GitHub 令牌。

两个 EXE 随 PyInstaller 包含运行时，普通用户不需要单独安装 Python。APK 不修改、不重新签名。每次从列表安装前校验大小和 SHA-256，校验失败不触发相机安装。

## 与原 v0.1.x 外壳的区别

基于 ma1co/Sony-PMCA-RE 源码 `a82f5baaa8e9c3d9f28f94699e860fb2e48cc8e0`，不是原 Go 网页外壳。保留社区 USB/安装协议；增加中文列表及用途、离线/在线应用来源、错误提示和完整日志保存。

Windows 应用版使用系统 native USB 后端。打包包括 pywin32、comtypes 与预生成 WPD 包装，移除了过时 COM 私有导入补丁。没有刷固件、修改相机语言、替换 MTP 驱动或开启公网服务的步骤。

## 使用

1. 相机正常开机、电量充足，以 USB 数据线直连电脑，USB 连接设为 MTP。
2. 关闭其他相机/安装器程序；可以先读取信息，但读取成功不能保证后续安装成功。
3. 从列表选一个应用，点击安装。不是一键把 21 个全部装入相机。
4. 任务结束后，在相机内确认应用名称和版本。失败时保存完整日志和相机屏幕提示，不盲目重试或刷固件。

## 已通过的检查

- Windows x64 / Python 3.11.9 构建成功，36 项模拟测试通过。
- 两个 EXE 均通过 COM、内置 WPD 包装、TLS 证书解析、AES 扩展和 Tk 初始化检查。
- 下载 CI 产物后，静态确认离线 EXE 内确有 21 个 APK，逐个大小和 SHA-256 匹配；在线 EXE 中无 APK，含 21 项清单。
- 实际在线下载路径已验证一个 APK 可匿名下载和校验。
- 源码提交：`5b6ed9e718c36d25d80713858a6c1f8a3d3d3441`；[Windows 构建记录](https://github.com/kkkhs/sony-pmca-app-installer/actions/runs/40084578279)。详细报告见 `BUILD-VERIFICATION.json` 和 self-test 附件。

**尚未完成本次版本的 A6000 真机安装验证或 USB/TLS 握手。冻结检查初始化了 Tk，不等于完整交互界面测试。不能保证全部 APK 在所有固件和已安装应用组合上可用。**

19 个 APK 声明了 zh 资源；Touchless Shutter 和 Recipe Lab 未声明。安装器汉化不会改变相机内 APK 的语言。延时摄影扩展可能有依赖，不建议第一个测试。

APK 的权利归各自权利人；维护者已确认本集合的发布授权。程序基于社区逆向工程成果，存在兼容性与设备操作风险。

校验 EXE 请使用附件 SHA256SUMS.txt。安装器没有代码签名证书，Windows SmartScreen 可能提示未知发布者；请核对下载来源和校验值，不关闭系统安全软件。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
