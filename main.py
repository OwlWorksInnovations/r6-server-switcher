import slint
import os
import re
import glob
import pystray
from PIL import Image, ImageDraw
import threading
import sys
import json

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Constants
SERVERS_DATA = [
    {"name": "Australia East", "hint": "playfab/australiaeast", "continent": "Australia"},
    {"name": "Brazil South", "hint": "playfab/brazilsouth", "continent": "South America"},
    {"name": "Central US", "hint": "playfab/centralus", "continent": "North America"},
    {"name": "East Asia", "hint": "playfab/eastasia", "continent": "Asia"},
    {"name": "East US", "hint": "playfab/eastus", "continent": "North America"},
    {"name": "Japan East", "hint": "playfab/japaneast", "continent": "Asia"},
    {"name": "North Europe", "hint": "playfab/northeurope", "continent": "Europe"},
    {"name": "South Africa North", "hint": "playfab/southafricanorth", "continent": "Africa"},
    {"name": "South Central US", "hint": "playfab/southcentralus", "continent": "North America"},
    {"name": "South East Asia", "hint": "playfab/southeastasia", "continent": "Asia"},
    {"name": "UAE North", "hint": "playfab/uaenorth", "continent": "Asia"},
    {"name": "West Europe", "hint": "playfab/westeurope", "continent": "Europe"},
    {"name": "West US", "hint": "playfab/westus", "continent": "North America"},
]

SERVERS = {s["name"]: s["hint"] for s in SERVERS_DATA}
SERVERS["Default (Auto)"] = "default"

def get_r6_accounts():
    base_path = os.path.join(os.environ['USERPROFILE'], 'Documents', 'My Games', 'Rainbow Six - Siege')
    accounts = {}
    if os.path.exists(base_path):
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                settings_file = os.path.join(item_path, 'GameSettings.ini')
                if os.path.exists(settings_file):
                    accounts[item] = settings_file
    return accounts

def get_current_datacenter(file_path):
    if not file_path or not os.path.exists(file_path):
        return "default"
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            match = re.search(r'^DataCenterHint=(.*)', content, re.MULTILINE)
            if match:
                return match.group(1).strip()
    except Exception as e:
        print(f"Error reading file: {e}")
    return "default"

def set_datacenter(file_path, hint):
    if not file_path or not os.path.exists(file_path):
        return False
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        if re.search(r'^DataCenterHint=', content, re.MULTILINE):
            new_content = re.sub(r'^DataCenterHint=.*', f'DataCenterHint={hint}', content, flags=re.MULTILINE)
        else:
            if '[ONLINE]' in content:
                new_content = content.replace('[ONLINE]', f'[ONLINE]\nDataCenterHint={hint}')
            else:
                new_content = content + f'\n[ONLINE]\nDataCenterHint={hint}'
        
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False

def create_tray_icon_image():
    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        try:
            return Image.open(icon_path)
        except Exception:
            pass
            
    image = Image.new('RGB', (64, 64), color=(43, 45, 49))
    draw = ImageDraw.Draw(image)
    draw.ellipse([10, 10, 54, 54], fill=(88, 101, 242))
    draw.rectangle([25, 20, 39, 44], fill=(255, 255, 255))
    return image

ui_file = resource_path("ui/app-window.slint")
ui_comp = slint.load_file(ui_file)

