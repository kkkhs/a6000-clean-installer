# A6000 社区 PMCA v0.2.1 · 中文 / English

离线版和在线版均加入 **中文与英文实时切换**：

- 窗口右上角点击 `English` / `中文`，无需重启。
- 切换按钮、标签页、21 个应用名称/说明、状态、下载提示及错误建议。
- 记住上次语言选择，保存到当前用户的 `A6000-PMCA/preferences.json`，不写入安装器目录。
- 切换语言时保留选中的应用和本地 APK 模式；相机通信期间暂时禁用切换，避免一条任务混用两种语言。
- 已产生的日志不事后重写；底层 PMCA 原始输出仍保留原文，便于排错。
- 兼容旧清单：若外部清单没有英文用途/备注，英文界面显示明确的回退说明，而不是默默显示中文。

## 两个版本

- **[下载离线版 · 49.8 MB](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/A6000-PMCA-Offline-ZH.exe)**：自带 21 个原始 APK 和双语列表，获取应用不需要联网。
- **[下载在线版 · 16.4 MB](https://github.com/kkkhs/a6000-clean-installer/releases/download/v0.2.1-community/A6000-PMCA-Online-ZH.exe)**：自带相同双语列表，从公开 `apk-set-v1` Release 下载选中的 APK，普通用户无需 GitHub 令牌。

文件名沿用 `-ZH.exe`，两个 EXE 都支持中文和英文；无需分别下载语言包。

本次只改语言呈现、应用说明元数据和测试。**21 个 APK 的字节、签名、版本、大小与 SHA-256 不变；底层相机安装协议不变。**

## 已通过的检查

- 本地及 Windows 环境的 **46 项模拟和语言测试**。
- 两个 Windows x64 EXE 构建成功，实际 GUI 中文→英文→中文切换检查通过；应用选择、本地 APK 路径/模式和状态保留，相机通信期间禁用切换。
- 冻结 COM/WPD 包装、TLS 证书解析、AES 扩展和 APK 资源检查通过。
- 构建源码：`a155cde100ca29569695381e945d9850c3e13200`；[Windows 构建与切换检查](https://github.com/kkkhs/a6000-clean-installer/actions/runs/40090020789)。
- EXE 校验值、详细结果及边界见 Release 的 `SHA256SUMS.txt`、`BUILD-VERIFICATION.json` 和 self-test 附件。

自动化 GUI 检查不等于所有交互均经过人工验证。

**尚未完成 A6000 真机安装或 USB/TLS 握手验证。** 界面语言切换不会汉化相机内 APK 或更改相机语言。建议一次测试一个应用，失败时保留完整日志和相机屏幕提示。

EXE 未进行 Authenticode 签名；Windows 可能提示未知发布者。请核对来源与 SHA-256，不关闭系统安全软件。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
