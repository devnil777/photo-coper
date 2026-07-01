import os
import psutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import fnmatch

def get_removable_drives():
    drives = []
    for partition in psutil.disk_partitions():
        if 'removable' in partition.opts or partition.fstype == '':
            # В Windows съемные диски обычно имеют опцию 'removable'
            # Если fstype пустой, это может быть неготов к работе диск, но мы его проверим
            if os.path.exists(partition.mountpoint):
                drives.append(partition.mountpoint)

    # Дополнительная проверка для Windows, если psutil не пометил как removable
    if os.name == 'nt':
        import ctypes
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if bitmask & 1:
                drive_path = f"{letter}:\\"
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
                # DRIVE_REMOVABLE = 2
                if drive_type == 2 and drive_path not in drives:
                    drives.append(drive_path)
            bitmask >>= 1

    return drives

def scan_drive(drive_path, extensions):
    files_by_date = defaultdict(list)
    dcim_path = Path(drive_path) / "DCIM"

    if not dcim_path.exists():
        # Если папки DCIM нет в корне, можно поискать её рекурсивно на небольшую глубину?
        # Но в ТЗ сказано "считаем что файлы должны быть в папке DCIM"
        return files_by_date

    for root, dirs, files in os.walk(dcim_path):
        for filename in files:
            if any(fnmatch.fnmatch(filename.lower(), ext.lower()) for ext in extensions):
                filepath = Path(root) / filename
                try:
                    stats = filepath.stat()
                    # Используем дату создания (ctime в Windows)
                    # На некоторых системах ctime - это время изменения метаданных,
                    # но в Windows это обычно именно дата создания.
                    dt = datetime.fromtimestamp(stats.st_ctime)
                    date_str = dt.strftime("%Y-%m-%d")
                    files_by_date[date_str].append({
                        "path": filepath,
                        "name": filename,
                        "size": stats.st_size,
                        "mtime": stats.st_mtime,
                        "ctime": stats.st_ctime,
                        "drive": drive_path
                    })
                except Exception as e:
                    print(f"Ошибка при чтении файла {filepath}: {e}")

    return files_by_date

def get_all_files(extensions):
    drives = get_removable_drives()
    all_files_by_date = defaultdict(list)

    for drive in drives:
        drive_files = scan_drive(drive, extensions)
        for date, files in drive_files.items():
            all_files_by_date[date].extend(files)

    return all_files_by_date

def check_name_collisions(files):
    name_counts = defaultdict(int)
    for f in files:
        name_counts[f['name'].lower()] += 1

    collisions = [name for name, count in name_counts.items() if count > 1]
    return collisions
