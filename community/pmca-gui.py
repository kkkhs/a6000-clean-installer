#!/usr/bin/env python3
"""A simple gui interface"""
import sys
import traceback
import webbrowser

import config
from pmca.catalog import build_mode, load_app_list
from pmca.friendly import error_hint
from tkinter.messagebox import showerror, showwarning
from tkinter.filedialog import asksaveasfilename
from pmca.commands.usb import *
from pmca.platform.backend.senser import *
from pmca.platform.backend.usb import *
from pmca.platform.tweaks import *
from pmca.ui import *

if getattr(sys, 'frozen', False):
 from frozenversion import version
else:
 version = None

class PrintRedirector(object):
 """Redirect writes to a function"""
 def __init__(self, func, parent=None):
  self.func = func
  self.parent = parent
 def write(self, str):
  if self.parent:
   self.parent.write(str)
  self.func(str)
 def flush(self):
  if self.parent:
   self.parent.flush()


class AppLoadTask(BackgroundTask):
 def doBefore(self):
  self.ui.setAppList([])
  self.ui.appLoadButton.config(state=DISABLED)

 def do(self, arg):
  try:
   print('')
   apps = load_app_list()
   source = '离线应用，无需下载' if build_mode() == 'offline' else '在线应用，安装时从 GitHub Release 下载'
   print('已加载 %d 个%s。' % (len(apps), source))
   return apps
  except Exception as error:
   print('应用清单加载失败：%s' % error)
   traceback.print_exc()

 def doAfter(self, result):
  self.ui.setAppList(result or [])
  self.ui.appLoadButton.config(state=DISABLED if self.ui.master.busy else NORMAL)


class InfoTask(BackgroundTask):
 """Task to run infoCommand()"""
 def doBefore(self):
  self.ui.master.setBusy(True)

 def do(self, arg):
  try:
   print('正在读取相机信息；这一步不会安装 APK。')
   infoCommand(driverName='native' if sys.platform == 'win32' else None)
   print('能够读取信息不代表 APK 安装链路一定可用。')
  except Exception as error:
   print('读取相机信息失败：%s\n建议：%s' % (error, error_hint(error)))
   traceback.print_exc()

 def doAfter(self, result):
  self.ui.master.setBusy(False)


class InstallTask(BackgroundTask):
 """The exact verified local bytes are handed to the upstream USB installer."""
 def doBefore(self):
  self.ui.master.setBusy(True)
  self.ui.statusVar.set('正在安装，请勿关闭程序或断开相机。')
  return self.ui.getMode(), self.ui.getSelectedApk(), self.ui.getSelectedApp()

 def do(self, args):
  (mode, apkFilename, app) = args
  try:
   print('')
   if mode == self.ui.MODE_APP and app:
    print('正在校验并安装：%s（%s）' % (app.name, app.english_name))
    with app.open_verified() as f:
     installCommand(driverName='native' if sys.platform == 'win32' else None, apkFile=f)
   elif mode == self.ui.MODE_APK and apkFilename:
    with open(apkFilename, 'rb') as f:
     installCommand(driverName='native' if sys.platform == 'win32' else None, apkFile=f)
   else:
    raise ValueError('请先从列表选择一个应用，或打开一个 APK 文件。')
   print('相机已返回安装任务成功。请在相机的应用列表中确认。')
   return True, '相机已返回安装任务成功，请在相机内确认。'
  except Exception as error:
   hint = error_hint(error)
   print('安装未完成：%s\n建议：%s' % (error, hint))
   traceback.print_exc()
   return False, hint

 def doAfter(self, result):
  success, message = result
  self.ui.statusVar.set(message)
  self.ui.master.setBusy(False)
  if not success:
   showerror('安装未完成', message + '\n\n完整错误保留在下方日志中。', parent=self.ui.master)


