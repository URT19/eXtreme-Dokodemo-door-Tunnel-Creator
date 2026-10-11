"""Server database."""
import uuid

from .config_builder import build_server_objects
from .constants import DEFAULT_SERVERS, DEFAULT_SETTINGS, SERVERS_FILE, SETTINGS_FILE
from .utils import now_iso, read_json, write_json


def load_settings():
    data = read_json(SETTINGS_FILE, dict(DEFAULT_SETTINGS)) or dict(DEFAULT_SETTINGS)
    for k, v in DEFAULT_SETTINGS.items():
        data.setdefault(k, v)
    return data


def save_settings(data):
    write_json(SETTINGS_FILE, data)


def load_servers():
    data = read_json(SERVERS_FILE, dict(DEFAULT_SERVERS))
    if not isinstance(data, dict) or not isinstance(data.get("servers"), list):
        return dict(DEFAULT_SERVERS)
    return data


def save_servers(data):
    data["last_updated"] = now_iso()
    write_json(SERVERS_FILE, data)


def list_servers(enabled_only=False):
    servers = load_servers().get("servers", [])
    if enabled_only:
        return [s for s in servers if s.get("enabled", True)]
    return servers


def find_server(identifier):
    ident = str(identifier).strip().lower()
    for i, srv in enumerate(load_servers().get("servers", [])):
        if srv.get("id", "").lower() == ident or srv.get("name", "").lower() == ident:
            return i, srv
    return None, None


def check_conflicts(name, listen_port, ignore_id=None):
    name_l = (name or "").strip().lower()
    for srv in load_servers().get("servers", []):
        if ignore_id and srv.get("id") == ignore_id:
            continue
        if name_l and srv.get("name", "").lower() == name_l:
            return True, f"Name '{name}' already exists"
        if listen_port and listen_port > 0 and srv.get("listen_port") == listen_port:
            return True, f"Port {listen_port} already used by '{srv.get('name')}'"
    return False, ""


def add_server(parsed, name, listen_port, enabled=True):
    conflict, msg = check_conflicts(name, listen_port)
    if conflict:
        raise ValueError(msg)
    settings = load_settings()
    safe, inbound, outbound, routing = build_server_objects(parsed, name, listen_port, settings)
    server = {
        "id": "srv_" + uuid.uuid4().hex[:8],
        "name": safe,
        "enabled": enabled,
        "listen_port": int(listen_port),
        "protocol": parsed.get("protocol"),
        "remote_address": parsed.get("address"),
        "remote_port": parsed.get("port"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "inbound": inbound,
        "outbound": outbound,
        "routing": routing,
        "parsed": parsed,
        "raw_link": parsed.get("raw_link", ""),
    }
    data = load_servers()
    data["servers"].append(server)
    save_servers(data)
    return server


def _mutate(identifier, fn):
    idx, srv = find_server(identifier)
    if srv is None:
        return False, "Server not found"
    data = load_servers()
    msg = fn(data["servers"][idx])
    if isinstance(msg, str):
        return False, msg
    data["servers"][idx]["updated_at"] = now_iso()
    save_servers(data)
    return True, "OK"


def set_enabled(identifier, enabled):
    return _mutate(identifier, lambda s: s.__setitem__("enabled", enabled))


def delete_server(identifier):
    idx, srv = find_server(identifier)
    if srv is None:
        return False, "Server not found"
    data = load_servers()
    data["servers"].pop(idx)
    save_servers(data)
    return True, "OK"


def rename_server(identifier, new_name):
    new_name = new_name.strip().replace(" ", "-")
    if not new_name:
        return False, "Empty name"
    _, srv = find_server(identifier)
    if srv is None:
        return False, "Server not found"
    conflict, msg = check_conflicts(new_name, -1, ignore_id=srv.get("id"))
    if conflict and "Name" in msg:
        return False, msg

    def apply(server):
        in_tag = f"in-{new_name}"
        out_tag = f"out-{new_name}"
        server["name"] = new_name
        server["inbound"]["tag"] = in_tag
        server["outbound"]["tag"] = out_tag
        server["routing"]["inboundTag"] = [in_tag]
        server["routing"]["outboundTag"] = out_tag

    return _mutate(identifier, apply)


def change_port(identifier, new_port):
    if not isinstance(new_port, int) or not 1 <= new_port <= 65535:
        return False, "Invalid port (1-65535)"
    _, srv = find_server(identifier)
    if srv is None:
        return False, "Server not found"
    conflict, msg = check_conflicts("", new_port, ignore_id=srv.get("id"))
    if conflict and "Port" in msg:
        return False, msg

    def apply(server):
        server["listen_port"] = new_port
        server["inbound"]["port"] = new_port

    return _mutate(identifier, apply)


def update_link(identifier, parsed):
    _, srv = find_server(identifier)
    if srv is None:
        return False, "Server not found"
    settings = load_settings()
    safe, inbound, outbound, routing = build_server_objects(
        parsed, srv["name"], srv["listen_port"], settings
    )

    def apply(server):
        server["protocol"] = parsed.get("protocol")
        server["remote_address"] = parsed.get("address")
        server["remote_port"] = parsed.get("port")
        server["inbound"] = inbound
        server["outbound"] = outbound
        server["routing"] = routing
        server["parsed"] = parsed
        server["raw_link"] = parsed.get("raw_link", "")
        server["name"] = safe

    return _mutate(identifier, apply)
