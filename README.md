# A6000 Clean Installer

一个面向 Sony A6000 / PMCA 应用安装的干净外壳。

公开版不内置 Sony 官方 APK。它默认加载本仓库的远程清单，目前公开清单只包含可公开引用的 Recipe Lab。你也可以放一个 `A6000CleanInstaller.config.json` 到 EXE 同目录，指向自己的清单 URL。

## 下载使用

1. 从 GitHub Release 下载 `A6000CleanInstaller.exe`。
2. Windows 上安装 Python 3。
3. 双击 EXE，浏览器会打开本地页面。
4. 首次安装时，程序会自动检查并安装 PMCA 运行时模块：`certifi`、`comtypes`、`pycryptodome`、`pyusb`、`pyyaml`。
5. USB 连接相机后，点击应用卡片上的安装按钮。

如果自动依赖安装失败，可手动运行：

```bat
python -m pip install --user --upgrade certifi comtypes pycryptodome pyusb pyyaml
```

## 远程清单

清单必须是 HTTPS URL，格式见 [`catalog/remote-catalog-template.json`](catalog/remote-catalog-template.json)。

每个应用需要提供：

- `id`
- `name`
- `downloadUrl`
- `sha256`

安装远程应用时，程序会先下载 APK，再校验 SHA-256，校验失败不会安装。

## 免费托管方案

- 清单 JSON：放在 GitHub 仓库里，用 raw URL。
- APK：放在 GitHub Releases assets。
- 更新应用：上传 APK，计算 SHA-256，修改清单 JSON；不用重新打包 EXE。

## 授权说明

本仓库的 Go 外壳使用 MIT License。内置的 PMCA 源码来自 ma1co/Sony-PMCA-RE，保留其 MIT License。

本仓库不再分发 Sony 官方 APK。`catalog/sony-apps-reference.json` 只保留应用元数据，方便你维护自己的私有清单。