class FirmwareUpdateTask(BackgroundTask):
 """Task to run firmwareUpdateCommand()"""
 def doBefore(self):
  self.ui.fwUpdateButton.config(state=DISABLED)
  return self.ui.getSelectedDat()

 def do(self, datFile):
  try:
   if datFile:
    print('')
    with open(datFile, 'rb') as f:
     firmwareUpdateCommand(f)
  except Exception:
   traceback.print_exc()

 def doAfter(self, result):
  self.ui.fwUpdateButton.config(state=NORMAL)


class StartPlatformShellTask(BackgroundTask):
 def doBefore(self):
  self.ui.startUpdaterShellButton.config(state=DISABLED)
  self.ui.startSenserShellButton.config(state=DISABLED)

 def do(self, arg):
  try:
   print('')
   self.start()
  except Exception:
   traceback.print_exc()

 def start(self):
  pass

 def launchShell(self, backend):
  backend.start()
  tweaks = TweakInterface(backend)

  if next(tweaks.getTweaks(), None):
   endFlag = threading.Event()
   root = self.ui.master
   root.run(lambda: root.after(0, lambda: TweakDialog(root, tweaks, endFlag)))
   endFlag.wait()
  else:
   print('No tweaks available')

  backend.stop()

 def doAfter(self, result):
  self.ui.startUpdaterShellButton.config(state=NORMAL)
  self.ui.startSenserShellButton.config(state=NORMAL)


class StartUpdaterShellTask(StartPlatformShellTask):
 """Task to run updaterShellCommand() and open TweakDialog"""
 def start(self):
  updaterShellCommand(complete=lambda dev: self.launchShell(UsbPlatformBackend(dev)))


class StartSenserShellTask(StartPlatformShellTask):
 """Task to run senserShellCommand() and open TweakDialog"""
 def start(self):
  senserShellCommand(complete=lambda dev: self.launchShell(SenserPlatformBackend(dev)))


class TweakApplyTask(BackgroundTask):
 """Task to run TweakInterface.apply()"""
 def doBefore(self):
  self.ui.setState(DISABLED)

 def do(self, arg):
  try:
   print('Applying tweaks...')
   self.ui.tweakInterface.apply()
  except Exception:
   traceback.print_exc()

 def doAfter(self, result):
  self.ui.setState(NORMAL)
  self.ui.cancel()


class MainUi(UiRoot):
 """Main window"""
 def __init__(self, title):
  UiRoot.__init__(self)

  self.title(title)
  self.geometry('760x800')
  self.minsize(660, 680)
  self['menu'] = Menu(self)
  self.busy = False
  self.protocol('WM_DELETE_WINDOW', self.closeWindow)

  tabs = Notebook(self, padding=5)
  tabs.pack(fill=X)
  self.infoFrame = InfoFrame(self, padding=10)
  self.installerFrame = InstallerFrame(self, padding=10)
  tabs.add(self.installerFrame, text='安装应用（离线）' if build_mode() == 'offline' else '安装应用（在线）')
  tabs.add(self.infoFrame, text='相机信息')
  # Keep upstream advanced classes but do not expose firmware/service operations
  # in an application-only personal build.

  docsLink = Label(self, text='查看社区机型兼容性说明', foreground='blue', cursor='hand2')
  docsLink.bind('<Button-1>', lambda e: webbrowser.open_new(config.docsUrl + '/devices.html'))
  docsLink.pack(pady=(0, 5))

  self.logText = ScrollingText(self)
  self.logText.text.configure(state=DISABLED)
  self.logText.pack(fill=BOTH, expand=True)
  Button(self, text='保存完整日志（可能含相机序列号，请先脱敏）', command=self.saveLog).pack(fill=X, padx=10, pady=5)

  self.redirectStreams()
  source = '自带 APK 的离线版' if build_mode() == 'offline' else 'GitHub Release 下载版'
  self.log('社区安装后端 + %s；不是官方版本，尚未通过本次 A6000 真机测试。\n' % source)

 def setBusy(self, busy):
  self.busy = busy
  state = DISABLED if busy else NORMAL
  self.infoFrame.infoButton.config(state=state)
  for widget in (self.installerFrame.installButton, self.installerFrame.appLoadButton,
                 self.installerFrame.apkSelectButton):
   widget.config(state=state)

 def closeWindow(self):
  if self.busy:
   showwarning('正在与相机通信', '请等待任务结束后再关闭程序，不要在传输时断开 USB。', parent=self)
  else:
   self.destroy()

 def saveLog(self):
  filename = asksaveasfilename(defaultextension='.txt', filetypes=[('文本日志', '*.txt')], parent=self)
  if filename:
   try:
    with open(filename, 'w', encoding='utf-8') as output:
     output.write(self.logText.text.get('1.0', END))
   except OSError as error:
    showerror('日志保存失败', str(error), parent=self)

 def log(self, msg):
  self.logText.text.configure(state=NORMAL)
  self.logText.text.insert(END, msg)
  self.logText.text.configure(state=DISABLED)
  self.logText.text.see(END)

 def redirectStreams(self):
  for stream in ['stdout', 'stderr']:
   setattr(sys, stream, PrintRedirector(lambda str: self.run(lambda: self.log(str)), getattr(sys, stream)))


