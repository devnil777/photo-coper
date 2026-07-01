import os
import shutil
import time
from pathlib import Path

# Попытка импорта win32gui для прогресса в таскбаре
try:
    import win32gui
    import win32api
    import win32con
    import comtypes.client
    # ITaskbarList3 GUIDs
    CLSID_TaskbarList = "{56FDF344-FD6D-11d0-958A-006097C9A090}"
    IID_ITaskbarList3 = "{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}"
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class FileCopier:
    def __init__(self, conflict_mode='date', delete_after=False):
        self.conflict_mode = conflict_mode
        self.delete_after = delete_after
        self.taskbar = None
        self.hwnd = None

        if HAS_WIN32:
            try:
                # Попробуем инициализировать COM для таскбара
                comtypes.CoInitialize()
                self.taskbar = comtypes.client.CreateObject(CLSID_TaskbarList, interface=None)
                # Пытаемся найти окно консоли
                self.hwnd = win32gui.GetForegroundWindow()
            except Exception:
                self.taskbar = None

    def copy_file(self, src_info, dest_dir):
        src = src_info['path']
        filename = src_info['name']

        # Определяем подпапку
        if self.conflict_mode == 'date':
            date_str = src_info['ctime_str']
            target_dir = Path(dest_dir) / date_str
        elif self.conflict_mode == 'number':
            target_dir = Path(dest_dir) / src_info['subdir']
        else:
            target_dir = Path(dest_dir)

        os.makedirs(target_dir, exist_ok=True)
        dst = target_dir / filename

        # Проверка на идентичность
        if dst.exists():
            dst_stat = dst.stat()
            if dst_stat.st_size == src_info['size'] and abs(dst_stat.st_mtime - src_info['mtime']) < 1:
                return "skipped"

        try:
            shutil.copy2(src, dst)

            # Проверка после копирования
            dst_stat = dst.stat()
            if dst_stat.st_size != src_info['size']:
                raise Exception("Размер файла после копирования не совпадает")

            return "copied"
        except Exception as e:
            raise Exception(f"Ошибка при копировании {src} -> {dst}: {e}")

    def update_taskbar_progress(self, current, total):
        if self.taskbar and self.hwnd:
            try:
                # ITaskbarList3::SetProgressValue (метод индекс 9)
                # Через comtypes это выглядит примерно так:
                self.taskbar.SetProgressValue(self.hwnd, current, total)
            except Exception:
                pass

    def set_taskbar_state(self, state="normal"):
        if self.taskbar and self.hwnd:
            try:
                # 0: No progress, 2: Normal, 4: Error, 8: Indeterminate
                flag = 2 if state == "normal" else (4 if state == "error" else 0)
                self.taskbar.SetProgressState(self.hwnd, flag)
            except Exception:
                pass

def copy_structure(src_pattern_dir, dst_dir):
    if not src_pattern_dir or not os.path.exists(src_pattern_dir):
        return

    src_path = Path(src_pattern_dir)
    dst_path = Path(dst_dir)

    for item in src_path.rglob('*'):
        rel_path = item.relative_to(src_path)
        target_path = dst_path / rel_path

        if item.is_dir():
            os.makedirs(target_path, exist_ok=True)
        else:
            if not target_path.exists():
                os.makedirs(target_path.parent, exist_ok=True)
                shutil.copy2(item, target_path)
