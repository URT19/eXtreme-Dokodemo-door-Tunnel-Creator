"""Xray install, systemd, config write, restart."""
import os
from pathlib import Path

from .config_builder import build_full_config
from .constants import (
    DEFAULT_SERVERS,
    DEFAULT_SETTINGS,
    SERVICE_FILE,
    SERVICE_NAME,
    SETTINGS_FILE,
    XRAY_BIN_DEFAULT,
    XRAY_CONFIG,
    XRAY_INSTALL_URL,
)
from .store import list_servers, load_settings, save_settings
from .utils import (
    err,
    find_xray_binary,
    get_public_ip,
    info,
    is_port_listening,
    ok,
    run_cmd,
    warn,
    write_json,
)


def detect_os():
    if Path("/etc/debian_version").exists():
        return "debian"
    if Path("/etc/redhat-release").exists():
        return "redhat"
    if Path("/etc/alpine-release").exists():
        return "alpine"
    if Path("/etc/arch-release").exists():
        return "arch"
    return "unknown"


def check_dependencies():
    missing = []
    for tool in ("curl", "systemctl", "unzip"):
        rc, _, _ = run_cmd(f"command -v {tool}")
        if rc != 0:
            missing.append(tool)
    return missing


def install_system_deps(missing):
    os_type = detect_os()
    if os_type == "debian":
        run_cmd("apt-get update -qq")
        rc, _, e = run_cmd("apt-get install -y " + " ".join(missing))
    elif os_type == "redhat":
        rc, _, e = run_cmd("yum install -y " + " ".join(missing))
    elif os_type == "alpine":
        run_cmd("apk update")
        rc, _, e = run_cmd("apk add " + " ".join(missing))
    elif os_type == "arch":
        rc, _, e = run_cmd("pacman -Sy --noconfirm " + " ".join(missing))
    else:
        err(f"Unsupported OS: {os_type}")
        return False
    if rc != 0:
        err(f"Package install failed: {e}")
        return False
    ok("System dependencies installed")
    return True


def install_xray():
    tmp = "/tmp/xray-install.sh"
    downloaded = False
    for method in (
        f"curl -fsSL {XRAY_INSTALL_URL} -o {tmp}",
        f"wget -q {XRAY_INSTALL_URL} -O {tmp}",
    ):
        rc, _, _ = run_cmd(method)
        if rc == 0 and Path(tmp).exists():
            downloaded = True
            break
    if not downloaded:
        err("Failed to download Xray install script")
        return False
    rc, _, e = run_cmd(f"bash {tmp} install")
    if rc != 0:
        err("Xray installation failed")
        if e:
            print(e[:500])
        return False
    ok("Xray installed")
    try:
        os.remove(tmp)
    except OSError:
        pass
    return True


def ensure_prerequisites():
    """Install missing OS packages, Xray, proxychains4 and speedtest-cli. No prompts."""
    os_type = detect_os()
    packages = {
        "debian": ["python3", "curl", "unzip", "ca-certificates", "proxychains4", "speedtest-cli"],
        "redhat": ["python3", "curl", "unzip", "ca-certificates", "proxychains-ng"],
        "alpine": ["python3", "curl", "unzip", "ca-certificates", "proxychains-ng"],
        "arch": ["python", "curl", "unzip", "ca-certificates", "proxychains-ng"],
    }.get(os_type, [])
    missing_bins = []
    for tool in ("python3", "curl", "unzip"):
        rc, _, _ = run_cmd(f"command -v {tool}")
        if rc != 0:
            missing_bins.append(tool)
    rc, _, _ = run_cmd("command -v proxychains4")
    need_proxy = rc != 0
    rc, _, _ = run_cmd("command -v speedtest-cli")
    need_speed = rc != 0
    if packages and (missing_bins or need_proxy or need_speed):
        info("Installing missing packages...")
        if not install_system_deps(packages):
            warn("Some packages could not be installed")
    if need_speed:
        rc, _, _ = run_cmd("command -v speedtest-cli")
        if rc != 0:
            info("Installing speedtest-cli with pip...")
            rc, _, e = run_cmd("pip3 install speedtest-cli --break-system-packages", timeout=180)
            if rc != 0:
                rc, _, e = run_cmd("pip3 install speedtest-cli", timeout=180)
            if rc != 0:
                warn((e or "speedtest-cli install failed")[:200])
    if not find_xray_binary():
        info("Installing Xray...")
        if not install_xray() or not find_xray_binary():
            err("Xray is required and could not be installed")
            return False
        ok(f"Xray ready: {find_xray_binary()}")
    else:
        ok(f"Xray found: {find_xray_binary()}")
    return True


