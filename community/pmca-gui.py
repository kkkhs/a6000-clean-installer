#!/usr/bin/env python3
"""A simple gui interface"""
import sys
import traceback
import webbrowser

import config
from pmca.catalog import build_mode, load_app_list
from pmca.friendly import error_hint
from pmca.i18n import get_language, load_language, set_language, tr
from tkinter.messagebox import showerror, showwarning, showinfo
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
   print(tr('loaded', count=len(apps), source=tr(build_mode())))
   return apps
  except Exception as error:
   print(tr('load_failed', error=error))
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
   print(tr('reading_info'))
   infoCommand(driverName='native' if sys.platform == 'win32' else None)
   print(tr('info_caution'))
  except Exception as error:
   print(tr('info_failed', error=error, hint=error_hint(error)))
   traceback.print_exc()

 def doAfter(self, result):
  self.ui.master.setBusy(False)


class InstallTask(BackgroundTask):
 """The exact verified local bytes are handed to the upstream USB installer."""
 def doBefore(self):
  self.ui.master.setBusy(True)
  self.ui.setStatus('install_running')
  return self.ui.getMode(), self.ui.getSelectedApk(), self.ui.getSelectedApp()

 def do(self, args):
  (mode, apkFilename, app) = args
  try:
   print('')
   if mode == self.ui.MODE_APP and app:
    print(tr('checking_app', name=app.name, original=app.english_name))
    with app.open_verified() as f:
     installCommand(driverName='native' if sys.platform == 'win32' else None, apkFile=f)
   elif mode == self.ui.MODE_APK and apkFilename:
    with open(apkFilename, 'rb') as f:
     installCommand(driverName='native' if sys.platform == 'win32' else None, apkFile=f)
   else:
    raise ValueError(tr('select_required'))
   print(tr('install_success'))
   return True, 'install_success'
  except Exception as error:
   hint = error_hint(error)
   print(tr('install_failed', error=error, hint=hint))
   traceback.print_exc()
   return False, error

 def doAfter(self, result):
  success, result_value = result
  if success:
   self.ui.setStatus(result_value)
  else:
   self.ui.setStatus('failure', result_value)
  self.ui.master.setBusy(False)
  if not success:
   message = error_hint(result_value)
   showerror(tr('failure_title'), message + '\n\n' + tr('full_error'), parent=self.ui.master)


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
 def __init__(self, load_apps=True, redirect=True):
  UiRoot.__init__(self)
  self.geometry('800x840')
  self.minsize(700, 720)
  self['menu'] = Menu(self)
  self.busy = False
  self.protocol('WM_DELETE_WINDOW', self.closeWindow)
  toolbar = Frame(self)
  toolbar.pack(fill=X, padx=10, pady=8)
  self.brandLabel = Label(toolbar, text='Sony PMCA App Installer', font=('TkDefaultFont', 12, 'bold'))
  self.brandLabel.pack(side=LEFT)
  self.languageButton = Button(toolbar, command=self.switchLanguage)
  self.languageButton.pack(side=RIGHT)
  self.aboutButton = Button(toolbar, command=self.showAbout)
  self.aboutButton.pack(side=RIGHT, padx=8)
  self.tabs = Notebook(self, padding=5)
  self.tabs.pack(fill=X)
  self.infoFrame = InfoFrame(self, padding=10)
  self.installerFrame = InstallerFrame(self, load_apps=load_apps, padding=10)
  self.tabs.add(self.installerFrame)
  self.tabs.add(self.infoFrame)
  # Firmware and service-mode operations remain hidden in this app build.
  self.docsLink = Label(self, foreground='blue', cursor='hand2')
  self.docsLink.bind('<Button-1>', lambda e: webbrowser.open_new(config.docsUrl + '/devices.html'))
  self.docsLink.pack(pady=(0, 5))
  self.logText = ScrollingText(self)
  self.logText.text.configure(state=DISABLED)
  self.logText.pack(fill=BOTH, expand=True)
  self.saveLogButton = Button(self, command=self.saveLog)
  self.saveLogButton.pack(fill=X, padx=10, pady=(5, 0))
  self.privacyNote = Label(self, wraplength=740)
  self.privacyNote.pack(fill=X, padx=10, pady=(3, 6))
  footer = Frame(self)
  footer.pack(fill=X, padx=10, pady=(0, 8))
  self.authorLabel = Label(footer)
  self.authorLabel.pack(side=LEFT)
  self.projectLink = Label(footer, foreground='blue', cursor='hand2')
  self.projectLink.bind('<Button-1>', lambda e: webbrowser.open_new('https://github.com/kkkhs/sony-pmca-app-installer'))
  self.projectLink.pack(side=RIGHT)
  self.applyLanguage()
  if redirect:
   self.redirectStreams()
  self.log(tr('startup', source=tr(build_mode())) + '\n')

 def applyLanguage(self):
  self.title(tr('title', source=tr(build_mode())) + (' ' + version if version else ''))
  self.languageButton.config(text='English' if get_language() == 'zh' else '中文')
  self.aboutButton.config(text=tr('about'))
  self.authorLabel.config(text=tr('author'))
  self.projectLink.config(text=tr('project'))
  self.privacyNote.config(text=tr('log_privacy'))
  self.tabs.tab(self.installerFrame, text=tr('tab_' + build_mode()))
  self.tabs.tab(self.infoFrame, text=tr('tab_info'))
  self.docsLink.config(text=tr('compatibility'))
  self.saveLogButton.config(text=tr('save_log'))
  self.infoFrame.applyLanguage()
  self.installerFrame.applyLanguage()

 def switchLanguage(self, persist=True):
  if self.busy:
   return
  target = 'en' if get_language() == 'zh' else 'zh'
  try:
   set_language(target, persist=persist)
  except OSError as error:
   self.log(tr('settings_failed', error=error) + '\n')
  self.applyLanguage()

 def setBusy(self, busy):
  self.busy = busy
  state = DISABLED if busy else NORMAL
  self.languageButton.config(state=state)
  self.infoFrame.infoButton.config(state=state)
  for widget in (self.installerFrame.installButton, self.installerFrame.appLoadButton,
                 self.installerFrame.apkSelectButton):
   widget.config(state=state)

 def showAbout(self):
  showinfo(tr('about_title'), tr('about_body', version=version or 'source'), parent=self)

 def closeWindow(self):
  if self.busy:
   showwarning(tr('busy_title'), tr('busy_warning'), parent=self)
  else:
   self.destroy()

 def saveLog(self):
  filename = asksaveasfilename(defaultextension='.txt', filetypes=[(tr('text_log'), '*.txt')], parent=self)
  if filename:
   try:
    with open(filename, 'w', encoding='utf-8') as output:
     output.write(self.logText.text.get('1.0', END))
   except OSError as error:
    showerror(tr('save_failed'), str(error), parent=self)

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

  self.infoNote = Label(self, wraplength=740)
  self.infoNote.pack(fill=X, pady=(0, 8))
  self.infoButton = Button(self, command=InfoTask(self).run, padding=5)
  self.infoButton.pack(fill=X)
  self.applyLanguage()

 def applyLanguage(self):
  self.infoNote.config(text=tr('info_note'))
  self.infoButton.config(text=tr('read_info'))


