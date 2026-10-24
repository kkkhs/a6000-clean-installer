"""Friendly summaries accompany, rather than hide or alter, raw PMCA errors."""


def error_hint(error):
    text = str(error).lower()
    if 'no devices found or too many sony devices' in text:
        return '未找到唯一可用的相机。请只连接一台相机，确认相机已开机、数据线可传输数据、USB 模式为 MTP；具体设备数量请查看完整日志。'
    if 'no devices found' in text:
        return '没有找到相机。请确认相机已开机，用可传输数据的 USB 线直连电脑，并将 USB 连接设为 MTP。关闭可能占用相机的照片导入或遥控软件后再试。'
    if 'too many sony devices' in text:
        return '同时发现多台索尼设备。请只保留需要安装的这一台相机连接。'
    if 'timed out' in text or 'timeout' in text:
        return '相机切换或通信超时。请等待相机恢复正常画面，再重新连接；不要在仍传输数据时拔线。'
    if 'unknown location' in text:
        return '相机拒绝了安装任务中的地址。这不是 APK 列表的问题。请保留完整日志，以便检查相机的安装协议与本地服务。'
    if '10048' in text or 'address already in use' in text:
        return '本地安装端口被占用。请关闭其他 PMCA/安装器实例后再试。'
    if '10061' in text or 'connection refused' in text:
        return '无法连接本机安装服务。请先关闭其他安装器，并检查系统或公司安全软件的拦截记录；不要直接关闭防火墙。'
    if 'ssl' in text or 'tls' in text or 'certificate' in text:
        return '本地安装服务的 TLS/证书通信失败。请保留完整错误和运行版本；不要修改全局 TLS 设置或关闭证书校验。'
    if 'win32' in text or 'no module named' in text:
        return '运行依赖缺失。Windows 原生 USB 后端需要 pywin32 和 comtypes；建议在独立虚拟环境按项目依赖文件安装，不要反复重试相机。'
    if 'sendcommand' in text or 'usb' in text or 'access denied' in text:
        return 'USB 通信失败或设备被占用。请关闭其他相机程序，检查数据线和 USB 模式。应用安装通常不需要用 Zadig 替换系统 MTP 驱动。'
    if 'does not support apps' in text:
        return '相机未接受应用安装模式。请记录机型、固件版本及完整日志；本工具不会自动刷固件或修改相机设置。'
    if 'cannot use camera in this mode' in text:
        return '当前 USB 模式不能安装应用。请退出服务/升级模式，恢复正常开机后将 USB 连接设为 MTP。'
    return '这次安装没有完成。请先保留完整日志，检查相机屏幕的提示，再决定下一步；不建议盲目反复重试。'
