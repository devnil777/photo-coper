import ctypes
import os
import sys
from ctypes import wintypes


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


def _parse_guid(s):
    g = _GUID()
    ctypes.windll.ole32.CLSIDFromString(ctypes.c_wchar_p(s), ctypes.byref(g))
    return g


_CLSID_TASKBAR_LIST = _parse_guid("{56FDF344-FD6D-11d0-958A-006097C9A090}")
_IID_ITASKBAR_LIST3 = _parse_guid("{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}")

# TBPFLAG values
_TBPF_NOPROGRESS = 0x0
_TBPF_INDETERMINATE = 0x1
_TBPF_NORMAL = 0x2
_TBPF_ERROR = 0x4
_TBPF_PAUSED = 0x8

# vtable offsets for ITaskbarList3 (zero-based)
# IUnknown: 0=QI, 1=AddRef, 2=Release
# ITaskbarList: 3=HrInit, 4=AddTab, 5=DeleteTab, 6=ActivateTab, 7=SetActiveAlt
# ITaskbarList2: 8=MarkFullscreenWindow
# ITaskbarList3: 9=SetProgressValue, 10=SetProgressState
_VT_HRINIT = 3
_VT_SET_PROGRESS_VALUE = 9
_VT_SET_PROGRESS_STATE = 10


class _COMEngine:
    def __init__(self):
        self._hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        self._ptr = None
        if not self._hwnd:
            return

        ole32 = ctypes.oledll.ole32
        ole32.CoInitialize(None)

        ptr = ctypes.c_void_p()
        hr = ole32.CoCreateInstance(
            ctypes.byref(_CLSID_TASKBAR_LIST),
            None,
            1,
            ctypes.byref(_IID_ITASKBAR_LIST3),
            ctypes.byref(ptr),
        )
        if hr != 0 or not ptr.value:
            return
        self._ptr = ptr

        fn = self._vt(_VT_HRINIT, wintypes.HRESULT)
        fn(self._ptr)

    def _vt(self, idx, restype, *argtypes):
        base = ctypes.c_void_p.from_address(self._ptr.value).value
        ps = ctypes.sizeof(ctypes.c_void_p)
        addr = ctypes.c_void_p.from_address(base + idx * ps).value
        return ctypes.CFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(addr)

    def update(self, current, total):
        if not self._ptr or total <= 0:
            return
        fn = self._vt(
            _VT_SET_PROGRESS_VALUE,
            wintypes.HRESULT,
            wintypes.HANDLE,
            ctypes.c_ulonglong,
            ctypes.c_ulonglong,
        )
        fn(self._ptr, self._hwnd, current, total)

    def set_state(self, state):
        if not self._ptr:
            return
        flags = {
            "normal": _TBPF_NORMAL,
            "error": _TBPF_ERROR,
            "paused": _TBPF_PAUSED,
            "indeterminate": _TBPF_INDETERMINATE,
            "noprogress": _TBPF_NOPROGRESS,
        }
        fn = self._vt(_VT_SET_PROGRESS_STATE, wintypes.HRESULT, wintypes.HANDLE, wintypes.UINT)
        fn(self._ptr, self._hwnd, flags.get(state, _TBPF_NOPROGRESS))

    def set_title(self, title):
        ctypes.windll.kernel32.SetConsoleTitleW(title)

    def close(self):
        self.set_state("noprogress")
        if self._ptr:
            ctypes.oledll.ole32.CoUninitialize()
            self._ptr = None


class _OSCEngine:
    def __init__(self):
        self._can_osc = False
        try:
            kernel32 = ctypes.windll.kernel32
            h = kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(h, ctypes.byref(mode)):
                kernel32.SetConsoleMode(h, mode.value | 0x0004)
                self._can_osc = True
        except Exception:
            pass

    def update(self, current, total):
        if not self._can_osc or total <= 0:
            return
        pct = int(current / total * 100)
        pct = min(100, max(0, pct))
        sys.stdout.write(f"\x1b]9;4;1;{pct}\x07")
        sys.stdout.flush()

    def set_state(self, state):
        if not self._can_osc:
            return
        mapping = {"normal": 1, "error": 2, "indeterminate": 3, "paused": 4, "noprogress": 0}
        sys.stdout.write(f"\x1b]9;4;{mapping.get(state, 0)}\x07")
        sys.stdout.flush()

    def set_title(self, title):
        if not self._can_osc:
            return
        sys.stdout.write(f"\x1b]0;{title}\x07")
        sys.stdout.flush()

    def close(self):
        self.set_state("noprogress")


def _is_wt():
    if "WT_SESSION" in os.environ:
        return True
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetClassNameW(hwnd, buf, 256)
        if buf.value == "PseudoConsoleWindow":
            return True
    try:
        import psutil
        for p in psutil.Process(os.getpid()).parents():
            if p.name().lower() in ("windowsterminal.exe", "wt.exe"):
                return True
    except Exception:
        pass
    return False


class TaskbarProgress:
    def __init__(self):
        if _is_wt():
            self._engine = _OSCEngine()
        else:
            self._engine = _COMEngine()

    def update(self, current, total):
        self._engine.update(current, total)

    def set_state(self, state):
        self._engine.set_state(state)

    def set_title(self, title):
        self._engine.set_title(title)

    def close(self):
        self._engine.close()
