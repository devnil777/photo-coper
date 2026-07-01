import unittest
import os
import shutil
import tempfile
from pathlib import Path
from photo_coper import scanner, copier

class TestPhotoCoper(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / "drive1" / "DCIM" / "100CANON"
        self.source_dir.mkdir(parents=True)

        self.dest_dir = Path(self.test_dir) / "dest"
        self.dest_dir.mkdir()

        # Создаем тестовые файлы
        self.file1 = self.source_dir / "IMG_0001.CR2"
        self.file1.write_text("dummy content 1")

        self.file2 = self.source_dir / "IMG_0002.CR2"
        self.file2.write_text("dummy content 2")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan_drive(self):
        files_by_date = scanner.scan_drive(Path(self.test_dir) / "drive1", ["*.cr2"])
        self.assertEqual(len(files_by_date), 1)
        date = list(files_by_date.keys())[0]
        self.assertEqual(len(files_by_date[date]), 2)

    def test_name_collisions(self):
        files = [
            {'name': 'img.cr2'},
            {'name': 'IMG.CR2'},
            {'name': 'photo.cr2'}
        ]
        collisions = scanner.check_name_collisions(files)
        self.assertEqual(len(collisions), 1)
        self.assertEqual(collisions[0], 'img.cr2')

    def test_copier_basic(self):
        cp = copier.FileCopier(conflict_mode='none')
        src_info = {
            'path': self.file1,
            'name': 'IMG_0001.CR2',
            'size': self.file1.stat().st_size,
            'mtime': self.file1.stat().st_mtime,
            'ctime': self.file1.stat().st_ctime
        }
        res = cp.copy_file(src_info, self.dest_dir)
        self.assertEqual(res, "copied")
        self.assertTrue((self.dest_dir / "IMG_0001.CR2").exists())

    def test_copier_skip_identical(self):
        cp = copier.FileCopier(conflict_mode='none')
        src_info = {
            'path': self.file1,
            'name': 'IMG_0001.CR2',
            'size': self.file1.stat().st_size,
            'mtime': self.file1.stat().st_mtime,
            'ctime': self.file1.stat().st_ctime
        }
        cp.copy_file(src_info, self.dest_dir)
        res = cp.copy_file(src_info, self.dest_dir)
        self.assertEqual(res, "skipped")

if __name__ == '__main__':
    unittest.main()
