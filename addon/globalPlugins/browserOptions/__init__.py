# NVDA Addon: Browser Options 
# Released under the GNU General Public License v2 
# Copyright (C) 2024 ANDHIM 

import globalPluginHandler
import gui
import wx
import subprocess
import winreg  
from globalPluginHandler import GlobalPlugin
import ui
from scriptHandler import script
import addonHandler
addonHandler.initTranslation()

class InteractiveDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Browser Options", size=(400, 200))

        # main panel for dialogelement 
        panel = wx.Panel(self)

        # Label instruksi
        self.label = wx.StaticText(panel, label=_("Input URL or Keywords"), pos=(20, 20))

        #  input box 
        self.input_box = wx.TextCtrl(panel, pos=(20, 50), size=(350, 25))

        open_button = wx.Button(panel, label=_("Search"), pos=(150, 100))
        open_button.Bind(wx.EVT_BUTTON, self.on_open_url)

        # handler global keyboard events  for enter searching 
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_press)

        # focus to  input  box 
        self.Bind(wx.EVT_SHOW, self.on_show)

    def on_show(self, event):
        self.input_box.SetFocus()

    def on_open_url(self, event=None):
        user_input = self.input_box.GetValue().strip()
        if not user_input:
            ui.message(_("Input Cannot be empty "))
            return

        # checking input URL or keywords
        if self.is_url(user_input):
            # if URL go open page 
            self.open_url_in_browser(user_input)
        else:
            # if keyword go search in google 
            search_url = f"https://www.google.com/search?q={user_input}"
            self.open_url_in_browser(search_url)

    def is_url(self, user_input):
        # checking URL   or not 
        return user_input.startswith("http://") or user_input.startswith("https://") or '.' in user_input

    def get_installed_browsers(self):
        # detect  browser in system 
        browsers = {}
# detect chrome  
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                chrome_command, _ = winreg.QueryValueEx(key, "")
                browsers["Chrome"] = chrome_command
        except FileNotFoundError:
            pass

        # detect firefox 
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe") as key:
                firefox_command, _ = winreg.QueryValueEx(key, "")
                browsers["Firefox"] = firefox_command
        except FileNotFoundError:
            pass

        # detect edge 
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe") as key:
                edge_command, _ = winreg.QueryValueEx(key, "")
                browsers["Edge"] = edge_command
        except FileNotFoundError:
            pass
        return browsers

    def open_url_in_browser(self, url):
        # open browser selected
        available_browsers = self.get_installed_browsers()
        if not available_browsers:
            ui.message(_("No Browser detect "))
            return

        # show dialog browser option 
        browser_names = list(available_browsers.keys())
        dialog = wx.SingleChoiceDialog(None, _("Select Browser"), "Browser Options", browser_names)

        if dialog.ShowModal() == wx.ID_OK:
            choice = dialog.GetStringSelection()
            browser_command = available_browsers[choice]

            try:
                subprocess.Popen([browser_command, url], shell=False)
                self.Destroy()  # close dialog after selected browser 
            except Exception as e:
                ui.message(f"Failed to open with {choice}: {str(e)}")

        dialog.Destroy()

    def on_key_press(self, event):
        key_code = event.GetKeyCode()
        if key_code == wx.WXK_RETURN or key_code == wx.WXK_NUMPAD_ENTER:
            self.on_open_url()  # call function open url if press enter 
        elif key_code == wx.WXK_ESCAPE:
            self.Destroy()  #close dialog if press esc 
        else:
            event.Skip()  # lets other event in process  

class GlobalPlugin(GlobalPlugin):
    def __init__(self):
        super().__init__()
        self.dialog = None  # initialitation dialog atribute 

    @script(
        description="Browser Options",
        category="Browser Options",
        gesture="kb:nvda+o"
    )
    def script_show_dialog(self, gesture):
        if not self.dialog:
            # if the dialog does not exist create a new dialog
            self.dialog = InteractiveDialog(None)
            self.dialog.Bind(wx.EVT_CLOSE, self.on_dialog_close)  # Bind event untuk menangani penutupan dialog
            self.dialog.Show()
            self.dialog.Raise()
            self.dialog.input_box.SetFocus()
        else:
            # if the dialogue already exists, bring up the dialogue and focus
            self.dialog.Raise()
            self.dialog.input_box.SetFocus()

    def on_dialog_close(self, event):
        self.dialog.Destroy()
        self.dialog = None

