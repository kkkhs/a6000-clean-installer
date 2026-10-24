# Sony PMCA App Installer v0.2.3

修复 Windows 冻结发行包在本地 TLS 握手时发生的纯 Python AES 初始化异常。两个版本仍提供相同的 21 项应用目录与中文 / English 界面。

## 修复内容

用户提供的完整日志显示：

```text
tlslite → cipherfactory.createAES → python_aes → deprecations.py
TypeError: 'NoneType' object is not iterable
Communication error 201: Error completed (SSL error)
```

该问题可在缺少调用处 Python 源码的环境中复现。`tlslite-ng` 的兼容旧类名装饰器会读取调用处源码，原 PyInstaller 构建只收集字节码，使源码上下文为空并触发崩溃。本地服务失败后，相机返回 SSL 201。

- 两个构建 spec 保留 TLS 依赖的 `.py` 源码，TLS 依赖固定为 `tlslite-ng==0.8.2`。
- 新增 TLS 纯 Python AES-CBC 已知答案测试。
- 新增实际本地 TLS 1.0 / 1.2、加密 HTTP、安装动作及 SPK 内容往返测试。
- 两个最终 Windows EXE 均须通过上述回归检查，而不只是检查证书解析或 Cryptodome 扩展。
- 调整双语 TLS 提示，避免仅凭 SSL 错误认定为证书故障。
- 本次构建采用更名后的仓库地址；EXE 文件名和语言配置路径不变。

**PMCA 原有 USB 安装协议、TLS 证书、正常握手设置及 APK 内容保持不变。** 内置应用、在线缓存和手动 APK 都使用同一安装后端，均会经过本地 TLS 服务。

详细证据：[SSL 201 打包兼容性分析](https://github.com/kkkhs/sony-pmca-app-installer/blob/main/docs/TLS-201.md)。201 是通用 SSL 失败结果；不能将所有 201 都归因于本次修复。

## 两个版本

- **[下载离线版 · 50.1 MB](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.3-community/A6000-PMCA-Offline-ZH.exe)**：内置全部 21 个原始 APK。
- **[下载在线版 · 16.6 MB](https://github.com/kkkhs/sony-pmca-app-installer/releases/download/v0.2.3-community/A6000-PMCA-Online-ZH.exe)**：下载选定 APK 后校验，公开下载不需要 GitHub 令牌。

## 验证与边界

- **51 项本地和 Windows 自动化测试通过。**
- 两个最终 Windows EXE 均通过 TLS 1.0 / 1.2、加密 HTTP、SPK 数据往返及界面检查。
- 静态核对两个 EXE 中的 TLS 源码、证书和应用清单；离线版 21 个 APK 的字节与原始副本一致，在线版不包含 APK。
- 构建源码：`bc067b04f4b082a3b93f7330a9438efd761d6304`；[Windows 构建与 TLS 回归](https://github.com/kkkhs/sony-pmca-app-installer/actions/runs/40096001822)。

完整结果见附件 `BUILD-VERIFICATION.json`、`self-test-Offline.json`、`self-test-Online.json` 和 `SHA256SUMS.txt`。本地 TLS 对端测试用于排除已复现的运行时崩溃，不证明真实相机接受证书、USB 通信或应用安装成功。

程序仅在 loopback 提供本地安装服务。不需要关闭防火墙、系统安全软件或证书校验。Windows SmartScreen 的未知发布者提示与本次 TLS 运行时异常是不同问题；EXE 仍未使用 Authenticode 签名。

作者 / 维护者：**[kkkhs](https://github.com/kkkhs)**。安装后端：**[ma1co / Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE)**。本项目不隶属于 Sony，不是 Sony 官方软件；APK 保留各自署名与许可。

## English

This release fixes a frozen-runtime Python AES exception behind the matching SSL 201 log. tlslite-ng 0.8.2 inspects caller source during AES initialization; bytecode-only packaging made that source unavailable and caused a `NoneType` iteration failure.

Both Windows installers retain TLS source and run actual loopback TLS 1.0 / 1.2, encrypted HTTP and SPK round-trip checks inside the final EXEs. Sony USB protocols, certificates, normal server settings and the 21 APKs are unchanged. TLS guidance no longer treats every SSL failure as a certificate rejection.

See the attached build and checksum reports. Synthetic TLS tests do not establish camera certificate trust or hardware installation success. This fix is unrelated to Windows SmartScreen publisher reputation; executables remain unsigned. Do not disable security protections.
