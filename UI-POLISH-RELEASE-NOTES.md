# Sony PMCA App Installer v0.2.2

为支持 PlayMemories Camera Apps 的 Sony 相机提供 21 项应用目录，支持离线安装、在线下载及中文 / English 切换。

## 本次更新

- 产品展示名统一为 **Sony PMCA App Installer**。A6000 是主要使用场景之一；适用范围以 PMCA 功能和各应用要求为准，不代表所有 Sony 相机都支持。
- 精简界面说明、状态和语言资源文案，删除主界面及每个应用详情中重复的开发状态说明。保留机型/固件适配、传输安全、文件校验和日志隐私提示。
- 新增双语 **关于 / About** 窗口、作者页脚与项目主页入口。
- 作者 / 维护者：**[kkkhs](https://github.com/kkkhs)**。安装后端来自 **[ma1co / Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE)**，署名及许可证保留。
- README 改为用户导向的中文首页与独立英文版本，包含下载选择、步骤、兼容性、故障排查；完整应用目录移到 `docs/APPS.md`。
- 仓库简介、主题标签与下载主页已补齐 Sony、PMCA、摄影、离线及双语相关信息。

仓库地址、EXE 文件名和语言偏好路径保持不变，兼容既有链接和配置。两个 EXE 均含中英文界面，不需要单独语言包。

## 两个版本

- **离线版**：内置 21 个原始 APK，获取应用不需要网络。
- **在线版**：从本仓库公开 Release 下载选中的 APK，下载后校验，普通用户不需要 GitHub 令牌。

本次是文案、展示和文档更新：**APK 内容与签名、下载地址、校验策略及底层相机安装协议没有变化。**

## 验证范围

构建记录、测试结果、两个 EXE 的 SHA-256 及 Windows 界面检查报告见附件。自动化检查与机型实际安装是不同证据；本改造版尚无相机安装实测记录，不把机型示例或应用收录视为真机验证名单。

安装器源码采用 MIT 许可，各 APK 保留其作者、署名和许可。本软件不隶属于 Sony，不是 Sony 官方软件。EXE 未做 Authenticode 签名，请核对下载来源和校验值，不关闭安全软件。

## English

This update introduces **Sony PMCA App Installer** branding, concise bilingual interface text, an About dialog, author attribution (**kkkhs**), and clearer user-oriented README pages. The upstream Sony-PMCA-RE attribution is retained.

The offline edition bundles 21 unchanged APKs. The online edition downloads the selected APK from public GitHub Releases, with integrity verification and no end-user token requirement. The repository URL, EXE filenames and preference location are unchanged. Camera protocols and APK bytes are not modified.

See the attached build/checksum reports for automated verification. Hardware installation has not been recorded for this modified installer; PMCA-capable model examples are not a hardware-tested compatibility list.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