class MainWindow(ui_comp.AppWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.accounts_dict = get_r6_accounts()
        self.settings_path = None
        self._history_list = []
        
        account_list = list(self.accounts_dict.keys())
        self.accounts = slint.ListModel(account_list)
        
        if account_list:
            default_account = max(account_list, key=lambda k: os.path.getmtime(self.accounts_dict[k]))
            self.selected_account = default_account
            self.load_account_settings(default_account, silent=True)
        else:
            self.show_toast("No R6 accounts found!", is_error=True)
            self.file_path_display = "Not found"
        
        self.sort_mode = "az"
        self.update_server_list()
        self.load_history()
    
    def sync_history_to_ui(self):
        # Map the top 3 items to properties. Slint strings are stable.
        try:
            self.recent_1 = self._history_list[0] if len(self._history_list) > 0 else ""
            self.recent_2 = self._history_list[1] if len(self._history_list) > 1 else ""
            self.recent_3 = self._history_list[2] if len(self._history_list) > 2 else ""
            print(f"Synced UI: {self.recent_1}, {self.recent_2}, {self.recent_3}")
        except Exception as e:
            print(f"Sync error: {e}")

    def load_history(self):
        config_path = os.path.join(os.environ['USERPROFILE'], '.r6_switcher_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    self._history_list = data.get('recent', [])
                    print(f"Loaded history: {self._history_list}")
                    self.sync_history_to_ui()
            except Exception as e:
                print(f"Error loading history: {e}")
                self._history_list = []
                self.sync_history_to_ui()
        else:
            print("No history file found.")
            self._history_list = []
            self.sync_history_to_ui()

    def save_history(self):
        config_path = os.path.join(os.environ['USERPROFILE'], '.r6_switcher_config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump({'recent': self._history_list}, f)
            print(f"Saved history: {self._history_list}")
        except Exception as e:
            print(f"Error saving history: {e}")

    def show_toast(self, message, is_error=False):
        self.toast_msg = message
        self.toast_err = is_error
        self.toast_showing = True

    def load_account_settings(self, account_id, silent=False):
        self.settings_path = self.accounts_dict.get(account_id)
        if self.settings_path:
            self.current_hint = get_current_datacenter(self.settings_path)
            self.file_path_display = self.settings_path
            
            current_display = "Default (Auto)"
            for name, hint in SERVERS.items():
                if hint == self.current_hint:
                    current_display = name
                    break
            self.selected_server = current_display
            if not silent:
                self.show_toast(f"Account Loaded: {account_id[:8]}...")
        else:
            self.show_toast("Failed to load account!", is_error=True)

    @slint.callback
    def sort_mode_changed(self, mode):
        self.sort_mode = mode
        self.update_server_list()

    def update_server_list(self):
        if self.sort_mode == "az":
            names = sorted([s["name"] for s in SERVERS_DATA])
            self.server_list = slint.ListModel(["Default (Auto)"] + names)
        else:
            # Group by continent
            continents = {}
            for s in SERVERS_DATA:
                c = s["continent"]
                if c not in continents:
                    continents[c] = []
                continents[c].append(s["name"])
            
            # Sort continents A-Z
            sorted_continents = sorted(continents.items())
            
            flat_list = ["Default (Auto)"]
            for continent, servers in sorted_continents:
                flat_list.append(f"--- {continent.upper()} ---")
                flat_list.extend(sorted(servers))
            
            self.server_list = slint.ListModel(flat_list)

    @slint.callback
    def account_changed(self, account_id):
        self.load_account_settings(account_id)

    @slint.callback
    def check_selection(self, value):
        if "---" in value:
            self.show_toast("Cannot select region headers", is_error=True)
            self.selected_server = "Default (Auto)"
            return True
        return False

    @slint.callback
    def start_update(self):
        self.show_toast("Starting download...")
        # This would pass the actual URL from the GitHub release to the thread
        # For now, we use a placeholder
        fake_url = "https://github.com/OwlWorksInnovations/r6-server-switcher/releases/latest/download/R6ServerSwitcher.exe"
        threading.Thread(target=download_and_restart, args=(fake_url,), daemon=True).start()

    @slint.callback
    def apply_changes(self, server_display_name):
        if "---" in server_display_name:
            self.show_toast("Cannot select region headers", is_error=True)
            self.selected_server = "Default (Auto)"
            return

        hint = SERVERS.get(server_display_name, "default")
        success = set_datacenter(self.settings_path, hint)
        if success:
            self.show_toast(f"Saved: {server_display_name}")
            # Update history safely avoiding headers
            try:
                # 1. Ignore if it's a category header (contains ---)
                if "---" in server_display_name:
                    return

                # 2. Only add if it's a known valid server
                if server_display_name in SERVERS:
                    if server_display_name in self._history_list:
                        self._history_list.remove(server_display_name)
                    self._history_list.insert(0, server_display_name)
                    self._history_list = self._history_list[:3]
                    
                    # Sync to stable UI properties
                    self.sync_history_to_ui()
                    self.save_history()
            except Exception as e:
                print(f"History update failed: {e}")
        else:
            self.show_toast("Error saving changes!", is_error=True)

    @slint.callback
    def reset_to_default(self):
        success = set_datacenter(self.settings_path, "default")
        if success:
            self.show_toast("Settings Reset to Default")
            self.selected_server = "Default (Auto)"
        else:
            self.show_toast("Error resetting settings!", is_error=True)

# Update System Configuration
VERSION = "1.1.2" # Official Release Version
# Placeholder: The user will replace this once they have a repo
REPO_URL = "https://api.github.com/repos/OwlWorksInnovations/r6-server-switcher/releases/latest"

def check_updates_background(window_instance):
    """ Checks for updates in a separate thread to avoid UI freezing """
    import requests
    import time
    
    # Wait for app to stabilize
    time.sleep(2)
    
    try:
        # Check for updates from GitHub
        response = requests.get(REPO_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get("tag_name", "v1.0.0").replace("v", "")
            
            # Simple version comparison
            if latest_version != VERSION:
                # Schedule the UI update on the main thread
                def do_update():
                    window_instance.update_version = latest_version
                    window_instance.update_available = True
                
                slint.invoke_from_event_loop(do_update)
    except Exception as e:
        print(f"Update check failed: {e}")

# Application Lifecycle Control
restore_event = threading.Event()
restore_event.set() # Show window on initial launch

def on_tray_show(icon, item):
    # Signaling the main thread to create a new window instance
    restore_event.set()

def on_tray_exit(icon, item):
    icon.stop()
    # Force exit the entire process
    os._exit(0)

def setup_tray():
    menu = pystray.Menu(
        pystray.MenuItem("Show Switcher", on_tray_show, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_tray_exit)
    )
    icon = pystray.Icon("r6_switcher", create_tray_icon_image(), "R6 Server Switcher", menu)
    icon.run_detached()

def download_and_restart(download_url):
    """ Downloads the new EXE and handles the swap/restart """
    import requests
    import subprocess
    import tempfile
    
    try:
        current_exe = sys.executable
        if not current_exe.endswith(".exe"):
            print("Not running from EXE, skipping update swap.")
            return

        temp_dir = tempfile.gettempdir()
        new_exe_path = os.path.join(temp_dir, "R6ServerSwitcher_new.exe")
        
        # Download
        print(f"Downloading update from {download_url}...")
        r = requests.get(download_url, stream=True)
        with open(new_exe_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                
        # Create a batch script to swap the files
        # It waits for the current process to exit, copies the new file over, restarts it, and deletes itself.
        bat_content = f"""
@echo off
timeout /t 2 /nobreak > NUL
move /y "{new_exe_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
        bat_path = os.path.join(temp_dir, "update_r6_switcher.bat")
        with open(bat_path, 'w') as f:
            f.write(bat_content)
            
        # Launch the batch script detached
        subprocess.Popen(["cmd.exe", "/c", bat_path], shell=True, creationflags=subprocess.DETACHED_PROCESS)
        
        # Exit the current app
        os._exit(0)
    except Exception as e:
        print(f"Update error: {e}")

if __name__ == "__main__":
    setup_tray()
    
    # Process Loop: Wait for restoration signals from the tray
    try:
        while True:
            # Wait until the tray icon (or startup) signals to show the window
            restore_event.wait()
            
            # Create a fresh UI instance
            # This ensures we always have a valid window handle
            app_instance = MainWindow()
            
            # Start background update check
            threading.Thread(target=check_updates_background, args=(app_instance,), daemon=True).start()
            
            # Reset the event so we don't loop infinitely
            restore_event.clear()
            
            # run() blocks the main thread until the window is closed via the 'X' button
            app_instance.run()
            
            # Once window is closed, we go back to waiting for the next restore_event.set()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Main loop error: {e}")
        os._exit(1)
