"""Paths, defaults, version."""
from pathlib import Path

VERSION = "2.0.0"
BASE_DIR = Path("/opt/exrelay")
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config" / "xray"
BACKUP_DIR = BASE_DIR / "backups"
LOG_DIR = BASE_DIR / "logs"
TEST_DIR = BASE_DIR / "test"
PKG_DIR = BASE_DIR / "pkg"

SERVERS_FILE = DATA_DIR / "servers.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
XRAY_CONFIG = CONFIG_DIR / "config.json"
XRAY_BIN_DEFAULT = "/usr/local/bin/xray"
SERVICE_NAME = "exrelay-xray"
SERVICE_FILE = Path(f"/etc/systemd/system/{SERVICE_NAME}.service")
INSTALL_PATH = Path("/usr/local/bin/exrelay")
XRAY_INSTALL_URL = "https://github.com/XTLS/Xray-install/raw/main/install-release.sh"
API_PORT = 10085
TEST_SOCKS_PORT = 18999

DEFAULT_SETTINGS = {
    "default_listen_host": "0.0.0.0",
    "default_udp": True,
    "default_listen_port_start": 443,
    "log_level": "warning",
    "public_ip": "",
}

DEFAULT_SERVERS = {"version": 2, "last_updated": None, "servers": []}
