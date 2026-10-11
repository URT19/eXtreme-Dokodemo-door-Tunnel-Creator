"""Xray config objects.

Relay model (true TCP/UDP port forward):
  dokodemo-door inbound on the Iran listen port
  -> routing
  -> freedom outbound with settings.redirect = remote_host:remote_port

Bytes are copied as-is. User links keep the original protocol and only
change the address to the Iran public IP. Protocol clients are built
separately for connectivity tests; they are NOT the relay outbound.
"""
from .constants import API_PORT, LOG_DIR


def build_relay_inbound(tag, listen_port, listen_host="0.0.0.0", udp=True):
    return {
        "tag": tag,
        "listen": listen_host,
        "port": int(listen_port),
        "protocol": "dokodemo-door",
        "settings": {
            "network": "tcp,udp" if udp else "tcp",
            "followRedirect": False,
        },
    }


def build_relay_outbound(parsed, tag):
    """Freedom redirect: every accepted connection is dialed to the remote."""
    address = parsed.get("address")
    port = parsed.get("port")
    if not address or not port:
        raise ValueError("Remote address/port missing")
    return {
        "tag": tag,
        "protocol": "freedom",
        "settings": {"redirect": f"{address}:{int(port)}"},
    }


def build_routing_rule(inbound_tag, outbound_tag):
    return {
        "type": "field",
        "inboundTag": [inbound_tag],
        "outboundTag": outbound_tag,
    }


def _stream_settings(parsed):
    network = parsed.get("network") or "tcp"
    security = parsed.get("security") or "none"
    stream = {"network": network}
    if security == "tls":
        tls = {"allowInsecure": bool(parsed.get("allowInsecure", False))}
        if parsed.get("sni"):
            tls["serverName"] = parsed["sni"]
        if parsed.get("fingerprint"):
            tls["fingerprint"] = parsed["fingerprint"]
        if parsed.get("alpn"):
            tls["alpn"] = parsed["alpn"]
        stream["security"] = "tls"
        stream["tlsSettings"] = tls
    elif security == "reality":
        reality = {
            "serverName": parsed.get("sni", ""),
            "fingerprint": parsed.get("fingerprint") or "chrome",
            "publicKey": parsed.get("publicKey", ""),
            "shortId": parsed.get("shortId", ""),
            "spiderX": parsed.get("spiderX", ""),
        }
        stream["security"] = "reality"
        stream["realitySettings"] = {k: v for k, v in reality.items() if v != ""}
    else:
        stream["security"] = "none"

    if network == "ws":
        ws = {"path": parsed.get("path") or "/"}
        if parsed.get("host"):
            ws["headers"] = {"Host": parsed["host"]}
        stream["wsSettings"] = ws
    elif network == "grpc":
        grpc = {}
        if parsed.get("serviceName"):
            grpc["serviceName"] = parsed["serviceName"]
        stream["grpcSettings"] = grpc
    elif network == "http":
        http = {"path": [parsed.get("path") or "/"]}
        if parsed.get("host"):
            http["host"] = [parsed["host"]]
        stream["httpSettings"] = http
    elif network == "httpupgrade":
        hu = {"path": parsed.get("path") or "/"}
        if parsed.get("host"):
            hu["host"] = parsed["host"]
        stream["httpupgradeSettings"] = hu
    return stream


def build_client_outbound(parsed, tag="proxy"):
    """Protocol client used only to test the remote server, not for relay."""
    protocol = parsed.get("protocol")
    address = parsed.get("address")
    port = int(parsed.get("port"))
    stream = _stream_settings(parsed)
    if protocol == "vless":
        user = {"id": parsed.get("uuid"), "encryption": "none"}
        if parsed.get("flow"):
            user["flow"] = parsed["flow"]
        return {
            "tag": tag,
            "protocol": "vless",
            "settings": {"vnext": [{"address": address, "port": port, "users": [user]}]},
            "streamSettings": stream,
        }
    if protocol == "vmess":
        user = {
            "id": parsed.get("uuid"),
            "alterId": parsed.get("alterId", 0),
            "security": parsed.get("security_cipher", "auto"),
        }
        return {
            "tag": tag,
            "protocol": "vmess",
            "settings": {"vnext": [{"address": address, "port": port, "users": [user]}]},
            "streamSettings": stream,
        }
    if protocol == "trojan":
        return {
            "tag": tag,
            "protocol": "trojan",
            "settings": {
                "servers": [{
                    "address": address,
                    "port": port,
                    "password": parsed.get("password"),
                }]
            },
            "streamSettings": stream,
        }
    if protocol == "shadowsocks":
        return {
            "tag": tag,
            "protocol": "shadowsocks",
            "settings": {
                "servers": [{
                    "address": address,
                    "port": port,
                    "method": parsed.get("method"),
                    "password": parsed.get("password"),
                }]
            },
            "streamSettings": {"network": "tcp", "security": "none"},
        }
    raise ValueError(f"Unsupported protocol: {protocol}")


def build_server_objects(parsed, name, listen_port, settings):
    safe = name.strip().replace(" ", "-")
    in_tag = f"in-{safe}"
    out_tag = f"out-{safe}"
    inbound = build_relay_inbound(
        in_tag,
        listen_port,
        settings.get("default_listen_host", "0.0.0.0"),
        settings.get("default_udp", True),
    )
    outbound = build_relay_outbound(parsed, out_tag)
    routing = build_routing_rule(in_tag, out_tag)
    return safe, inbound, outbound, routing


def build_full_config(servers, settings):
    inbounds = [{
        "tag": "api",
        "listen": "127.0.0.1",
        "port": API_PORT,
        "protocol": "dokodemo-door",
        "settings": {"address": "127.0.0.1"},
    }]
    outbounds = []
    rules = [{
        "type": "field",
        "inboundTag": ["api"],
        "outboundTag": "api",
    }]
    for srv in servers:
        if not srv.get("enabled", True):
            continue
        inbounds.append(srv["inbound"])
        outbounds.append(srv["outbound"])
        rules.append(srv["routing"])
    if not outbounds:
        outbounds.append({"tag": "blackhole", "protocol": "blackhole", "settings": {}})
    outbounds.append({"tag": "direct", "protocol": "freedom", "settings": {}})
    return {
        "log": {
            "loglevel": settings.get("log_level", "warning"),
            "access": str(LOG_DIR / "access.log"),
            "error": str(LOG_DIR / "error.log"),
        },
        "api": {
            "tag": "api",
            "services": ["HandlerService", "LoggerService", "StatsService"],
        },
        "stats": {},
        "policy": {
            "levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}},
            "system": {
                "statsInboundUplink": True,
                "statsInboundDownlink": True,
                "statsOutboundUplink": True,
                "statsOutboundDownlink": True,
            },
        },
        "inbounds": inbounds,
        "outbounds": outbounds,
        "routing": {
            "domainStrategy": "AsIs",
            "rules": rules,
        },
    }
