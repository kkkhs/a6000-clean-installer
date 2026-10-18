# A6000 Clean Installer

这是一个围绕 PMCA v0.11 和 21 个离线 APK payload 做的干净安装外壳。
页面默认中文，并提供 English 切换。

已移除：

- 原易语言外壳。
- Sony Market 登录入口。
- Sony Market 下载路径。
- 内置下载凭据。

保留：

- 本地浏览器 UI。
- 离线 APK 列表。
- PMCA 本地 APK 安装命令。

中文支持结论：

- 已解析每个 APK 的 `resources.arsc` locale 声明。
- 多数原 Sony 应用声明了 `zh` 资源。
- `Touchless Shutter` 只声明 `default/ja`。
- `Recipe Lab v1.9.0` 只声明 `default`。
- 页面列表里会直接显示每个应用的中文支持状态。

运行说明：

Windows 完整版 EXE 自带外壳、离线资源和 Python 运行时，普通用户不需要单独安装 Python。
PMCA 安装动作仍通过内置 Python 执行。若你通过 `A6000_PYTHON` 指定自己的 Python，程序会检查 PMCA 运行时模块：

- certifi
- comtypes
- pycryptodome
- pyusb
- pyyaml

自定义 Python 缺失模块时会自动调用 pip 安装。若自动安装失败，可以手动运行：

```bat
python -m pip install certifi comtypes pycryptodome pyusb pyyaml
```

安装前请用 USB 连接相机。
相机菜单里的 USB 连接建议设为 MTP 或 Auto。程序会先做相机连接预检，再开始安装 APK。
也可以先点击页面上的“检测环境/相机”，确认运行时、依赖和相机连接都正常。

如果日志里出现 `Unknown location`，通常是相机拒绝了安装任务里的下载地址。当前版本已经改为让相机看到 PlayMemories 官方域名，再由 USB 代理转到本机服务。仍然出现时，先重启相机，关闭相机 Wi-Fi，再重新点击安装。

远程清单：

可以把应用清单放在静态 HTTPS 地址，APK 放在支持直链下载的位置。清单格式：

```json
{
  "version": 1,
  "apps": [
    {
      "id": "recipe-lab",
      "name": "Recipe Lab",
      "note": "Sony PMCA app",
      "package": "com.voxivoid.recipelab",
      "versionName": "1.9.0",
      "downloadUrl": "https://example.com/RecipeLab.apk",
      "sha256": "bb6e1b72b84451b5034e311e537bf0cfb255ea78d9f1fe5df937aaf25d8073c7",
      "size": 437000,
      "locales": ["default"],
      "chinese": false,
      "chineseNote": "No zh locale declared."
    }
  ]
}
```

远程安装时会先下载 APK，再校验 `sha256`，校验失败不会安装。

默认远程清单：

把下面这个配置文件放在 `A6000CleanInstaller.exe` 同目录，程序启动时会自动加载：

```json
{
  "catalogUrl": "https://raw.githubusercontent.com/YOUR_NAME/YOUR_REPO/main/a6000-catalog.json"
}
```

文件名必须是：

```text
A6000CleanInstaller.config.json
```

推荐免费方案：

- 清单 JSON：GitHub 仓库里的 `a6000-catalog.json`，用 raw URL。
- APK 文件：GitHub Releases assets。
- 清单里的 `downloadUrl` 写 release asset 下载地址。
- 每次新增应用：上传 APK 到 Release，算 SHA-256，改 JSON 即可；不用重新打包 EXE。

English summary: this is an offline PMCA shell with a Chinese-first local web UI,
21 embedded APK payloads, and no Sony Market login/download path.
