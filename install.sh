#!/usr/bin/env bash
# eXrelay installer.
# Downloads the GitHub zip (unless this script already sits next to the package),
# unpacks it, installs missing packages, Xray, proxychains4 and speedtest-cli,
# then registers the systemd service and the `exrelay` command.
#
# Usage (after you publish the repo):
#   sudo GITHUB_REPO=yourname/exrelay bash install.sh
#
# Or a direct zip URL:
#   sudo ZIP_URL=https://github.com/yourname/exrelay/archive/refs/heads/main.zip bash install.sh
#
# From an already extracted tree (install.sh beside the exrelay/ folder):
#   sudo bash install.sh
set -euo pipefail

GITHUB_REPO="${GITHUB_REPO:-}"
BRANCH="${BRANCH:-main}"
ZIP_URL="https://github.com/URT19/eXtreme-Dokodemo-door-Tunnel-Creator/raw/refs/heads/main/exrelay-2.0.0.zip"
INSTALL_ROOT="${INSTALL_ROOT:-/opt/exrelay/pkg}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo bash install.sh" >&2
  exit 1
fi

need_cmd() { command -v "$1" >/dev/null 2>&1; }

install_base_packages() {
  if [[ -f /etc/debian_version ]]; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y python3 curl unzip ca-certificates proxychains4 speedtest-cli
  elif [[ -f /etc/redhat-release ]]; then
    if command -v dnf >/dev/null 2>&1; then
      dnf install -y python3 curl unzip ca-certificates proxychains-ng
    else
      yum install -y python3 curl unzip ca-certificates proxychains-ng
    fi
  elif [[ -f /etc/alpine-release ]]; then
    apk update
    apk add python3 curl unzip ca-certificates proxychains-ng bash
  elif [[ -f /etc/arch-release ]]; then
    pacman -Sy --noconfirm python curl unzip ca-certificates proxychains-ng
  else
    echo "Unknown distro. Install python3, curl and unzip yourself, then re-run." >&2
    exit 1
  fi
  if ! need_cmd speedtest-cli; then
    pip3 install speedtest-cli --break-system-packages || pip3 install speedtest-cli || true
  fi
}

install_xray() {
  if need_cmd xray || [[ -x /usr/local/bin/xray ]]; then
    echo "Xray already installed."
    return
  fi
  local tmp
  tmp="$(mktemp)"
  curl -fsSL "https://github.com/XTLS/Xray-install/raw/main/install-release.sh" -o "$tmp"
  bash "$tmp" install
  rm -f "$tmp"
}

find_source_tree() {
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -f "$here/exrelay/__main__.py" ]]; then
    echo "$here"
    return
  fi
  echo ""
}

download_zip() {
  local dest="$1"
  local url="$ZIP_URL"
  if [[ -z "$url" ]]; then
    if [[ -z "$GITHUB_REPO" ]]; then
      echo "No local package and GITHUB_REPO is empty." >&2
      echo "Set it to your GitHub repo, for example:" >&2
      echo "  sudo GITHUB_REPO=yourname/exrelay bash install.sh" >&2
      exit 1
    fi
    url="https://github.com/${GITHUB_REPO}/archive/refs/heads/${BRANCH}.zip"
  fi
  echo "Downloading ${url}"
  curl -fL --retry 3 -o "$dest" "$url"
}

unpack_zip() {
  local zip="$1" work="$2"
  rm -rf "$work"
  mkdir -p "$work"
  unzip -q "$zip" -d "$work"
  local found
  found="$(find "$work" -type f -path '*/exrelay/__main__.py' | head -n 1 || true)"
  if [[ -z "$found" ]]; then
    echo "Zip does not contain exrelay/__main__.py" >&2
    exit 1
  fi
  dirname "$(dirname "$found")"
}

echo "== eXrelay install =="
install_base_packages
install_xray

SRC="$(find_source_tree)"
if [[ -z "$SRC" ]]; then
  TMPZIP="$(mktemp --suffix=.zip)"
  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPZIP" "$TMPDIR"' EXIT
  download_zip "$TMPZIP"
  SRC="$(unpack_zip "$TMPZIP" "$TMPDIR")"
fi

echo "Installing files from ${SRC} to ${INSTALL_ROOT}"
mkdir -p "$INSTALL_ROOT"
rm -rf "${INSTALL_ROOT}/exrelay"
cp -a "${SRC}/exrelay" "${INSTALL_ROOT}/exrelay"
if [[ -f "${SRC}/exrelay.py" ]]; then
  cp -a "${SRC}/exrelay.py" "${INSTALL_ROOT}/exrelay.py"
fi

python3 "${INSTALL_ROOT}/exrelay/__main__.py" --setup
echo
echo "Done. Open the menu with:  exrelay"
