"""Test a foreign server through a short-lived local SOCKS client.

Location comes from https://myip.wtf/json only (never ipinfo.io).
Speed uses proxychains4 + speedtest-cli against that SOCKS port.
The proxychains file is written under the test dir and passed with -f,
so /etc/proxychains4.conf is left alone.
"""
import json
import subprocess
import time

from .config_builder import build_client_outbound
from .constants import TEST_DIR, TEST_SOCKS_PORT
from .utils import find_xray_binary, run_cmd, write_json

PROXYCHAINS_FILE = TEST_DIR / "proxychains.conf"


def _client_config(parsed):
    outbound = build_client_outbound(parsed, tag="proxy")
    return {
        "log": {"loglevel": "warning"},
        "inbounds": [{
            "tag": "socks-in",
            "listen": "127.0.0.1",
            "port": TEST_SOCKS_PORT,
            "protocol": "socks",
            "settings": {"auth": "noauth", "udp": True},
        }],
        "outbounds": [
            outbound,
            {"tag": "direct", "protocol": "freedom", "settings": {}},
        ],
        "routing": {
            "rules": [{
                "type": "field",
                "inboundTag": ["socks-in"],
                "outboundTag": "proxy",
            }]
        },
    }


def write_proxychains(port=TEST_SOCKS_PORT):
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    PROXYCHAINS_FILE.write_text(
        "\n".join([
            "strict_chain",
            "proxy_dns",
            "tcp_read_time_out 20000",
            "tcp_connect_time_out 10000",
            "[ProxyList]",
            f"socks5 127.0.0.1 {int(port)}",
            "",
        ]),
        encoding="utf-8",
    )
    return PROXYCHAINS_FILE


def tool_status():
    def has(cmd):
        rc, _, _ = run_cmd(f"command -v {cmd}")
        return rc == 0
    return {"proxychains4": has("proxychains4"), "speedtest-cli": has("speedtest-cli"), "curl": has("curl")}


def install_test_tools():
    """Install proxychains4 and speedtest-cli. Returns (ok, message)."""
    rc, _, err = run_cmd("apt-get update -qq && apt-get install -y proxychains4 curl", timeout=180)
    if rc != 0:
        return False, (err or "apt install proxychains4 failed")[:300]
    if tool_status()["speedtest-cli"]:
        return True, "proxychains4 ready, speedtest-cli already installed"
    rc, _, err = run_cmd("apt-get install -y speedtest-cli", timeout=180)
    if rc != 0:
        rc, _, err = run_cmd("pip3 install speedtest-cli --break-system-packages", timeout=180)
    if rc != 0:
        return False, (err or "speedtest-cli install failed")[:300]
    return True, "proxychains4 and speedtest-cli installed"


