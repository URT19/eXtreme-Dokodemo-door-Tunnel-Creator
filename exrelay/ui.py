"""Interactive menus."""
import shutil
from pathlib import Path

from .constants import INSTALL_PATH, TEST_SOCKS_PORT, VERSION
from .links import generate_user_link
from .parsers import ParseError, parse_link
from .service import (
    apply_and_restart,
    service_is_active,
    service_restart,
    service_start,
    service_stop,
    xray_test_config,
)
from .backup import create_backup, list_backups, restore_backup
from .store import (
    add_server,
    change_port,
    check_conflicts,
    delete_server,
    list_servers,
    load_settings,
    rename_server,
    save_settings,
    set_enabled,
    update_link,
)
from .testing import (
    SocksClient,
    fetch_location,
    install_test_tools,
    run_speedtest,
    tool_status,
)
from .utils import (
    C,
    ask,
    ask_yes_no,
    clear_screen,
    colorize,
    err,
    find_xray_binary,
    get_public_ip,
    info,
    is_port_listening,
    line,
    menu_block,
    ok,
    pause,
    screen,
    section,
    status_row,
    title,
    warn,
)


def _print_table(servers):
    if not servers:
        warn("No servers yet")
        return
    print()
    print(colorize("  ┌" + "─" * 86 + "┐", C.CYAN))
    header = f" {'#':<3} {'Name':<16} {'Port':<7} {'Proto':<10} {'Remote':<26} {'Status':<10}"
    print(colorize("  │", C.CYAN) + colorize(header, C.CYAN + C.BOLD) + colorize(" │", C.CYAN))
    print(colorize("  ├" + "─" * 86 + "┤", C.CYAN))
    for i, srv in enumerate(servers, 1):
        enabled = srv.get("enabled", True)
        status = "enabled" if enabled else "disabled"
        status_c = C.GREEN + C.BOLD if enabled else C.RED
        proto_c = {
            "vless": C.MAGENTA,
            "vmess": C.BLUE,
            "trojan": C.YELLOW,
            "shadowsocks": C.CYAN,
        }.get(srv.get("protocol"), C.WHITE)
        remote = f"{srv.get('remote_address')}:{srv.get('remote_port')}"
        row = (
            colorize(f" {str(i):<3}", C.YELLOW + C.BOLD)
            + colorize(f" {srv.get('name', '')[:16]:<16}", C.WHITE)
            + colorize(f" {str(srv.get('listen_port', '')):<7}", C.WHITE)
            + colorize(f" {str(srv.get('protocol', ''))[:9]:<10}", proto_c)
            + colorize(f" {remote[:26]:<26}", C.DIM)
            + colorize(f" {status:<10}", status_c)
        )
        print(colorize("  │", C.CYAN) + row + colorize("│", C.CYAN))
    print(colorize("  └" + "─" * 86 + "┘", C.CYAN))
    print()


def _pick(servers, prompt="Server number (0 cancel)"):
    if not servers:
        pause()
        return None
    choice = ask(prompt).strip()
    if choice in ("", "0"):
        return None
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(servers):
            raise ValueError
    except ValueError:
        err("Invalid number")
        pause()
        return None
    return servers[idx]


def _prompt_port(default):
    while True:
        raw = ask("Listen port on this (Iran) server", default=str(default))
        if not raw:
            return None
        try:
            port = int(raw)
        except ValueError:
            err("Not a number")
            continue
        if not 1 <= port <= 65535:
            err("Port must be 1-65535")
            continue
        conflict, msg = check_conflicts("", port)
        if conflict:
            err(msg)
            continue
        return port


def _show_link(srv):
    ip = get_public_ip()
    if not ip:
        err("Public IP unknown. Set it in Settings.")
        return
    link = generate_user_link(srv, ip)
    print()
    info(f"Iran {ip}:{srv.get('listen_port')}  ->  "
         f"{srv.get('remote_address')}:{srv.get('remote_port')}  (raw TCP/UDP forward)")
    print(colorize("  " + (link or "(could not build link)"), C.GREEN))
    print()


