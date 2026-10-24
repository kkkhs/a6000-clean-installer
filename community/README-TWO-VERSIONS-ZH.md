# 两个版本：自带离线 APK / GitHub Release 在线下载

> 21 个 APK 已导入并逐一校验，两份清单已生成，36 项 Python 3.11 模拟测试通过。
> Windows 构建和冻结启动由仓库 CI 检查；成品下载及实际检查报告以仓库首页和 Release 为准。尚未完成 A6000 真机安装验证。

## 大的变化

不是重新实现 USB 协议，不是修改 ma1co 的公共 AppStore，也不是修改已下载的官方 EXE。
这是 Sony-PMCA-RE 源码的独立个人工作副本：

1. 保留社区 PMCA 的 USB/安装协议与现有 tlslite-ng 后端。
2. 用我们自己的 21 项中文应用清单取代个人版 GUI 的公共在线列表入口。
3. 共用一套中文界面、校验、原始错误日志和安装失败反馈。
4. 根据打包模式，从内置文件或 GitHub Release 取得所选 APK。
5. 一次只安装选中的一个应用，不自动把 21 个全部装入相机。

## 两个成品的预期差别

| 项目 | 自带 APK 离线版 | GitHub Release 在线版 |
| --- | --- | --- |
| 目标文件名 | `A6000-PMCA-Offline-ZH.exe` | `A6000-PMCA-Online-ZH.exe` |
| 应用列表 | 自带 21 项中文清单 | 自带相同 21 项中文清单及固定 Release 地址 |
| APK 文件 | 21 个原始 APK 随 EXE 打包 | EXE 内不包含 APK，文件在维护者 GitHub Release |
| 首次安装 | 不联网 | 下载选中的一个 APK，再校验和安装 |
| 后续安装 | 使用内置文件 | SHA-256 正确的下载缓存可以复用 |
| 更新 | 修改清单/包后重新打离线包 | 新 Release + 更新在线清单；可使用 EXE 同目录清单替换 |
| Python | PyInstaller 的运行时随安装器打包 | 同左，不要求普通用户另装 Python |
| 相机通信 | 社区 PMCA，回环地址本地服务 | 同左，GitHub 只负责提供 APK |

两个版本不会共用模糊的“有网就在线、没网就离线”行为。冻结 EXE 的模式由自己的 build_profile 固定。源代码启动则默认离线，`python pmca-gui.py --online` 选择在线。

## 逐文件说明

### 修改社区已有文件

| 文件 | 修改 |
| --- | --- |
| `pmca-gui.py` | 中文应用列表/用途/提示；支持离线和在线模式；选中应用先取得并校验 APK，再调用原 installCommand；保留完整日志及中文失败弹窗；保存日志；安装和读取信息不能并发；应用专用 GUI 隐藏固件/服务模式入口；修复无控制台时 flush 的空对象问题。 |
| `pmca/commands/usb.py` | 只改变失败反馈和返回值：没有唯一设备、不支持应用、切换超时、模式错误时明确抛异常；成功返回原 installApp 结果。不重写设备发现、USB 指令或安装协议。读取信息无设备时也明确失败。 |
| `pmca/marketserver/server.py` | 任务退出时在 shutdown 后补 server_close，释放监听端口。不改 TLS 实现/证书或绑定地址。 |
| `.gitignore` | 排除 `offline-apps/*.apk`，避免将根目录已有的 APK 再重复提交一份；发布为独立 Release assets。 |
| `pmca/usb/driver/windows/wpd.py` | 删除旧 comtypes 私有导入补丁，由固定版本 comtypes 自行处理缓存；构建前预生成 COM 包装。GUI 在 Windows 明确使用 native，不依赖 libusb 自动回退。 |

### 新增功能文件

| 文件 | 职责 |
| --- | --- |
| `pmca/offline.py` | 本地应用对象、中文详情、清单验证、路径限制、大小/SHA-256 校验；返回同一份已校验字节。两种版本共用元数据验证。 |
| `pmca/online.py` | GitHub Release 固定版本 APK 下载、校验、缓存；下载失败不访问 USB；公开 Release 直连，私有 Release 使用用户环境变量令牌通过 API 下载；跨主机重定向不携带令牌，只允许 GitHub 官方 HTTPS 下载主机。 |
| `pmca/catalog.py` | 根据构建模式选择离线或在线清单；在线版可读取 EXE 同目录 `online-apps/catalog.json`，用于更新列表。 |
| `pmca/friendly.py` | 将 USB、TLS、超时、依赖等错误附上友好的中文排查建议，原始 traceback 不被替换。 |
| `tools/import_offline_apps.py` | 从原 manifest 导入全部 21 项中文说明，原样复制 APK，生成离线清单和完整校验值。不执行 APK，不上传。 |
| `tools/export_online_catalog.py` | 从已校验的离线清单生成相同 21 项在线清单，为每个 APK 增加 OWNER/REPO、固定 tag 对应的 Release URL。不创建或上传 Release。 |

