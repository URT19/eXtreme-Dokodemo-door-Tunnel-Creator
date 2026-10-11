"""User-facing share links pointed at the Iran relay IP."""
import json
from urllib.parse import quote

from .parsers import b64_encode


def generate_user_link(srv, iran_ip):
    parsed = srv.get("parsed") or {}
    protocol = parsed.get("protocol", "")
    name = srv.get("name", "server")
    port = srv.get("listen_port", 443)
    if not protocol or not iran_ip:
        return ""

    def qparams(keys):
        params = []
        for key, value in keys:
            if value in (None, "", [], {}):
                continue
            if isinstance(value, list):
                value = ",".join(value)
            params.append(f"{key}={quote(str(value), safe='')}")
        return "&".join(params)

    if protocol == "vless":
        query = qparams([
            ("type", parsed.get("network", "tcp")),
            ("security", parsed.get("security") if parsed.get("security") != "none" else ""),
            ("sni", parsed.get("sni")),
            ("fp", parsed.get("fingerprint")),
            ("alpn", parsed.get("alpn")),
            ("pbk", parsed.get("publicKey")),
            ("sid", parsed.get("shortId")),
            ("spx", parsed.get("spiderX")),
            ("path", parsed.get("path")),
            ("host", parsed.get("host")),
            ("serviceName", parsed.get("serviceName")),
            ("flow", parsed.get("flow")),
            ("headerType", parsed.get("headerType")),
        ])
        return f"vless://{parsed.get('uuid')}@{iran_ip}:{port}?{query}#{quote(name)}-via-IR"

    if protocol == "vmess":
        payload = {
            "v": "2",
            "ps": f"{name}-via-IR",
            "add": iran_ip,
            "port": str(port),
            "id": parsed.get("uuid", ""),
            "aid": str(parsed.get("alterId", 0)),
            "scy": parsed.get("security_cipher", "auto"),
            "net": parsed.get("network", "tcp"),
            "type": parsed.get("headerType") or "none",
            "host": parsed.get("host", ""),
            "path": parsed.get("serviceName", "") if parsed.get("network") == "grpc" else parsed.get("path", ""),
            "tls": parsed.get("security", "none"),
            "sni": parsed.get("sni", ""),
            "fp": parsed.get("fingerprint", ""),
        }
        if parsed.get("alpn"):
            payload["alpn"] = ",".join(parsed["alpn"])
        return "vmess://" + b64_encode(json.dumps(payload, ensure_ascii=False))

    if protocol == "trojan":
        query = qparams([
            ("type", parsed.get("network", "tcp")),
            ("security", parsed.get("security")),
            ("sni", parsed.get("sni")),
            ("fp", parsed.get("fingerprint")),
            ("alpn", parsed.get("alpn")),
            ("pbk", parsed.get("publicKey")),
            ("sid", parsed.get("shortId")),
            ("path", parsed.get("path")),
            ("host", parsed.get("host")),
            ("serviceName", parsed.get("serviceName")),
        ])
        return f"trojan://{quote(parsed.get('password') or '', safe='')}@{iran_ip}:{port}?{query}#{quote(name)}-via-IR"

    if protocol == "shadowsocks":
        userinfo = b64_encode(f"{parsed.get('method')}:{parsed.get('password')}")
        return f"ss://{userinfo}@{iran_ip}:{port}#{quote(name)}-via-IR"
    return ""