def flow_add():
    clear_screen()
    screen("ADD RELAY", "raw TCP/UDP forward  ·  protocol is not re-wrapped")
    section("Share link")
    info("vless://   vmess://   trojan://   ss://")
    print()
    link = input(colorize("  Link › ", C.YELLOW + C.BOLD)).strip()
    if not link:
        return
    try:
        parsed = parse_link(link)
    except ParseError as e:
        err(str(e))
        pause()
        return
    info(f"{parsed['protocol'].upper()}  {parsed['address']}:{parsed['port']}  {parsed.get('network')} / {parsed.get('security')}")
    settings = load_settings()
    port = _prompt_port(settings.get("default_listen_port_start", 443))
    if port is None:
        return
    default_name = (parsed.get("name") or parsed.get("address") or "server").replace(" ", "-")
    while True:
        name = ask("Name", default=default_name)
        conflict, msg = check_conflicts(name, -1)
        if conflict and "Name" in msg:
            err(msg)
            continue
        break
    if not ask_yes_no("Add and apply?", default=True):
        return
    try:
        srv = add_server(parsed, name, port)
    except ValueError as e:
        err(str(e))
        pause()
        return
    ok(f"Added {srv['id']} ({srv['name']})")
    apply_and_restart()
    _show_link(srv)
    pause()


def _print_location(loc):
    print()
    print(colorize("  ┌" + "─" * 60 + "┐", C.GREEN))
    print(colorize("  │", C.GREEN) + colorize("  CONNECTION", C.GREEN + C.BOLD))
    rows = [
        ("Exit IP", loc.get("ip")),
        ("Location", loc.get("location")),
        ("City", loc.get("city")),
        ("Country", " ".join(x for x in (loc.get("country"), loc.get("country_code")) if x)),
        ("ISP", loc.get("isp")),
        ("Hostname", loc.get("hostname")),
    ]
    for label, value in rows:
        if not value:
            continue
        print(
            colorize("  │", C.GREEN)
            + colorize(f"  {label:<12}", C.CYAN)
            + colorize(str(value), C.WHITE)
        )
    print(colorize("  └" + "─" * 60 + "┘", C.GREEN))


def _print_speed(speed):
    print()
    print(colorize("  ┌" + "─" * 60 + "┐", C.YELLOW))
    print(colorize("  │", C.YELLOW) + colorize(f"  SPEED  via {speed.get('via', '')}", C.YELLOW + C.BOLD))
    for label, key, unit in (
        ("Ping", "ping_ms", "ms"),
        ("Download", "download_mbit", "Mbit/s"),
        ("Upload", "upload_mbit", "Mbit/s"),
    ):
        val = speed.get(key)
        shown = f"{val:.2f} {unit}" if isinstance(val, float) else "n/a"
        print(
            colorize("  │", C.YELLOW)
            + colorize(f"  {label:<12}", C.CYAN)
            + colorize(shown, C.WHITE + C.BOLD)
        )
    print(colorize("  └" + "─" * 60 + "┘", C.YELLOW))


def _run_server_test(srv, mode):
    """mode: location | speed | both."""
    clear_screen()
    screen(
        "TESTING  " + srv.get("name", ""),
        f"{srv.get('protocol', '').upper()}  {srv.get('remote_address')}:{srv.get('remote_port')}",
    )
    print()
    info(f"Local SOCKS  127.0.0.1:{TEST_SOCKS_PORT}")
    info("Location source: https://myip.wtf/json")
    print()
    try:
        with SocksClient(srv.get("parsed") or {}):
            ok(f"Client is up on 127.0.0.1:{TEST_SOCKS_PORT}")
            if mode in ("location", "both"):
                info("curl --socks5-hostname … https://myip.wtf/json")
                loc = fetch_location()
                _print_location(loc)
                if loc.get("ip"):
                    ok("Remote server accepts the connection")
                else:
                    warn("Connected but exit IP was empty")
            if mode in ("speed", "both"):
                info("Speed: speedtest-cli, or curl through the tunnel if that tool crashes")
                speed = run_speedtest()
                if speed.get("note"):
                    warn(speed["note"])
                _print_speed(speed)
    except Exception as e:
        err(str(e))
    pause()