class InstallerFrame(UiFrame):
 MODE_APP = 0
 MODE_APK = 1

 def __init__(self, parent, load_apps=True, **kwargs):
  UiFrame.__init__(self, parent, **kwargs)
  self.modeVar = IntVar(value=self.MODE_APP)
  self.connectNote = Label(self, wraplength=740)
  self.connectNote.pack(fill=X, pady=(0, 8))
  appFrame = Labelframe(self, padding=8)
  self.listRadio = Radiobutton(appFrame, variable=self.modeVar, value=self.MODE_APP)
  appFrame['labelwidget'] = self.listRadio
  appFrame.columnconfigure(0, weight=1)
  appFrame.pack(fill=X)
  self.appCombo = Combobox(appFrame, state='readonly', height=21)
  self.appCombo.bind('<<ComboboxSelected>>', self.selectApp)
  self.appCombo.grid(row=0, column=0, sticky=W+E)
  self.appLoadButton = Button(appFrame, command=AppLoadTask(self).run)
  self.appLoadButton.grid(row=0, column=1, padx=(5, 0))
  self.detailsVar = StringVar()
  Label(appFrame, textvariable=self.detailsVar, wraplength=730, justify=LEFT).grid(row=1, column=0, columnspan=2, sticky=W, pady=(8, 0))
  apkFrame = Labelframe(self, padding=8)
  self.apkRadio = Radiobutton(apkFrame, variable=self.modeVar, value=self.MODE_APK)
  apkFrame['labelwidget'] = self.apkRadio
  apkFrame.columnconfigure(0, weight=1)
  apkFrame.pack(fill=X, pady=(8, 0))
  self.apkFile = Entry(apkFrame)
  self.apkFile.grid(row=0, column=0, sticky=W+E)
  self.apkSelectButton = Button(apkFrame, command=self.openApk)
  self.apkSelectButton.grid(row=0, column=1, padx=(5, 0))
  self.installButton = Button(self, command=InstallTask(self).run, padding=8)
  self.installButton.pack(fill=X, pady=(8, 0))
  self.statusVar = StringVar()
  self.statusKey, self.statusError = 'idle', None
  Label(self, textvariable=self.statusVar, wraplength=740, justify=LEFT).pack(fill=X, pady=(8, 0))
  self.setAppList([])
  self.applyLanguage()
  if load_apps:
   self.run(AppLoadTask(self).run)

 def applyLanguage(self):
  self.connectNote.config(text=tr('connect_note'))
  self.listRadio.config(text=tr('list_' + build_mode()))
  self.apkRadio.config(text=tr('other_apk'))
  self.appLoadButton.config(text=tr('refresh'))
  self.apkSelectButton.config(text=tr('open_apk'))
  self.installButton.config(text=tr('install_selected'))
  index = self.appCombo.current()
  self.appCombo['values'] = [tr('choose_app')] + [app.label for app in self.appList]
  self.appCombo.current(index if 0 <= index <= len(self.appList) else 0)
  self.refreshDetails()
  self.setStatus(self.statusKey, self.statusError)

 def setStatus(self, key, error=None):
  self.statusKey, self.statusError = key, error
  self.statusVar.set(error_hint(error) if key == 'failure' else tr(key))

 def refreshDetails(self):
  app = self.getSelectedApp()
  self.detailsVar.set(app.details if app else tr('choose_details' if self.appList else 'list_not_loaded'))

 def getMode(self):
  return self.modeVar.get()

 def selectApp(self, event=None):
  self.modeVar.set(self.MODE_APP)
  self.refreshDetails()

 def openApk(self):
  fn = askopenfilename(filetypes=[(tr('android_app'), '*.apk'), (tr('all_files'), '*.*')], parent=self.master)
  if fn:
   self.apkFile.delete(0, END)
   self.apkFile.insert(0, fn)
   self.modeVar.set(self.MODE_APK)

 def getSelectedApk(self):
  return self.apkFile.get()

 def setAppList(self, apps):
  self.appList = apps
  self.appCombo['values'] = [tr('choose_app')] + [app.label for app in apps]
  self.appCombo.current(0)
  self.refreshDetails()

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
 # Construct the real UI without background tasks or stream redirection.
 # Exercise both languages and verify switching preserves the selected app/mode.
 set_language('zh')
 root = MainUi(load_apps=False, redirect=False)
 root.withdraw()
 root.installerFrame.setAppList(apps)
 root.installerFrame.appCombo.current(2)
 root.installerFrame.selectApp()
 selected = root.installerFrame.getSelectedApp().package
 root.installerFrame.setStatus('install_success')
 root.setBusy(True)
 root.switchLanguage(persist=False)
 assert get_language() == 'zh'
 assert str(root.languageButton.cget('state')) == DISABLED
 root.setBusy(False)
 root.update_idletasks()
 assert root.installerFrame.installButton.cget('text') == tr('install_selected')
 assert root.brandLabel.cget('text') == 'Sony PMCA App Installer'
 assert root.aboutButton.cget('text') == '关于'
 assert 'kkkhs' in root.authorLabel.cget('text')
 root.switchLanguage(persist=False)
 assert get_language() == 'en'
 assert root.installerFrame.getSelectedApp().package == selected
 assert root.installerFrame.getMode() == root.installerFrame.MODE_APP
 assert root.installerFrame.installButton.cget('text') == 'Install selected app'
 assert root.installerFrame.statusVar.get() == tr('install_success')
 assert root.aboutButton.cget('text') == 'About'
 assert root.authorLabel.cget('text') == 'Author: kkkhs · Based on Sony-PMCA-RE'
 assert root.projectLink.cget('text') == 'Project page'
 assert root.saveLogButton.cget('text') == 'Export diagnostic log'
 assert 'serial numbers' in root.privacyNote.cget('text')
 assert 'ma1co' in tr('about_body', version=version or 'source')
 for app in apps:
  assert app.name == app.english_name
  assert app.metadata.get('descriptionEn')
 root.installerFrame.modeVar.set(root.installerFrame.MODE_APK)
 root.installerFrame.apkFile.insert(0, 'selected-local.apk')
 root.installerFrame.setStatus('failure', RuntimeError('Operation timed out'))
 root.switchLanguage(persist=False)
 assert get_language() == 'zh'
 assert root.installerFrame.getSelectedApp().package == selected
 assert root.installerFrame.getMode() == root.installerFrame.MODE_APK
 assert root.installerFrame.getSelectedApk() == 'selected-local.apk'
 assert '超时' in root.installerFrame.statusVar.get()
 root.update_idletasks()
 root.destroy()
 result = {'mode': build_mode(), 'appCount': len(apps),
           'driverImports': ['win32file', 'comtypes', 'wpd', 'msc', 'driverless'],
           'tkStartup': True, 'apkMetadataVerified': build_mode() == 'offline',
           'certificateLoaded': True, 'aesExtensionLoaded': True,
           'comWrappers': [api_wrapper.__file__, types_wrapper.__file__],
           'languages': ['zh', 'en'], 'uiLanguageSwitchVerified': True,
           'selectionPreserved': True, 'authorAttributionVerified': True,
           'professionalUiCopyVerified': True, 'cameraConnected': False}
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
 load_language()
 for stream in (sys.stdout, sys.stderr):
  if hasattr(stream, 'reconfigure'):
   stream.reconfigure(encoding='utf-8', errors='replace')
 ui = MainUi()
 ui.mainloop()


if __name__ == '__main__':
 main()
