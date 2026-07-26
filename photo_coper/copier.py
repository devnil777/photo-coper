import os
import shutil
from pathlib import Path
from photo_coper.taskbar import TaskbarProgress

class FileCopier:
    def __init__(self, conflict_mode='date', delete_after=False):
        self.conflict_mode = conflict_mode
        self.delete_after = delete_after
        self._progress = TaskbarProgress()

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
        self._progress.update(current, total)

    def set_taskbar_state(self, state="normal"):
        self._progress.set_state(state)

    def set_title(self, title: str):
        self._progress.set_title(title)

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
