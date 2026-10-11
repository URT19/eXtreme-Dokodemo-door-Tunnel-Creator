"""Share-link parsers: vless, vmess, trojan, shadowsocks."""
import base64
import json
from urllib.parse import parse_qs, unquote, urlparse

from .utils import safe_int


class ParseError(Exception):
    pass


def _b64_decode(data):
    data = data.strip().replace("-", "+").replace("_", "/")
    pad = len(data) % 4
    if pad:
        data += "=" * (4 - pad)
    try:
        return base64.b64decode(data).decode("utf-8")
    except Exception as e:
        raise ParseError(f"Base64 decode failed: {e}") from e


def b64_encode(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.b64encode(data).decode("utf-8")


def _split_alpn(value):
    if not value:
        return []
    return [x.strip() for x in str(value).split(",") if x.strip()]


def parse_vless(link):
    parsed = urlparse("http://" + link[len("vless://") :])
    if not parsed.hostname or not parsed.username:
        raise ParseError("Invalid vless link")
    try:
        port = parsed.port or 443
    except ValueError as e:
        raise ParseError("Invalid port") from e
    params = parse_qs(parsed.query, keep_blank_values=True)

    def get(key, default=""):
        vals = params.get(key)
        return vals[0] if vals else default

    security = get("security", "none").lower()
    if security not in ("none", "tls", "reality", "xtls"):
        security = "none"
    network = get("type", "tcp").lower()
    result = {
        "protocol": "vless",
        "address": parsed.hostname,
        "port": port,
        "uuid": unquote(parsed.username),
        "flow": get("flow", ""),
        "network": network,
        "security": security,
        "sni": get("sni", ""),
        "fingerprint": get("fp", ""),
        "alpn": _split_alpn(get("alpn", "")),
        "publicKey": get("pbk", ""),
        "shortId": get("sid", ""),
        "spiderX": get("spx", ""),
        "path": get("path", ""),
        "host": get("host", ""),
        "serviceName": get("serviceName", ""),
        "headerType": get("headerType", ""),
        "allowInsecure": get("allowInsecure", "0") in ("1", "true"),
        "name": unquote(parsed.fragment) if parsed.fragment else "",
        "raw_link": link,
    }
    if security in ("tls", "reality") and not result["sni"]:
        result["sni"] = parsed.hostname
    if security in ("tls", "reality") and not result["fingerprint"]:
        result["fingerprint"] = "chrome"
    if network in ("ws", "http") and not result["path"]:
        result["path"] = "/"
    return result


def parse_vmess(link):
    data = json.loads(_b64_decode(link[len("vmess://") :].strip()))
    if not isinstance(data, dict):
        raise ParseError("vmess payload is not an object")
    address = str(data.get("add", "")).strip()
    uuid = str(data.get("id", "")).strip()
    if not address or not uuid:
        raise ParseError("Missing add/id in vmess")
    network = str(data.get("net", "tcp")).lower()
    if network == "h2":
        network = "http"
    tls_flag = str(data.get("tls", "")).lower()
    security = "tls" if tls_flag in ("tls", "1", "true") else "none"
    result = {
        "protocol": "vmess",
        "address": address,
        "port": safe_int(data.get("port", 443), 443),
        "uuid": uuid,
        "alterId": safe_int(data.get("aid", 0), 0),
        "security_cipher": str(data.get("scy", "auto")).lower() or "auto",
        "network": network,
        "security": security,
        "sni": str(data.get("sni", "")).strip(),
        "fingerprint": str(data.get("fp", "")).strip(),
        "alpn": _split_alpn(str(data.get("alpn", ""))),
        "path": str(data.get("path", "")).strip(),
        "host": str(data.get("host", "")).strip(),
        "serviceName": str(data.get("path", "")).strip() if network == "grpc" else "",
        "headerType": str(data.get("type", "")).strip(),
        "allowInsecure": False,
        "name": str(data.get("ps", "")).strip(),
        "raw_link": link,
        "publicKey": "",
        "shortId": "",
        "spiderX": "",
        "flow": "",
    }
    if security == "tls" and not result["sni"]:
        result["sni"] = address
    if network in ("ws", "http") and not result["path"]:
        result["path"] = "/"
    return result


def parse_trojan(link):
    parsed = urlparse("http://" + link[len("trojan://") :])
    if not parsed.hostname or not parsed.username:
        raise ParseError("Invalid trojan link")
    try:
        port = parsed.port or 443
    except ValueError as e:
        raise ParseError("Invalid port") from e
    params = parse_qs(parsed.query, keep_blank_values=True)

    def get(key, default=""):
        vals = params.get(key)
        return vals[0] if vals else default

    security = get("security", "tls").lower()
    if security not in ("tls", "none", "reality"):
        security = "tls"
    network = get("type", "tcp").lower()
    result = {
        "protocol": "trojan",
        "address": parsed.hostname,
        "port": port,
        "password": unquote(parsed.username),
        "network": network,
        "security": security,
        "sni": get("sni", ""),
        "fingerprint": get("fp", ""),
        "alpn": _split_alpn(get("alpn", "")),
        "publicKey": get("pbk", ""),
        "shortId": get("sid", ""),
        "spiderX": get("spx", ""),
        "path": get("path", ""),
        "host": get("host", ""),
        "serviceName": get("serviceName", ""),
        "headerType": get("headerType", ""),
        "allowInsecure": get("allowInsecure", "0") in ("1", "true"),
        "name": unquote(parsed.fragment) if parsed.fragment else "",
        "raw_link": link,
        "uuid": "",
        "flow": "",
    }
    if security in ("tls", "reality") and not result["sni"]:
        result["sni"] = parsed.hostname
    if network in ("ws", "http") and not result["path"]:
        result["path"] = "/"
    return result


def parse_shadowsocks(link):
    body = link[len("ss://") :]
    fragment = ""
    if "#" in body:
        body, fragment = body.rsplit("#", 1)
        fragment = unquote(fragment)
    if "?" in body:
        body = body.split("?", 1)[0]
    if "@" not in body:
        decoded = _b64_decode(body)
        if "@" not in decoded:
            raise ParseError("Invalid shadowsocks payload")
        userinfo, hostport = decoded.rsplit("@", 1)
    else:
        userinfo, hostport = body.rsplit("@", 1)
        try:
            userinfo = _b64_decode(userinfo)
        except ParseError:
            pass
    if ":" not in userinfo or ":" not in hostport:
        raise ParseError("Invalid shadowsocks userinfo/host")
    method, password = userinfo.split(":", 1)
    address, port_str = hostport.rsplit(":", 1)
    port = safe_int(port_str, 0)
    if not address or port <= 0 or not method or not password:
        raise ParseError("Invalid shadowsocks fields")
    return {
        "protocol": "shadowsocks",
        "address": address,
        "port": port,
        "method": method.lower(),
        "password": password,
        "network": "tcp",
        "security": "none",
        "name": fragment,
        "raw_link": link,
        "uuid": "",
        "flow": "",
        "sni": "",
        "fingerprint": "",
        "alpn": [],
        "publicKey": "",
        "shortId": "",
        "spiderX": "",
        "path": "",
        "host": "",
        "serviceName": "",
        "headerType": "",
        "allowInsecure": False,
    }


def parse_link(link):
    if not link or not isinstance(link, str):
        raise ParseError("Empty link")
    link = link.strip().split(" ", 1)[0]
    lower = link.lower()
    if lower.startswith("vless://"):
        return parse_vless(link)
    if lower.startswith("vmess://"):
        return parse_vmess(link)
    if lower.startswith("trojan://"):
        return parse_trojan(link)
    if lower.startswith("ss://"):
        return parse_shadowsocks(link)
    raise ParseError("Unknown protocol. Supported: vless, vmess, trojan, ss")