class SocksClient:
    def __init__(self, parsed):
        self.parsed = parsed
        self.proc = None

    def __enter__(self):
        xray = find_xray_binary()
        if not xray:
            raise RuntimeError("Xray binary not found")
        cfg = TEST_DIR / "client_test.json"
        write_json(cfg, _client_config(self.parsed))
        rc, out, e = run_cmd(f"{xray} run -test -config {cfg}")
        if rc != 0:
            rc, out, e = run_cmd(f"{xray} -test -config {cfg}")
        if rc != 0:
            raise RuntimeError(((out or "") + (e or ""))[:300] or "client config invalid")
        self.proc = subprocess.Popen(
            [xray, "run", "-config", str(cfg)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(24):
            time.sleep(0.25)
            rc, _, _ = run_cmd(f"ss -tln 2>/dev/null | grep ':{TEST_SOCKS_PORT} '")
            if rc == 0:
                write_proxychains(TEST_SOCKS_PORT)
                return self
        raise RuntimeError(f"SOCKS did not listen on 127.0.0.1:{TEST_SOCKS_PORT}")

    def __exit__(self, *_exc):
        if not self.proc:
            return
        try:
            self.proc.terminate()
            self.proc.wait(timeout=3)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass


def fetch_location(timeout=20):
    """curl --socks5-hostname against myip.wtf. Returns dict or raises RuntimeError."""
    rc, body, err = run_cmd(
        f"curl -sS --max-time {timeout} "
        f"--socks5-hostname 127.0.0.1:{TEST_SOCKS_PORT} "
        f"https://myip.wtf/json",
        timeout=timeout + 5,
    )
    if rc != 0 or not (body or "").strip():
        raise RuntimeError((err or body or "myip.wtf failed")[:250])
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"myip.wtf did not return JSON: {body[:180]}") from e
    return {
        "ip": data.get("YourFuckingIPAddress") or "",
        "location": data.get("YourFuckingLocation") or "",
        "city": data.get("YourFuckingCity") or "",
        "country": data.get("YourFuckingCountry") or "",
        "country_code": data.get("YourFuckingCountryCode") or "",
        "isp": data.get("YourFuckingISP") or "",
        "hostname": data.get("YourFuckingHostname") or "",
        "raw": data,
    }


def run_speedtest(timeout=120):
    """Try speedtest-cli through proxychains. The apt package often crashes
    with 'string index out of range' because Ookla retired its old API.
    When that happens, measure the tunnel with curl instead.
    """
    cli = _speedtest_cli(timeout=timeout)
    if cli and cli.get("download_mbit"):
        return cli
    note = ""
    if cli and cli.get("error"):
        note = cli["error"]
    measured = _curl_speed(timeout=min(timeout, 45))
    if note:
        measured["note"] = "speedtest-cli failed (" + note + "). Measured through the SOCKS tunnel with curl."
    return measured


def _speedtest_cli(timeout=120):
    tools = tool_status()
    if not tools["speedtest-cli"]:
        return None
    if tools["proxychains4"] and PROXYCHAINS_FILE.exists():
        cmd = f"proxychains4 -q -f {PROXYCHAINS_FILE} speedtest-cli --simple"
        via = "proxychains4 speedtest-cli"
    else:
        cmd = f"speedtest-cli --simple --proxy socks5://127.0.0.1:{TEST_SOCKS_PORT}"
        via = "speedtest-cli --proxy"
    rc, out, err = run_cmd(cmd, timeout=timeout)
    text = ((out or "") + "\n" + (err or "")).strip()
    parsed = _parse_speed(text)
    parsed["via"] = via
    parsed["raw"] = text[-800:]
    if parsed.get("download_mbit"):
        return parsed
    message = text.replace("\n", " ")[-180:] or "no output"
    parsed["error"] = message
    if rc != 0:
        return parsed
    return parsed


def _curl_speed(timeout=40):
    socks = f"--socks5-hostname 127.0.0.1:{TEST_SOCKS_PORT}"
    ping = _curl_latency(socks, timeout=min(20, timeout))
    download = None
    for url, nbytes in (
        ("https://speed.cloudflare.com/__down?bytes=15000000", 15000000),
        ("https://proof.ovh.net/files/10Mb.dat", 10000000),
    ):
        download = _curl_download(socks, url, timeout=timeout)
        if download:
            break
    upload = _curl_upload(socks, timeout=min(30, timeout))
    if download is None and ping is None:
        raise RuntimeError("speed test failed: tunnel did not return a download sample")
    return {
        "ping_ms": ping,
        "download_mbit": download,
        "upload_mbit": upload,
        "via": "curl via SOCKS (speedtest-cli unavailable)",
        "note": "",
    }


def _curl_latency(socks, timeout):
    rc, out, _ = run_cmd(
        f"curl -sS -o /dev/null -w '%{{time_starttransfer}}' --max-time {timeout} {socks} "
        f"'https://speed.cloudflare.com/__down?bytes=1'",
        timeout=timeout + 5,
    )
    if rc != 0:
        return None
    try:
        return round(float((out or "").strip()) * 1000, 1)
    except ValueError:
        return None


def _curl_download(socks, url, timeout):
    rc, out, _ = run_cmd(
        f"curl -sS -o /dev/null -w '%{{size_download}} %{{time_total}}' --max-time {timeout} {socks} '{url}'",
        timeout=timeout + 5,
    )
    if rc != 0:
        return None
    parts = (out or "").split()
    if len(parts) != 2:
        return None
    try:
        size = float(parts[0])
        seconds = float(parts[1])
    except ValueError:
        return None
    if size < 100000 or seconds <= 0:
        return None
    return round((size * 8) / seconds / 1_000_000, 2)


def _curl_upload(socks, timeout):
    rc, out, _ = run_cmd(
        f"dd if=/dev/zero bs=1000000 count=3 2>/dev/null | "
        f"curl -sS -o /dev/null -w '%{{size_upload}} %{{time_total}}' --max-time {timeout} {socks} "
        f"-X POST --data-binary @- 'https://speed.cloudflare.com/__up'",
        timeout=timeout + 5,
    )
    if rc != 0:
        return None
    parts = (out or "").split()
    if len(parts) != 2:
        return None
    try:
        size = float(parts[0])
        seconds = float(parts[1])
    except ValueError:
        return None
    if size < 100000 or seconds <= 0:
        return None
    return round((size * 8) / seconds / 1_000_000, 2)


def _parse_speed(text):
    result = {"ping_ms": None, "download_mbit": None, "upload_mbit": None}
    for line in text.splitlines():
        low = line.lower()
        if "ping" in low:
            result["ping_ms"] = _first_float(line)
        elif "download" in low:
            result["download_mbit"] = _first_float(line)
        elif "upload" in low:
            result["upload_mbit"] = _first_float(line)
    return result


def _first_float(line):
    num = ""
    seen = False
    for ch in line:
        if ch.isdigit() or (ch == "." and seen):
            num += ch
            seen = True
        elif seen:
            break
    try:
        return float(num) if num else None
    except ValueError:
        return None


def probe_remote(srv, timeout=20):
    """Compatibility helper: connection check only. Returns (ok, summary)."""
    try:
        with SocksClient(srv.get("parsed") or {}):
            loc = fetch_location(timeout=timeout)
    except Exception as e:
        return False, str(e)
    place = loc.get("location") or ", ".join(x for x in (loc.get("city"), loc.get("country")) if x)
    return True, f"{loc.get('ip') or '?'}  {place}  {loc.get('isp') or ''}".strip()
