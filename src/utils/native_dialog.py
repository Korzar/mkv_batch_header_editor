"""
Native Windows dialog helpers for multi-folder selection with Quick Access support.
"""

import sys
from typing import List

if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes, c_long, POINTER, c_void_p, c_uint32, byref

    windll_ole32 = ctypes.windll.ole32
    windll_ole32.CoTaskMemFree.argtypes = [c_void_p]
    windll_ole32.CoTaskMemFree.restype = None

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", wintypes.BYTE * 8),
        ]

    def _str_to_guid(s: str) -> GUID:
        guid = GUID()
        windll_ole32.CLSIDFromString(ctypes.c_wchar_p(s), byref(guid))
        return guid

    # CLSID_FileOpenDialog = {DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7}
    CLSID_FileOpenDialog = _str_to_guid('{DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7}')
    # IID_IFileOpenDialog = {D57C7288-D4AD-4768-BE02-9D969532D960}
    # Note: 42F85136-DB7E-439C-85F1-E4075D135FC8 is IFileDialog (which lacks GetResults at index 27)
    # D57C7288-D4AD-4768-BE02-9D969532D960 is IFileOpenDialog (which implements GetResults)
    IID_IFileOpenDialog = _str_to_guid('{D57C7288-D4AD-4768-BE02-9D969532D960}')


def pick_multiple_folders(parent_hwnd: int = 0, title: str = "Select Folder(s)") -> List[str]:
    """
    Opens the native Windows Explorer dialog configured to allow selecting
    one or multiple folders at once, with full Quick Access and sidebar navigation.
    Returns a list of selected absolute directory paths, or empty list if cancelled.
    """
    if sys.platform != 'win32':
        return []

    need_uninit = False
    hr_init = windll_ole32.CoInitialize(None)
    if hr_init in (0, 1):
        need_uninit = True

    try:
        pDialog = c_void_p()
        hr = windll_ole32.CoCreateInstance(
            byref(CLSID_FileOpenDialog),
            None,
            1,  # CLSCTX_INPROC_SERVER
            byref(IID_IFileOpenDialog),
            byref(pDialog),
        )
        if hr != 0 or not pDialog.value:
            raise RuntimeError(f"CoCreateInstance failed with hr={hex(hr & 0xFFFFFFFF)}")

        vtable = ctypes.cast(pDialog, POINTER(POINTER(c_void_p))).contents
        # Use c_long return types so ctypes does not raise automatic OSError on non-zero codes
        ReleaseDialog = ctypes.WINFUNCTYPE(c_long, c_void_p)(vtable[2])
        Show = ctypes.WINFUNCTYPE(c_long, c_void_p, wintypes.HWND)(vtable[3])
        SetOptions = ctypes.WINFUNCTYPE(c_long, c_void_p, c_uint32)(vtable[9])
        GetOptions = ctypes.WINFUNCTYPE(c_long, c_void_p, POINTER(c_uint32))(vtable[10])
        SetTitle = ctypes.WINFUNCTYPE(c_long, c_void_p, wintypes.LPCWSTR)(vtable[17])
        GetResult = ctypes.WINFUNCTYPE(c_long, c_void_p, POINTER(c_void_p))(vtable[20])
        GetResults = ctypes.WINFUNCTYPE(c_long, c_void_p, POINTER(c_void_p))(vtable[27])

        opts = c_uint32()
        GetOptions(pDialog, byref(opts))
        # 32 = FOS_PICKFOLDERS, 64 = FOS_FORCEFILESYSTEM, 512 = FOS_ALLOWMULTISELECT
        SetOptions(pDialog, opts.value | 32 | 64 | 512)

        if title:
            SetTitle(pDialog, title)

        hwnd_val = wintypes.HWND(parent_hwnd) if parent_hwnd else wintypes.HWND(0)
        hr_show = Show(pDialog, hwnd_val)
        selected_folders = []

        # Check for user cancellation (ERROR_CANCELLED = 0x800704C7 / -2147023673)
        if hr_show in (0x800704C7, -2147023673):
            ReleaseDialog(pDialog)
            return []

        if hr_show != 0:
            ReleaseDialog(pDialog)
            raise RuntimeError(f"IFileOpenDialog.Show failed with hr={hex(hr_show & 0xFFFFFFFF)}")

        # First try multi-selection via GetResults (index 27 on IFileOpenDialog)
        pArray = c_void_p()
        hr_results = GetResults(pDialog, byref(pArray))
        if hr_results == 0 and pArray.value:
            array_vtable = ctypes.cast(pArray, POINTER(POINTER(c_void_p))).contents
            ReleaseArray = ctypes.WINFUNCTYPE(c_long, c_void_p)(array_vtable[2])
            GetCount = ctypes.WINFUNCTYPE(c_long, c_void_p, POINTER(c_uint32))(array_vtable[7])
            GetItemAt = ctypes.WINFUNCTYPE(c_long, c_void_p, c_uint32, POINTER(c_void_p))(array_vtable[8])

            count = c_uint32()
            if GetCount(pArray, byref(count)) == 0:
                for i in range(count.value):
                    pItem = c_void_p()
                    if GetItemAt(pArray, i, byref(pItem)) == 0 and pItem.value:
                        item_vtable = ctypes.cast(pItem, POINTER(POINTER(c_void_p))).contents
                        ReleaseItem = ctypes.WINFUNCTYPE(c_long, c_void_p)(item_vtable[2])
                        GetDisplayName = ctypes.WINFUNCTYPE(
                            c_long, c_void_p, c_uint32, POINTER(c_void_p)
                        )(item_vtable[5])

                        pName = c_void_p()
                        # 0x80058000 = SIGDN_FILESYSPATH
                        hr_name = GetDisplayName(pItem, 0x80058000, byref(pName))
                        if hr_name != 0 or not pName.value:
                            # Fallback to SIGDN_DESKTOPABSOLUTEPARSING (0x80028000)
                            hr_name = GetDisplayName(pItem, 0x80028000, byref(pName))

                        if hr_name == 0 and pName.value:
                            folder_path = ctypes.wstring_at(pName.value)
                            if folder_path:
                                selected_folders.append(folder_path)
                            windll_ole32.CoTaskMemFree(pName)

                        ReleaseItem(pItem)

            ReleaseArray(pArray)
        else:
            # Fallback to single item via GetResult (index 20)
            pItem = c_void_p()
            if GetResult(pDialog, byref(pItem)) == 0 and pItem.value:
                item_vtable = ctypes.cast(pItem, POINTER(POINTER(c_void_p))).contents
                ReleaseItem = ctypes.WINFUNCTYPE(c_long, c_void_p)(item_vtable[2])
                GetDisplayName = ctypes.WINFUNCTYPE(
                    c_long, c_void_p, c_uint32, POINTER(c_void_p)
                )(item_vtable[5])

                pName = c_void_p()
                hr_name = GetDisplayName(pItem, 0x80058000, byref(pName))
                if hr_name != 0 or not pName.value:
                    hr_name = GetDisplayName(pItem, 0x80028000, byref(pName))

                if hr_name == 0 and pName.value:
                    folder_path = ctypes.wstring_at(pName.value)
                    if folder_path:
                        selected_folders.append(folder_path)
                    windll_ole32.CoTaskMemFree(pName)

                ReleaseItem(pItem)

        ReleaseDialog(pDialog)
        return selected_folders
    finally:
        if need_uninit:
            try:
                windll_ole32.CoUninitialize()
            except Exception:
                pass
