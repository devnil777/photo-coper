# photo-coper — AGENTS.md

Windows-only Python TUI app that copies photos from camera SD cards (DCIM folders) to a hard drive.  
Single package, no monorepo complexity.

## Commands

- Run: `python -m photo_coper.main`
- Test (single file, unittest): `python tests.py`
- Build EXE: `pyinstaller --onefile --name photo-coper photo_coper/main.py` or `build.bat`
- Install: `pip install -r requirements.txt`

## Architecture

- `photo_coper/` package with 5 modules:
  - `main.py` — entry point, orchestrates the 7-step workflow
  - `config.py` — YAML config at `~/.photo-coper.yaml` (auto-created on first run)
  - `scanner.py` — enumerates removable drives, scans `DCIM` folders, groups files by date, detects name collisions
  - `copier.py` — `FileCopier` class with conflict resolution (date/number subdirs), Windows taskbar progress, post-copy verification
  - `tui.py` — `questionary`-based screens (checkboxes, selects, confirms, path input)
- No `__main__.py` — run via explicit `python -m photo_coper.main`
- Russian-only UI strings (not localizable)

## Testing

- Single file `tests.py` using `unittest` — no test runner/discovery needed
- Only covers `scanner` and `copier` (no TUI tests)
- No external fixtures — uses `tempfile.mkdtemp()`

## Windows-specific

- Drive detection: `psutil` + `ctypes.windll.kernel32` fallback for removable drives
- Taskbar progress: `comtypes` + `pywin32` (silently degrades if unavailable)
- Build EXE: `build.bat` → `pyinstaller --onefile` → `dist/photo-coper.exe`

## Toolchain

- No linter, typechecker, or formatter configured — none expected
- No CI workflows
- No code generation or migrations

## Config

- Location: `~/.photo-coper.yaml`
- Key fields: `extensions`, `destination_directories`, `lr_template_path`, `lightroom_exe`
- Extensions default: `*.cr2, *.cr3, *.raf, *.jpg`