### 新增构建、验证和说明文件

| 文件 | 职责 |
| --- | --- |
| `pmca-a6000-offline.spec` | 打包中文 GUI、证书、21 项清单和 21 个 APK；打包前校验文件；输出 Offline EXE。 |
| `pmca-a6000-online.spec` | 只打包中文 GUI、证书和在线清单；不打包 APK；输出 Online EXE。 |
| `packaging/frozenversion.py` | 个人改造的版本标识，不冒充官方发行版本。 |
| `packaging/offline/build_profile.py` | 固定离线 EXE 模式。 |
| `packaging/online/build_profile.py` | 固定在线 EXE 模式。 |
| `requirements-offline.txt` | 两种个人构建共用的开发依赖输入，包含 pywin32/comtypes 与 PyInstaller；尚非实测锁定环境。 |
| `tests/test_offline.py` | 离线校验、完整 21 项集合、GUI/安装失败分支；USB 用 mock，已通过。 |
| `tests/test_online.py` | 在线列表、模拟下载/缓存、SHA-256 失败、私有 Release、令牌重定向防泄漏测试；网络用 mock，已通过。 |
| `ANALYSIS-A6000.md` | 原自制外壳的源码问题、证据和验证边界。 |
| `README-A6000-ZH.md` | 离线版细节、中文应用名、开发构建和真机验证说明。 |
| `README-TWO-VERSIONS-ZH.md` | 本文件：两个版本设计、逐文件修改和 Release 管理方式。 |

## 重新构建两个版本

先导入一次 21 个原始 APK：

```bash
python tools/import_offline_apps.py /path/to/a6000-clean-installer/payload/apps
```

然后为在线版生成同一批 APK 的 Release 地址：

```bash
python tools/export_online_catalog.py --repo kkkhs/a6000-clean-installer --tag apk-set-v1
```

维护者已选择公开 `kkkhs/a6000-clean-installer`。固定 tag 便于追溯，不用 latest 地址静默替换 APK。清单的版本、大小和 SHA-256 与这一批文件一致。

先安装构建依赖、导入 APK、运行测试，并在同一 Windows 构建环境预生成两份 WPD COM 包装，再生成两个 EXE：

```bat
.venv\Scripts\python -m PyInstaller --clean --noconfirm pmca-a6000-offline.spec
.venv\Scripts\python -m PyInstaller --clean --noconfirm pmca-a6000-online.spec
```

此 Linux 主机不能替代 Windows 驱动/打包/启动验证。仓库的 Windows CI 负责构建两个 EXE，并用 --self-test 检查冻结导入、21 项清单、APK 元数据及 Tk 创建/销毁，不连接相机。

## GitHub Release 文件组织建议

将 APK 内容版本与安装器版本分开：

```text
Release: apk-set-v1
  21 个原文件名的 APK assets
  catalog.json（21 项中文在线清单；每项含 versionName、size、sha256、downloadUrl）

Release: installer-vX.Y.Z（在构建和验证以后）
  A6000-PMCA-Offline-ZH.exe
  A6000-PMCA-Online-ZH.exe
  SHA256SUMS.txt
```

当前下载器不会自动拉取最新版远程清单。在线 EXE 内置已知清单，或显式使用 EXE 同目录的 `online-apps/catalog.json` 替换。这样更容易知道安装的是哪一版本。

上传行为是独立步骤：生成 URL 并不代表文件已经上传，未上传的 URL 会返回 404。实际发布状态以本仓库的 apk-set-v1 和 v0.2.0-community Release 为准。

### 公开与私有 Release

- **公开 Release**：无令牌直接下载，但上传前必须确认 APK 再分发授权，源码 MIT 许可不能替代 APK 授权。
- **私有 Release**：直接浏览器链接通常不能匿名下载。支持用户自己的 `A6000_GITHUB_TOKEN`，经 GitHub API 查询资产再下载。
- 不把维护者 PAT、账号密码或浏览器 cookie 打进任何 EXE/清单。私有访问令牌仅在运行时读取，初始请求只发给 `api.github.com`，不在日志显示，也不转发到资产 CDN。
- 更新本地清单同时会更新信任来源；哈希不能证明清单本身可信。只接收可信维护者的清单，并遵守账号/组织的访问权限要求。

### 验证边界

- 21 个原始 APK 导入和完整性校验、两份清单生成、36 项模拟测试已完成。
- 维护者确认发布权限，并授权将当前仓库公开；普通下载不需要令牌。
- Windows 构建、冻结启动及依赖报告附在 Release，未通过不发布 EXE。
- A6000 真机安装尚未验证。失败时保留日志，不盲目重复安装。
