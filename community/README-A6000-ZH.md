# A6000 离线应用列表 · 社区 PMCA 中文个人版

在线下载版、两个打包入口及逐文件修改说明见 [两种版本说明](README-TWO-VERSIONS-ZH.md)。

> **v0.2.0-community 已发布，但不是 Sony 或 ma1co 发布的官方安装包。**
> 21 个 APK 已导入并校验，两份清单已生成，36 项模拟测试、Windows 构建及冻结启动检查通过；尚未完成 A6000 真机安装验证。
> [下载两个版本及验证报告](https://github.com/kkkhs/a6000-clean-installer/releases/tag/v0.2.0-community)
> 此工作副本的上游基线是 Sony-PMCA-RE `a82f5baaa8e9c3d9f28f94699e860fb2e48cc8e0`。

## 为什么这样改

保留社区 Sony-PMCA-RE 的 USB/应用安装实现，仅补充个人离线应用列表、中文说明和更明确的失败反馈。上游新版使用 `tlslite-ng` 处理相机的旧 TLS 协议，不照搬原自制外壳中 Python 3.11 + `ssl.wrap_socket` 的路径，也不修改电脑的全局 TLS 安全策略。

下载量大不等于没有问题。这次改造也不能保证每一个 APK 都适用于你的相机、固件或已安装应用版本。

## 已写入代码的功能

- 默认从 `offline-apps/catalog.json` 加载私人应用列表，不再为这份列表访问 GitHub/AppStore。
- 21 个应用都有中文名称、用途、英文名、版本、包名和语言资源说明。
- 从列表安装前，校验大小和 SHA-256，并将**同一份已校验的字节**直接交给 PMCA，不重新下载 APK。
- 没有找到设备、切换应用模式超时、设备不支持应用或模式错误时抛出明确失败，不把正常返回误当成功。
- 安装结果只有在 PMCA 完成相机任务且未抛异常后才显示成功，并提醒在相机应用列表确认。
- 保留原始错误日志，附中文排查建议，可将完整日志保存到本地。
- 应用安装版不显示固件升级和服务模式操作；安装时禁用并发读取相机信息，并阻止直接关闭窗口。
- 任务结束时释放本机服务器端口。服务仍仅使用 `127.0.0.1`，没有隧道、公共 URL 或系统代理设置。

## 导入已有的 21 个包

发布工作副本已从原 manifest 导入全部 21 个 APK 并校验。源码仓库避免重复提交 APK，重新构建时从根目录 `payload/apps` 导入：

```bash
python tools/import_offline_apps.py /path/to/a6000-clean-installer/payload/apps
```

脚本从原 `manifest.json` 读取 21 个应用，将 APK 原样复制到 `offline-apps/`，计算完整 SHA-256，并生成中文列表。不修改 AndroidManifest、资源、签名或安装包内容；不上传任何文件。

APK 通过 `.gitignore` 排除，避免误提交。应用目录及清单是程序数据，不是上游在线 `apps.yaml`。离线版不需要托管 APK、配置在线清单或修改 ma1co 的公共仓库；在线版使用独立的 `online-apps/catalog.json` 和 GitHub Release 下载模块。

**注意：校验和只能检查本地文件是否与清单一致，不能证明来源、版权授权或签名可信。**

## 应用名称

| 编号 | 中文显示名称 | 原清单英文名称 |
| --- | --- | --- |
| 01 | 延时摄影扩展 | Timelapse add-on |
| 02 | 延时摄影 | Time-lapse |
| 03 | 平滑反射 | Smooth Photo / Smooth Reflection |
| 04 | 实时色彩预设（名称待确认） | LVG preset app |
| 05 | 光绘 | Light Graffiti |
| 06 | 专业包围拍摄 | Bracket tools |
| 07 | 人像美化 | Beauty Effect |
| 08 | 定格动画 | Stop Motion |
| 09 | 照片润饰 | Photo Retouch / EZ Edit |
| 10 | 渐变滤镜 | Graduated Filter |
| 11 | 手动镜头补偿 | Optical Compensation |
| 12 | 增强图片效果 | Effect Master |
| 13 | 非接触快门 | Touchless Shutter |
| 14 | 光线效果 | Light effects |
| 15 | 多重曝光 | Multiple Exposure |
| 16 | 智能遥控 | Smart Remote Control |
| 17 | 运动轨迹 | Motion Shot |
| 18 | 星轨 | Star Trail |
| 19 | 数码滤镜 | Digital Filter |
| 20 | 人像光效 | Portrait Lighting |
| 21 | 影像配方实验室（Recipe Lab） | Recipe Lab |

名称是友好的中文说明，未声称均为 Sony 官方中文产品名。部分原名由资源字符串推断，列表明确保留不确定性。

原清单有 19 个应用声明了 `zh` 资源；非接触快门和 Recipe Lab 没有。中文安装界面**不会汉化相机内的 APK**，也不会更改相机区域或语言设置。

## 无相机测试（36 项已通过）

```bash
python -X utf8 -I -m unittest discover -s tests -v
```

测试针对离线列表、21 个文件完整性、错误清单/重复项/路径越界、GUI 的安装选择及失败反馈。USB 调用使用 mock，不连接或修改相机，不访问远程商店，不启动 HTTP/TLS 服务。

**测试通过也只能验证代码层面，不能代替 Windows 驱动、TLS 握手和 A6000 真机安装。**

## Windows 开发构建

这台主机是 Linux，不能把它的 PyInstaller 输出当作 Windows EXE。最终 Windows 构建和驱动验证必须在 Windows 上完成。

准备独立虚拟环境，先导入 APK，再运行：

```bat
py -3.11 -m venv .venv
.venv\Scripts\python -X utf8 -m pip install -r requirements-offline.txt
.venv\Scripts\python -X utf8 -m unittest discover -s tests -v
.venv\Scripts\python -X utf8 -c "from comtypes.client import GetModule; GetModule('PortableDeviceApi.dll'); GetModule('PortableDeviceTypes.dll')"
.venv\Scripts\python -X utf8 -m PyInstaller --clean --noconfirm pmca-a6000-offline.spec
```

CI 使用 Windows x64 / Python 3.11，固定 comtypes 1.4.17 和 PyInstaller 6.22.3，同环境预生成 WPD 包装并收集进冻结包。删除了旧的私有导入补丁；应用 GUI 明确使用 Windows native 驱动，避免没有 libusb DLL 的自动回退。完整构建依赖版本保留在 Release 报告中。不要执行上游老的 CI 下载步骤来替换本机 USB 驱动。

打包目标为 `dist/A6000-PMCA-Offline-ZH.exe`。spec 在打包前检查完整清单及每个 APK 的 SHA-256，打包数据含应用和证书；包括 `pywin32`/`comtypes` 原生 Windows USB 依赖。没有复制原自制外壳的残缺 Python 目录。

## 真机验证顺序

1. 电量充足，使用能传数据的 USB 线，直连电脑；相机正常开机，USB 连接设为 MTP。
2. 关闭其他相机遥控、照片导入及安装器程序，不要同时运行两个 PMCA 实例。
3. 先读取相机信息并记录机型、固件版本。读取成功不等于安装必定成功。
4. 只选择一个适用于相机的应用测试。不要先测试需要其他应用的延时摄影扩展，不做 21 个包自动批量安装。
5. 保留完整日志及相机屏幕提示；任务结束后在相机应用列表核验名称和版本。
6. 出错后先分析日志，不恢复出厂设置、不刷固件、不盲目替换系统 MTP 驱动、不关闭防火墙或全局证书验证。

对外发送日志前，删除可能出现的相机序列号、账户字段和个人路径。

## 许可与边界

上游源码的 MIT 许可不等于 APK 的再分发授权。维护者已确认这批文件的发布授权，并选择公开 `kkkhs/a6000-clean-installer`；普通用户从公开 Release 下载无需令牌。APK 的权利仍归各自权利人。最新 Release 和实际构建验证状态以仓库首页及 Release 报告为准。

源码改造与实际发行包是两种证据。未下载/拆包验证原 `A6000CleanInstaller-full.exe`，不能断言它包含的文件和源码完全一致。当前改造的成功率也尚未实测。