def flow_test():
    while True:
        clear_screen()
        tools = tool_status()
        screen("TEST SERVER", "does this foreign node actually connect?")
        print()
        status_row("SOCKS port", f"127.0.0.1:{TEST_SOCKS_PORT}")
        status_row("proxychains4", "installed" if tools["proxychains4"] else "missing", good=tools["proxychains4"])
        status_row("speedtest-cli", "installed" if tools["speedtest-cli"] else "missing", good=tools["speedtest-cli"])
        status_row("Location", "myip.wtf", good=True)
        servers = list_servers()
        _print_table(servers)
        menu_block([
            ("#", "Pick a server", "then choose location or speed"),
            ("i", "Install test tools", "proxychains4 + speedtest-cli"),
            ("0", "Back", ""),
        ])
        choice = ask("Select").strip().lower()
        if choice in ("", "0"):
            return
        if choice == "i":
            info("Installing proxychains4 and speedtest-cli…")
            success, msg = install_test_tools()
            (ok if success else err)(msg)
            pause()
            continue
        try:
            srv = servers[int(choice) - 1]
        except (ValueError, IndexError):
            warn("Invalid number")
            pause()
            continue
        _test_mode_menu(srv)


def _test_mode_menu(srv):
    while True:
        clear_screen()
        screen(
            "TEST  " + srv.get("name", ""),
            f"{srv.get('remote_address')}:{srv.get('remote_port')}",
        )
        print()
        menu_block([
            ("1", "Connection + location", "myip.wtf via SOCKS"),
            ("2", "Speed test", "speedtest-cli, then curl if it crashes"),
            ("3", "Both", "location, then speed"),
            ("0", "Back", ""),
        ])
        choice = ask("Select").strip()
        if choice in ("", "0"):
            return
        mode = {"1": "location", "2": "speed", "3": "both"}.get(choice)
        if not mode:
            warn("Invalid option")
            pause()
            continue
        _run_server_test(srv, mode)


def flow_list():
    while True:
        clear_screen()
        screen("RELAYS", "number = details    lN = user link    tN = test remote")
        servers = list_servers()
        _print_table(servers)
        if not servers:
            pause()
            return
        menu_block([
            ("#", "Details", "port, redirect, listen state"),
            ("l#", "User link", "example: l1"),
            ("t#", "Test remote", "example: t1"),
            ("0", "Back", ""),
        ])
        choice = ask("Select").strip().lower()
        if choice in ("", "0"):
            return
        kind = "d"
        raw = choice
        if choice[:1] in ("l", "t") and choice[1:].isdigit():
            kind, raw = choice[0], choice[1:]
        try:
            srv = servers[int(raw) - 1]
        except (ValueError, IndexError):
            continue
        if kind == "l":
            _show_link(srv)
            pause()
        elif kind == "t":
            _test_mode_menu(srv)
        else:
            redir = (srv.get("outbound") or {}).get("settings", {}).get("redirect")
            info(f"id={srv.get('id')} enabled={srv.get('enabled')} listen={srv.get('listen_port')}")
            info(f"freedom redirect -> {redir}")
            listening = is_port_listening(srv.get("listen_port", 0))
            (ok if listening else warn)("listen port is up" if listening else "listen port is down")
            pause()


def flow_edit():
    clear_screen()
    servers = list_servers()
    _print_table(servers)
    srv = _pick(servers)
    if not srv:
        return
    sid = srv["id"]
    while True:
        clear_screen()
        enabled = srv.get("enabled", True)
        screen(
            "EDIT  " + srv.get("name", ""),
            f":{srv.get('listen_port')}  →  {srv.get('remote_address')}:{srv.get('remote_port')}",
        )
        print()
        status_row("Status", "enabled" if enabled else "disabled", good=enabled)
        status_row("Protocol", str(srv.get("protocol", "")).upper())
        print()
        menu_block([
            ("1", "Rename", ""),
            ("2", "Change listen port", ""),
            ("3", "Enable / disable", ""),
            ("4", "Replace remote link", "rebuilds freedom redirect"),
            ("5", "Show user link", ""),
            ("6", "Delete", ""),
            ("0", "Back", ""),
        ])
        sub = ask("Select").strip()
        if sub == "0":
            return
        if sub == "1":
            success, msg = rename_server(sid, ask("New name", default=srv.get("name")))
            (ok if success else err)(msg if not success else "Renamed")
            if success and ask_yes_no("Apply now?", True):
                apply_and_restart()
        elif sub == "2":
            try:
                port = int(ask("New port", default=str(srv.get("listen_port"))))
            except ValueError:
                err("Invalid port")
                pause()
                continue
            success, msg = change_port(sid, port)
            (ok if success else err)(msg if not success else "Port changed")
            if success and ask_yes_no("Apply now?", True):
                apply_and_restart()
        elif sub == "3":
            success, msg = set_enabled(sid, not srv.get("enabled", True))
            (ok if success else err)("Toggled" if success else msg)
            if success:
                apply_and_restart()
        elif sub == "4":
            link = input(colorize("  New link: ", C.WHITE)).strip()
            if not link:
                continue
            try:
                parsed = parse_link(link)
            except ParseError as e:
                err(str(e))
                pause()
                continue
            success, msg = update_link(sid, parsed)
            (ok if success else err)(msg if not success else "Link updated (redirect rebuilt)")
            if success and ask_yes_no("Apply now?", True):
                apply_and_restart()
        elif sub == "5":
            _show_link(srv)
        elif sub == "6":
            if ask_yes_no(f"Delete {srv.get('name')}?", False):
                delete_server(sid)
                apply_and_restart()
                pause()
                return
        from .store import find_server
        _, fresh = find_server(sid)
        if fresh:
            srv = fresh
        pause()


def flow_delete():
    servers = list_servers()
    _print_table(servers)
    srv = _pick(servers, "Delete which (0 cancel)")
    if not srv:
        return
    if ask_yes_no(f"Delete '{srv.get('name')}'?", False):
        delete_server(srv["id"])
        ok("Deleted")
        apply_and_restart()
    pause()


def flow_links():
    clear_screen()
    ip = get_public_ip()
    screen("USER LINKS", "hand these to clients")
    print()
    if not ip:
        err("Set public IP in Settings")
        pause()
        return
    status_row("Iran IP", ip, good=True)
    print()
    for srv in list_servers(enabled_only=True):
        print(colorize("  ┌" + "─" * 60 + "┐", C.MAGENTA))
        head = f" {srv.get('name')}   :{srv.get('listen_port')}"
        print(colorize("  │", C.MAGENTA) + colorize(head, C.WHITE + C.BOLD))
        link = generate_user_link(srv, ip)
        print(colorize("  │ ", C.MAGENTA) + colorize(link, C.GREEN))
        print(colorize("  └" + "─" * 60 + "┘", C.MAGENTA))
        print()
    pause()


def flow_settings():
    while True:
        clear_screen()
        screen("SETTINGS", "defaults for new relays")
        settings = load_settings()
        print()
        status_row("Listen host", settings.get("default_listen_host"))
        udp = settings.get("default_udp")
        status_row("UDP forward", "on" if udp else "off", good=bool(udp))
        status_row("Default port", settings.get("default_listen_port_start"))
        ip = settings.get("public_ip") or get_public_ip() or "(unknown)"
        status_row("Public IP", ip, good=bool(settings.get("public_ip") or get_public_ip()))
        print()
        menu_block([
            ("1", "Toggle UDP", ""),
            ("2", "Default listen port", ""),
            ("3", "Listen host", ""),
            ("4", "Set public IP", ""),
            ("0", "Back", ""),
        ])
        choice = ask("Select").strip()
        if choice == "0":
            return
        if choice == "1":
            settings["default_udp"] = not settings.get("default_udp", True)
        elif choice == "2":
            try:
                settings["default_listen_port_start"] = int(ask("Port", default="443"))
            except ValueError:
                err("Invalid")
                pause()
                continue
        elif choice == "3":
            settings["default_listen_host"] = ask("Host", default="0.0.0.0")
        elif choice == "4":
            settings["public_ip"] = ask("Public IP", default=get_public_ip() or "")
        else:
            continue
        save_settings(settings)
        ok("Saved. Re-apply from the main menu so existing relays pick this up.")
        pause()


def flow_service():
    while True:
        clear_screen()
        active = service_is_active()
        xray = find_xray_binary()
        screen("SERVICE", "systemd  ·  exrelay-xray")
        print()
        status_row("State", "active" if active else "inactive", good=active)
        status_row("Xray", xray or "NOT FOUND", good=bool(xray))
        print()
        menu_block([
            ("1", "Start", ""),
            ("2", "Stop", ""),
            ("3", "Restart", ""),
            ("4", "Test config", ""),
            ("5", "Apply database + restart", ""),
            ("0", "Back", ""),
        ])
        choice = ask("Select").strip()
        if choice == "0":
            return
        if choice == "1":
            s, m = service_start()
        elif choice == "2":
            s, m = service_stop()
        elif choice == "3":
            s, m = service_restart()
        elif choice == "4":
            s, m = xray_test_config()
            m = "valid" if s else m[:800]
        elif choice == "5":
            apply_and_restart()
            pause()
            continue
        else:
            continue
        (ok if s else err)(m)
        pause()


def flow_backups():
    while True:
        clear_screen()
        screen("BACKUPS", "config + database snapshots")
        backups = list_backups()
        print()
        if not backups:
            warn("No backups yet")
        else:
            print(colorize("  ┌" + "─" * 60 + "┐", C.CYAN))
            for i, b in enumerate(backups, 1):
                tag = b["tag"] or "-"
                line_s = (
                    colorize(f" {i:>2} ", C.YELLOW + C.BOLD)
                    + colorize(f" {b['name'][:32]:<32}", C.WHITE)
                    + colorize(f" {tag}", C.DIM)
                )
                print(colorize("  │", C.CYAN) + line_s)
            print(colorize("  └" + "─" * 60 + "┘", C.CYAN))
        print()
        menu_block([
            ("n", "New backup", ""),
            ("r", "Restore", ""),
            ("d", "Delete", ""),
            ("0", "Back", ""),
        ])
        choice = ask("Select").strip().lower()
        if choice in ("", "0"):
            return
        if choice == "n":
            path = create_backup(ask("Tag", default="") or None)
            ok(path.name)
            pause()
            continue
        if choice in ("r", "d"):
            try:
                item = backups[int(ask("Number")) - 1]
            except (ValueError, IndexError):
                err("Invalid")
                pause()
                continue
            if choice == "r" and ask_yes_no(f"Restore {item['name']}?", False):
                s, m = restore_backup(item["name"])
                (ok if s else err)(m)
                if s:
                    apply_and_restart()
            elif choice == "d" and ask_yes_no(f"Delete {item['name']}?", False):
                shutil.rmtree(item["path"])
                ok("Deleted")
            pause()


def install_command():
    """Write /usr/local/bin/exrelay that runs this package."""
    pkg = Path(__file__).resolve().parent
    launcher = (
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"sys.path.insert(0, {str(pkg.parent)!r})\n"
        "from exrelay.__main__ import main\n"
        "main()\n"
    )
    INSTALL_PATH.write_text(launcher)
    INSTALL_PATH.chmod(0o755)
    return True, str(INSTALL_PATH)


def main_menu():
    while True:
        clear_screen()
        screen(f"eXrelay   v{VERSION}", "TCP/UDP port-forward relay")
        xray = find_xray_binary()
        active = service_is_active()
        servers = list_servers()
        enabled = sum(1 for s in servers if s.get("enabled", True))
        ip = get_public_ip() or "(unknown)"
        print()
        status_row("Xray", xray or "NOT FOUND", good=bool(xray))
        status_row("Service", "active" if active else "inactive", good=active)
        status_row("Relays", f"{enabled} enabled  /  {len(servers)} total")
        status_row("Public IP", ip, good=ip != "(unknown)")
        print()
        menu_block([
            ("1", "Add relay", "paste a share link"),
            ("2", "List relays", "details, link, quick test"),
            ("3", "Edit relay", ""),
            ("4", "Delete relay", ""),
            ("5", "User links", "all enabled relays"),
            ("6", "Apply + restart", "write config.json"),
            ("7", "Service", "start / stop / test"),
            ("8", "Backups", ""),
            ("9", "Settings", ""),
            ("10", "Test server", "location + speed"),
            ("0", "Exit", ""),
        ])
        choice = ask("Select").strip()
        actions = {
            "1": flow_add,
            "2": flow_list,
            "3": flow_edit,
            "4": flow_delete,
            "5": flow_links,
            "7": flow_service,
            "8": flow_backups,
            "9": flow_settings,
            "10": flow_test,
        }
        if choice == "0":
            info("Goodbye.")
            return
        if choice == "6":
            apply_and_restart()
            pause()
            continue
        fn = actions.get(choice)
        if fn:
            fn()
        else:
            warn("Invalid option")
            pause()