class InfoFrame(UiFrame):
 def __init__(self, parent, **kwargs):
  UiFrame.__init__(self, parent, **kwargs)

  Label(self, text='读取信息只能确认当前连接；不能保证后续应用安装成功。', wraplength=700).pack(fill=X, pady=(0, 8))
  self.infoButton = Button(self, text='读取相机信息（不安装应用）', command=InfoTask(self).run, padding=5)
  self.infoButton.pack(fill=X)


class InstallerFrame(UiFrame):
 MODE_APP = 0
 MODE_APK = 1

 def __init__(self, parent, **kwargs):
  UiFrame.__init__(self, parent, **kwargs)
  self.modeVar = IntVar(value=self.MODE_APP)
  Label(self, text='先开机，用数据线直连电脑，将 USB 连接设为 MTP。\n只安装一个选定应用，不会批量安装或刷固件。', wraplength=700).pack(fill=X, pady=(0, 8))

  appFrame = Labelframe(self, padding=8)
  list_title = '从 21 个离线应用中选择（不联网）' if build_mode() == 'offline' else '从 21 个应用中选择（GitHub Release 下载）'
  appFrame['labelwidget'] = Radiobutton(appFrame, text=list_title, variable=self.modeVar, value=self.MODE_APP)
  appFrame.columnconfigure(0, weight=1)
  appFrame.pack(fill=X)
  self.appCombo = Combobox(appFrame, state='readonly', height=21)
  self.appCombo.bind('<<ComboboxSelected>>', self.selectApp)
  self.appCombo.grid(row=0, column=0, sticky=W+E)
  self.appLoadButton = Button(appFrame, text='重新读取列表', command=AppLoadTask(self).run)
  self.appLoadButton.grid(row=0, column=1, padx=(5, 0))
  self.detailsVar = StringVar()
  Label(appFrame, textvariable=self.detailsVar, wraplength=690, justify=LEFT).grid(row=1, column=0, columnspan=2, sticky=W, pady=(8, 0))
  self.setAppList([])

  apkFrame = Labelframe(self, padding=8)
  apkFrame['labelwidget'] = Radiobutton(apkFrame, text='可选：安装其他本地 APK', variable=self.modeVar, value=self.MODE_APK)
  apkFrame.columnconfigure(0, weight=1)
  apkFrame.pack(fill=X, pady=(8, 0))
  self.apkFile = Entry(apkFrame)
  self.apkFile.grid(row=0, column=0, sticky=W+E)
  self.apkSelectButton = Button(apkFrame, text='打开 APK…', command=self.openApk)
  self.apkSelectButton.grid(row=0, column=1, padx=(5, 0))
  self.installButton = Button(self, text='安装选中的应用', command=InstallTask(self).run, padding=8)
  self.installButton.pack(fill=X, pady=(8, 0))
  self.statusVar = StringVar(value='请选择一个应用；列表中的中文说明不会改动 APK 本身。')
  Label(self, textvariable=self.statusVar, wraplength=700, justify=LEFT).pack(fill=X, pady=(8, 0))
  self.run(AppLoadTask(self).run)

 def getMode(self):
  return self.modeVar.get()

 def selectApp(self, event=None):
  self.modeVar.set(self.MODE_APP)
  app = self.getSelectedApp()
  self.detailsVar.set(app.details if app else '请选择要安装的应用。')

 def openApk(self):
  fn = askopenfilename(filetypes=[('Android 应用', '*.apk'), ('所有文件', '*.*')], parent=self.master)
  if fn:
   self.apkFile.delete(0, END)
   self.apkFile.insert(0, fn)
   self.modeVar.set(self.MODE_APK)

 def getSelectedApk(self):
  return self.apkFile.get()

 def setAppList(self, apps):
  self.appList = apps
  self.appCombo['values'] = ['请选择应用…'] + [app.label for app in apps]
  self.appCombo.current(0)
  self.detailsVar.set('请选择应用查看中文用途、英文名、版本和语言说明。' if apps else '列表尚未加载。请检查应用清单文件夹或下方日志。')

 def getSelectedApp(self):
  index = self.appCombo.current() - 1
  if 0 <= index < len(self.appList):
   return self.appList[index]