def write_runtime_config():
    """Always rebuild relay objects from parsed so old 1.9 protocol outbounds
    are replaced with freedom+redirect on apply."""
    from .config_builder import build_server_objects
    from .store import load_servers, save_servers

    settings = load_settings()
    data = load_servers()
    changed = False
    for srv in data.get("servers", []):
        parsed = srv.get("parsed") or {}
        if not parsed.get("address"):
            continue
        safe, inbound, outbound, routing = build_server_objects(
            parsed, srv.get("name") or "server", srv.get("listen_port"), settings
        )
        if srv.get("outbound") != outbound or srv.get("inbound") != inbound:
            srv["name"] = safe
            srv["inbound"] = inbound
            srv["outbound"] = outbound
            srv["routing"] = routing
            changed = True
    if changed:
        save_servers(data)
    config = build_full_config(data.get("servers", []), settings)
    write_json(XRAY_CONFIG, config)
    return config


def xray_test_config():
    xray = find_xray_binary()
    if not xray:
        return False, "Xray binary not found"
    if not XRAY_CONFIG.exists():
        write_runtime_config()
    rc, out, e = run_cmd(f"{xray} run -test -config {XRAY_CONFIG}")
    if rc != 0:
        rc, out2, e2 = run_cmd(f"{xray} -test -config {XRAY_CONFIG}")
        out = (out or "") + (out2 or "")
        e = (e or "") + (e2 or "")
    return rc == 0, ((out or "") + (e or "")).strip()


def service_exists():
    return SERVICE_FILE.exists()


def service_is_active():
    rc, out, _ = run_cmd(f"systemctl is-active {SERVICE_NAME}")
    return rc == 0 and (out or "").strip() == "active"


def create_systemd_service():
    xray_bin = find_xray_binary() or XRAY_BIN_DEFAULT
    content = f"""[Unit]
Description=eXrelay Xray Service
After=network.target nss-lookup.target

[Service]
Type=simple
User=root
ExecStart={xray_bin} run -config {XRAY_CONFIG}
Restart=on-failure
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
"""
    SERVICE_FILE.write_text(content)
    run_cmd("systemctl daemon-reload")


def service_start():
    rc, out, e = run_cmd(f"systemctl start {SERVICE_NAME}")
    return rc == 0, "Started" if rc == 0 else (e or out or "").strip()


def service_stop():
    rc, out, e = run_cmd(f"systemctl stop {SERVICE_NAME}")
    return rc == 0, "Stopped" if rc == 0 else (e or out or "").strip()


def service_restart():
    rc, out, e = run_cmd(f"systemctl restart {SERVICE_NAME}")
    return rc == 0, "Restarted" if rc == 0 else (e or out or "").strip()


def apply_and_restart():
    info("Writing single config.json (inbounds + freedom redirects)...")
    write_runtime_config()
    ok(f"Wrote {XRAY_CONFIG}")
    success, output = xray_test_config()
    if not success:
        err("Config test failed")
        if output:
            print(output[:1200])
        return False
    ok("Config is valid")
    if not service_exists():
        create_systemd_service()
        run_cmd(f"systemctl enable {SERVICE_NAME}")
    success, msg = service_restart()
    if not success:
        err(msg)
        return False
    ok(msg)
    bad = False
    for srv in list_servers(enabled_only=True):
        if not is_port_listening(srv.get("listen_port", 0)):
            warn(f"Port {srv.get('listen_port')} ({srv.get('name')}) is not listening yet")
            bad = True
    if not bad and list_servers(enabled_only=True):
        ok("Relay ports are listening")
    return True


def bootstrap_files():
    if not SETTINGS_FILE.exists():
        write_json(SETTINGS_FILE, dict(DEFAULT_SETTINGS))
    from .constants import SERVERS_FILE
    if not SERVERS_FILE.exists():
        write_json(SERVERS_FILE, dict(DEFAULT_SERVERS))
    ip = get_public_ip()
    if ip:
        settings = load_settings()
        if not settings.get("public_ip"):
            settings["public_ip"] = ip
            save_settings(settings)
            ok(f"Public IP: {ip}")
    write_runtime_config()
