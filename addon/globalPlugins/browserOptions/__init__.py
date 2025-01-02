# NVDA Addon: Browser Options 
# Released under the GNU General Public License v2 
# Copyright (C) 2024 - 2025 Andhi Mardianto

import globalPluginHandler 
import gui 
import os
import json
import wx
import subprocess
import winreg
from globalPluginHandler import GlobalPlugin
import ui
import api 
from scriptHandler import script
addonHandler.initTranslation()


def get_browser_options_folder():
    """Mengembalikan path ke folder browserOptions di AppData\Roaming"""
    appdata_folder = os.getenv("APPDATA")  # Lokasi AppData\Roaming
    browser_options_folder = os.path.join(appdata_folder, "browserOptions")
    if not os.path.exists(browser_options_folder):
        os.makedirs(browser_options_folder)
    return browser_options_folder

def get_favorites_file():
    """Mengembalikan path ke file favorites.json di dalam folder browserOptions"""
    browser_options_folder = get_browser_options_folder()
    favorites_file = os.path.join(browser_options_folder, "favorites.json")
    if not os.path.exists(favorites_file):
        # Jika file belum ada, buat file baru dengan data kosong
        with open(favorites_file, "w") as f:
            json.dump({}, f)  # Struktur data kosong
    return favorites_file

def load_favorites():
    """Memuat data dari file favorites.json"""
    favorites_file = get_favorites_file()
    try:
        with open(favorites_file, "r") as f:
            return json.load(f)  # Kembalikan data dalam bentuk dictionary
    except json.JSONDecodeError:
        # Jika terjadi kesalahan saat membaca file JSON, gunakan data kosong
        return {}

def save_favorites(favorites):
    """Menyimpan data ke file favorites.json"""
    favorites_file = get_favorites_file()
    with open(favorites_file, "w") as f:
        json.dump(favorites, f, indent=4)  # Simpan dengan format JSON yang rapi


class AddFavoriteDialog(wx.Dialog):
    def __init__(self, parent, favorites):
        super().__init__(parent, title=_("Add Favorite"), size=(400, 200))
        self.favorites = favorites

        panel = wx.Panel(self)
        wx.StaticText(panel, label=_("Name:"), pos=(20, 20))
        wx.StaticText(panel, label=_("URL:"), pos=(20, 60))

        self.name_box = wx.TextCtrl(panel, pos=(100, 20), size=(250, 25))
        self.url_box = wx.TextCtrl(panel, pos=(100, 60), size=(250, 25))

        save_button = wx.Button(panel, label=_("Save"), pos=(150, 100))
        save_button.Bind(wx.EVT_BUTTON, self.on_save)

        self.Bind(wx.EVT_SHOW, self.on_show)

    def on_show(self, event):
        self.name_box.SetFocus()

    def on_save(self, event):
        name = self.name_box.GetValue().strip()
        url = self.url_box.GetValue().strip()

        if not name or not url:
            ui.message(_("Both Name and URL are required."))
            return

        if not (url.startswith("http://") or url.startswith("https://")):
            ui.message(_("Invalid URL. It should start with http:// or https://"))
            return

        self.favorites[name] = url
        save_favorites(self.favorites)  # Simpan data favorit yang diperbarui

        ui.message(_("Favorite added successfully!"))
        self.Destroy()


class InteractiveDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Browser Options", size=(400, 350))

        panel = wx.Panel(self)
        self.label = wx.StaticText(panel, label=_("Input URL or Keywords"), pos=(20, 20))
        self.input_box = wx.TextCtrl(panel, pos=(20, 50), size=(350, 25))

        open_button = wx.Button(panel, label=_("Search"), pos=(150, 100))
        open_button.Bind(wx.EVT_BUTTON, self.on_open_url)

        favorites_button = wx.Button(panel, label=_("Favorites"), pos=(150, 140))
        favorites_button.Bind(wx.EVT_BUTTON, self.open_favorites)

        add_favorite_button = wx.Button(panel, label=_("Add Favorite"), pos=(150, 180))
        add_favorite_button.Bind(wx.EVT_BUTTON, self.add_favorite)

        delete_favorite_button = wx.Button(panel, label=_("Delete Favorite"), pos=(150, 220))
        delete_favorite_button.Bind(wx.EVT_BUTTON, self.delete_favorite)

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_press)
        self.Bind(wx.EVT_SHOW, self.on_show)

        self.favorites = load_favorites()  # Memuat data dari favorites.json

    def on_show(self, event):
        self.input_box.SetFocus()

    def on_open_url(self, event=None):
        user_input = self.input_box.GetValue().strip()
        if not user_input:
            ui.message(_("Input cannot be empty"))
            return

        if self.is_url(user_input):
            self.open_url_in_browser(user_input)
        else:
            search_url = f"https://www.google.com/search?q={user_input}"
            self.open_url_in_browser(search_url)

    def is_url(self, user_input):
        return user_input.startswith("http://") or user_input.startswith("https://") or '.' in user_input

    def open_url_in_browser(self, url):
        available_browsers = self.get_installed_browsers()
        if not available_browsers:
            ui.message(_("No browser detected"))
            return

        browser_names = list(available_browsers.keys())
        dialog = wx.SingleChoiceDialog(None, _("Select Browser"), "Browser Options", browser_names)

        if dialog.ShowModal() == wx.ID_OK:
            choice = dialog.GetStringSelection()
            browser_command = available_browsers[choice]

            try:
                subprocess.Popen([browser_command, url], shell=False)
                self.Destroy()
            except Exception as e:
                ui.message(f"Failed to open with {choice}: {str(e)}")

        dialog.Destroy()

    def get_installed_browsers(self):
        browsers = {}
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                chrome_command, _ = winreg.QueryValueEx(key, "")
                browsers["Chrome"] = chrome_command
        except FileNotFoundError:
            pass

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe") as key:
                firefox_command, _ = winreg.QueryValueEx(key, "")
                browsers["Firefox"] = firefox_command
        except FileNotFoundError:
            pass

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe") as key:
                edge_command, _ = winreg.QueryValueEx(key, "")
                browsers["Edge"] = edge_command
        except FileNotFoundError:
            pass
        return browsers
    def open_favorites(self, event):
        if not self.favorites:
            ui.message(_("No favorites found"))
            return

        def show_dialog():
            names = list(self.favorites.keys())
            dialog = wx.SingleChoiceDialog(None, _("Select Favorite"), "Favorites", names)

            if dialog.ShowModal() == wx.ID_OK:
                choice = dialog.GetStringSelection()
                self.open_url_in_browser(self.favorites[choice])

            dialog.Destroy()

        wx.CallAfter(show_dialog)  

    
    def add_favorite(self, event):
        dialog = AddFavoriteDialog(self, self.favorites)
        dialog.ShowModal()

    def delete_favorite(self, event):
        if not self.favorites:
            ui.message("No favorites found")
            return

        names = list(self.favorites.keys())
        dialog = wx.SingleChoiceDialog(None, _("Select Favorite Link to Delete"), "Delete Favorites", names)

        if dialog.ShowModal() == wx.ID_OK:
            choice = dialog.GetStringSelection()
            del self.favorites[choice]
            save_favorites(self.favorites)  # Simpan setelah menghapus favorit
            ui.message(_("Favorite deleted successfully!"))

        dialog.Destroy()

    def on_key_press(self, event):
        key_code = event.GetKeyCode()
        if key_code == wx.WXK_RETURN or key_code == wx.WXK_NUMPAD_ENTER:
            self.on_open_url()
        elif key_code == wx.WXK_ESCAPE:
            self.Destroy()
        else:
            event.Skip()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self):
        super().__init__()
        self.dialog = None

    @script(
        description="Browser Options",
        category="Browser Options",
        gesture="kb:nvda+o"
    )
    def script_show_dialog(self, gesture):
        if not self.dialog:
            self.dialog = InteractiveDialog(None)
            self.dialog.Bind(wx.EVT_CLOSE, self.on_dialog_close)
            self.dialog.Show()
            self.dialog.Raise()
            self.dialog.input_box.SetFocus()
        else:
            self.dialog.Raise()
            self.dialog.input_box.SetFocus()

    @script(
        description="Open Favorites Menu",
        category="Browser Options",
        gesture="kb:nvda+shift+o"
    )
    def script_open_favorites(self, gesture):
        if not self.dialog:
            self.dialog = InteractiveDialog(None)
            self.dialog.Bind(wx.EVT_CLOSE, self.on_dialog_close)
            self.dialog.Show()
            self.dialog.Raise()
            self.dialog.input_box.SetFocus()
        self.dialog.open_favorites(None)

    def on_dialog_close(self, event):
        self.dialog.Destroy()
        self.dialog = None
