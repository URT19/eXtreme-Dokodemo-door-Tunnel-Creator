# eXrelay

eXrelay turns one middle server (usually a VPS in Iran) into a raw TCP/UDP port forward in front of one or more foreign Xray servers.

The middle server does **not** speak VLESS, VMess, Trojan or Shadowsocks. It copies bytes:

```
client  --protocol-->  Iran:listen_port  --raw TCP/UDP-->  foreign:remote_port
```

Xray on the Iran host uses:

- inbound `dokodemo-door` on the public listen port
- outbound `freedom` with `settings.redirect = foreignHost:foreignPort`

The share link you give users keeps the original UUID, password, SNI, Reality key, path and flow. Only the address and port change to the Iran server. Because the stream is not re-encoded, the foreign server still sees a normal client handshake.

## Requirements

Installed automatically by `install.sh` or the first `exrelay` run when they are missing:

| Tool | Why |
|---|---|
| python3 | the menu |
| curl, unzip, ca-certificates | downloads |
| Xray | the relay process |
| systemd | `exrelay-xray.service` |
| proxychains4 | speed test through the temporary SOCKS client |
| speedtest-cli | download / upload / ping |

Test location data comes from `https://myip.wtf/json` only. `ipinfo.io` is not used.

## Install

Publish this folder to GitHub, then on the Iran server:

```bash
sudo GITHUB_REPO=yourname/exrelay bash -c "$(curl -fsSL https://raw.githubusercontent.com/yourname/exrelay/main/install.sh)"
```

Or download the branch zip yourself and run the script that sits next to `exrelay/`:

```bash
sudo bash install.sh
```

A direct zip URL also works:

```bash
sudo ZIP_URL=https://github.com/yourname/exrelay/archive/refs/heads/main.zip bash install.sh
```

The script copies the package to `/opt/exrelay/pkg`, installs missing packages and Xray, writes `/etc/systemd/system/exrelay-xray.service`, and links `/usr/local/bin/exrelay`.

Open the menu:

```bash
sudo exrelay
```

## Example (fictional)

Foreign server you were given. Nothing here is a real node:

```text
vless://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee@203.0.113.50:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.microsoft.com&fp=chrome&pbk=ExamplePublicKey_not_real_0123456789&sid=0123456789abcdef&type=tcp#Example-DE
```

| Field | Value |
|---|---|
| Foreign address | `203.0.113.50` (documentation range) |
| Foreign port | `443` |
| Protocol | VLESS + Reality + Vision |
| Iran public IP | `198.51.100.10` (documentation range) |
| Listen port you choose | `8443` |

In the menu: **1) Add relay**, paste the link, listen port `8443`, name `Example-DE`. Apply writes one `config.json` whose outbound is:

```json
{
  "tag": "out-Example-DE",
  "protocol": "freedom",
  "settings": { "redirect": "203.0.113.50:443" }
}
```

The link to hand to users (same parameters, Iran address):

```text
vless://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee@198.51.100.10:8443?type=tcp&security=reality&sni=www.microsoft.com&fp=chrome&pbk=ExamplePublicKey_not_real_0123456789&sid=0123456789abcdef&flow=xtls-rprx-vision#Example-DE-via-IR
```

The client connects to `198.51.100.10:8443`. Iran forwards the TCP stream untouched to `203.0.113.50:443`. Reality is terminated only on the foreign server.

## Menu

| Key | Action |
|---|---|
| 1 | Add a relay from a share link |
| 2 | List relays, details, user link (`l1`), test (`t1`) |
| 3 | Rename, change port, enable, replace link, delete |
| 4 | Delete |
| 5 | Print every enabled user link |
| 6 | Rebuild `config.json` and restart |
| 7 | systemctl start / stop / restart / test |
| 8 | Backup and restore `/opt/exrelay` config and data |
| 9 | Listen host, UDP, default port, public IP |
| 10 | Test one foreign server |
| 0 | Exit |

## Test a foreign server

Option **10** starts a temporary Xray **client** (not the relay) on `127.0.0.1:18999` using the parsed protocol, then:

1. **Connection + location** — `curl --socks5-hostname 127.0.0.1:18999 https://myip.wtf/json`  
   Shows exit IP, city, country, ISP, hostname. An IP means the foreign node accepted the handshake.
2. **Speed** — writes `/opt/exrelay/test/proxychains.conf` for that SOCKS port and runs  
   `proxychains4 -f /opt/exrelay/test/proxychains.conf speedtest-cli --simple`  
   `/etc/proxychains4.conf` is not modified.
3. **Both.**

If `proxychains4` or `speedtest-cli` is missing, the test screen can install them, and a normal `exrelay` start also installs missing prerequisites.

## Files

```
/opt/exrelay/pkg/exrelay/     Python package
/opt/exrelay/data/servers.json
/opt/exrelay/data/settings.json
/opt/exrelay/config/xray/config.json
/opt/exrelay/backups/
/opt/exrelay/test/            temporary client config and proxychains file
/etc/systemd/system/exrelay-xray.service
/usr/local/bin/exrelay
```

## Uninstall

```bash
sudo systemctl disable --now exrelay-xray
sudo rm -f /etc/systemd/system/exrelay-xray.service /usr/local/bin/exrelay
sudo systemctl daemon-reload
sudo rm -rf /opt/exrelay
```

Xray itself is left installed. Remove it with the upstream script if you want: `bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ remove --purge`

Persian documentation: [README-fa.md](README-fa.md).
