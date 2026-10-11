"""Entry point: python -m exrelay"""
import sys

from .constants import SERVICE_FILE, SETTINGS_FILE
from .service import bootstrap_files, create_systemd_service, ensure_prerequisites
from .ui import install_command, main_menu
from .utils import ensure_dirs, err, info, is_root, ok, pause, title


def setup_wizard():
    title("  eXrelay setup")
    if not ensure_prerequisites():
        return False
    ensure_dirs()
    bootstrap_files()
    create_systemd_service()
    ok("systemd unit written")
    success, msg = install_command()
    (ok if success else err)(f"Command: {msg}")
    info("Run: exrelay")
    return True


def main():
    if not is_root():
        err("Run as root.")
        sys.exit(1)
    ensure_dirs()
    if "--setup" in sys.argv or not SETTINGS_FILE.exists() or not SERVICE_FILE.exists():
        if not setup_wizard():
            sys.exit(1)
        if "--setup" in sys.argv:
            return
        pause()
    else:
        ensure_prerequisites()
        bootstrap_files()
    try:
        main_menu()
    except KeyboardInterrupt:
        print()
        info("Interrupted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
