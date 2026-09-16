"""Gestione dell'avvio automatico dell'app all'accensione del PC (Windows/Linux/macOS)."""
from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "StickyPy"


def _get_executable_command() -> str:
    """Comando da lanciare all'avvio: l'eseguibile PyInstaller oppure `python main.py`."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    main_script = Path(__file__).resolve().parent.parent / "main.py"
    return f'"{sys.executable}" "{main_script}"'


def _linux_desktop_path() -> Path:
    return Path.home() / ".config" / "autostart" / f"{APP_NAME.lower()}.desktop"


def is_enabled() -> bool:
    if sys.platform.startswith("win"):
        return _windows_is_enabled()
    if sys.platform == "darwin":
        return _macos_plist_path().exists()
    return _linux_desktop_path().exists()


def enable() -> None:
    if sys.platform.startswith("win"):
        _windows_enable()
    elif sys.platform == "darwin":
        _macos_enable()
    else:
        _linux_enable()


def disable() -> None:
    if sys.platform.startswith("win"):
        _windows_disable()
    elif sys.platform == "darwin":
        _macos_plist_path().unlink(missing_ok=True)
    else:
        _linux_desktop_path().unlink(missing_ok=True)


# ---------- Linux ----------
def _linux_enable() -> None:
    path = _linux_desktop_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        f"Exec={_get_executable_command()}\n"
        "X-GNOME-Autostart-enabled=true\n"
    )
    path.write_text(content, encoding="utf-8")


# ---------- macOS ----------
def _macos_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"com.{APP_NAME.lower()}.plist"


def _macos_enable() -> None:
    path = _macos_plist_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    exe = sys.executable if getattr(sys, "frozen", False) else sys.executable
    args = [exe] if getattr(sys, "frozen", False) else [
        exe, str(Path(__file__).resolve().parent.parent / "main.py")
    ]
    args_xml = "\n".join(f"        <string>{a}</string>" for a in args)
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{APP_NAME.lower()}</string>
    <key>ProgramArguments</key>
    <array>
{args_xml}
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
    path.write_text(content, encoding="utf-8")


# ---------- Windows ----------
def _windows_registry_key():
    import winreg  # disponibile solo su Windows

    return winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"


def _windows_is_enabled() -> bool:
    import winreg

    hive, subkey = _windows_registry_key()
    try:
        with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False


def _windows_enable() -> None:
    import winreg

    hive, subkey = _windows_registry_key()
    with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_executable_command())


def _windows_disable() -> None:
    import winreg

    hive, subkey = _windows_registry_key()
    try:
        with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass
