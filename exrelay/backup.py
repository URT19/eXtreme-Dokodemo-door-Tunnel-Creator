"""Config/data backups."""
import os
import shutil

from .constants import BACKUP_DIR, CONFIG_DIR, DATA_DIR, VERSION
from .utils import now_iso, now_stamp, read_json, write_json


def create_backup(tag=None):
    stamp = now_stamp()
    path = BACKUP_DIR / f"{stamp}{'_' + tag if tag else ''}"
    path.mkdir(parents=True, exist_ok=True)
    if CONFIG_DIR.exists():
        shutil.copytree(CONFIG_DIR, path / "xray", dirs_exist_ok=True)
    if DATA_DIR.exists():
        shutil.copytree(DATA_DIR, path / "data", dirs_exist_ok=True)
    write_json(path / "meta.json", {"created_at": now_iso(), "version": VERSION, "tag": tag or ""})
    return path


def list_backups():
    if not BACKUP_DIR.exists():
        return []
    items = []
    for p in sorted(BACKUP_DIR.iterdir(), reverse=True):
        if not p.is_dir():
            continue
        meta = read_json(p / "meta.json", {}) or {}
        size = 0
        for root, _, files in os.walk(p):
            for f in files:
                try:
                    size += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        items.append({"name": p.name, "path": str(p), "tag": meta.get("tag", ""), "size": size})
    return items


def restore_backup(name):
    src = BACKUP_DIR / name
    if not src.exists():
        return False, "Backup not found"
    create_backup(tag="before_restore")
    if (src / "xray").exists():
        if CONFIG_DIR.exists():
            shutil.rmtree(CONFIG_DIR)
        shutil.copytree(src / "xray", CONFIG_DIR)
    if (src / "data").exists():
        if DATA_DIR.exists():
            shutil.rmtree(DATA_DIR)
        shutil.copytree(src / "data", DATA_DIR)
    return True, "Restored"
