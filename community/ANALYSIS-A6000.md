# 原安装外壳的静态问题记录

分析对象：`kkkhs/a6000-clean-installer` 的源码提交
`690036cfc38d6df3adb12bcdbe83cc4962617780`。

没有运行原仓库程序、构建、安装或相机握手，也没有下载/拆包已发布 EXE。
下述发现不能直接证明用户下载的 EXE 具备完全相同的文件或行为。

## 1. Windows 依赖缺项（源码确认）

- `main.go:95–104` 的依赖检查/自动补装清单没有 `win32file` / `pywin32`。
- `payload/pmca/pmca/usb/driver/windows/msc.py:8` 必须导入 `win32file`。
- Windows auto/native 在 `payload/pmca/pmca/commands/usb.py:113–116` 先导入 MSC 后端，因此相机使用 MTP 也不能规避这项导入依赖。
- 缺少 pywin32 的 Python 环境会在 USB 访问前失败；重复安装或换 APK 没有帮助。

## 2. 源码内置 Python 缺少启动文件（源码确认）

- 资源清单中没有 `payload/runtime/python-win64/python.exe`。
- `main.go:875–880` 会查找该启动文件并在缺少时回退系统 Python。
- 干净 Windows 无其他 Python 时，在 `main.go:894` 失败。
- `.gitignore:4` 的 `*.exe` 与缺失相关；不推断发布包也一定缺失。

## 3. 旧证书链与新运行时安全策略冲突（静态兼容性推导）

- `payload/pmca/pmca/marketserver/server.py:69` 使用默认 `ssl.wrap_socket` 加载旧证书链。
- 证书链包含 SHA-1 签名，与内置 Python 3.11 / OpenSSL 3 的默认安全策略不兼容，可能在服务初始化时产生 `CA_MD_TOO_WEAK` 等错误。
- Python 3.11 仍有 `wrap_socket`，问题不是 API 在此版本被删除。
- 具体异常未实测。改变 USB 模式或关闭代理不能解决证书加载策略冲突，不应关闭全局 TLS 安全设置。

## 4. 进程退出成功不等于相机预检/安装成功（源码确认）

- `payload/pmca/pmca/commands/usb.py:162–170` 在没有设备或有多台设备时只打印信息并返回 None。
- `infoCommand` 的 `:175–177` 没有设备时没有抛出失败。
- `installCommand` 的 `:220–224` 切换超时只打印错误，可能未安装任何 APK 而正常退出。
- `main.go:584–589` 仅根据进程执行错误判断预检，通过普通退出即可打印 `Camera preflight: OK`。
- `main.go:540–546` 的安装判断同样只检查进程错误，可能将未安装状态向上返回为成功。

## 社区工作副本的处理

`/home/kuanghuangshuo.12/a6000-pmca-community` 基于上游
Sony-PMCA-RE `a82f5baaa8e9c3d9f28f94699e860fb2e48cc8e0`。

- 使用已有的 tlslite-ng 安装后端，不照搬旧 ssl.wrap_socket 路径。
- 写入独立的 pywin32/comtypes 构建依赖与打包说明。
- 个人版列表绕过公共 AppStore；离线版先校验原 APK，在线版从指定 GitHub Release 下载并校验，两者均向 PMCA 传入同一份校验后的字节。
- 明确抛出无设备/错模式/切换超时等安装失败，中文 GUI 保留完整日志。
- 两种版本与逐文件修改见 README-TWO-VERSIONS-ZH.md；Release 尚未创建或上传。

维护者随后明确批准执行与发布。21 个 APK 已导入并校验，两份清单生成，36 项 Python 3.11 模拟测试通过。Windows 构建/冻结启动由仓库 CI 检查，结果以 Release 报告为准；A6000 真机安装尚未验证。
