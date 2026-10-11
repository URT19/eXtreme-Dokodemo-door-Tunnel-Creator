"""CLI helpers, process, json, IP detection."""
import datetime
import json
import os
import re
import subprocess
from pathlib import Path

from .constants import (
    BACKUP_DIR,
    BASE_DIR,
    CONFIG_DIR,
    DATA_DIR,
    LOG_DIR,
    SETTINGS_FILE,
    TEST_DIR,
)


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


def colorize(text, color):
    return f"{color}{text}{C.RESET}"


def ok(msg):
    print(colorize(f"  [OK] {msg}", C.GREEN))


def err(msg):
    print(colorize(f"  [ERR] {msg}", C.RED))


def warn(msg):
    print(colorize(f"  [WARN] {msg}", C.YELLOW))


def info(msg):
    print(colorize(f"  [INFO] {msg}", C.CYAN))


def step(msg):
    print(colorize(f"  [*] {msg}", C.BLUE))


def title(msg):
    print(colorize(msg, C.MAGENTA + C.BOLD))


def line(char="-", length=62):
    print(colorize(char * length, C.DIM))


def screen(heading, subtitle=""):
    width = 62
    bar = "═" * width
    print(colorize("  ╔" + bar + "╗", C.MAGENTA))
    print(colorize("  ║ ", C.MAGENTA) + colorize(heading.center(width - 1), C.WHITE + C.BOLD) + colorize("║", C.MAGENTA))
    if subtitle:
        print(colorize("  ║ ", C.MAGENTA) + colorize(subtitle.center(width - 1), C.CYAN) + colorize("║", C.MAGENTA))
    print(colorize("  ╚" + bar + "╝", C.MAGENTA))


def status_row(label, value, good=None):
    label_s = colorize(f"  {label:<16}", C.DIM)
    if good is True:
        value_s = colorize(str(value), C.GREEN + C.BOLD)
    elif good is False:
        value_s = colorize(str(value), C.RED + C.BOLD)
    else:
        value_s = colorize(str(value), C.WHITE)
    print(label_s + value_s)


def menu_block(items):
    """items: list of (key, label, hint)."""
    print(colorize("  ┌" + "─" * 60 + "┐", C.BLUE))
    for key, label, hint in items:
        badge = f"\033[30;103m {str(key):>2} \033[0m"
        label_s = colorize(f"  {label}", C.WHITE + C.BOLD)
        hint_s = colorize(f"   {hint}", C.DIM) if hint else ""
        print(colorize("  │", C.BLUE) + f" {badge}{label_s}{hint_s}")
    print(colorize("  └" + "─" * 60 + "┘", C.BLUE))


def section(text):
    print(colorize(f"\n  ▸ {text}", C.CYAN + C.BOLD))


def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")


def pause():
    input(colorize("\n  Press Enter to continue...", C.DIM))


def ask(prompt, default=None):
    full = f"  {prompt} [{default}]: " if default is not None else f"  {prompt}: "
    ans = input(colorize(full, C.WHITE)).strip()
    if not ans and default is not None:
        return default
    return ans


def ask_yes_no(prompt, default=True):
    suffix = "[Y/n]" if default else "[y/N]"
    ans = input(colorize(f"  {prompt} {suffix}: ", C.WHITE)).strip().lower()
    if not ans:
        return default
    return ans in ("y", "yes")


def is_root():
    return os.geteuid() == 0


def run_cmd(cmd, capture=True, check=False, timeout=None):
    try:
        result = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            capture_output=capture,
            text=True,
            check=check,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "Timeout"
    except Exception as e:
        return 1, "", str(e)


def ensure_dirs():
    for d in (BASE_DIR, DATA_DIR, CONFIG_DIR, BACKUP_DIR, LOG_DIR, TEST_DIR):
        d.mkdir(parents=True, exist_ok=True)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def now_stamp():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def find_xray_binary():
    for c in ("/usr/local/bin/xray", "/usr/bin/xray", "/opt/xray/xray"):
        if Path(c).exists() and os.access(c, os.X_OK):
            return c
    rc, out, _ = run_cmd("which xray")
    if rc == 0 and out.strip():
        return out.strip()
    return None


def get_public_ip():
    settings = read_json(SETTINGS_FILE, {}) or {}
    saved = (settings.get("public_ip") or "").strip()
    if saved:
        return saved
    sources = [
        "curl -s --max-time 5 https://ifconfig.me",
        "curl -s --max-time 5 https://ipinfo.io/ip",
        "curl -s --max-time 5 https://api.ipify.org",
    ]
    for cmd in sources:
        rc, out, _ = run_cmd(cmd, timeout=8)
        ip = (out or "").strip()
        if rc == 0 and re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
            return ip
    return ""


def is_port_listening(port):
    rc, out, _ = run_cmd(f"ss -tlnp 2>/dev/null | grep ':{int(port)} '")
    return rc == 0 and bool((out or "").strip())