class FirmwareFrame(UiFrame):
 def __init__(self, parent, **kwargs):
  UiFrame.__init__(self, parent, **kwargs)

  datFrame = Labelframe(self, padding=5)
  datFrame['labelwidget'] = Label(datFrame, text='Firmware file')
  datFrame.pack(fill=X)

  self.datFile = Entry(datFrame)
  self.datFile.pack(side=LEFT, fill=X, expand=True)

  self.datSelectButton = Button(datFrame, text='Open...', command=self.openDat)
  self.datSelectButton.pack()

  self.fwUpdateButton = Button(self, text='Update firmware', command=FirmwareUpdateTask(self).run, padding=5)
  self.fwUpdateButton.pack(fill=X, pady=(5, 0))

 def openDat(self):
  fn = askopenfilename(filetypes=[('Firmware files', '.dat'), ('All files', '.*')])
  if fn:
   self.datFile.delete(0, END)
   self.datFile.insert(0, fn)

 def getSelectedDat(self):
  return self.datFile.get()


class UpdaterShellFrame(UiFrame):
 def __init__(self, parent, **kwargs):
  UiFrame.__init__(self, parent, **kwargs)

  self.startUpdaterShellButton = Button(self, text='Start tweaking (updater mode)', command=StartUpdaterShellTask(self).run, padding=5)
  self.startUpdaterShellButton.pack(fill=X)

  self.startSenserShellButton = Button(self, text='Start tweaking (service mode)', command=StartSenserShellTask(self).run, padding=5)
  self.startSenserShellButton.pack(fill=X, pady=(5, 0))


class TweakDialog(UiDialog):
 def __init__(self, parent, tweakInterface, endFlag=None):
  self.tweakInterface = tweakInterface
  self.endFlag = endFlag
  UiDialog.__init__(self, parent, "Tweaks")

 def body(self, top):
  tweakFrame = Labelframe(top, padding=5)
  tweakFrame['labelwidget'] = Label(tweakFrame, text='Tweaks')
  tweakFrame.pack(fill=X)

  self.boxFrame = Frame(tweakFrame)
  self.boxFrame.pack(fill=BOTH, expand=True)

  self.applyButton = Button(top, text='Apply', command=TweakApplyTask(self).run, padding=5)
  self.applyButton.pack(fill=X)

  self.updateStatus()

 def updateStatus(self):
  for child in self.boxFrame.winfo_children():
   child.destroy()
  for id, desc, status, value in self.tweakInterface.getTweaks():
   var = IntVar(value=status)
   c = Checkbutton(self.boxFrame, text=desc + '\n' + value, variable=var, command=lambda id=id, var=var: self.setTweak(id, var.get()))
   c.pack(fill=X)

 def setTweak(self, id, enabled):
  self.tweakInterface.setEnabled(id, enabled)
  self.updateStatus()

 def setState(self, state):
  for widget in self.boxFrame.winfo_children() + [self.applyButton]:
   widget.config(state=state)

 def cancel(self, event=None):
  UiDialog.cancel(self, event)
  if self.endFlag:
   self.endFlag.set()


def self_test(output_filename):
 """Frozen startup/resource check. No USB access, server or download is used."""
 import json
 from pathlib import Path
 from pmca.usb.driver.windows import msc, wpd, driverless
 from comtypes.client import GetModule
 import types
 assert isinstance(GetModule('PortableDeviceApi.dll'), types.ModuleType)
 assert isinstance(GetModule('PortableDeviceTypes.dll'), types.ModuleType)
 import comtypes.gen.PortableDeviceApiLib as api_wrapper
 import comtypes.gen.PortableDeviceTypesLib as types_wrapper
 import tlslite
 from Cryptodome.Cipher import AES
 from pmca.apk import ApkParser
 cert_path = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'certs' / 'localtest.me.pem'
 cert = cert_path.read_text()
 chain = tlslite.X509CertChain()
 chain.parsePemList(cert)
 tlslite.parsePEMKey(cert, private=True)
 cipher = AES.new(b'\x00' * 16, AES.MODE_ECB)
 assert len(cipher.encrypt(b'\x00' * 16)) == 16
 if getattr(sys, 'frozen', False):
  bundle = Path(sys._MEIPASS).resolve()
  assert bundle in Path(api_wrapper.__file__).resolve().parents
  assert bundle in Path(types_wrapper.__file__).resolve().parents
 apps = load_app_list()
 if len(apps) != 21 or len({app.package for app in apps}) != 21:
  raise RuntimeError('Self-test requires 21 unique app entries')
 for app in apps:
  if build_mode() == 'offline':
   with app.open_verified() as apk:
    parsed = ApkParser(apk)
    if parsed.getPackageName() != app.package or parsed.getVersionName() != app.version:
     raise RuntimeError('APK metadata does not match catalog: ' + app.filename)
    parsed.getVersionCode()
    parsed.getCert()
   del parsed
 # Tcl/Tk must initialize in the bundled Windows executable.
 root = UiRoot()
 root.withdraw()
 root.update_idletasks()
 root.destroy()
 result = {'mode': build_mode(), 'appCount': len(apps),
           'driverImports': ['win32file', 'comtypes', 'wpd', 'msc', 'driverless'],
           'tkStartup': True, 'apkMetadataVerified': build_mode() == 'offline',
           'certificateLoaded': True, 'aesExtensionLoaded': True,
           'comWrappers': [api_wrapper.__file__, types_wrapper.__file__],
           'cameraConnected': False}
 Path(output_filename).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
 """Gui main"""
 if '--self-test' in sys.argv:
  index = sys.argv.index('--self-test')
  output = sys.argv[index + 1]
  try:
   self_test(output)
  except Exception:
   import json
   from pathlib import Path
   Path(output).write_text(json.dumps({'error': traceback.format_exc()}, indent=2), encoding='utf-8')
   raise SystemExit(1)
  return
 source = '离线版' if build_mode() == 'offline' else '在线下载版'
 ui = MainUi('A6000 应用安装 · 社区 PMCA 中文%s' % source + (' ' + version if version else ''))
 ui.mainloop()


if __name__ == '__main__':
 main()
